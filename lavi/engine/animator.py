import math

class Animator:
    def __init__(self, config=None):
        config = config or {}
        anim_config = config.get("animation", {})
        self.transition_speed = anim_config.get("transition_speed", 0.3)
        self.transition_progress = 1.0
        self.is_transitioning = False
        self.transition_type = "pop"  # pop, fade, scale

        self.scale = 1.0
        self.alpha = 255
        self.offset_x = 0
        self.offset_y = 0

    def start_transition(self, transition_type="pop"):
        self.transition_progress = 0.0
        self.is_transitioning = True
        self.transition_type = transition_type

    def start_nod(self):
        self.start_transition("nod")

    def start_shake(self):
        self.start_transition("shake")

    def update(self, dt):
        if not self.is_transitioning:
            return

        self.transition_progress += dt / self.transition_speed

        if self.transition_progress >= 1.0:
            self.transition_progress = 1.0
            self.is_transitioning = False
            self.scale = 1.0
            self.alpha = 255
            self.offset_x = 0
            self.offset_y = 0
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
        # Shrink to 0 at t=0.5, grow back
        if t < 0.5:
            # Shrink phase
            st = t / 0.5
            self.scale = 1.0 - st
            self.alpha = 255 - int(200 * st)
        else:
            # Grow phase
            st = (t - 0.5) / 0.5
            self.scale = st
            self.alpha = 55 + int(200 * st)

    def _update_nod(self, t):
        # Yes nod - tilt down then up
        self.scale = 1.0
        self.alpha = 255
        if t < 0.3:
            self.offset_y = 15 * (t / 0.3)
        elif t < 0.6:
            self.offset_y = 15 * (1 - (t - 0.3) / 0.3)
        elif t < 0.8:
            self.offset_y = 8 * ((t - 0.6) / 0.2)
        else:
            self.offset_y = 8 * (1 - (t - 0.8) / 0.2)

    def _update_shake(self, t):
        # No shake - left right left
        self.scale = 1.0
        self.alpha = 255
        cycles = 3
        self.offset_x = 12 * math.sin(t * cycles * 2 * math.pi)

    def _update_fade(self, t):
        if t < 0.5:
            self.alpha = 255 - int(200 * (t / 0.5))
        else:
            self.alpha = 55 + int(200 * ((t - 0.5) / 0.5))
        self.scale = 1.0

    def get_scale(self):
        return self.scale

    def get_alpha(self):
        return self.alpha

    def get_offset(self):
        return (self.offset_x, self.offset_y)

    def is_done(self):
        return not self.is_transitioning
