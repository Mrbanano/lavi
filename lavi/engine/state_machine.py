import math
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
        self.paused = False

    def update(self):
        now = time.time()

        if self.is_blinking:
            if now - self.blink_start >= self.blink_duration:
                self.is_blinking = False
                self.next_blink = now + random.uniform(self.blink_interval_min, self.blink_interval_max)
                return "blink_end"
            return None

        if not self.paused and now - self.last_change >= self.expression_duration:
            self.current_index = (self.current_index + 1) % len(self.expression_names)
            self.current_name = self.expression_names[self.current_index]
            self.last_change = now
            return "expression_change"

        if now >= self.next_blink:
            self.is_blinking = True
            self.blink_start = now
            return "blink_start"

        return None

    def set_current(self, name):
        """Fuerza una expresión, saltándose el ciclo. La usa la presencia."""
        if name not in self.expression_names:
            return False
        self.current_index = self.expression_names.index(name)
        self.current_name = name
        self.last_change = time.time()
        return True

    def pause(self):
        self.paused = True

    def resume(self):
        self.paused = False
        self.last_change = time.time()

    def get_blink_progress(self):
        """0 abierto, 1 cerrado. Sube y baja como medio seno: cierra y abre sin cortes."""
        if not self.is_blinking:
            return 0.0
        t = (time.time() - self.blink_start) / self.blink_duration
        t = max(0.0, min(1.0, t))
        return math.sin(math.pi * t)

    def get_current(self):
        return self.current_name

    def get_next(self):
        idx = (self.current_index + 1) % len(self.expression_names)
        return self.expression_names[idx]
