# Lavi - Milestone 1: Cara Animada

## Overview
Asistente personal para adultos mayores que corre en Raspberry Pi 3B con pantalla HDMI/GPIO. Primer hito: UI kiosko full-screen con cara animada modular y transiciones suaves.

## Hardware
- Raspberry Pi 3B (1GB RAM, ARM Cortex-A53)
- Pantalla HDMI o GPIO (no táctil, cualquier resolución)
- Sin cámara (milestone 2)

## Stack
- Python 3 + Pygame
- Sin dependencias externas pesadas
- Config via `config.json`

## Arquitectura

```
lavi/
├── main.py              # Entry point, fullscreen kiosk mode
├── config.json          # Color fondo, velocidad, expresiones
├── engine/
│   ├── __init__.py
│   ├── state_machine.py # Controla ciclo de expresiones
│   └── animator.py      # Transiciones suaves (interpolación)
├── faces/
│   ├── __init__.py
│   ├── base.py          # Clase Face (posición, opacidad, partes)
│   ├── parts/
│   │   ├── __init__.py
│   │   ├── eye.py       # Ojos: circulares, parpadeo, corazones, guiño
│   │   └── mouth.py     # Bocas: sonrisa, risa, triste, sorprendido
│   └── expressions/     # Expresiones compuestas
│       ├── __init__.py
│       ├── happy.py
│       ├── laugh.py
│       ├── wink.py
│       ├── love.py
│       ├── sad.py
│       ├── surprised.py
│       └── sleepy.py
└── renderer.py          # Dibuja cara en pantalla Pygame
```

## Face System

### Partes modulares
Cada expresión se compone de partes independientes:

**Ojos (Eye):**
- `normal`: Círculo blanco sólido
- `closed`: Línea cerrada (parpadeo)
- `heart`: Corazón rosa
- `wink`: Un ojo normal + uno cerrado
- `sleepy`: Línea horizontal baja

**Bocas (Mouth):**
- `smile`: Arco hacia abajo (sonrisa)
- `open`: Boca abierta (risa)
- `sad`: Arco hacia arriba
- `surprise`: Círculo pequeño
- `line`: Línea neutral

### Expresiones predefinidas
| Expresión | Ojos | Boca | Parpadeo |
|-----------|------|------|----------|
| happy | normal | smile | sí |
| laugh | closed | open | no |
| wink | normal+closed | smile | no |
| love | heart | line | no |
| sad | normal | sad | sí |
| surprised | normal (grande) | surprise | no |
| sleepy | line | line | no |

## State Machine

### Ciclo automático
```
happy → laugh → wink → love → sad → surprised → sleepy → happy
```

### Transiciones
- Duración: 0.4s (configurable)
- Tipo: interpolación lineal de opacidad
- Parpadeo: cada 3-5s (aleatorio), duración 0.15s

### Comportamiento
- Loop infinito, cada expresión dura ~3-4s
- Parpadeo intermitente para sensación de vida
- Transiciones suaves entre expresiones

## Config (`config.json`)

```json
{
  "display": {
    "fullscreen": true,
    "bg_color": "#000000"
  },
  "animation": {
    "transition_speed": 0.4,
    "expression_duration": 3.5,
    "blink_interval_min": 3,
    "blink_interval_max": 5
  },
  "expressions": ["happy", "laugh", "wink", "love", "sad", "surprised", "sleepy"],
  "face": {
    "eye_color": "#ffffff",
    "mouth_color": "#ffffff",
    "heart_color": "#ff6b9d"
  }
}
```

## Renderer

- Pygame surface full-screen
- Renderiza partes según expresión activa
- Aplica transiciones de opacidad
- Maneja resize de ventana (responsive)
- FPS: 30 (suficiente para animaciones suaves, bajo consumo)

## Performance Target
- <50MB RAM
- <15% CPU en RPi 3B
- 30 FPS constante

## Milestone 2 (futuro)
- Cámara RPi para detectar usuario
- Gestos (saludo, mostrar objetos)
- Expresiones reactivas
- Transiciones más elaboradas
