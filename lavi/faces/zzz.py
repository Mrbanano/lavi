import math
import random

import pygame


class SleepZs:
    """Las Z que suben mientras Lavi duerme.

    Van aparte de los rasgos del rostro a propósito: no son una parte de la cara
    sino algo que sale de ella, y no tienen nada que interpolar. Se emiten, suben
    y se apagan.

    Al despertarse no se cortan de golpe: las que estén en el aire terminan su
    viaje y sencillamente no se emiten más. Cortarlas sería el mismo pecado que
    el pop.
    """

    def __init__(self, config=None):
        config = config or {}
        zzz_config = config.get("zzz", {})

        self.enabled = zzz_config.get("enabled", True)
        self.interval = zzz_config.get("interval", 1.6)
        self.lifetime = zzz_config.get("lifetime", 3.2)
        self.rise = zzz_config.get("rise", 0.42)       # fracción de la cara que sube
        self.drift = zzz_config.get("drift", 0.16)     # cuánto se va de lado
        self.color = pygame.Color(zzz_config.get("color", "#ffffff"))

        self._particles = []
        self._next_at = 0.0
        self._t = 0.0
        self._font = None
        self._font_size = None

    def update(self, dt, sleeping):
        self._t += dt

        if self.enabled and sleeping and self._t >= self._next_at:
            self._particles.append({
                "born": self._t,
                # Un poco de desorden: tres Z idénticas subiendo en fila son un
                # bucle de animación, no un sueño.
                "sway": random.uniform(-1.0, 1.0),
                "size": random.uniform(0.8, 1.2),
            })
            self._next_at = self._t + self.interval * random.uniform(0.75, 1.25)

        self._particles = [p for p in self._particles
                           if self._t - p["born"] < self.lifetime]

    def draw(self, surface, face_rect):
        if not self._particles:
            return

        x, y, w, h = face_rect
        # Salen de la sien derecha, que es de donde saldrían si estuviera
        # apoyada durmiendo.
        origin_x = x + w * 0.72
        origin_y = y + h * 0.30

        for p in self._particles:
            age = (self._t - p["born"]) / self.lifetime
            if age < 0 or age > 1:
                continue

            size = int(w * 0.09 * p["size"] * (0.6 + 0.4 * age))
            font = self._get_font(size)
            if font is None:
                continue

            # Se desvanece al final, no desde el principio: si no, nace medio
            # transparente y parece un fallo de dibujo.
            alpha = int(255 * min(1.0, (1.0 - age) * 2.5))
            if alpha <= 0:
                continue

            px = origin_x + w * self.drift * age + math.sin(age * math.pi * 1.5) * w * 0.03 * p["sway"]
            py = origin_y - h * self.rise * age

            glyph = font.render("Z", True, self.color[:3])
            glyph.set_alpha(alpha)
            surface.blit(glyph, (int(px), int(py)))

    def _get_font(self, size):
        size = max(8, size)
        if self._font is None or self._font_size != size:
            self._font = pygame.font.SysFont("menlo,dejavusansmono,monospace", size, bold=True)
            self._font_size = size
        return self._font
