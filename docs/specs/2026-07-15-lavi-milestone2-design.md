# Lavi - Milestone 2: Cámara y Detección de Presencia

## Overview
Lavi deja de ciclar expresiones en el vacío y reacciona a si hay alguien delante:
duerme cuando no hay nadie y despierta cuando alguien se le pone enfrente. La
cámara se elige sola según la plataforma, de forma que el mismo código corre en
la mac (desarrollo) y en la Raspberry Pi (destino final).

## Alcance

Dentro:
- Detección de plataforma (mac / Raspberry Pi / otro Linux)
- Backend de cámara por plataforma
- Detección de rostro frontal
- Presencia con histéresis: dormida / despierta
- Preview colapsable de lo que ve la cámara, con cajas de detección

Fuera, y a propósito:
- **Gestos** (saludo, mostrar objetos). El spec del milestone 1 los listaba, pero
  en la práctica piden landmarks de mano, que es MediaPipe. Ver "Por qué no
  MediaPipe" más abajo. Quedan pendientes de decidir hardware.
- Reconocer *quién* es la persona. Aquí solo se detecta que hay una cara, no de
  quién es.
- Seguir la cara con la mirada. La posición de la cara ya se conoce y está
  disponible en `VisionService.snapshot()`, pero la cara no la usa todavía.

## Decisiones de dependencias

### OpenCV 4.x, no 5.x
`opencv-python` 5.0 **eliminó `cv2.CascadeClassifier` y dejó de traer los XML de
Haar**, y en Raspberry Pi no hay wheels de la 5: habría que compilarla, que en
una 3B son horas. Por eso `requirements.txt` fija `opencv-python>=4.8,<5`.

Lo que ya no vale es la razón por la que este spec descartaba YuNet. Decía que
`FaceDetectorYN` era cosa de OpenCV 5: **es falso**, está desde la 4.5.4 y
funciona en la 4.13 que hay instalada. Lo único que pide de verdad es el modelo
ONNX aparte, que ahora va versionado en `lavi/vision/models/`.

### Por qué YuNet y no Haar
Haar era la elección original, con el argumento de que un kiosko se mira de
frente y eso es justo lo que Haar sabe hacer. **Medido, no se sostiene.** Contra
la cámara real, con una persona delante moviéndose de forma normal:

| detector | enganche | ms/frame | tamaño |
|---|---|---|---|
| Haar frontal | **28%** | 2.3 | (viene en OpenCV) |
| YuNet | **96%** | 3.4 | 227 KB |

692 frames. El fallo de Haar es que **no es invariante a rotación**: basta con
ladear la cabeza para que deje de ver una cara que está de frente. En la práctica
Lavi se dormía con alguien delante, que es justo lo que la presencia debía
evitar. YuNet cuesta 1.1 ms más, irrelevante con `detect_fps` a 8, que da 125 ms
de presupuesto por detección.

Se midieron y descartaron, en vez de suponerlos:
- **`haarcascade_upperbody`**: 0% de enganche en 690 frames. No detectó a nadie
  ni una sola vez. Busca cabeza+hombros de alguien a distancia, y quien mira un
  kiosko de cerca le llena el encuadre con la cara.
- **`haarcascade_profileface`**: 2%.

### Por qué no MediaPipe (sigue en pie, por otro motivo)
El argumento viejo era que MediaPipe va lento en un Cortex-A53. El motivo real y
comprobable es más simple: **PyPI no publica ninguna wheel de MediaPipe para
Linux ARM**. Las únicas ARM son `macosx_11_0_arm64` y `win_arm64`. O sea que
MediaPipe instala en la mac de desarrollo y **no** en la Pi de destino, que es la
peor combinación posible: no te enteras hasta el día del montaje.

Lo que sí sirve es que OpenCV Zoo publica los modelos de MediaPipe **exportados a
ONNX**, que corren sobre el `cv2.dnn` que ya está instalado. Esa es la vía para
los gestos, y no el paquete `mediapipe`.

## Arquitectura

```
lavi/
├── vision/
│   ├── __init__.py
│   ├── platform_detect.py  # mac / raspberry / linux
│   ├── camera.py           # OpenCVCamera, PiCamera, open_camera()
│   ├── detector.py         # FaceDetector (YuNet, con Haar de respaldo)
│   ├── service.py          # VisionService: captura y detecta en un thread
│   ├── preview.py          # CameraPreview: overlay colapsable
│   └── models/
│       └── face_detection_yunet_2023mar.onnx   # 227 KB, versionado
├── engine/
│   ├── presence.py         # PresenceTracker: dormida / despierta
│   └── gaze.py             # GazeTracker: hacia dónde mira
```

