import math

# Landmarks de MediaPipe: 0 muñeca, y luego cuatro por dedo de la base a la punta.
WRIST = 0
FINGERS = {
    # dedo: (punta, nudillo intermedio)
    "indice": (8, 6),
    "corazon": (12, 10),
    "anular": (16, 14),
    "menique": (20, 18),
}


def _distance(a, b):
    return math.hypot(a[0] - b[0], a[1] - b[1])


class GestureRecognizer:
    """Interpreta 21 landmarks de mano como gestos: saludo, ✌️ y .l.

    **Corre en el thread de visión, no en el de render, y eso es a propósito.**
    El saludo se detecta siguiendo la muñeca en el tiempo, y el loop de render va
    a 30 FPS mientras la detección va a 8: desde el render vería siete veces el
    mismo resultado y contaría vaivenes que no existen. Es la misma trampa que ya
    documentó la presencia, que por eso hace su debounce por tiempo.

    Hay un límite de muestreo que conviene tener presente: **un saludo es una
    oscilación de 1-2 Hz, así que no se puede detectar por debajo de ~8 FPS de
    detección** sin aliasing. Eso fija el ritmo mínimo de la detección de manos,
    y por tanto su coste. El "amor y paz" no tiene ese problema, porque es una
    postura quieta: ese sí se reconocería a 2 FPS.
    """

    def __init__(self, config=None):
        config = config or {}
        gesture_config = config.get("gestures", {})

        # Vaivenes de la muñeca para dar un saludo por bueno. Uno solo lo produce
        # cualquiera moviendo la mano sin querer.
        self.wave_reversals = gesture_config.get("wave_reversals", 3)
        self.wave_window = gesture_config.get("wave_window", 2.0)
        # En fracción del ancho del frame, para que no dependa de la resolución.
        self.wave_min_amplitude = gesture_config.get("wave_min_amplitude", 0.05)
        # Sin esto, mantener el ✌️ dispararía el gesto en cada detección.
        self.cooldown = gesture_config.get("cooldown", 3.0)

        self._direction = 0
        self._last_extreme = None
        self._reversals = []
        self._last_fired = -1e9

    def update(self, hands, frame_size, now):
        """hands: lista de manos (21 puntos). Devuelve el gesto o None."""
        if not hands or not frame_size:
            self._reset_wave()
            return None

        landmarks = hands[0]
        width = frame_size[0]
        if width <= 0:
            return None

        extended = self._extended_fingers(landmarks)

        gesture = None
        # Las posturas ganan al vaivén: si estás enseñando algo y además mueves
        # la mano, lo que quieres decir es lo que enseñas.
        if extended["indice"] and extended["corazon"] and not extended["anular"] and not extended["menique"]:
            gesture = "amor_y_paz"
        elif extended["corazon"] and not extended["indice"] and not extended["anular"] and not extended["menique"]:
            gesture = "peineta"
        elif self._update_wave(landmarks[WRIST][0] / float(width), now):
            gesture = "saludo"

        if gesture and now - self._last_fired >= self.cooldown:
            self._last_fired = now
            self._reset_wave()
            return gesture
        return None

    def _extended(self, landmarks, tip, pip):
        """Un dedo está estirado si su punta queda más lejos de la muñeca que su nudillo.

        Se mide contra la muñeca y no contra la vertical de la imagen para que
        valga con la mano girada: es el error que mató a Haar.
        """
        wrist = landmarks[WRIST]
        return _distance(landmarks[tip], wrist) > _distance(landmarks[pip], wrist) * 1.15

    def _extended_fingers(self, landmarks):
        return {name: self._extended(landmarks, tip, pip)
                for name, (tip, pip) in FINGERS.items()}

    def _update_wave(self, x, now):
        if self._last_extreme is None:
            self._last_extreme = x
            return False

        delta = x - self._last_extreme
        if self._direction == 0:
            if abs(delta) >= self.wave_min_amplitude:
                self._direction = 1 if delta > 0 else -1
                self._last_extreme = x
        elif (delta > 0) == (self._direction > 0):
            # Sigue hacia el mismo lado: el extremo se corre con la mano.
            self._last_extreme = x
        elif abs(delta) >= self.wave_min_amplitude:
            # Ha vuelto sobre sus pasos lo bastante como para contar.
            self._direction = -self._direction
            self._last_extreme = x
            self._reversals.append(now)

        self._reversals = [t for t in self._reversals if now - t <= self.wave_window]
        return len(self._reversals) >= self.wave_reversals

    def _reset_wave(self):
        self._direction = 0
        self._last_extreme = None
        self._reversals = []
