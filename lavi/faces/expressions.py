"""Las expresiones dejan de ser clases y pasan a ser datos.

Antes `happy` era un objeto `HappyFace` con su propio `draw()`, y pasar de
`happy` a `sad` era cambiar de objeto: un corte, que había que tapar con el pop.
Aquí `contenta` es un puñado de números, y pasar de una a otra es moverlos. Un
ser vivo no tiene siete caras: tiene una, y le cambia.
"""

# Todo lo que define un rostro. Si algo no está aquí, no se puede interpolar, y
# si no se puede interpolar volvemos a tener cortes que tapar.
FEATURES = ("mouth_curve", "mouth_open", "eye_open", "eye_widen", "hearts")

PRESETS = {
    # Donde Lavi vive. No es neutra del todo: una cara en reposo absoluto parece
    # apagada, así que la calma lleva media sonrisa de fondo.
    "calma": {"mouth_curve": 0.30, "mouth_open": 0.00, "eye_open": 1.00, "eye_widen": 0.0, "hearts": 0.0},

    "contenta": {"mouth_curve": 0.85, "mouth_open": 0.10, "eye_open": 0.85, "eye_widen": 0.0, "hearts": 0.0},
    "emocionada": {"mouth_curve": 1.00, "mouth_open": 0.65, "eye_open": 1.00, "eye_widen": 0.7, "hearts": 0.0},
    "sorpresa": {"mouth_curve": 0.15, "mouth_open": 0.75, "eye_open": 1.00, "eye_widen": 1.0, "hearts": 0.0},
    "triste": {"mouth_curve": -0.70, "mouth_open": 0.00, "eye_open": 0.70, "eye_widen": 0.0, "hearts": 0.0},
    "enamorada": {"mouth_curve": 0.80, "mouth_open": 0.10, "eye_open": 1.00, "eye_widen": 0.0, "hearts": 1.0},

    # No decae hacia la calma: es un reposo alternativo. Ver Mood.set_baseline.
    "dormida": {"mouth_curve": 0.05, "mouth_open": 0.00, "eye_open": 0.05, "eye_widen": 0.0, "hearts": 0.0},
}

BASELINE = "calma"
SLEEP = "dormida"


def preset(name):
    return dict(PRESETS.get(name, PRESETS[BASELINE]))


def blend(a, b, t):
    """Mezcla dos juegos de rasgos. t=0 devuelve a, t=1 devuelve b."""
    t = max(0.0, min(1.0, t))
    return {k: a[k] + (b[k] - a[k]) * t for k in FEATURES}
