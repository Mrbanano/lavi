import pygame

class EyeType:
    NORMAL = "normal"
    CLOSED = "closed"
    HEART = "heart"
    WINK = "wink"
    SLEEPY = "sleepy"

class Eye:
    def __init__(self, color="#ffffff"):
        self.color = pygame.Color(color)
        self.current_type = EyeType.NORMAL
        self.alpha = 255
        self.blink_progress = 0.0

    def set_type(self, eye_type):
        self.current_type = eye_type

    def set_alpha(self, alpha):
        self.alpha = alpha

    def set_blink(self, progress):
        """0 = abierto, 1 = cerrado del todo."""
        self.blink_progress = max(0.0, min(1.0, progress))

    def draw(self, surface, x, y, size):
        if self.alpha <= 0:
            return

        temp = pygame.Surface((size, size), pygame.SRCALPHA)
        center = (size // 2, size // 2)
        radius = size // 2

        color = (*self.color[:3], int(self.alpha))

        if self.current_type == EyeType.NORMAL:
            # El párpado aplasta el ojo verticalmente; al final del recorrido
            # se convierte en la misma línea que el ojo cerrado.
            open_amount = 1.0 - self.blink_progress
            if open_amount <= 0.15:
                pygame.draw.line(temp, color, (size * 0.2, center[1]), (size * 0.8, center[1]), max(2, size // 15))
            else:
                h = max(2, int(size * open_amount))
                pygame.draw.ellipse(temp, color, pygame.Rect(0, center[1] - h // 2, size, h))

        elif self.current_type == EyeType.CLOSED:
            line_color = color
            pygame.draw.line(temp, line_color, (size * 0.2, center[1]), (size * 0.8, center[1]), max(2, size // 15))

        elif self.current_type == EyeType.HEART:
            self._draw_heart(temp, center, radius, color)

        elif self.current_type == EyeType.WINK:
            pygame.draw.circle(temp, color, center, radius)

        elif self.current_type == EyeType.SLEEPY:
            line_color = color
            pygame.draw.line(temp, line_color, (size * 0.15, center[1]), (size * 0.85, center[1]), max(2, size // 12))

        surface.blit(temp, (x, y))

    def _draw_heart(self, surface, center, radius, color):
        import math
        cx, cy = center
        r = radius * 0.8
        points = []
        for angle in range(360):
            t = math.radians(angle)
            x = r * 16 * math.sin(t) ** 3
            y = -r * (13 * math.cos(t) - 5 * math.cos(2*t) - 2 * math.cos(3*t) - math.cos(4*t))
            points.append((cx + x/17, cy + y/17))
        if len(points) > 2:
            pygame.draw.polygon(surface, color, points)