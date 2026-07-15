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
Haar**. Ofrece `FaceDetectorYN` (YuNet, basado en DNN) en su lugar, que es mejor
detector, pero:
- pide descargar y versionar un modelo ONNX aparte,
- y en Raspberry Pi no hay wheels: la 5 habría que compilarla, que en una 3B son
  horas.

Por eso `requirements.txt` fija `opencv-python>=4.8,<5`. Si algún día se salta a
la 5, hay que migrar `lavi/vision/detector.py` a `FaceDetectorYN` y bundlear el
modelo. `detector.py` detecta este caso y falla con un mensaje explícito en vez
de con un `AttributeError` a secas.

### Por qué Haar y no MediaPipe
El destino es una Pi 3B: Cortex-A53, 1GB de RAM. MediaPipe no tiene wheels para
32 bits, y en ese SoC va a pocos FPS. Haar viene dentro de OpenCV, no descarga
modelos y a 320x240 corre de sobra.

El precio de Haar es que **pide cara de frente**: si la persona mira hacia abajo
o de perfil, no la ve. Para un kiosko al que uno se acerca a mirarlo, ese es
justo el caso bueno. Se comprobó en la mac: mirando al teclado da `caras 0`,
mirando a la pantalla engancha al instante.

## Arquitectura

```
lavi/
├── vision/
│   ├── __init__.py
│   ├── platform_detect.py  # mac / raspberry / linux
│   ├── camera.py           # OpenCVCamera, PiCamera, open_camera()
│   ├── detector.py         # FaceDetector (Haar)
│   ├── service.py          # VisionService: captura y detecta en un thread
│   └── preview.py          # CameraPreview: overlay colapsable
├── engine/
│   └── presence.py         # PresenceTracker: dormida / despierta
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
    "scale_factor": 1.2, "min_neighbors": 5, "min_face_fraction": 0.15
  },
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
      camino de `picamera2` está escrito a ciegas contra su API documentada.
- [ ] Medir RAM, CPU y ms de detección reales en la 3B, y revisar el objetivo de
      rendimiento con esos números.
- [ ] `pygame` y `cv2` traen cada uno su propia copia de `libSDL2`, y macOS avisa
      de clases duplicadas ("may cause mysterious crashes"). No dio problemas en
      las pruebas. En la Pi con `python3-opencv` de apt no debería pasar, porque
      usa la librería del sistema.
- [ ] Decidir qué hacer con los gestos: o hardware más potente (Pi 4/5), o
      heurística por movimiento en vez de landmarks.
- [ ] La posición de la cara ya se detecta pero no se usa. Es lo que habilitaría
      que la mirada siga a la persona.

## Cómo se verificó

- Detección de plataforma y cámara: contra la FaceTime HD real.
- Presencia: guionizando `has_face` sobre el `main()` real, comprobando que
  arranca dormida, despierta 0.47s después de aparecer la cara, cicla, se duerme
  al irse, y nunca muestra `sleepy` con alguien delante.
- Pop y parpadeo: capturando frames del `main()` real con driver de vídeo dummy y
  midiendo escala/alpha frame a frame.
