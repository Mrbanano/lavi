import math
import random

import pygame


class FloatingGlyphs:
    """Glifos que salen de la cara, suben y se apagan. Las Z de dormir, las notas de bailar.

    Van aparte de los rasgos del rostro a propósito: no son partes de la cara
    sino cosas que salen de ella, y no tienen nada que interpolar. Se emiten,
    suben y se apagan.

    Cuando deja de haber motivo no se cortan de golpe: las que estén en el aire
    terminan su viaje y sencillamente no se emiten más. Cortarlas sería el mismo
    pecado que el pop.
    """

    def __init__(self, glyphs, origin, settings=None):
        settings = settings or {}

        # Varios glifos y no uno: tres notas idénticas en fila son un bucle de
        # animación, no música.
        self.glyphs = glyphs
        self.origin = origin  # (fx, fy) en fracción del rect de la cara

        self.enabled = settings.get("enabled", True)
        self.interval = settings.get("interval", 1.6)
        self.lifetime = settings.get("lifetime", 3.2)
        self.rise = settings.get("rise", 0.42)      # fracción de la cara que sube
        self.drift = settings.get("drift", 0.16)    # cuánto se va de lado
        self.size = settings.get("size", 0.09)      # fracción del ancho de la cara
        # A qué distancia del origen nacen ya. Las notas nacen al costado de la
        # cabeza y no en mitad de la cara: naciendo en el centro le cruzan los
        # ojos por encima y parecen un fallo de dibujo, no música.
        self.spawn_offset = settings.get("spawn_offset", 0.0)
        # Las Z salen todas hacia el mismo lado, como el humo de una sien. Las
        # notas se reparten a los dos, que es como suena la música.
        self.spread = settings.get("spread", False)
        self.color = pygame.Color(settings.get("color", "#ffffff"))

        self._particles = []
        self._next_at = 0.0
        self._t = 0.0
        self._font = None
        self._font_size = None

    def update(self, dt, emitting):
        self._t += dt

        if self.enabled and emitting and self._t >= self._next_at:
            self._particles.append({
                "born": self._t,
                "glyph": random.choice(self.glyphs),
                "sway": random.uniform(-1.0, 1.0),
                "scale": random.uniform(0.8, 1.2),
                "side": random.choice((-1.0, 1.0)) if self.spread else 1.0,
            })
            self._next_at = self._t + self.interval * random.uniform(0.75, 1.25)

        self._particles = [p for p in self._particles
                           if self._t - p["born"] < self.lifetime]

    def draw(self, surface, face_rect):
        if not self._particles:
            return

        x, y, w, h = face_rect
        origin_x = x + w * self.origin[0]
        origin_y = y + h * self.origin[1]

        for p in self._particles:
            age = (self._t - p["born"]) / self.lifetime
            if age < 0.0 or age > 1.0:
                continue

            size = int(w * self.size * p["scale"] * (0.6 + 0.4 * age))
            font = self._get_font(size)
            if font is None:
                continue

            # Se desvanece al final, no desde el principio: si no, nace medio
            # transparente y parece un fallo de dibujo.
            alpha = int(255 * min(1.0, (1.0 - age) * 2.5))
            if alpha <= 0:
                continue

            px = (origin_x
                  + w * (self.spawn_offset + self.drift * age) * p["side"]
                  + math.sin(age * math.pi * 1.5) * w * 0.03 * p["sway"])
            py = origin_y - h * self.rise * age

            glyph = font.render(p["glyph"], True, self.color[:3])
            glyph.set_alpha(alpha)
            surface.blit(glyph, (int(px), int(py)))

    def _get_font(self, size):
        size = max(8, size)
        if self._font is None or self._font_size != size:
            self._font = pygame.font.SysFont("menlo,dejavusansmono,monospace", size, bold=True)
            self._font_size = size
        return self._font
