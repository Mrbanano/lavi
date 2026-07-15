import math

# Punto del pop donde la cara cambia: el instante más pequeño y transparente,
# que es lo que enmascara el cambio.
POP_SWAP_POINT = 0.42
POP_MIN_SCALE = 0.65
POP_MIN_ALPHA = 70
POP_OVERSHOOT = 2.0

# Los offsets son fracción del tamaño de la cara, no píxeles: la misma
# animación tiene que verse igual en la ventana de 800x600 y en el HDMI de la Pi.
NOD_AMPLITUDE = 0.05
NOD_CYCLES = 1.5
SHAKE_AMPLITUDE = 0.04
SHAKE_CYCLES = 3


def _ease_in_cubic(t):
    return t * t * t


def _ease_out_cubic(t):
    return 1 - (1 - t) ** 3


def _ease_in_out_sine(t):
    return 0.5 * (1 - math.cos(math.pi * t))


def _ease_out_back(t, overshoot=POP_OVERSHOOT):
    c1 = overshoot
    c3 = c1 + 1
    return 1 + c3 * (t - 1) ** 3 + c1 * (t - 1) ** 2


class Animator:
    def __init__(self, config=None):
        config = config or {}
        anim_config = config.get("animation", {})
        self.transition_speed = anim_config.get("transition_speed", 0.4)

        self.transition_progress = 1.0
        self.is_transitioning = False
        self.transition_type = "pop"
        self._swapped = True

        self.scale = 1.0
        self.alpha = 255
        self.offset_x = 0.0
        self.offset_y = 0.0

    def start_transition(self, transition_type="pop"):
        self.transition_progress = 0.0
        self.is_transitioning = True
        self.transition_type = transition_type
        self._swapped = False
        self._reset_pose()

    def start_nod(self):
        self.start_transition("nod")

    def start_shake(self):
        self.start_transition("shake")

    def _reset_pose(self):
        self.scale = 1.0
        self.alpha = 255
        self.offset_x = 0.0
        self.offset_y = 0.0

    def update(self, dt):
        if not self.is_transitioning:
            return

        self.transition_progress += dt / self.transition_speed

        if self.transition_progress >= 1.0:
            self.transition_progress = 1.0
            self.is_transitioning = False
            self._reset_pose()
            return

        t = self.transition_progress

        if self.transition_type == "pop":
            self._update_pop(t)
        elif self.transition_type == "nod":
            self._update_nod(t)
        elif self.transition_type == "shake":
            self._update_shake(t)
        elif self.transition_type == "fade":
            self._update_fade(t)

    def _update_pop(self, t):
        if t < POP_SWAP_POINT:
            # Se comprime acelerando, como tomando impulso.
            st = _ease_in_cubic(t / POP_SWAP_POINT)
            self.scale = 1.0 - (1.0 - POP_MIN_SCALE) * st
            self.alpha = 255 - int((255 - POP_MIN_ALPHA) * st)
        else:
            # Y rebota hacia afuera pasándose de 1.0 antes de asentarse.
            st = (t - POP_SWAP_POINT) / (1.0 - POP_SWAP_POINT)
            self.scale = POP_MIN_SCALE + (1.0 - POP_MIN_SCALE) * _ease_out_back(st)
            self.alpha = POP_MIN_ALPHA + int((255 - POP_MIN_ALPHA) * _ease_out_cubic(st))

    def _update_nod(self, t):
        # Oscilación amortiguada: cae, vuelve, y se asienta sola en 0 al llegar a t=1.
        decay = (1 - t) ** 1.5
        self.offset_y = NOD_AMPLITUDE * math.sin(t * NOD_CYCLES * 2 * math.pi) * decay

    def _update_shake(self, t):
        decay = (1 - t) ** 1.5
        self.offset_x = SHAKE_AMPLITUDE * math.sin(t * SHAKE_CYCLES * 2 * math.pi) * decay

    def _update_fade(self, t):
        if t < 0.5:
            self.alpha = 255 - int((255 - POP_MIN_ALPHA) * _ease_in_out_sine(t / 0.5))
        else:
            self.alpha = POP_MIN_ALPHA + int((255 - POP_MIN_ALPHA) * _ease_in_out_sine((t - 0.5) / 0.5))

    def should_swap(self):
        """True una sola vez por transición, cuando toca cambiar de cara."""
        if self._swapped:
            return False

        if self.transition_type == "pop":
            ready = self.transition_progress >= POP_SWAP_POINT
        elif self.transition_type == "fade":
            ready = self.transition_progress >= 0.5
        else:
            # nod y shake son reacciones: la cara no cambia, no hay que enmascarar nada.
            ready = True

        if ready:
            self._swapped = True
        return ready

    def get_scale(self):
        return self.scale

    def get_alpha(self):
        return self.alpha

    def get_offset(self):
        """Offset (x, y) como fracción del tamaño de la cara."""
        return (self.offset_x, self.offset_y)

    def is_done(self):
        return not self.is_transitioning
