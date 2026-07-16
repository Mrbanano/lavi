import math
import random

from lavi.engine.dance import Dance


def _ease_out(t):
    return 1.0 - (1.0 - t) ** 2


def _ease_in_out(t):
    return 0.5 * (1.0 - math.cos(math.pi * t))


class _OneShot:
    """Un movimiento que ocurre una vez y se acaba. Devuelve 0..1 mientras dura."""

    def __init__(self, duration):
        self.duration = duration
        self._start = None

    def fire(self, now):
        self._start = now

    def progress(self, now):
        if self._start is None:
            return None
        p = (now - self._start) / self.duration
        if p >= 1.0:
            self._start = None
            return None
        return p

    @property
    def active(self):
        return self._start is not None


class Body:
    """Todo lo que mueve la cara entera: bailar, estirarse, dar un respingo, suspirar.

    Va aparte de los rasgos porque no es la cara lo que cambia, es dónde está.
    Los rasgos los lleva el Mood; esto es el cuerpo.

    Todo se suma: se puede dar un respingo en mitad de un bostezo sin que una
    cosa pise a la otra, igual que el parpadeo se compone con la emoción.
    """

    def __init__(self, config=None):
        config = config or {}
        body_config = config.get("body", {})

        self.dance = Dance(config)

        self.stretch_amount = body_config.get("stretch_amount", 0.055)
        self.stretch_lean = body_config.get("stretch_lean", 0.03)
        self._stretch = _OneShot(body_config.get("stretch_duration", 1.3))

        self.twitch_amount = body_config.get("twitch_amount", 0.018)
        self._twitch = _OneShot(body_config.get("twitch_duration", 0.28))
        twitch_every = body_config.get("twitch_interval", [7.0, 22.0])
        self.twitch_min, self.twitch_max = twitch_every[0], twitch_every[1]
        self._twitch_at = random.uniform(self.twitch_min, self.twitch_max)
        self._twitch_dir = 1.0

        self.sigh_amount = body_config.get("sigh_amount", 0.05)
        self._sigh = _OneShot(body_config.get("sigh_duration", 2.0))

        self._t = 0.0

    def update(self, dt, calm, sleeping):
        self._t += dt
        self.dance.update(dt, calm)

        # El respingo del que duerme: solo dormida, y de tarde en tarde.
        if sleeping:
            if not self._twitch.active and self._t >= self._twitch_at:
                self._twitch.fire(self._t)
                self._twitch_dir = random.choice((-1.0, 1.0))
                self._twitch_at = self._t + random.uniform(self.twitch_min, self.twitch_max)
        else:
            self._twitch_at = self._t + random.uniform(self.twitch_min, self.twitch_max)

    def stretch(self):
        """Al despertar. Se despereza."""
        self._stretch.fire(self._t)

    def sigh(self):
        """Coge aire y se desinfla."""
        self._sigh.fire(self._t)

    def is_dancing(self):
        return self.dance.is_dancing()

    def get_offset(self):
        x, y = self.dance.get_offset()

        p = self._stretch.progress(self._t)
        if p is not None:
            # Se ladea al desperezarse y vuelve: medio seno, empieza y acaba en 0.
            x += math.sin(math.pi * p) * self.stretch_lean

        p = self._twitch.progress(self._t)
        if p is not None:
            # Una sacudida que se apaga enseguida, no un vaivén.
            x += math.sin(math.pi * p * 3.0) * (1.0 - p) * self.twitch_amount * self._twitch_dir

        return (x, y)

    def get_scale(self):
        """Lo que hay que sumarle a la respiración."""
        scale = 0.0

        p = self._stretch.progress(self._t)
        if p is not None:
            scale += math.sin(math.pi * p) * self.stretch_amount

        p = self._sigh.progress(self._t)
        if p is not None:
            # Tres tiempos: coge aire, lo suelta pasándose de largo, y vuelve.
            # El bajón por debajo del reposo es el suspiro: sin él solo se hincha
            # y se deshincha, que es respirar hondo, no suspirar.
            a = self.sigh_amount
            if p < 0.30:
                scale += a * _ease_out(p / 0.30)
            elif p < 0.72:
                q = (p - 0.30) / 0.42
                scale += a + (-0.5 * a - a) * _ease_in_out(q)
            else:
                q = (p - 0.72) / 0.28
                scale += -0.5 * a * (1.0 - _ease_out(q))

        return scale
