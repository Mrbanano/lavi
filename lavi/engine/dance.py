import math
import random


class Dance:
    """De vez en cuando, si está tranquila, a Lavi le da por bailar.

    Es lo mismo que respirar o mirar alrededor, solo que más grande: cosas que
    hace un bicho porque sí. No rompe la regla de "nada aparece sin causa", que
    va de las **emociones**: bailar no es una emoción, es un gesto ocioso, y solo
    ocurre cuando no está pasando nada. En cuanto pasa algo, deja de bailar.

    El movimiento son dos ritmos encajados: un rebote a cada tiempo y un vaivén
    más lento cada cuatro. Eso es lo que hace que se lea como compás y no como
    una oscilación cualquiera.

    Entra y sale con un `level` que sube y baja despacio, así que nunca arranca
    ni frena de golpe: eso sería el pop otra vez.
    """

    def __init__(self, config=None):
        config = config or {}
        dance_config = config.get("dance", {})

        self.enabled = dance_config.get("enabled", True)
        self.bpm = dance_config.get("bpm", 96)
        self.duration = dance_config.get("duration", 7.0)
        interval = dance_config.get("interval", [18.0, 40.0])
        self.interval_min, self.interval_max = interval[0], interval[1]

        # En fracción del tamaño de la cara, como todos los offsets.
        self.sway = dance_config.get("sway", 0.045)
        self.bob = dance_config.get("bob", 0.028)
        self.fade = dance_config.get("fade", 0.7)

        self._t = 0.0
        self._started = None
        self._level = 0.0
        self._next_at = random.uniform(self.interval_min, self.interval_max)

    def update(self, dt, calm):
        self._t += dt

        if not self.enabled:
            calm = False

        if self._started is None:
            if calm and self._t >= self._next_at:
                self._started = self._t
        else:
            # Deja de bailar si se acaba la canción o si pasa cualquier cosa.
            if self._t - self._started >= self.duration or not calm:
                self._started = None
                self._next_at = self._t + random.uniform(self.interval_min, self.interval_max)

        target = 1.0 if self._started is not None else 0.0
        self._level += (target - self._level) * (1.0 - math.exp(-dt / self.fade))

    def is_dancing(self):
        return self._started is not None

    def get_offset(self):
        if self._level < 0.005:
            return (0.0, 0.0)

        beat = self._t * self.bpm / 60.0
        # El rebote va a cada tiempo y siempre hacia arriba: por eso el valor
        # absoluto. Un seno normal la hundiría media negra en cada compás.
        bob = -abs(math.sin(math.pi * beat)) * self.bob
        # El vaivén tarda cuatro tiempos en ir y volver: es el compás.
        sway = math.sin(2.0 * math.pi * beat / 4.0) * self.sway
        return (sway * self._level, bob * self._level)
