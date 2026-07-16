import pygame


class Brow:
    """Una ceja. Siempre está.

    Antes se apagaba en la calma y aparecía al enfadarse, buscando mantener la
    cara mínima. Era un error: a un ser vivo no le crecen cejas cuando se cabrea.
    Que salgan y entren delata que detrás hay un parámetro, que es justo la
    ilusión que este milestone intenta sostener. Si las tiene, las tiene siempre;
    lo que cambia es cómo están puestas.

    Los dos extremos no son iguales: el de dentro (el que mira a la nariz) es el
    que se mueve. Bajarlo es enfadarse y subirlo es preocuparse, y esa asimetría
    es la que hace que se lea la emoción.
    """

    def __init__(self, color="#ffffff", side=-1):
        # side: -1 la ceja izquierda, +1 la derecha. Se necesita porque el
        # extremo de dentro está en un lado distinto en cada una.
        self.color = pygame.Color(color)
        self.side = side
        self.alpha = 255

        self.angle = 0.0   # -1 enfadada (dentro abajo), +1 preocupada (dentro arriba)
        self.raise_ = 0.0  # 0 baja, 1 levantada

    def set_alpha(self, alpha):
        self.alpha = alpha

    def set_features(self, angle=None, raise_=None):
        if angle is not None:
            self.angle = max(-1.0, min(1.0, angle))
        if raise_ is not None:
            self.raise_ = max(0.0, min(1.0, raise_))

    def draw(self, surface, x, y, width, height):
        if self.alpha < 1:
            return

        temp = pygame.Surface((width, height), pygame.SRCALPHA)
        color = (*self.color[:3], int(self.alpha))
        line_width = max(2, int(height * 0.30))

        # Levantarla la sube dentro de su hueco, sin salirse.
        base_y = height * (0.72 - 0.42 * self.raise_)
        tilt = self.angle * height * 0.42

        if self.side < 0:
            outer = (width * 0.05, base_y)
            inner = (width * 0.95, base_y - tilt)
        else:
            outer = (width * 0.95, base_y)
            inner = (width * 0.05, base_y - tilt)

        pygame.draw.line(temp, color, outer, inner, line_width)
        surface.blit(temp, (x, y))
