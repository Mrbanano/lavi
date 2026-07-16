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
        self.detect_fps = cam_config.get("detect_fps", 5)
        self.flip_horizontal = cam_config.get("flip_horizontal", True)

        gesture_config = config.get("gestures", {})
        self.gestures_enabled = gesture_config.get("enabled", True)
        self.gesture_fps = gesture_config.get("detect_fps", 5)
        self._min_hand_face_frac = gesture_config.get("min_hand_face_fraction", 0.18)

        # Detección adaptativa: rastrear movimiento de cara para ajustar FPS.
        adaptive_config = config.get("adaptive", {})
        self._adaptive_enabled = adaptive_config.get("enabled", True)
        self._adapt_low = adaptive_config.get("low_fps", 3)
        self._adapt_high = adaptive_config.get("high_fps", 8)
        self._adapt_move_threshold = adaptive_config.get("move_threshold", 0.03)
        self._face_history = []
        self._history_len = adaptive_config.get("history_len", 4)
        self._current_detect_fps = self.detect_fps

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

        # Double buffer: pre-capturar siguiente frame mientras se procesa.
        next_frame = None

        try:
            while not self._stop.is_set():
                start = time.time()

                # Double buffer: reusar frame pre-capturado o leer uno nuevo.
                if next_frame is not None:
                    frame = next_frame
                    next_frame = None
                else:
                    frame = self._camera.read()

                if frame is None:
                    time.sleep(capture_interval)
                    continue

                if self.flip_horizontal:
                    frame = cv2.flip(frame, 1)

                # Pre-capturar siguiente frame en paralelo (no bloquea, la
                # cámara ya va a 60+ FPS y el buffer lo absorbe).
                # Solo lo hacemos si no hay nada que procesar ahora.
                if start - last_detect >= detect_interval:
                    next_frame = self._camera.read()
                    if next_frame is not None and self.flip_horizontal:
                        next_frame = cv2.flip(next_frame, 1)

                # Detección adaptativa: ajustar intervalo según movimiento.
                if self._adaptive_enabled:
                    current_interval = 1.0 / max(1, self._current_detect_fps)
                else:
                    current_interval = detect_interval

                faces = None
                detect_ms = None
                if start - last_detect >= current_interval:
                    t0 = time.time()
                    faces = self._detector.detect(frame)
                    detect_ms = (time.time() - t0) * 1000.0
                    last_detect = start

                    # Actualizar historial y decidir siguiente FPS.
                    if self._adaptive_enabled:
                        self._update_adaptive(faces, frame.shape[:2])

                # Buscar manos solo si hay alguien delante y está cerca.
                hands = None
                gesture = None
                gesture_ms = None
                someone_here = faces if faces is not None else self._faces
                face_big_enough = False
                if someone_here:
                    biggest = max(someone_here, key=lambda f: f[2] * f[3])
                    _, _, fw, fh = biggest
                    height, width = frame.shape[:2]
                    face_big_enough = (fw / width >= self._min_hand_face_frac
                                       or fh / height >= self._min_hand_face_frac)
                if (self._hand_detector is not None and face_big_enough
                        and start - last_gesture >= gesture_interval):
                    t0 = time.time()
                    hands = self._hand_detector.detect(frame)
                    gesture_ms = (time.time() - t0) * 1000.0
                    last_gesture = start
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
                        self._gesture = gesture
                    if delta > 0:
                        self._capture_fps_actual = 0.9 * self._capture_fps_actual + 0.1 * (1.0 / delta)

                sleep_for = capture_interval - (time.time() - start)
                if sleep_for > 0:
                    time.sleep(sleep_for)
        except Exception as e:
            with self._lock:
                self._error = "el thread de visión murió: %r" % (e,)

    def _update_adaptive(self, faces, frame_size):
        """Ajusta la frecuencia de detección según el movimiento de la cara.

        Si la cara está quieta, baja a _adapt_low FPS para ahorrar CPU.
        Si se movió mucho o se perdió, sube a _adapt_high FPS para reaccionar
        rápido.
        """
        if faces:
            biggest = max(faces, key=lambda f: f[2] * f[3])
            cx = (biggest[0] + biggest[2] / 2) / frame_size[1]
            cy = (biggest[1] + biggest[3] / 2) / frame_size[0]
            self._face_history.append((cx, cy))
        else:
            self._face_history.append(None)

        if len(self._face_history) > self._history_len:
            self._face_history.pop(0)

        if len(self._face_history) < 2:
            return

        # Calcular movimiento máximo entre frames consecutivos.
        max_move = 0.0
        prev = None
        for pos in self._face_history:
            if pos is not None and prev is not None:
                dx = pos[0] - prev[0]
                dy = pos[1] - prev[1]
                max_move = max(max_move, (dx * dx + dy * dy) ** 0.5)
            prev = pos

        # Si la cara se perdió (último frame None), subir a máximo.
        if self._face_history[-1] is None:
            self._current_detect_fps = self._adapt_high
        elif max_move < self._adapt_move_threshold:
            self._current_detect_fps = self._adapt_low
        else:
            self._current_detect_fps = self._adapt_high

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
