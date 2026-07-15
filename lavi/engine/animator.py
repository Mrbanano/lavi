class Animator:
    def __init__(self, config=None):
        config = config or {}
        anim_config = config.get("animation", {})
        self.transition_speed = anim_config.get("transition_speed", 0.4)
        self.transition_progress = 1.0
        self.is_transitioning = False
        self.from_alpha = 0
        self.to_alpha = 255

    def start_transition(self, from_alpha=0, to_alpha=255):
        self.transition_progress = 0.0
        self.is_transitioning = True
        self.from_alpha = from_alpha
        self.to_alpha = to_alpha

    def update(self, dt):
        if not self.is_transitioning:
            return

        self.transition_progress += dt / self.transition_speed

        if self.transition_progress >= 1.0:
            self.transition_progress = 1.0
            self.is_transitioning = False

    def get_alpha(self):
        if not self.is_transitioning:
            return self.to_alpha

        t = self.transition_progress
        return int(self.from_alpha + (self.to_alpha - self.from_alpha) * t)

    def is_done(self):
        return not self.is_transitioning
