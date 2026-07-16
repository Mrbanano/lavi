import math


class GazeTracker:
    """Convierte dónde está la cara detectada en hacia dónde mira Lavi.

    Devuelve (x, y) en -1..1: -1 es todo a la izquierda / arriba, 1 todo a la
    derecha / abajo, 0 al frente. Quién traduce eso a píxeles es la cara, que es
    la que sabe cómo de grandes son sus ojos.

    Las coordenadas salen del frame ya invertido (flip_horizontal), y eso hace
    que el mapeo sea directo: en un espejo, quien se mueve a su derecha aparece
    a la derecha de la imagen, que es justo el lado al que Lavi tiene que mirar.
    """

    def __init__(self, config=None):
        config = config or {}
        gaze_config = config.get("gaze", {})

        self.enabled = gaze_config.get("enabled", True)
        # Cuánto tarda la mirada en recorrer ~63% del camino hasta la cara.
        # Sin esto la mirada da saltos: la detección va a 8 FPS y salta unos
        # píxeles entre frames aunque la persona esté quieta.
        self.time_constant = gaze_config.get("time_constant", 0.25)

        self.x = 0.0
        self.y = 0.0

    def update(self, box, frame_size, dt):
        """box es (x, y, w, h) o None; frame_size es (w, h) o None."""
        target_x, target_y = 0.0, 0.0

        if self.enabled and box is not None and frame_size is not None:
            fx, fy, fw, fh = box
            width, height = frame_size
            if width > 0 and height > 0:
                target_x = ((fx + fw / 2.0) / width - 0.5) * 2.0
                target_y = ((fy + fh / 2.0) / height - 0.5) * 2.0
                target_x = max(-1.0, min(1.0, target_x))
                target_y = max(-1.0, min(1.0, target_y))

        # Suavizado exponencial por tiempo y no por frames: el loop va a 30 FPS
        # en la mac y puede que a menos en la Pi, y la mirada tiene que tardar lo
        # mismo en llegar en las dos.
        if self.time_constant > 0:
            alpha = 1.0 - math.exp(-dt / self.time_constant)
        else:
            alpha = 1.0

        self.x += (target_x - self.x) * alpha
        self.y += (target_y - self.y) * alpha
        return self.get()

    def get(self):
        return (self.x, self.y)
