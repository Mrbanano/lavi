from lavi.faces.parts.eye import Eye, EyeType
from lavi.faces.parts.mouth import Mouth, MouthType

class Face:
    def __init__(self, config=None):
        config = config or {}
        face_config = config.get("face", {})

        self.left_eye = Eye(face_config.get("eye_color", "#ffffff"))
        self.right_eye = Eye(face_config.get("eye_color", "#ffffff"))
        self.mouth = Mouth(face_config.get("mouth_color", "#ffffff"))
        self.alpha = 255
        self.name = "base"

    def set_alpha(self, alpha):
        self.alpha = alpha
        self.left_eye.set_alpha(alpha)
        self.right_eye.set_alpha(alpha)
        self.mouth.set_alpha(alpha)

    def setup(self):
        pass

    def draw(self, surface, face_rect):
        x, y, w, h = face_rect
        eye_size = int(w * 0.18)
        eye_y = int(y + h * 0.35)
        left_eye_x = int(x + w * 0.22)
        right_eye_x = int(x + w * 0.60)

        self.left_eye.draw(surface, left_eye_x, eye_y, eye_size)
        self.right_eye.draw(surface, right_eye_x, eye_y, eye_size)

        mouth_width = int(w * 0.28)
        mouth_height = int(h * 0.15)
        mouth_x = x + (w - mouth_width) // 2
        mouth_y = int(y + h * 0.60)

        self.mouth.draw(surface, mouth_x, mouth_y, mouth_width, mouth_height)
