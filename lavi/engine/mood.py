import math

from lavi.faces.expressions import BASELINE, FEATURES, blend, preset


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

    def set_baseline(self, name):
        """Dónde vuelve cuando se le pasa: `calma` despierta, `dormida` sin nadie."""
        self.baseline = name

    def push(self, name, intensity=1.0):
        """Le ha pasado algo. Se le pasará solo."""
        self.emotion = name
        # max() y no asignación: un empujón flojo no debe apagar una emoción que
        # todavía está viva.
        self.intensity = max(self.intensity, max(0.0, min(1.0, intensity)))

    def update(self, dt):
        if self.decay > 0:
            self.intensity = max(0.0, self.intensity - dt / self.decay)
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
