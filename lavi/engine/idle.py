import math
import random


class IdleLife:
    """Lo que hace Lavi cuando no pasa absolutamente nada.

    Es el 90% de que algo parezca vivo, y hasta ahora no había nada: entre
    cambio y cambio de cara, Lavi era una imagen fija. Un ser vivo quieto sigue
    respirando, parpadeando y mirando alrededor.

    Todo va contra un reloj propio acumulado de los `dt`, y no contra
    `time.time()`, para poder guionizarlo en las pruebas sin esperar en real.
    """

    def __init__(self, config=None):
        config = config or {}
        idle_config = config.get("idle", {})

        # Tan sutil que no se ve mirándola. Se nota al quitarlo, que es la gracia.
        self.breath_amplitude = idle_config.get("breath_amplitude", 0.015)
        self.breath_period = idle_config.get("breath_period", 4.0)

        blink_interval = idle_config.get("blink_interval", [2.0, 6.0])
        self.blink_min, self.blink_max = blink_interval[0], blink_interval[1]
        self.blink_duration = idle_config.get("blink_duration", 0.14)
        self.double_blink_chance = idle_config.get("double_blink_chance", 0.15)

        self.drift_enabled = idle_config.get("gaze_drift", True)
        self.drift_amount = idle_config.get("gaze_drift_amount", 0.25)
        drift_interval = idle_config.get("gaze_drift_interval", [1.5, 4.0])
        self.drift_min, self.drift_max = drift_interval[0], drift_interval[1]

        self.t = 0.0
        self.blink = 0.0

        self._blink_at = random.uniform(self.blink_min, self.blink_max)
        self._blink_start = None
        self._double_pending = False

        self._drift = [0.0, 0.0]
        self._drift_target = [0.0, 0.0]
        self._drift_at = random.uniform(self.drift_min, self.drift_max)

    def update(self, dt):
        self.t += dt
        self._update_blink()
        self._update_drift(dt)

    def _update_blink(self):
        if self._blink_start is None:
            if self.t >= self._blink_at:
                self._blink_start = self.t
            return

        progress = (self.t - self._blink_start) / self.blink_duration
        if progress >= 1.0:
            self.blink = 0.0
            self._blink_start = None
            if self._double_pending:
                # Un parpadeo doble de vez en cuando: parpadear siempre igual y
                # siempre solo es de reloj, no de bicho.
                self._double_pending = False
                self._blink_at = self.t + 0.12
            else:
                self._blink_at = self.t + random.uniform(self.blink_min, self.blink_max)
                self._double_pending = random.random() < self.double_blink_chance
        else:
            # Medio seno: cierra y abre sin cortes.
            self.blink = math.sin(math.pi * progress)

    def _update_drift(self, dt):
        if not self.drift_enabled:
            self._drift = [0.0, 0.0]
            return

        if self.t >= self._drift_at:
            self._drift_target = [
                random.uniform(-1.0, 1.0) * self.drift_amount,
                # Menos recorrido en vertical: mirar arriba y abajo canta más
                # que mirar de lado, y queda raro.
                random.uniform(-1.0, 1.0) * self.drift_amount * 0.5,
            ]
            self._drift_at = self.t + random.uniform(self.drift_min, self.drift_max)

        # Lento a propósito: es mirar sin mirar, no buscar algo.
        alpha = 1.0 - math.exp(-dt / 0.8)
        for i in (0, 1):
            self._drift[i] += (self._drift_target[i] - self._drift[i]) * alpha

    def breath_scale(self):
        return 1.0 + self.breath_amplitude * math.sin(2.0 * math.pi * self.t / self.breath_period)

    def get_blink(self):
        return self.blink

    def get_drift(self):
        return (self._drift[0], self._drift[1])