### Detección de plataforma
`/proc/device-tree/model` es la fuente fiable en la Pi: contiene
`"Raspberry Pi 3 Model B Rev 1.2"`. Viene terminado en NUL, por eso se lee en
binario. Como respaldo, para imágenes de 64 bits que no exponen el device-tree,
se mira el SoC en `/proc/cpuinfo` (`bcm27*` / `bcm28*`).

### Cámara
| Plataforma | Backend | Notas |
|---|---|---|
| mac | `cv2.VideoCapture` | AVFoundation |
| Raspberry Pi | `picamera2` | cámara CSI, vía libcamera |
| Raspberry Pi sin picamera2 | `cv2.VideoCapture` | caída automática: webcam USB |
| otro Linux | `cv2.VideoCapture` | V4L2 |

Dos trampas que costaron descubrir y están resueltas en el código:
- **La cámara ignora la resolución que le pides.** La FaceTime HD devuelve
  640x480 aunque le pidas 320x240, así que `OpenCVCamera.read()` reescala igual.
- **Los primeros frames salen negros** mientras la cámara expone (se midió: brillo
  medio 9 en el frame 0, ~150 a partir del frame 5). De ahí `warmup_frames`.
- **`picamera2` llama "RGB888" a lo que numpy entrega como BGR.** El nombre
  engaña; el orden resultante es justo el que quiere OpenCV.

### Modelo de threads
La captura y la detección corren en un thread aparte (`VisionService`); el loop
de render solo lee el último resultado, que es instantáneo. Esto no es
sobreingeniería: `detectMultiScale` tarda decenas de ms y hacerlo dentro del loop
tiraría los 30 FPS en la Pi.

La detección va limitada a `detect_fps` (8 por defecto), más lenta que la captura
(15), porque no hace falta detectar en cada frame para decidir si hay alguien.

Si el thread revienta, guarda el error en vez de morir en silencio.

### Presencia
Histéresis en las dos direcciones, porque Haar pierde la cara en frames sueltos
aunque la persona siga ahí, y de vez en cuando saca un falso positivo:

- **Despertar**: cara vista de forma sostenida durante `wake_delay` (0.4s)
- **Dormirse**: sin ver a nadie durante `sleep_delay` (8s)

El debounce va **por tiempo y no por frames** a propósito: el loop de render va a
30 FPS y la detección a 8, así que contar frames contaría el mismo resultado
cuatro veces.

### Ciclo de expresiones
`sleepy` sale del ciclo y pasa a ser exclusivamente la cara de "no hay nadie". Si
también apareciera con alguien delante, no habría forma de distinguir los dos
estados de un vistazo.

```
sin nadie            -> sleepy (ciclo pausado)
llega alguien        -> surprised, y arranca el ciclo
        happy -> laugh -> wink -> love -> sad -> surprised -> happy ...
se va                -> sleepy (ciclo pausado)
```

### Preview
Colapsable, y **arranca colapsado**: es una herramienta de diagnóstico para
encuadrar la cámara y ver si la detección engancha, no parte de la cara. Se
alterna con la tecla `C`.

- Colapsado: solo un punto de estado (verde hay cara / gris no hay / rojo error)
- Expandido: vídeo + cajas de detección + plataforma, FPS y ms de detección

La imagen se reescala con OpenCV y no con pygame porque es bastante más barato.

## Config nueva (`config.json`)

```json
{
  "camera": {
    "enabled": true, "index": 0,
    "width": 320, "height": 240,
    "capture_fps": 15, "detect_fps": 8,
    "flip_horizontal": true, "warmup_frames": 10,
    "score_threshold": 0.7,
    "scale_factor": 1.2, "min_neighbors": 5, "min_face_fraction": 0.15
  },
  "gaze": { "enabled": true, "time_constant": 0.25 },
  "preview": {
    "enabled": true, "start_expanded": false,
    "position": "bottom_right", "width_fraction": 0.22,
    "margin_fraction": 0.02, "show_stats": true
  },
  "presence": { "wake_delay": 0.4, "sleep_delay": 8.0 }
}
```

`flip_horizontal` pone la imagen en espejo, para que la persona se vea como en un
espejo y las coordenadas del preview coincidan con lo que percibe.

## CLI

```
python lavi/main.py                # kiosko: pantalla completa, con cámara
python lavi/main.py --windowed     # ventana, para desarrollar en la mac
python lavi/main.py --preview      # arranca con el preview abierto
python lavi/main.py --no-camera    # sin cámara: se comporta como el milestone 1
```

Teclas: `C` alterna el preview, `ESC` sale.

## Degradación

