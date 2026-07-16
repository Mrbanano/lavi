import pygame


class Brow:
    """Una ceja. Existe solo cuando hace falta.

    Se apaga (`show` a 0) en la calma a propósito: la cara de Lavi son dos
    círculos y una boca, y ponerle cejas permanentes le cambiaría el carácter a
    todas las expresiones. Aparecen cuando aportan algo — enfado, sorpresa — y se
    van solas. Como `show` es un rasgo continuo más, entran y salen con un
    fundido, sin corte.

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

        self.show = 0.0    # 0 invisible, 1 del todo
        self.angle = 0.0   # -1 enfadada (dentro abajo), +1 preocupada (dentro arriba)
        self.raise_ = 0.0  # 0 baja, 1 levantada

    def set_alpha(self, alpha):
        self.alpha = alpha

    def set_features(self, show=None, angle=None, raise_=None):
        if show is not None:
            self.show = max(0.0, min(1.0, show))
        if angle is not None:
            self.angle = max(-1.0, min(1.0, angle))
        if raise_ is not None:
            self.raise_ = max(0.0, min(1.0, raise_))

    def draw(self, surface, x, y, width, height):
        alpha = self.alpha * self.show
        if alpha < 1:
            return

        temp = pygame.Surface((width, height), pygame.SRCALPHA)
        color = (*self.color[:3], int(alpha))
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
