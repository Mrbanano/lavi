# Lavi - Milestone 3: Que parezca un ser vivo

## Overview
Lavi deja de ser una colección de caras que rotan solas y pasa a comportarse como
un bicho: está tranquila, espera, te sigue con la mirada, y se emociona **cuando
pasa algo**. La diferencia no es tener más caras; es no tenerlas.

## El diagnóstico

Hoy Lavi tiene siete objetos `Face` (`happy`, `sad`, `wink`...), cada uno con su
`setup()` y su `draw()`, y un `StateMachine` con un temporizador que los rota cada
`expression_duration` segundos. Eso la delata de dos maneras, y las dos las cazó
el usuario mirándola treinta segundos:

**1. Cambia de cara sin motivo.** Un ser vivo no pasa de contento a triste porque
hayan pasado 3 segundos. Cambia porque le ha pasado algo. El ciclo por
temporizador es literalmente un programa recorriendo una lista, y se nota.

**2. El zoom in/out al cambiar.** No es una decisión estética: es un **parche**.
El `main` cambia el objeto `Face` de golpe, y eso sería un corte visible de un
frame. El pop encoge la cara y le baja el alpha justo en el instante del
cambiazo (`POP_SWAP_POINT = 0.42`) para **tapar el corte**.

Y aquí está lo importante: **mientras la cara sea una colección de objetos
discretos, habrá un corte que tapar**. Quitar el pop sin tocar lo de abajo solo
deja el salto al aire. El pop es el síntoma; la colección de caras es la
enfermedad.

## Alcance

Dentro:
- Rostro de rasgos continuos: se interpola, no se conmuta
- Vida en reposo: respiración, parpadeo con ritmo natural, derivas de mirada
- Expresiones como **reacciones** a eventos, con decaimiento de vuelta a la calma
- Gestos de mano (saludo y "amor y paz") como fuente de esos eventos

Fuera:
- Reconocer *quién* es la persona
- Voz o sonido
- Que la mirada distinga entre varias personas (se sigue mirando a la más grande)

## La arquitectura nueva

### El rostro se vuelve continuo
Un solo `Face`. En vez de subclases con `draw()` propio, un vector de rasgos que
se puede interpolar:

| rasgo | rango | qué hace |
|---|---|---|
| `mouth_curve` | -1 .. +1 | -1 boca hacia abajo, +1 sonrisa |
| `mouth_open` | 0 .. 1 | de línea a boca abierta |
| `eye_open` | 0 .. 1 | de cerrado a abierto |
| `eye_widen` | 0 .. 1 | ojo abierto de más: sorpresa |
| `gaze_x`, `gaze_y` | -1 .. 1 | ya existe, se queda |

Las "expresiones" dejan de ser clases y pasan a ser **datos**: un dict de nombre
a valores de esos rasgos. `happy` no es un objeto, es
`{mouth_curve: 0.8, eye_open: 0.9}`.

Cada rasgo persigue su objetivo con suavizado exponencial por tiempo, igual que
ya hace `GazeTracker`. **La transición deja de existir como concepto**: no hay
transición, hay rasgos moviéndose. Y por tanto no hay corte, y por tanto no hace
falta pop.

`eye_open` lo escriben dos cosas a la vez, y se componen multiplicando:
`eye_open_final = eye_open_emocion * (1 - blink)`. Así se puede parpadear estando
triste sin que una cosa pise a la otra.

### El temporizador se muere
`StateMachine` pierde el ciclo. En su lugar, un `Mood` con **decaimiento**:

- Hay un estado de reposo (`calma`) que es donde Lavi vive por defecto.
- Un evento **empuja** el mood a una emoción con una intensidad.
- La intensidad **decae sola** con el tiempo, y el rostro vuelve a la calma.

Eso es lo que hace que parezca un ser y no una máquina de estados: no se queda
clavada en "contenta", se le va pasando la alegría.

```
                    (nada, mucho rato)
     calma  ---------------------------> dormida
       ^                                    |
       | decae                              | llega alguien
       |                                    v
   emoción  <------------------------  sorpresa -> contenta
       ^
       | te saluda -> emocionada
       | amor y paz -> enamorada
```

### Vida en reposo
Es el 90% de que algo parezca vivo, y hoy no hay nada de esto. En reposo, sin
que pase absolutamente nada:

- **Respiración**: oscilación de escala mínima, amplitud ~0.015, periodo ~4s.
  Tan sutil que no se ve mirándola, pero se nota si se quita.
- **Parpadeo**: ya existe. Cambia el ritmo: intervalos aleatorios de 2-6s en vez
  de regulares, y algún parpadeo doble ocasional.
- **Derivas de mirada**: sin nadie delante, la mirada no se queda clavada al
  frente: deriva despacio a puntos cercanos, como quien mira sin mirar.

La respiración va sobre la escala, que es justo el canal que hoy ocupa el pop.
Otra razón para que el pop se vaya: molesta.

