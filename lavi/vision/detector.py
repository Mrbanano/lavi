import os

import cv2
import cv2.data

MODEL_DIR = os.path.join(os.path.dirname(__file__), "models")
YUNET_MODEL = os.path.join(MODEL_DIR, "face_detection_yunet_2023mar.onnx")


class DetectorError(Exception):
    pass


class FaceDetector:
    """Detección de rostro. YuNet si el modelo está, Haar si no.

    YuNet y no Haar porque Haar no aguanta: medido contra la cámara real, con
    la persona delante moviéndose de forma normal (ladear la cabeza, mirar al
    teclado), Haar enganchó el 28% de los frames y YuNet el 96%. Haar no es
    invariante a rotación, así que basta con inclinar la cara para que deje de
    verla, y eso hacía que Lavi se durmiera con alguien delante.

    El precio es 1.1 ms más por detección en la mac (2.3 -> 3.4), que con
    detect_fps a 8 no se nota: hay 125 ms de presupuesto por detección.

    YuNet corre sobre cv2.dnn, que ya viene en OpenCV, así que no añade ninguna
    dependencia de pip. Eso es justo lo que descarta a MediaPipe: no publica
    wheel para Linux ARM, o sea que instalaría en la mac y no en la Pi.
    """

    def __init__(self, config=None):
        config = config or {}
        cam_config = config.get("camera", {})

        self.score_threshold = cam_config.get("score_threshold", 0.7)
        self.min_size_fraction = cam_config.get("min_face_fraction", 0.15)
        # Solo los usa el respaldo Haar.
        self.scale_factor = cam_config.get("scale_factor", 1.2)
        self.min_neighbors = cam_config.get("min_neighbors", 5)

        self.backend = None
        self._yunet = None
        self._cascade = None
        self._input_size = None

        if os.path.exists(YUNET_MODEL) and hasattr(cv2, "FaceDetectorYN"):
            self._yunet = cv2.FaceDetectorYN.create(
                YUNET_MODEL, "", (320, 240), self.score_threshold
            )
            self.backend = "yunet"
        else:
            # Un kiosko no puede quedarse a oscuras porque falte un .onnx.
            self._init_haar()
            self.backend = "haar"

    def _init_haar(self):
        cascade_file = os.path.join(cv2.data.haarcascades, "haarcascade_frontalface_default.xml")
        if not os.path.exists(cascade_file):
            raise DetectorError(
                "no está el modelo de YuNet (%s) ni el Haar cascade de respaldo (%s). "
                "OpenCV 5 quitó los cascades: hace falta opencv-python 4.x." % (YUNET_MODEL, cascade_file)
            )
        self._cascade = cv2.CascadeClassifier(cascade_file)
        if self._cascade.empty():
            raise DetectorError("el Haar cascade existe pero no cargó: %s" % cascade_file)

    def detect(self, frame):
        """Devuelve una lista de cajas (x, y, w, h) en píxeles del frame."""
        if frame is None:
            return []
        if self._yunet is not None:
            return self._detect_yunet(frame)
        return self._detect_haar(frame)

    def _detect_yunet(self, frame):
        h, w = frame.shape[:2]
        # setInputSize reconstruye la malla de anclas, así que solo cuando cambia.
        if self._input_size != (w, h):
            self._yunet.setInputSize((w, h))
            self._input_size = (w, h)

        # YuNet come BGR directamente: ni gris ni ecualizado, al contrario que Haar.
        _, faces = self._yunet.detect(frame)
        if faces is None:
            return []

        min_side = min(h, w) * self.min_size_fraction
        boxes = []
        for f in faces:
            x, y, fw, fh = f[:4]
            if fw < min_side and fh < min_side:
                continue
            boxes.append((int(x), int(y), int(fw), int(fh)))
        return boxes

    def _detect_haar(self, frame):
        gray = cv2.cvtColor(frame, cv2.COLOR_BGR2GRAY)
        # Iguala el histograma: ayuda bastante con luz de interior mala,
        # que es donde vive un kiosko.
        gray = cv2.equalizeHist(gray)

        min_side = int(min(frame.shape[0], frame.shape[1]) * self.min_size_fraction)
        faces = self._cascade.detectMultiScale(
            gray,
            scaleFactor=self.scale_factor,
            minNeighbors=self.min_neighbors,
            minSize=(min_side, min_side),
        )
        return [tuple(int(v) for v in face) for face in faces]
