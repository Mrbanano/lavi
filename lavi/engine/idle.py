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

        # La mosca: algo que no está pero que Lavi sigue. Es lo único de la vida
        # en reposo que implica que existe un mundo fuera de la pantalla; sin
        # ella, sola, Lavi solo mira al vacío dentro de su caja negra.
        fly_config = idle_config.get("fly", {})
        self.fly_enabled = fly_config.get("enabled", True)
        fly_every = fly_config.get("interval", [20.0, 50.0])
        self.fly_min, self.fly_max = fly_every[0], fly_every[1]
        self.fly_duration = fly_config.get("duration", 5.0)
        self.fly_range = fly_config.get("range", 0.8)
        self.fly_speed = fly_config.get("speed", 2.2)

        self._fly_until = None
        self._fly_at = random.uniform(self.fly_min, self.fly_max)
        self._fly_pos = [0.0, 0.0]
        self._fly_vel = [0.0, 0.0]
        self._fly_turn_at = 0.0

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

    def _update_fly(self, dt):
        """La mosca zigzaguea: cambia de rumbo cada poco, sin llegar a pararse."""
        if self._fly_until is None:
            if self.fly_enabled and self.t >= self._fly_at:
                self._fly_until = self.t + self.fly_duration
                # Entra por un lado, no aparece en el centro.
                self._fly_pos = [random.choice((-1.0, 1.0)) * self.fly_range, 0.0]
                self._fly_turn_at = 0.0
            return

        if self.t >= self._fly_until:
            # Se pierde de vista, y la mirada vuelve sola a lo suyo.
            self._fly_until = None
            self._fly_at = self.t + random.uniform(self.fly_min, self.fly_max)
            return

        if self.t >= self._fly_turn_at:
            self._fly_vel = [random.uniform(-1.0, 1.0) * self.fly_speed,
                             random.uniform(-1.0, 1.0) * self.fly_speed * 0.6]
            self._fly_turn_at = self.t + random.uniform(0.12, 0.45)

        for i in (0, 1):
            self._fly_pos[i] += self._fly_vel[i] * dt
            limit = self.fly_range if i == 0 else self.fly_range * 0.6
            if abs(self._fly_pos[i]) > limit:
                # Rebota en vez de salirse: una mosca no atraviesa la pared.
                self._fly_pos[i] = max(-limit, min(limit, self._fly_pos[i]))
                self._fly_vel[i] *= -1.0

    def is_watching_fly(self):
        return self._fly_until is not None

    def _update_drift(self, dt):
        if not self.drift_enabled:
            self._drift = [0.0, 0.0]
            return

        self._update_fly(dt)

        if self._fly_until is not None:
            # Seguir algo es rápido y con intención; mirar sin mirar es lento.
            # Esa diferencia de velocidad es lo que hace que se note que hay algo.
            alpha = 1.0 - math.exp(-dt / 0.12)
            for i in (0, 1):
                self._drift[i] += (self._fly_pos[i] - self._drift[i]) * alpha
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


class IdleMoods:
    """Lo que le pasa a la cara de puro aburrimiento.

    Devuelve el nombre de la emoción a empujar, y quien la empuja es el `main`:
    así esto no necesita conocer al `Mood`, y `Mood` sigue sin saber nada de
    temporizadores.

    No rompe la regla de "nada aparece sin causa": la causa es llevar un buen
    rato sin que pase nada, que es una causa como otra cualquiera. La diferencia
    con el ciclo viejo es que aquello cambiaba de cara **cada** 3.5s pasara lo que
    pasara; esto solo ocurre precisamente cuando **no** pasa nada, y se corta en
    cuanto pasa algo.

    Y son dos cosas distintas: empanarse es estar sola, suspirar es estar con
    alguien que no te hace ni caso. La segunda solo tiene sentido si hay alguien.
    """

    def __init__(self, config=None):
        config = config or {}
        moods_config = config.get("idle_moods", {})

        self.enabled = moods_config.get("enabled", True)

        zone_out = moods_config.get("zone_out_interval", [25.0, 60.0])
        self.zone_min, self.zone_max = zone_out[0], zone_out[1]

        sigh = moods_config.get("sigh_interval", [30.0, 70.0])
        self.sigh_min, self.sigh_max = sigh[0], sigh[1]

        self._t = 0.0
        self._zone_at = random.uniform(self.zone_min, self.zone_max)
        self._sigh_at = random.uniform(self.sigh_min, self.sigh_max)

    def update(self, dt, calm, someone_here):
        self._t += dt

        if not self.enabled or not calm:
            # Si está pasando algo, el reloj del aburrimiento se reinicia: no se
            # aburre a medias mientras reacciona.
            self._zone_at = max(self._zone_at, self._t + self.zone_min)
            self._sigh_at = max(self._sigh_at, self._t + self.sigh_min)
            return None

        if someone_here and self._t >= self._sigh_at:
            self._sigh_at = self._t + random.uniform(self.sigh_min, self.sigh_max)
            self._zone_at = max(self._zone_at, self._t + self.zone_min)
            return "suspiro"

        if self._t >= self._zone_at:
            self._zone_at = self._t + random.uniform(self.zone_min, self.zone_max)
            return "empanada"

        return None
