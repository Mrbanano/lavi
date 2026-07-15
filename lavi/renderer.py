import pygame

class Renderer:
    def __init__(self, config=None):
        config = config or {}
        display_config = config.get("display", {})

        self.bg_color = pygame.Color(display_config.get("bg_color", "#000000"))
        self.fullscreen = display_config.get("fullscreen", True)

        pygame.init()
        info = pygame.display.Info()
        self.width = info.current_w
        self.height = info.current_h

        if self.fullscreen:
            self.screen = pygame.display.set_mode((0, 0), pygame.FULLSCREEN)
        else:
            self.screen = pygame.display.set_mode((800, 600))

        pygame.display.set_caption("Lavi")
        self.clock = pygame.time.Clock()
        self.running = True

    def clear(self):
        self.screen.fill(self.bg_color)

    def draw_face(self, face, alpha):
        face.set_alpha(alpha)
        face_rect = self._get_face_rect()
        face.draw(self.screen, face_rect)

    def _get_face_rect(self):
        w = self.screen.get_width()
        h = self.screen.get_height()
        size = min(w, h) * 0.6
        x = (w - size) / 2
        y = (h - size) / 2
        return (x, y, size, size)

    def update(self):
        pygame.display.flip()

    def tick(self, fps=30):
        return self.clock.tick(fps) / 1000.0

    def handle_events(self):
        for event in pygame.event.get():
            if event.type == pygame.QUIT:
                self.running = False
            elif event.type == pygame.KEYDOWN:
                if event.key == pygame.K_ESCAPE:
                    self.running = False

    def quit(self):
        pygame.quit()
