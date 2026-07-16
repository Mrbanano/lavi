import math

import pygame


class Eye:
    """Un ojo, descrito con números y no con tipos.

    Antes había EyeType.NORMAL / CLOSED / HEART / SLEEPY: siete caras discretas
    que se conmutaban, y por eso hacía falta el pop que tapase el corte. Aquí
    todo son valores continuos, así que un ojo puede estar a medio camino entre
    dormido y despierto, y llegar hasta ahí es solo moverse.

    El corazón es la excepción confesada: no se puede interpolar desde un
    círculo, así que va con un crossfade. Se lo permitimos porque solo aparece
    como respuesta a un gesto explícito, y un salto que contesta a algo que has
    hecho tú se lee como intención y no como fallo.
    """

    def __init__(self, color="#ffffff"):
        self.color = pygame.Color(color)
        self.alpha = 255

        self.open = 1.0     # 0 cerrado del todo, 1 abierto
        self.widen = 0.0    # 0..1, se abre de más: sorpresa
        self.hearts = 0.0   # 0..1, crossfade de círculo a corazón

    def set_alpha(self, alpha):
        self.alpha = alpha

    def set_features(self, open=None, widen=None, hearts=None):
        if open is not None:
            self.open = max(0.0, min(1.0, open))
        if widen is not None:
            self.widen = max(0.0, min(1.0, widen))
        if hearts is not None:
            self.hearts = max(0.0, min(1.0, hearts))

    def draw(self, surface, x, y, size):
        if self.alpha <= 0:
            return

        temp = pygame.Surface((size, size), pygame.SRCALPHA)
        cx = cy = size // 2
        rgb = self.color[:3]

        # widen agranda el ojo entero: es lo que hace legible la sorpresa.
        diameter = size * (0.82 + 0.18 * self.widen)

        circle_alpha = self.alpha * (1.0 - self.hearts)
        heart_alpha = self.alpha * self.hearts

        # Cada forma va en su propia capa y se pega con blit. Dibujarlas las dos
        # sobre la misma superficie no funciona: pygame.draw *escribe* el alpha
        # en vez de mezclarlo, así que la segunda le pisa el suyo a la primera
        # donde se solapan y el ojo sale gris a mitad del fundido. El blit sí
        # mezcla, que es lo que hace que esto sea un crossfade y no una pelea.
        if circle_alpha >= 1:
            layer = pygame.Surface((size, size), pygame.SRCALPHA)
            self._draw_circle(layer, cx, cy, diameter, size, (*rgb, int(circle_alpha)))
            temp.blit(layer, (0, 0))
        if heart_alpha >= 1:
            layer = pygame.Surface((size, size), pygame.SRCALPHA)
            self._draw_heart(layer, cx, cy, diameter * 0.5, (*rgb, int(heart_alpha)))
            temp.blit(layer, (0, 0))

        surface.blit(temp, (x, y))

    def _draw_circle(self, temp, cx, cy, diameter, size, color):
        # El párpado aplasta el ojo verticalmente. Pasado el mínimo ya no es una
        # elipse de 1px: es la línea del ojo cerrado, y ahí acaba el recorrido.
        height = diameter * self.open
        min_height = max(2.0, size * 0.07)

        if height <= min_height:
            width = max(2, int(size // 14))
            pygame.draw.line(temp, color,
                             (cx - diameter / 2, cy), (cx + diameter / 2, cy), width)
            return

        rect = pygame.Rect(cx - diameter / 2, cy - height / 2, diameter, height)
        pygame.draw.ellipse(temp, color, rect)

    def _draw_heart(self, temp, cx, cy, radius, color):
        # El corazón también se aplasta al parpadear: si no, cerraría los ojos y
        # los corazones se quedarían mirando fijo.
        squash = max(0.05, self.open)
        points = []
        for angle in range(0, 360, 4):
            t = math.radians(angle)
            hx = 16 * math.sin(t) ** 3
            hy = -(13 * math.cos(t) - 5 * math.cos(2 * t) - 2 * math.cos(3 * t) - math.cos(4 * t))
            points.append((cx + hx * radius / 17.0, cy + hy * radius / 17.0 * squash))
        if len(points) > 2:
            pygame.draw.polygon(temp, color, points)
