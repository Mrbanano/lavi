import os

import numpy as np

from lavi.vision.vendor.mp_palmdet import MPPalmDet
from lavi.vision.vendor.mp_handpose import MPHandPose

MODEL_DIR = os.path.join(os.path.dirname(__file__), "models")
PALM_MODEL = os.path.join(MODEL_DIR, "palm_detection_mediapipe_2023feb.onnx")
HANDPOSE_MODEL = os.path.join(MODEL_DIR, "handpose_estimation_mediapipe_2023feb.onnx")

# El vendor devuelve np.r_[bbox(4), landmarks(21*3), world(21*3), handedness, conf].
# Los de pantalla, que son los que interesan, están en 4:67.
LANDMARKS_SLICE = slice(4, 4 + 21 * 3)


class HandError(Exception):
    pass


class HandDetector:
    """Manos con 21 landmarks, en dos pasos: encontrar la palma y luego los dedos.

    Los modelos son los de MediaPipe exportados a ONNX por OpenCV Zoo, corriendo
    sobre cv2.dnn. El paquete `mediapipe` no vale: PyPI no publica wheel para
    Linux ARM, o sea que instalaría en la mac y no en la Pi.

    Es caro comparado con la cara: medido en la mac, palma 10.4 ms + pose 5.9 ms
    = 16.3 ms, contra los 3.4 ms de YuNet. De ahí que vaya a su propio ritmo, más
    lento, y que solo se busquen manos si hay alguien delante.
    """

    def __init__(self, config=None):
        config = config or {}
        gesture_config = config.get("gestures", {})

        for path in (PALM_MODEL, HANDPOSE_MODEL):
            if not os.path.exists(path):
                raise HandError("falta el modelo de manos: %s" % path)

        self._palm = MPPalmDet(
            modelPath=PALM_MODEL,
            scoreThreshold=gesture_config.get("palm_score_threshold", 0.8),
        )
        self._handpose = MPHandPose(
            modelPath=HANDPOSE_MODEL,
            confThreshold=gesture_config.get("hand_conf_threshold", 0.8),
        )

    def detect(self, frame):
        """Devuelve una lista de manos, cada una con 21 puntos (x, y) en píxeles."""
        if frame is None:
            return []

        palms = self._palm.infer(frame)
        if palms is None or len(palms) == 0:
            return []

        hands = []
        for palm in palms:
            result = self._handpose.infer(frame, palm)
            if result is None:
                continue
            landmarks = np.array(result[LANDMARKS_SLICE]).reshape(21, 3)
            hands.append(landmarks[:, :2])
        return hands
