import pygame
import math

class MouthType:
    SMILE = "smile"
    OPEN = "open"
    SAD = "sad"
    SURPRISE = "surprise"
    LINE = "line"

class Mouth:
    def __init__(self, color="#ffffff"):
        self.color = pygame.Color(color)
        self.current_type = MouthType.SMILE
        self.alpha = 255

    def set_type(self, mouth_type):
        self.current_type = mouth_type

    def set_alpha(self, alpha):
        self.alpha = alpha

    def draw(self, surface, x, y, width, height):
        if self.alpha <= 0:
            return

        temp = pygame.Surface((width, height), pygame.SRCALPHA)
        color = (*self.color[:3], int(self.alpha))
        line_width = max(2, width // 15)

        cx, cy = width // 2, height // 2

        if self.current_type == MouthType.SMILE:
            rect = pygame.Rect(width * 0.1, 0, width * 0.8, height * 0.8)
            pygame.draw.arc(temp, color, rect, math.radians(200), math.radians(340), line_width)

        elif self.current_type == MouthType.OPEN:
            mouth_rect = pygame.Rect(width * 0.15, height * 0.1, width * 0.7, height * 0.8)
            pygame.draw.ellipse(temp, color, mouth_rect)

        elif self.current_type == MouthType.SAD:
            rect = pygame.Rect(width * 0.1, height * 0.2, width * 0.8, height * 0.8)
            pygame.draw.arc(temp, color, rect, math.radians(20), math.radians(160), line_width)

        elif self.current_type == MouthType.SURPRISE:
            pygame.draw.circle(temp, color, (cx, cy), min(width, height) // 3)

        elif self.current_type == MouthType.LINE:
            pygame.draw.line(temp, color, (width * 0.2, cy), (width * 0.8, cy), line_width)

        surface.blit(temp, (x, y))
