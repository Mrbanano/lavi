import time
import random

class StateMachine:
    def __init__(self, expression_names, config=None):
        config = config or {}
        anim_config = config.get("animation", {})

        self.expression_names = expression_names
        self.current_index = 0
        self.current_name = expression_names[0]
        self.next_name = None

        self.expression_duration = anim_config.get("expression_duration", 3.5)
        self.blink_interval_min = anim_config.get("blink_interval_min", 3)
        self.blink_interval_max = anim_config.get("blink_interval_max", 5)

        self.last_change = time.time()
        self.next_blink = time.time() + random.uniform(self.blink_interval_min, self.blink_interval_max)
        self.is_blinking = False
        self.blink_start = 0
        self.blink_duration = 0.15

    def update(self):
        now = time.time()

        if self.is_blinking:
            if now - self.blink_start >= self.blink_duration:
                self.is_blinking = False
                self.next_blink = now + random.uniform(self.blink_interval_min, self.blink_interval_max)
            return "blink_end"

        if now - self.last_change >= self.expression_duration:
            self.current_index = (self.current_index + 1) % len(self.expression_names)
            self.current_name = self.expression_names[self.current_index]
            self.last_change = now
            return "expression_change"

        if now >= self.next_blink:
            self.is_blinking = True
            self.blink_start = now
            return "blink_start"

        return None

    def get_current(self):
        return self.current_name

    def get_next(self):
        idx = (self.current_index + 1) % len(self.expression_names)
        return self.expression_names[idx]
