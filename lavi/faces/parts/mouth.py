import pygame

# Cuánto se arquea la boca con curve=1, en fracción de su ancho. Pasado ~0.3 la
# sonrisa se vuelve una U y deja de leerse como boca.
CURVE_DEPTH = 0.22
# Puntos de cada labio. 16 bastan: a esta escala no se ve el polígono.
SEGMENTS = 16


class Mouth:
    """Una boca, descrita con dos números en vez de con cinco tipos.

    Antes había MouthType.SMILE / OPEN / SAD / SURPRISE / LINE, y pasar de una a
    otra era un corte. Aquí hay dos labios que se dibujan a partir de `curve` y
    `open`, y todos los estados intermedios existen: una sonrisa puede abrirse
    poco a poco, y una boca triste puede enderezarse sin saltar.
    """

    def __init__(self, color="#ffffff"):
        self.color = pygame.Color(color)
        self.alpha = 255

        self.curve = 0.4   # -1 hacia abajo, 0 recta, +1 sonrisa
        self.open = 0.0    # 0 cerrada, 1 abierta del todo

    def set_alpha(self, alpha):
        self.alpha = alpha

    def set_features(self, curve=None, open=None):
        if curve is not None:
            self.curve = max(-1.0, min(1.0, curve))
        if open is not None:
            self.open = max(0.0, min(1.0, open))

    def draw(self, surface, x, y, width, height):
        if self.alpha <= 0:
            return

        temp = pygame.Surface((width, height), pygame.SRCALPHA)
        color = (*self.color[:3], int(self.alpha))

        line_width = max(2, width // 15)
        gap = self.open * height * 0.9

        if gap <= line_width:
            # Cerrada: no hay hueco que rellenar, es un trazo.
            pygame.draw.lines(temp, color, False, self._lip(width, height, 0.0), line_width)
        else:
            # Los dos labios se separan por igual del centro, y solo por el
            # centro: así el hueco sale con forma de lente, que es una O cuando
            # se abre del todo. Si solo bajara el de abajo saldría un trapecio,
            # y un asombro con boca de trapecio no se lee como asombro.
            upper = self._lip(width, height, -gap / 2.0)
            lower = self._lip(width, height, +gap / 2.0)
            pygame.draw.polygon(temp, color, upper + list(reversed(lower)))

        surface.blit(temp, (x, y))

    def _lip(self, width, height, spread):
        """Un labio. `spread` lo aparta del centro de la boca (+ abajo, - arriba)."""
        points = []
        for i in range(SEGMENTS):
            t = i / (SEGMENTS - 1.0)
            # 0 en las comisuras, 1 en el centro: las comisuras están clavadas y
            # lo único que se mueve es el centro.
            bend = 4.0 * t * (1.0 - t)
            px = width * 0.12 + t * width * 0.76
            # En pygame la y crece hacia abajo: sonreír es bajar el centro.
            py = height * 0.5 + self.curve * bend * width * CURVE_DEPTH + spread * bend
            points.append((px, py))
        return points