Sin cámara, Lavi **no se cae ni se queda en negro**: avisa por stdout y se
comporta como en el milestone 1, ciclando expresiones siempre despierta. Un
kiosko no puede quedarse a oscuras porque no encuentre un `/dev/video0`.

## Rendimiento

Medido en la mac (M-series, 320x240):
| Métrica | Valor |
|---|---|
| Detección Haar | 1.6 - 19 ms |
| Captura | 13 - 17 FPS |
| RSS pico | **252 MB** |

### El objetivo de RAM del milestone 1 ya no vale
El spec del milestone 1 fijaba **<50MB de RAM**. Con la cámara eso es
inalcanzable: solo importar OpenCV ya son ~17MB, y el stack de captura se dispara
a 252MB de pico en la mac. En la Pi será menos (picamera2 es más ligero que
AVFoundation), pero muy por encima de 50MB igualmente.

En una Pi 3B de 1GB, ~200MB es asumible pero deja de ser holgado. **Falta medirlo
en la Pi de verdad**; si aprieta, las palancas son bajar `detect_fps`, bajar la
resolución de captura, o usar `python3-opencv` de apt en vez de la wheel de pip.

## Pendiente / riesgos

- [ ] **Nada de esto se ha probado en la Pi.** Todo lo verificado es en mac. El
      camino de `picamera2` está escrito a ciegas contra su API documentada. Ya
      van tres decisiones seguidas que acaban aquí (RAM, YuNet, gestos): esto ha
      dejado de ser un pendiente y es *el* bloqueo del proyecto.
- [ ] Medir RAM, CPU y ms de detección reales en la 3B, y revisar el objetivo de
      rendimiento con esos números. YuNet es una red, no un cascade: en un
      Cortex-A53 los 3.4 ms de la mac serán bastantes más.
- [ ] `pygame` y `cv2` traen cada uno su propia copia de `libSDL2`, y macOS avisa
      de clases duplicadas ("may cause mysterious crashes"). No dio problemas en
      las pruebas. En la Pi con `python3-opencv` de apt no debería pasar, porque
      usa la librería del sistema.
- [x] ~~La posición de la cara ya se detecta pero no se usa.~~ Hecho:
      `GazeTracker` mueve los ojos hacia la persona.
- [ ] **Gestos**: la vía está abierta y medida, falta decidir. OpenCV Zoo publica
      los modelos de MediaPipe en ONNX, o sea que corren sobre `cv2.dnn` sin el
      paquete `mediapipe` y por tanto sí van en ARM. Medido en la mac:
      `palm_detection` 10.4 ms + `handpose` (21 landmarks) 5.9 ms = **16.3 ms**,
      5.4x YuNet, y 7.6 MB de modelos. Cabe en los 125 ms de presupuesto en la
      mac; **en la 3B es una incógnita seria**. Con 21 landmarks, "amor y paz"
      es contar dedos extendidos y el saludo es seguir la muñeca en el tiempo.
- [ ] **Lavi parece un programa, no un ser vivo.** El ciclo por temporizador la
      delata: cambia de cara sola cada pocos segundos sin que pase nada. Y el pop
      es un síntoma, no una decisión estética — existe para tapar el corte de
      cambiar de objeto `Face`. Mientras la cara sea una colección de siete caras
      discretas, habrá cortes que tapar. Lo que pide el diseño es lo contrario:
      un estado de reposo tranquilo con micro-movimiento (respiración, parpadeo,
      derivas de mirada) y expresiones que sean **reacciones a algo**, morfando
      de forma continua en vez de conmutando.

## Cómo se verificó

- Detección de plataforma y cámara: contra la FaceTime HD real.
- Detectores: 690-692 frames contra la cámara real con una persona delante
  moviéndose. Haar 28%, YuNet 96%, profile 2%, upperbody 0%. De ahí el cambio a
  YuNet, y de ahí que upperbody se descartara en vez de integrarse.
- MediaPipe: consultando las wheels que publica PyPI, no suponiendo. Ninguna para
  Linux ARM.
- Mirada: comprobando el mapeo (cara a la izquierda -> gaze -0.75, a la derecha
  -> +0.74, sin cara -> vuelve a 0) y que el suavizado no copia los saltos de
  golpe (0.09 del recorrido en el primer frame).
- Presencia: guionizando `has_face` sobre el `main()` real, comprobando que
  arranca dormida, despierta 0.47s después de aparecer la cara, cicla, se duerme
  al irse, y nunca muestra `sleepy` con alguien delante.
- Pop y parpadeo: capturando frames del `main()` real con driver de vídeo dummy y
  midiendo escala/alpha frame a frame.
