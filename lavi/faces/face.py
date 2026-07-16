from lavi.faces.parts.eye import Eye
from lavi.faces.parts.mouth import Mouth
from lavi.faces.parts.brow import Brow
from lavi.faces.expressions import FEATURES, preset

# Cuánto se desplaza el ojo al mirar del todo a un lado, en fracción del propio
# ojo. Pasado ~0.4 el ojo se sale de su hueco y la cara se deforma.
GAZE_RANGE = 0.35


class Face:
    """El rostro de Lavi. Uno, no siete.

    No tiene subclases y no decide nada: solo sabe dibujar los rasgos que le
    den. Qué rasgos tocan lo decide el Mood, y lo que se mueve sin que pase nada
    lo pone IdleLife. Aquí ya no hay temporizadores ni expresiones con nombre.
    """

    def __init__(self, config=None):
        config = config or {}
        face_config = config.get("face", {})

        self.left_eye = Eye(face_config.get("eye_color", "#ffffff"))
        self.right_eye = Eye(face_config.get("eye_color", "#ffffff"))
        self.mouth = Mouth(face_config.get("mouth_color", "#ffffff"))
        brow_color = face_config.get("brow_color", face_config.get("eye_color", "#ffffff"))
        self.left_brow = Brow(brow_color, side=-1)
        self.right_brow = Brow(brow_color, side=1)

        self.alpha = 255
        self.gaze_x = 0.0
        self.gaze_y = 0.0
        self.blink = 0.0
        self.features = preset("calma")

    def set_alpha(self, alpha):
        self.alpha = alpha
        self.left_eye.set_alpha(alpha)
        self.right_eye.set_alpha(alpha)
        self.mouth.set_alpha(alpha)
        self.left_brow.set_alpha(alpha)
        self.right_brow.set_alpha(alpha)

    def set_features(self, features):
        for key in FEATURES:
            if key in features:
                self.features[key] = features[key]

    def set_gaze(self, x, y):
        """Hacia dónde mira, en -1..1. (0, 0) es al frente."""
        self.gaze_x = max(-1.0, min(1.0, x))
        self.gaze_y = max(-1.0, min(1.0, y))

    def set_blink(self, progress):
        """0 abierto, 1 cerrado. Se compone con la emoción, no la pisa."""
        self.blink = max(0.0, min(1.0, progress))

    def draw(self, surface, face_rect):
        x, y, w, h = face_rect
        f = self.features

        # El parpadeo y la emoción escriben los dos sobre la apertura del ojo, y
        # se componen multiplicando: así se puede parpadear estando triste sin
        # que una cosa pise a la otra.
        eye_open = f["eye_open"] * (1.0 - self.blink)
        for eye in (self.left_eye, self.right_eye):
            eye.set_features(open=eye_open, widen=f["eye_widen"], hearts=f["hearts"])
        self.mouth.set_features(curve=f["mouth_curve"], open=f["mouth_open"])
        for brow in (self.left_brow, self.right_brow):
            brow.set_features(show=f["brow_show"], angle=f["brow_angle"], raise_=f["brow_raise"])

        eye_size = int(w * 0.18)
        eye_y = int(y + h * 0.35)
        left_eye_x = int(x + w * 0.22)
        right_eye_x = int(x + w * 0.60)

        # Los dos ojos se mueven juntos: son un par mirando al mismo sitio, no
        # dos piezas sueltas.
        gaze_dx = int(eye_size * GAZE_RANGE * self.gaze_x)
        gaze_dy = int(eye_size * GAZE_RANGE * self.gaze_y)

        self.left_eye.draw(surface, left_eye_x + gaze_dx, eye_y + gaze_dy, eye_size)
        self.right_eye.draw(surface, right_eye_x + gaze_dx, eye_y + gaze_dy, eye_size)

        # Las cejas no siguen a la mirada: los ojos se mueven dentro de la cara,
        # las cejas van con la cara. Moverlas con el gaze las despegaría.
        brow_h = int(eye_size * 0.45)
        brow_y = eye_y - int(eye_size * 0.52)
        self.left_brow.draw(surface, left_eye_x, brow_y, eye_size, brow_h)
        self.right_brow.draw(surface, right_eye_x, brow_y, eye_size, brow_h)

        mouth_width = int(w * 0.28)
        mouth_height = int(h * 0.15)
        mouth_x = x + (w - mouth_width) // 2
        mouth_y = int(y + h * 0.60)

        self.mouth.draw(surface, mouth_x, mouth_y, mouth_width, mouth_height)
