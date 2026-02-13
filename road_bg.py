from __future__ import annotations

import pygame


class ScrollingRoadBackground:
    """A simple horizontally scrolling road background.

    The image is tiled across the full width of the screen and scrolls
    horizontally at `scroll_speed` pixels/second.

    NOTE: This uses the road image as a *lane fill* behind obstacles.
    """

    def __init__(
        self,
        image_path: str,
        screen_size: tuple[int, int],
        lane_rects: list[pygame.Rect],
        scroll_speed: float = 140.0,
    ):
        self.screen_width, self.screen_height = screen_size
        # Keep background stable (no scrolling)
        self.scroll_speed = 0.0
        self._offset_x = 0.0

        # Load once
        img = pygame.image.load(image_path).convert()
        self._src_image = img

        # Pre-scale to each lane height and full screen width tiling.
        self._lane_surfaces: list[pygame.Surface] = []
        self._lane_rects: list[pygame.Rect] = []

        for r in lane_rects:
            # Scale road image to exactly lane height while keeping aspect by stretching.
            scaled = pygame.transform.smoothscale(self._src_image, (self.screen_width, r.height)).convert()
            self._lane_surfaces.append(scaled)
            self._lane_rects.append(r.copy())

    def update(self, dt: float):
        self._offset_x = (self._offset_x + self.scroll_speed * dt) % self.screen_width

    def draw(self, screen: pygame.Surface):
        # Tile each lane surface twice to cover the wrap.
        ox = int(self._offset_x)
        for surf, r in zip(self._lane_surfaces, self._lane_rects):
            x1 = -ox
            x2 = x1 + self.screen_width
            screen.blit(surf, (x1, r.top))
            screen.blit(surf, (x2, r.top))
