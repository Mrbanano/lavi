import math

from lavi.faces.expressions import BASELINE, FEATURES, SLEEP, blend, preset


class Mood:
    """El estado de ánimo. Reacciona a lo que pasa y se le va pasando solo.

    Sustituye al ciclo por temporizador, que es lo que delataba a Lavi como
    programa: cambiaba de cara cada 3.5s sin que hubiera ocurrido nada. Aquí
    ninguna emoción aparece si no la empuja un evento.

    El modelo son dos cosas:
      - un **reposo** (`baseline`), que es donde vive por defecto,
      - una **emoción** con una **intensidad** que decae sola hasta cero.

    Los rasgos que se dibujan son la mezcla de los dos según la intensidad, así
    que la vuelta a la calma sale gratis: no hay que programarla, ocurre.

    De ahí sale también el ataque rápido y la vuelta lenta, sin ningún caso
    especial: al empujar, la intensidad salta a 1 de golpe y los rasgos corren
    hacia la emoción en ~0.5s; luego la intensidad tarda `decay` segundos en
    bajar, y los rasgos la siguen sin esfuerzo. Rápido al reaccionar, lento al
    calmarse, con un solo suavizado.
    """

    def __init__(self, config=None):
        config = config or {}
        mood_config = config.get("mood", {})

        # Cuánto tarda una emoción a tope en apagarse del todo.
        self.decay = mood_config.get("decay", 6.0)
        # Cuánto tardan los rasgos en alcanzar su objetivo.
        self.time_constant = mood_config.get("feature_time_constant", 0.18)

        self.baseline = BASELINE
        self.emotion = BASELINE
        self.intensity = 0.0
        self.features = preset(BASELINE)
        self._decay = self.decay

    def set_baseline(self, name):
        """Dónde vuelve cuando se le pasa: `calma` despierta, `dormida` sin nadie."""
        self.baseline = name

    def push(self, name, intensity=1.0, decay=None):
        """Le ha pasado algo. Se le pasará solo.

        `decay` deja que cada emoción dure lo suyo: un bostezo se va en dos
        segundos y un enamoramiento no. Con un único decaimiento para todas,
        Lavi se quedaba bostezando como si fuera un estado de ánimo.
        """
        self.emotion = name
        # max() y no asignación: un empujón flojo no debe apagar una emoción que
        # todavía está viva.
        self.intensity = max(self.intensity, max(0.0, min(1.0, intensity)))
        self._decay = decay if decay is not None else self.decay

    def update(self, dt):
        if self._decay > 0:
            self.intensity = max(0.0, self.intensity - dt / self._decay)
        else:
            self.intensity = 0.0

        target = blend(preset(self.baseline), preset(self.emotion), self.intensity)

        if self.time_constant > 0:
            alpha = 1.0 - math.exp(-dt / self.time_constant)
        else:
            alpha = 1.0

        for key in FEATURES:
            self.features[key] += (target[key] - self.features[key]) * alpha
        return self.features

    def get(self):
        return self.features

    def is_sleeping(self):
        """Duerme si su reposo es dormir y no le queda emoción encima."""
        return self.baseline == SLEEP and self.intensity < 0.15

    def is_calm(self):
        """Despierta y sin que le esté pasando nada."""
        return self.baseline != SLEEP and self.intensity < 0.15