### Los gestos alimentan las emociones
Sin gestos, las únicas reacciones posibles son "llega alguien" y "se va", que se
quedan cortas para "emocionarse cuando lo saludas". Por eso los gestos entran
aquí y no en un milestone aparte: son la **causa** que le falta al sistema.

- **Saludo** (mover la mano) -> emocionada
- **Amor y paz** (✌️) -> enamorada (ojos de corazón)

Vía OpenCV Zoo en ONNX sobre `cv2.dnn`, **no** el paquete `mediapipe`: PyPI no
publica wheel de MediaPipe para Linux ARM, o sea que instalaría en la mac de
desarrollo y no en la Pi de destino.

Medido en la mac, 320x240:

| modelo | coste | tamaño |
|---|---|---|
| `palm_detection` | 10.4 ms | 3.7 MB |
| `handpose` (21 landmarks, por mano) | 5.9 ms | 3.9 MB |
| **total** | **16.3 ms** | 7.6 MB |

Con 21 landmarks, "amor y paz" es contar dedos extendidos (índice y corazón
arriba, el resto plegados) y el saludo es seguir la muñeca en el tiempo: un
vaivén horizontal de N ciclos en M segundos.

## Lo que se muere

Merece la pena decirlo explícito, porque es borrar código que funciona:

- El ciclo por temporizador de `StateMachine`.
- `_update_pop` y `_update_fade` del `Animator`, y `POP_SWAP_POINT` y
  `should_swap()` con ellos. El swap deja de tener sentido: no hay nada que
  intercambiar.
- Las siete subclases de `Face`. Pasan a ser un dict de presets.
- `nod` y `shake` **sobreviven**, y encajan mejor que antes: son reacciones, que
  es justo lo que ahora sí existe.

## El cabo suelto: los corazones

`love` tiene ojos de corazón, y **un corazón no se interpola desde un círculo**.
Es la única pieza que no encaja en el modelo continuo. Opciones:

1. **Crossfade solo de los ojos**: el círculo se desvanece y el corazón aparece
   encima. Es un corte disimulado, o sea el pecado que este milestone viene a
   quitar — pero localizado en un ojo y no en toda la cara.
2. **Que sea rara y deliberada**: los corazones solo salen con "amor y paz", que
   es un gesto explícito. Si es raro y es respuesta a algo que has hecho tú, el
   salto se lee como intención y no como fallo.

Van juntas: la 2 justifica la 1. Es el plan, pero es lo más frágil del diseño.

## Config nueva

```json
{
  "mood": {
    "decay": 6.0,
    "feature_time_constant": 0.18
  },
  "idle": {
    "breath_amplitude": 0.015,
    "breath_period": 4.0,
    "gaze_drift": true,
    "blink_interval": [2.0, 6.0]
  },
  "gestures": {
    "enabled": true,
    "detect_fps": 4,
    "wave_cycles": 2,
    "wave_window": 1.5
  }
}
```

`gestures.detect_fps` va aparte y más bajo que el de la cara: los gestos cuestan
5.4x lo que cuesta YuNet, y no hace falta buscar manos tan a menudo como caras.

## Pendiente / riesgos

- [ ] **La Pi sigue sin tocarse, y ya es el bloqueo del proyecto.** Van cuatro
      decisiones seguidas que terminan en "hay que medirlo en la 3B": la RAM, el
      coste de YuNet, el de los gestos, y ahora si el reposo vivo mantiene los
      FPS. Los 16.3 ms de gestos son de un M-series; en un Cortex-A53 pueden
      irse a 200-500 ms y reventar el presupuesto. **Antes de implementar esto
      convendría medir de una vez.**
- [ ] Que el morfeo continuo no quede *blandengue*. Un ser vivo también tiene
      movimientos rápidos: si todo se interpola suave, parece gelatina. Puede
      que haga falta que algunas reacciones (la sorpresa) tengan ataque casi
      instantáneo y solo la vuelta sea lenta.
- [ ] El crossfade de los corazones.
- [ ] Detectar el saludo por movimiento de muñeca es una heurística con umbrales
      (cuántos ciclos, en cuánto tiempo). Los umbrales habrá que ajustarlos a
      ojo contra la cámara real, y lo que funcione en la mesa puede no funcionar
      a dos metros.
- [ ] 7.6 MB más de modelos sobre una Pi de 1GB que ya iba a 252 MB de pico.

## Cómo se verificará

- Reposo: capturando frames del `main()` real con driver dummy y comprobando que
  la escala oscila (respiración) y que la mirada deriva sin nadie delante.
- Mood: guionizando eventos y midiendo que la intensidad decae y el rostro vuelve
  a la calma, y que **ninguna expresión aparece sin un evento que la cause**.
- Gestos: contra la cámara real, midiendo enganche y falsos positivos como se
  hizo con Haar vs YuNet. Nada de dar por bueno lo que no se haya medido.
