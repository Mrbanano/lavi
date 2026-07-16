from lavi.faces.parts.eye import Eye, EyeType
from lavi.faces.parts.mouth import Mouth, MouthType

# Cuánto se desplaza el ojo al mirar del todo a un lado, en fracción del propio
# ojo. Pasado ~0.4 el ojo se sale de su hueco y la cara se deforma.
GAZE_RANGE = 0.35

class Face:
    def __init__(self, config=None):
        config = config or {}
        face_config = config.get("face", {})

        self.left_eye = Eye(face_config.get("eye_color", "#ffffff"))
        self.right_eye = Eye(face_config.get("eye_color", "#ffffff"))
        self.mouth = Mouth(face_config.get("mouth_color", "#ffffff"))
        self.alpha = 255
        self.name = "base"
        self.gaze_x = 0.0
        self.gaze_y = 0.0

    def set_alpha(self, alpha):
        self.alpha = alpha
        self.left_eye.set_alpha(alpha)
        self.right_eye.set_alpha(alpha)
        self.mouth.set_alpha(alpha)

    def set_blink(self, progress):
        # Sin filtrar por expresión: solo los ojos NORMAL reaccionan al párpado.
        # Los cerrados, dormidos, de corazón y de guiño ya lo ignoran por su
        # cuenta, así que no hay que ir marcando a mano quién puede parpadear.
        self.left_eye.set_blink(progress)
        self.right_eye.set_blink(progress)

    def set_gaze(self, x, y):
        """Hacia dónde mira, en -1..1. (0, 0) es al frente."""
        self.gaze_x = max(-1.0, min(1.0, x))
        self.gaze_y = max(-1.0, min(1.0, y))

    def setup(self):
        pass

    def draw(self, surface, face_rect):
        x, y, w, h = face_rect
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

        mouth_width = int(w * 0.28)
        mouth_height = int(h * 0.15)
        mouth_x = x + (w - mouth_width) // 2
        mouth_y = int(y + h * 0.60)

        self.mouth.draw(surface, mouth_x, mouth_y, mouth_width, mouth_height)
