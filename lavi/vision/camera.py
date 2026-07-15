import cv2

from lavi.vision.platform_detect import detect_platform, Platform


class CameraError(Exception):
    pass


class BaseCamera:
    """Devuelve frames BGR (el orden que espera OpenCV), o None si no hay."""

    def read(self):
        raise NotImplementedError

    def close(self):
        pass


class OpenCVCamera(BaseCamera):
    """Webcam vía OpenCV. Es el camino de la mac y el de una USB en la Pi."""

    def __init__(self, index=0, width=320, height=240, warmup_frames=10):
        self.width = width
        self.height = height

        self.cap = cv2.VideoCapture(index)
        if not self.cap.isOpened():
            raise CameraError(
                "no se pudo abrir la cámara %d. En macOS revisa que la terminal "
                "tenga permiso de cámara en Ajustes > Privacidad y Seguridad." % index
            )

        # La cámara puede ignorar esto y dar su resolución nativa (la FaceTime HD
        # devuelve 640x480 aunque le pidas 320x240), así que igual reescalamos al leer.
        self.cap.set(cv2.CAP_PROP_FRAME_WIDTH, width)
        self.cap.set(cv2.CAP_PROP_FRAME_HEIGHT, height)

        # Los primeros frames de la FaceTime salen en negro mientras expone.
        for _ in range(warmup_frames):
            self.cap.read()

    def read(self):
        ok, frame = self.cap.read()
        if not ok or frame is None:
            return None
        if frame.shape[1] != self.width or frame.shape[0] != self.height:
            frame = cv2.resize(frame, (self.width, self.height), interpolation=cv2.INTER_AREA)
        return frame

    def close(self):
        if self.cap is not None:
            self.cap.release()
            self.cap = None


class PiCamera(BaseCamera):
    """Cámara CSI de la Pi vía picamera2 (libcamera)."""

    def __init__(self, width=320, height=240, warmup_frames=10):
        try:
            from picamera2 import Picamera2
        except ImportError as e:
            raise CameraError(
                "picamera2 no está instalado. En Raspberry Pi OS: "
                "sudo apt install -y python3-picamera2"
            ) from e

        self.width = width
        self.height = height
        self.cam = Picamera2()
        # Ojo con el nombre: libcamera llama "RGB888" a lo que numpy entrega
        # como BGR. Es el orden que queremos para OpenCV, pero el nombre engaña.
        cfg = self.cam.create_preview_configuration(
            main={"size": (width, height), "format": "RGB888"}
        )
        self.cam.configure(cfg)
        self.cam.start()

        for _ in range(warmup_frames):
            self.cam.capture_array()

    def read(self):
        frame = self.cam.capture_array()
        if frame is None or len(frame.shape) != 3:
            return None
        if frame.shape[2] == 4:  # algunos modos entregan XBGR
            frame = frame[:, :, :3]
        return frame

    def close(self):
        if self.cam is not None:
            self.cam.stop()
            self.cam.close()
            self.cam = None


def open_camera(config=None):
    """Abre la cámara que toque según la plataforma.

    En la Pi intenta la cámara CSI y cae a USB si no hay picamera2, que es el
    caso de una webcam enchufada por USB.
    """
    config = config or {}
    cam_config = config.get("camera", {})
    width = cam_config.get("width", 320)
    height = cam_config.get("height", 240)
    index = cam_config.get("index", 0)
    warmup = cam_config.get("warmup_frames", 10)

    target = detect_platform()

    if target == Platform.RASPBERRY:
        try:
            return PiCamera(width=width, height=height, warmup_frames=warmup)
        except Exception:
            # Cualquier fallo del camino CSI (sin picamera2, sin cámara conectada,
            # libcamera protestando) cae a USB. Un kiosko prefiere una webcam a
            # un stack trace.
            return OpenCVCamera(index=index, width=width, height=height, warmup_frames=warmup)

    return OpenCVCamera(index=index, width=width, height=height, warmup_frames=warmup)
