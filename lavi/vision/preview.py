import cv2
import numpy as np
import pygame

PANEL_BG = (18, 18, 22, 220)
PANEL_BORDER = (70, 70, 82)
TEXT_COLOR = (200, 200, 210)
FACE_BOX_COLOR = (0, 230, 120)
HAND_DOT_COLOR = (255, 190, 60)
DOT_FACE = (0, 230, 120)
DOT_IDLE = (110, 110, 120)
DOT_ERROR = (230, 70, 70)


class CameraPreview:
    """Overlay colapsable con lo que ve la cámara.

    Es una herramienta de diagnóstico: sirve para encuadrar la cámara y ver si
    la detección engancha. Por eso arranca colapsada — en el kiosko la cara es
    lo único que debería verse.
    """

    def __init__(self, config=None):
        config = config or {}
        preview_config = config.get("preview", {})

        self.enabled = preview_config.get("enabled", True)
        self.expanded = preview_config.get("start_expanded", False)
        self.width_fraction = preview_config.get("width_fraction", 0.22)
        self.margin_fraction = preview_config.get("margin_fraction", 0.02)
        self.position = preview_config.get("position", "bottom_right")
        self.show_stats = preview_config.get("show_stats", True)

        self._font = None
        self._font_size = None

    def toggle(self):
        self.expanded = not self.expanded
        return self.expanded

    def _get_font(self, surface):
        size = max(11, int(min(surface.get_width(), surface.get_height()) * 0.018))
        if self._font is None or self._font_size != size:
            self._font = pygame.font.SysFont("menlo,dejavusansmono,monospace", size)
            self._font_size = size
        return self._font

    def _anchor(self, surface, w, h):
        sw, sh = surface.get_width(), surface.get_height()
        margin = int(min(sw, sh) * self.margin_fraction)
        if self.position == "bottom_left":
            return margin, sh - h - margin
        if self.position == "top_right":
            return sw - w - margin, margin
        if self.position == "top_left":
            return margin, margin
        return sw - w - margin, sh - h - margin

    def draw(self, surface, service):
        if not self.enabled:
            return
        if self.expanded:
            self._draw_expanded(surface, service)
        else:
            self._draw_collapsed(surface, service)

    def _draw_collapsed(self, surface, service):
        """Colapsado: solo un punto de estado, para no competir con la cara."""
        font = self._get_font(surface)
        label = font.render("cam  C", True, TEXT_COLOR)

        pad = font.get_height() // 2
        dot_r = max(3, font.get_height() // 5)
        w = label.get_width() + pad * 3 + dot_r * 2
        h = label.get_height() + pad
        x, y = self._anchor(surface, w, h)

        panel = pygame.Surface((w, h), pygame.SRCALPHA)
        pygame.draw.rect(panel, PANEL_BG, panel.get_rect(), border_radius=h // 3)
        pygame.draw.rect(panel, PANEL_BORDER, panel.get_rect(), width=1, border_radius=h // 3)
        surface.blit(panel, (x, y))

        if service.error:
            dot_color = DOT_ERROR
        elif service.has_face():
            dot_color = DOT_FACE
        else:
            dot_color = DOT_IDLE
        pygame.draw.circle(surface, dot_color, (x + pad + dot_r, y + h // 2), dot_r)
        surface.blit(label, (x + pad * 2 + dot_r * 2, y + (h - label.get_height()) // 2))

    def _draw_expanded(self, surface, service):
        font = self._get_font(surface)
        pad = max(4, font.get_height() // 3)

        panel_w = int(surface.get_width() * self.width_fraction)
        frame, faces = service.snapshot()

        if frame is not None:
            aspect = frame.shape[0] / frame.shape[1]
        else:
            aspect = 0.75
        video_h = int(panel_w * aspect)

        stats_lines = self._stats_lines(service) if self.show_stats else []
        stats_h = len(stats_lines) * (font.get_height() + 2)
        panel_h = video_h + stats_h + pad * 2

        x, y = self._anchor(surface, panel_w, panel_h)

        panel = pygame.Surface((panel_w, panel_h), pygame.SRCALPHA)
        pygame.draw.rect(panel, PANEL_BG, panel.get_rect(), border_radius=8)
        pygame.draw.rect(panel, PANEL_BORDER, panel.get_rect(), width=1, border_radius=8)
        surface.blit(panel, (x, y))

        if frame is not None:
            video = self._frame_to_surface(frame, panel_w, video_h)
            surface.blit(video, (x, y))
            self._draw_face_boxes(surface, faces, frame, x, y, panel_w, video_h)
            self._draw_hands(surface, service.hands(), frame, x, y, panel_w, video_h)
        else:
            msg = font.render("sin señal", True, TEXT_COLOR)
            surface.blit(msg, (x + (panel_w - msg.get_width()) // 2, y + video_h // 2))

        text_y = y + video_h + pad
        for line in stats_lines:
            label = font.render(line, True, TEXT_COLOR)
            surface.blit(label, (x + pad, text_y))
            text_y += font.get_height() + 2

    def _frame_to_surface(self, frame, width, height):
        # Reescalar en OpenCV y no en pygame: es bastante más barato, y en la Pi
        # cada milisegundo del loop de render cuenta.
        small = cv2.resize(frame, (width, height), interpolation=cv2.INTER_AREA)
        rgb = cv2.cvtColor(small, cv2.COLOR_BGR2RGB)
        rgb = np.ascontiguousarray(rgb)
        return pygame.image.frombuffer(rgb.tobytes(), (width, height), "RGB")

    def _draw_face_boxes(self, surface, faces, frame, x, y, view_w, view_h):
        if not faces:
            return
        scale_x = view_w / frame.shape[1]
        scale_y = view_h / frame.shape[0]
        for (fx, fy, fw, fh) in faces:
            rect = pygame.Rect(
                int(x + fx * scale_x),
                int(y + fy * scale_y),
                int(fw * scale_x),
                int(fh * scale_y),
            )
            pygame.draw.rect(surface, FACE_BOX_COLOR, rect, width=2)

    def _draw_hands(self, surface, hands, frame, x, y, view_w, view_h):
        """Los 21 puntos. Es la única forma de ver por qué un gesto no engancha."""
        if not hands:
            return
        scale_x = view_w / frame.shape[1]
        scale_y = view_h / frame.shape[0]
        radius = max(1, int(view_w * 0.008))
        for landmarks in hands:
            for (px, py) in landmarks:
                pygame.draw.circle(surface, HAND_DOT_COLOR,
                                   (int(x + px * scale_x), int(y + py * scale_y)), radius)

    def _stats_lines(self, service):
        stats = service.stats()
        if stats["error"]:
            return ["error: " + stats["error"][:38]]
        return [
            "%s  %s" % (stats["platform"], stats["detector"] or "?"),
            "caras %d   %.0f fps   %.0f ms" % (stats["faces"], stats["capture_fps"], stats["detect_ms"]),
            "manos %d   gestos %.0f ms" % (stats["hands"], stats["gesture_ms"]),
        ]
