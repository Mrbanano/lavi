import os

import cv2
import cv2.data


class DetectorError(Exception):
    pass


class FaceDetector:
    """Detección de rostro frontal con Haar cascade.

    Haar y no MediaPipe porque el objetivo es una Pi 3B: MediaPipe no tiene
    wheels para 32 bits y ahí va a pocos FPS. Haar viene dentro de OpenCV, no
    descarga modelos, y a 320x240 corre de sobra. A cambio pide cara de frente,
    que es justo el caso de alguien mirando el kiosko.
    """

    def __init__(self, config=None):
        config = config or {}
        cam_config = config.get("camera", {})

        cascade_file = os.path.join(cv2.data.haarcascades, "haarcascade_frontalface_default.xml")
        if not os.path.exists(cascade_file):
            raise DetectorError(
                "no se encontró el Haar cascade en %s. OpenCV 5 los quitó: "
                "hace falta opencv-python 4.x." % cascade_file
            )

        self.cascade = cv2.CascadeClassifier(cascade_file)
        if self.cascade.empty():
            raise DetectorError("el Haar cascade existe pero no cargó: %s" % cascade_file)

        self.scale_factor = cam_config.get("scale_factor", 1.2)
        self.min_neighbors = cam_config.get("min_neighbors", 5)
        self.min_size_fraction = cam_config.get("min_face_fraction", 0.15)

    def detect(self, frame):
        """Devuelve una lista de cajas (x, y, w, h) en píxeles del frame."""
        if frame is None:
            return []

        gray = cv2.cvtColor(frame, cv2.COLOR_BGR2GRAY)
        # Iguala el histograma: ayuda bastante con luz de interior mala,
        # que es donde vive un kiosko.
        gray = cv2.equalizeHist(gray)

        # Descarta caras diminutas: son casi siempre ruido, y menos escalas
        # que recorrer es menos CPU en la Pi.
        min_side = int(min(frame.shape[0], frame.shape[1]) * self.min_size_fraction)
        faces = self.cascade.detectMultiScale(
            gray,
            scaleFactor=self.scale_factor,
            minNeighbors=self.min_neighbors,
            minSize=(min_side, min_side),
        )
        return [tuple(int(v) for v in face) for face in faces]
