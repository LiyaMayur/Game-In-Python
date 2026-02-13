from __future__ import annotations

import pygame


class Button:
    def __init__(
        self,
        text: str,
        center: tuple[int, int],
        size: tuple[int, int] = (220, 55),
    ):
        self.text = text
        self.rect = pygame.Rect(0, 0, size[0], size[1])
        self.rect.center = center
        self.enabled = True

        self._font = pygame.font.SysFont("Segoe UI", 22, bold=True)

    def handle_event(self, event: pygame.event.Event) -> bool:
        if not self.enabled:
            return False
        if event.type == pygame.MOUSEBUTTONDOWN and event.button == 1:
            if self.rect.collidepoint(event.pos):
                return True
        return False

    def draw(self, screen: pygame.Surface):
        # DRAWS: Interactive button with text, background, border, and hover effects
        mouse_pos = pygame.mouse.get_pos()
        hovered = self.rect.collidepoint(mouse_pos)

        if not self.enabled:
            bg = (70, 74, 82)
            fg = (160, 165, 175)
        else:
            bg = (80, 130, 255) if hovered else (60, 110, 235)
            fg = (245, 248, 255)

        pygame.draw.rect(screen, bg, self.rect, border_radius=12)
        pygame.draw.rect(screen, (12, 12, 16), self.rect, width=2, border_radius=12)

        label = self._font.render(self.text, True, fg)
        screen.blit(label, label.get_rect(center=self.rect.center))


class UI:
    def __init__(self, screen: pygame.Surface):
        self.screen = screen
        self.w, self.h = screen.get_size()

        self.font_title = pygame.font.SysFont("Segoe UI", 48, bold=True)
        self.font_sub = pygame.font.SysFont("Segoe UI", 22)
        self.font_hud = pygame.font.SysFont("Consolas", 18, bold=True)

    def draw_title(self, text: str):
        # DRAWS: Large title text centered on screen
        label = self.font_title.render(text, True, (245, 248, 255))
        self.screen.blit(label, label.get_rect(center=(self.w // 2, 160)))

    def draw_subtitle(self, text: str, y: int = 210):
        # DRAWS: Medium subtitle text centered on screen at specified Y position
        label = self.font_sub.render(text, True, (190, 198, 212))
        self.screen.blit(label, label.get_rect(center=(self.w // 2, y)))

    def draw_hud(self, level_name: str, time_elapsed: float):
        # DRAWS: Top-left HUD overlay showing level name, elapsed time, and control hints
        pad = 10
        text = f"{level_name}   Time: {time_elapsed:0.2f}s   (ESC: Home, R: Restart)"
        label = self.font_hud.render(text, True, (230, 235, 245))
        bg = pygame.Surface((label.get_width() + pad * 2, label.get_height() + pad * 2), pygame.SRCALPHA)
        bg.fill((0, 0, 0, 120))
        self.screen.blit(bg, (12, 12))
        self.screen.blit(label, (12 + pad, 12 + pad))

    def draw_end_overlay(self, title: str, subtitle: str, stars: int, level_name: str):
        # DRAWS: Full-screen end-of-level panel with title, level name, subtitle, and star rating
        # translucent overlay
        overlay = pygame.Surface((self.w, self.h), pygame.SRCALPHA)
        overlay.fill((0, 0, 0, 160))
        self.screen.blit(overlay, (0, 0))

        panel_w, panel_h = 640, 360
        panel = pygame.Rect(0, 0, panel_w, panel_h)
        panel.center = (self.w // 2, self.h // 2 - 40)
        pygame.draw.rect(self.screen, (28, 32, 42), panel, border_radius=16)
        pygame.draw.rect(self.screen, (12, 12, 16), panel, width=2, border_radius=16)

        # header texts
        t = self.font_title.render(title, True, (245, 248, 255))
        self.screen.blit(t, t.get_rect(center=(panel.centerx, panel.top + 70)))

        l_name = self.font_sub.render(level_name, True, (170, 180, 200))
        self.screen.blit(l_name, l_name.get_rect(center=(panel.centerx, panel.top + 120)))

        sub = self.font_sub.render(subtitle, True, (205, 212, 224))
        self.screen.blit(sub, sub.get_rect(center=(panel.centerx, panel.top + 160)))

        # Stars
        self._draw_stars(center=(panel.centerx, panel.top + 235), stars=stars)

    def _draw_stars(self, center: tuple[int, int], stars: int):
        # DRAWS: Three stars total, with specified number filled (rest are outlined)
        cx, cy = center
        spacing = 90
        for i in range(3):
            x = cx + (i - 1) * spacing
            filled = i < stars
            self._draw_star((x, cy), r_outer=28, r_inner=12, filled=filled)

    def _draw_star(self, center: tuple[int, int], r_outer: int, r_inner: int, filled: bool):
        # DRAWS: Single 5-point star, either filled (gold) or outlined (gray)
        # 5-point star
        import math

        cx, cy = center
        points = []
        for k in range(10):
            angle = -math.pi / 2 + k * (math.pi / 5)
            r = r_outer if k % 2 == 0 else r_inner
            points.append((cx + math.cos(angle) * r, cy + math.sin(angle) * r))

        if filled:
            pygame.draw.polygon(self.screen, (255, 215, 90), points)
        else:
            pygame.draw.polygon(self.screen, (90, 96, 110), points)
        pygame.draw.polygon(self.screen, (12, 12, 16), points, width=2)
