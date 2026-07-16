import threading
import time

import cv2

from lavi.vision.camera import open_camera, CameraError
from lavi.vision.detector import FaceDetector, DetectorError
from lavi.vision.hands import HandDetector, HandError
from lavi.vision.platform_detect import describe_platform
from lavi.engine.gestures import GestureRecognizer


class VisionService:
    """Captura y detecta en un thread aparte.

    La detección tarda decenas de ms en la Pi 3B; hacerla dentro del loop de
    render tiraría los 30 FPS. Aquí el loop principal solo lee el último
    resultado, que es una operación instantánea.
    """

    def __init__(self, config=None):
        config = config or {}
        cam_config = config.get("camera", {})

        self._config = config
        self.enabled = cam_config.get("enabled", True)
        self.capture_fps = cam_config.get("capture_fps", 15)
        self.detect_fps = cam_config.get("detect_fps", 8)
        self.flip_horizontal = cam_config.get("flip_horizontal", True)

        gesture_config = config.get("gestures", {})
        self.gestures_enabled = gesture_config.get("enabled", True)
        # No baja de ~8: un saludo es una oscilación de 1-2 Hz y por debajo de
        # eso hay aliasing. Ver GestureRecognizer.
        self.gesture_fps = gesture_config.get("detect_fps", 8)

        # Se resuelve una vez: en la Pi esto abre /proc/device-tree/model, y
        # stats() se llama en cada frame con el preview abierto.
        self._platform_name = describe_platform()

        self._camera = None
        self._detector = None
        self._hand_detector = None
        self._gestures = GestureRecognizer(config)
        self._thread = None
        self._stop = threading.Event()
        self._lock = threading.Lock()

        self._frame = None
        self._faces = []
        self._hands = []
        self._gesture = None
        self._error = None
        self._detect_ms = 0.0
        self._gesture_ms = 0.0
        self._capture_fps_actual = 0.0

    def start(self):
        if not self.enabled:
            self._error = "cámara desactivada en config.json"
            return False

        try:
            self._camera = open_camera(self._config)
            self._detector = FaceDetector(self._config)
        except (CameraError, DetectorError) as e:
            # Sin cámara el kiosko tiene que seguir mostrando la cara igual:
            # es un fallo degradado, no fatal.
            self._error = str(e)
            self._close_camera()
            return False

        if self.gestures_enabled:
            try:
                self._hand_detector = HandDetector(self._config)
            except HandError as e:
                # Quedarse sin gestos es perder una gracia, no el kiosko: Lavi
                # sigue despertando y siguiéndote con la mirada.
                print("[lavi] sin gestos: %s" % e)
                self.gestures_enabled = False

        self._stop.clear()
        self._thread = threading.Thread(target=self._loop, name="lavi-vision", daemon=True)
        self._thread.start()
        return True

    def _loop(self):
        capture_interval = 1.0 / max(1, self.capture_fps)
        detect_interval = 1.0 / max(1, self.detect_fps)
        gesture_interval = 1.0 / max(1, self.gesture_fps)
        last_detect = 0.0
        last_gesture = 0.0
        last_frame_time = time.time()

        try:
            while not self._stop.is_set():
                start = time.time()

                frame = self._camera.read()
                if frame is None:
                    time.sleep(capture_interval)
                    continue

                if self.flip_horizontal:
                    # Espejo: que la persona se vea como en un espejo, y que las
                    # coordenadas del preview coincidan con lo que percibe.
                    frame = cv2.flip(frame, 1)

                faces = None
                detect_ms = None
                if start - last_detect >= detect_interval:
                    t0 = time.time()
                    faces = self._detector.detect(frame)
                    detect_ms = (time.time() - t0) * 1000.0
                    last_detect = start

                # Buscar manos solo si hay alguien delante. Cuesta 5x lo que la
                # cara, y un saludo sin nadie a quien saludar no existe: así la
                # sala vacía no paga nada.
                hands = None
                gesture = None
                gesture_ms = None
                someone_here = faces if faces is not None else self._faces
                if (self._hand_detector is not None and someone_here
                        and start - last_gesture >= gesture_interval):
                    t0 = time.time()
                    hands = self._hand_detector.detect(frame)
                    gesture_ms = (time.time() - t0) * 1000.0
                    last_gesture = start
                    height, width = frame.shape[:2]
                    gesture = self._gestures.update(hands, (width, height), start)

                now = time.time()
                delta = now - last_frame_time
                last_frame_time = now

                with self._lock:
                    self._frame = frame
                    if faces is not None:
                        self._faces = faces
                        self._detect_ms = detect_ms
                    if hands is not None:
                        self._hands = hands
                        self._gesture_ms = gesture_ms
                    if gesture is not None:
                        # Se queda esperando a que el render lo recoja: si lo
                        # sobrescribiera el siguiente ciclo, un saludo podría
                        # perderse entre dos frames de render.
                        self._gesture = gesture
                    if delta > 0:
                        # Media móvil: si no, el número baila y no se puede leer.
                        self._capture_fps_actual = 0.9 * self._capture_fps_actual + 0.1 * (1.0 / delta)

                sleep_for = capture_interval - (time.time() - start)
                if sleep_for > 0:
                    time.sleep(sleep_for)
        except Exception as e:  # el thread muere en silencio si no se registra
            with self._lock:
                self._error = "el thread de visión murió: %r" % (e,)

    def snapshot(self):
        """Último frame y últimas caras. No bloquea."""
        with self._lock:
            return self._frame, list(self._faces)

    def hands(self):
        with self._lock:
            return list(self._hands)

    def take_gesture(self):
        """Devuelve el gesto pendiente y lo consume. None si no hay."""
        with self._lock:
            gesture = self._gesture
            self._gesture = None
            return gesture

    def primary_face(self):
        """Caja de la cara más grande y tamaño del frame, o (None, None).

        La más grande y no la primera: si pasa alguien por detrás, Lavi tiene
        que seguir mirando a quien tiene delante, que es quien ocupa más.
        """
        with self._lock:
            if not self._faces or self._frame is None:
                return None, None
            biggest = max(self._faces, key=lambda f: f[2] * f[3])
            height, width = self._frame.shape[:2]
            return biggest, (width, height)

    def has_face(self):
        with self._lock:
            return len(self._faces) > 0

    def face_count(self):
        with self._lock:
            return len(self._faces)

    def stats(self):
        with self._lock:
            return {
                "detect_ms": self._detect_ms,
                "capture_fps": self._capture_fps_actual,
                "faces": len(self._faces),
                "error": self._error,
                "platform": self._platform_name,
                # Interesa verlo en el preview: si falta el .onnx, esto cae a
                # "haar" en silencio y la detección empeora mucho sin avisar.
                "detector": self._detector.backend if self._detector else None,
                "hands": len(self._hands),
                "gesture_ms": self._gesture_ms,
            }

    @property
    def error(self):
        with self._lock:
            return self._error

    @property
    def running(self):
        return self._thread is not None and self._thread.is_alive()

    def _close_camera(self):
        if self._camera is not None:
            try:
                self._camera.close()
            except Exception:
                pass
            self._camera = None

    def stop(self):
        self._stop.set()
        if self._thread is not None:
            self._thread.join(timeout=2.0)
            self._thread = None
        self._close_camera()
