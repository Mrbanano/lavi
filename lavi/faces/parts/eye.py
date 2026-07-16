import math

import pygame

# El ojo es más alto que ancho: un círculo perfecto se lee como un punto, y un
# óvalo vertical tiene más carácter. De paso le da recorrido al parpadeo, que
# con un círculo se quedaba corto.
EYE_ASPECT = 0.76      # ancho / alto
SEGMENTS = 72
HEART_BUCKETS = 180


def _build_heart_radius():
    """Radio del corazón en cada ángulo, para poder morfear desde un círculo.

    Un círculo es "radio 1 en todos los ángulos". Si el corazón se describe
    igual — un radio por ángulo — pasar de uno a otro es interpolar números, y
    entonces el corazón deja de ser la excepción del diseño: se morfea como todo
    lo demás, sin crossfade y sin corte.

    Se calcula una vez al importar. El bucle fino es para que ningún ángulo se
    quede sin muestra.
    """
    table = [0.0] * HEART_BUCKETS
    for i in range(7200):
        t = 2.0 * math.pi * i / 7200.0
        x = 16.0 * math.sin(t) ** 3
        # En pygame la y crece hacia abajo, de ahí el signo.
        y = -(13.0 * math.cos(t) - 5.0 * math.cos(2 * t)
              - 2.0 * math.cos(3 * t) - math.cos(4 * t))
        radius = math.hypot(x, y) / 17.0
        angle = math.atan2(y, x) % (2.0 * math.pi)
        bucket = int(angle / (2.0 * math.pi) * HEART_BUCKETS) % HEART_BUCKETS
        table[bucket] = max(table[bucket], radius)

    # Por si algún ángulo se quedara a cero: mejor copiar al vecino que dibujar
    # un pico hacia el centro.
    for i, value in enumerate(table):
        if value <= 0.0:
            table[i] = table[i - 1]
    return table


_HEART_RADIUS = _build_heart_radius()


class Eye:
    """Un ojo, descrito con números y no con tipos.

    Antes había EyeType.NORMAL / CLOSED / HEART / SLEEPY: estados discretos que
    se conmutaban, y por eso hacía falta el pop que tapase el corte. Aquí todo
    son valores continuos, así que un ojo puede estar a medio camino de
    cualquier cosa, y llegar hasta ahí es solo moverse.

    Los corazones eran la excepción confesada: no se podían interpolar desde un
    círculo, así que iban con un crossfade que se notaba. Ya no: el ojo es un
    polígono cuyo radio se interpola ángulo a ángulo, de círculo a corazón. Es
    un morfeo de verdad y no una mezcla de dos dibujos.
    """

    def __init__(self, color="#ffffff"):
        self.color = pygame.Color(color)
        self.alpha = 255

        self.open = 1.0     # 0 cerrado del todo, 1 abierto
        self.widen = 0.0    # 0..1, se abre de más: sorpresa
        self.hearts = 0.0   # 0..1, morfea de círculo a corazón

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
        cx = cy = size / 2.0
        color = (*self.color[:3], int(self.alpha))

        full_height = size * (0.92 + 0.08 * self.widen)
        ry = full_height / 2.0 * self.open
        rx = full_height / 2.0 * EYE_ASPECT * (1.0 + 0.10 * self.widen)

        # El párpado aplasta el ojo. Pasado el mínimo ya no es un óvalo de 1px:
        # es la línea del ojo cerrado, y ahí acaba el recorrido.
        min_height = max(2.0, size * 0.05)
        if ry * 2.0 <= min_height:
            width = max(2, int(size // 16))
            pygame.draw.line(temp, color, (cx - rx, cy), (cx + rx, cy), width)
        else:
            pygame.draw.polygon(temp, color, self._points(cx, cy, rx, ry))

        surface.blit(temp, (x, y))

    def _points(self, cx, cy, rx, ry):
        points = []
        for i in range(SEGMENTS):
            angle = 2.0 * math.pi * i / SEGMENTS
            bucket = int(angle / (2.0 * math.pi) * HEART_BUCKETS) % HEART_BUCKETS
            # Radio 1 es el óvalo; la tabla es el corazón. En medio, cualquier cosa.
            radius = 1.0 + (_HEART_RADIUS[bucket] - 1.0) * self.hearts
            points.append((cx + math.cos(angle) * radius * rx,
                           cy + math.sin(angle) * radius * ry))
        return points
