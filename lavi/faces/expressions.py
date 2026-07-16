"""Las expresiones dejan de ser clases y pasan a ser datos.

Antes `happy` era un objeto `HappyFace` con su propio `draw()`, y pasar de
`happy` a `sad` era cambiar de objeto: un corte, que había que tapar con el pop.
Aquí `contenta` es un puñado de números, y pasar de una a otra es moverlos. Un
ser vivo no tiene siete caras: tiene una, y le cambia.
"""

# Todo lo que define un rostro. Si algo no está aquí, no se puede interpolar, y
# si no se puede interpolar volvemos a tener cortes que tapar.
FEATURES = (
    "mouth_curve", "mouth_open",
    "eye_open", "eye_widen",
    "hearts",
    "brow_show", "brow_angle", "brow_raise",
)

PRESETS = {
    # Donde Lavi vive. No es neutra del todo: una cara en reposo absoluto parece
    # apagada, así que la calma lleva media sonrisa de fondo. Y sin cejas: son
    # dos círculos y una boca, y así se queda mientras no haga falta más.
    "calma": {"mouth_curve": 0.30, "mouth_open": 0.00, "eye_open": 1.00, "eye_widen": 0.0,
              "hearts": 0.0, "brow_show": 0.0, "brow_angle": 0.0, "brow_raise": 0.40},

    "contenta": {"mouth_curve": 0.85, "mouth_open": 0.10, "eye_open": 0.85, "eye_widen": 0.0,
                 "hearts": 0.0, "brow_show": 0.0, "brow_angle": 0.0, "brow_raise": 0.50},

    "emocionada": {"mouth_curve": 1.00, "mouth_open": 0.65, "eye_open": 1.00, "eye_widen": 0.7,
                   "hearts": 0.0, "brow_show": 0.6, "brow_angle": 0.0, "brow_raise": 0.90},

    "sorpresa": {"mouth_curve": 0.15, "mouth_open": 0.75, "eye_open": 1.00, "eye_widen": 1.0,
                 "hearts": 0.0, "brow_show": 0.7, "brow_angle": 0.0, "brow_raise": 1.00},

    "triste": {"mouth_curve": -0.70, "mouth_open": 0.00, "eye_open": 0.70, "eye_widen": 0.0,
               "hearts": 0.0, "brow_show": 0.6, "brow_angle": 0.7, "brow_raise": 0.30},

    # El enfado es lo único que las cejas hacen legible de verdad: sin ellas, una
    # boca hacia abajo y los ojos entornados se leen como tristeza, no como
    # enfado. Por eso van a tope y con el extremo de dentro caído.
    "enfadada": {"mouth_curve": -0.50, "mouth_open": 0.10, "eye_open": 0.72, "eye_widen": 0.0,
                 "hearts": 0.0, "brow_show": 1.0, "brow_angle": -1.0, "brow_raise": 0.00},

    "enamorada": {"mouth_curve": 0.80, "mouth_open": 0.10, "eye_open": 1.00, "eye_widen": 0.0,
                  "hearts": 1.0, "brow_show": 0.0, "brow_angle": 0.0, "brow_raise": 0.50},

    # No decae hacia la calma: es un reposo alternativo. Ver Mood.set_baseline.
    "dormida": {"mouth_curve": 0.05, "mouth_open": 0.00, "eye_open": 0.05, "eye_widen": 0.0,
                "hearts": 0.0, "brow_show": 0.0, "brow_angle": 0.0, "brow_raise": 0.30},
}

BASELINE = "calma"
SLEEP = "dormida"


def preset(name):
    return dict(PRESETS.get(name, PRESETS[BASELINE]))


def blend(a, b, t):
    """Mezcla dos juegos de rasgos. t=0 devuelve a, t=1 devuelve b."""
    t = max(0.0, min(1.0, t))
    return {k: a[k] + (b[k] - a[k]) * t for k in FEATURES}
