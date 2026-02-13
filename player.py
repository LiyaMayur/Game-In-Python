from __future__ import annotations

import os
import sys
import pygame

# TODO: Defunct function to be removed
def _resource_path(*parts: str) -> str:
    """Return absolute path to an asset inside this project.

    Supports both normal execution and PyInstaller bundles by checking
    the special attribute `sys._MEIPASS`.
    """
    base_path = getattr(sys, "_MEIPASS", os.path.dirname(os.path.abspath(__file__)))
    return os.path.join(base_path, *parts)


class Player:
    """Player character: holds position, handles step movement, and drawing.

    Attributes:
        start_x, start_y: Starting coordinates, also used when resetting.
        radius: Visual radius for fallback circle rendering.
        speed: Unused for step motion, but available for smooth movement if needed.
        step: Pixels moved per key press for a grid-like feel.
        bounds: Playfield rectangle (left, top, width, height) for clamping.
        x, y: Current position of the player center in pixels.
        _move_cooldown: Remaining cooldown time to throttle step inputs.
        _cooldown_time: Fixed delay between accepted key presses (seconds).
        _sprite: Loaded chicken image surface or None if not available.
        _sprite_size: Target size for the player sprite when loaded.
    """

    def __init__(
        self,
        x: int,
        y: int,
        radius: int = 18,
        speed: float = 420.0,
        step: int = 70,
        bounds: tuple[int, int, int, int] = (0, 0, 900, 700),
    ):
        # Spawn/Reset position
        self.start_x = int(x)
        self.start_y = int(y)
        # Visual/collision helpers
        self.radius = int(radius)
        self.speed = float(speed)
        self.step = int(step)
        self.bounds = bounds

        # Live position
        self.x = float(x)
        self.y = float(y)

        # Input throttling for step movement
        self._move_cooldown = 0.0
        self._cooldown_time = 0.09  # seconds between step moves

        # Sprite loading (optional)
        self._sprite = None  # pygame.Surface | None
        self._sprite_size = (self.radius * 2 + 10, self.radius * 2 + 10)
        try:
            img = pygame.image.load(_resource_path("assets", "Chicken.png")).convert_alpha()
            self._sprite = pygame.transform.smoothscale(img, self._sprite_size)
        except Exception:
            # If sprite fails to load, fallback drawing is used in draw()
            self._sprite = None

    def reset(self):
        """Reset live position and cooldown to starting state."""
        self.x = float(self.start_x)
        self.y = float(self.start_y)
        self._move_cooldown = 0.0

    @property
    def rect(self) -> pygame.Rect:
        """Return the player's collision rectangle centered on (x, y).

        If a sprite is present, the rect is intentionally shrunken vs. the
        full sprite dimensions to be more forgiving around transparent edges.
        Fallback: a rect derived from the circle radius.
        """
        if self._sprite is not None:
            w, h = self._sprite.get_size()
            # Shrink collision bounds (tweak these numbers if needed)
            shrink_x = int(w * 0.28)
            shrink_y = int(h * 0.32)
            cw = max(8, w - shrink_x)
            ch = max(8, h - shrink_y)
            return pygame.Rect(int(self.x - cw / 2), int(self.y - ch / 2), cw, ch)

        # Fallback collision for non-sprite rendering
        r = self.radius
        shrink = max(0, int(r * 0.35))
        cr = max(6, r - shrink)
        return pygame.Rect(int(self.x - cr), int(self.y - cr), cr * 2, cr * 2)

    def update(self, dt: float, events: list[pygame.event.Event]):
        """Handle discrete step movement on keydown and clamp to bounds.

        Args:
            dt: Delta time in seconds since last frame.
            events: Pygame event list for this frame.
        """
        # Reduce input cooldown each frame
        self._move_cooldown = max(0.0, self._move_cooldown - dt)

        # Step movement on keydown (Crossy-Road style)
        for event in events:
            if event.type == pygame.KEYDOWN and self._move_cooldown <= 0.0:
                dx = 0
                dy = 0
                if event.key in (pygame.K_UP, pygame.K_w):
                    dy = -self.step
                elif event.key in (pygame.K_DOWN, pygame.K_s):
                    dy = self.step
                elif event.key in (pygame.K_LEFT, pygame.K_a):
                    dx = -self.step
                elif event.key in (pygame.K_RIGHT, pygame.K_d):
                    dx = self.step

                if dx != 0 or dy != 0:
                    self.x += dx
                    self.y += dy
                    self._move_cooldown = self._cooldown_time  # re-arm cooldown

        # Clamp to bounds (keep center within screen area minus radius)
        left, top, width, height = self.bounds
        right = left + width
        bottom = top + height

        self.x = max(left + self.radius, min(right - self.radius, self.x))
        self.y = max(top + self.radius, min(bottom - self.radius, self.y))

    def draw(self, screen: pygame.Surface):
        """Render the player sprite (centered) or a fallback circle."""
        if self._sprite is not None:
            # Draw sprite centered on logical position so visuals align with collision rect center
            w, h = self._sprite.get_size()
            screen.blit(self._sprite, (int(self.x - w / 2), int(self.y - h / 2)))
            return

        # Fallback shape if sprite can't be loaded
        pygame.draw.circle(screen, (120, 220, 255), (int(self.x), int(self.y)), self.radius)
        pygame.draw.circle(screen, (10, 10, 14), (int(self.x), int(self.y)), self.radius, 2)
        pygame.draw.circle(screen, (10, 10, 14), (int(self.x - 6), int(self.y - 5)), 3)
        pygame.draw.circle(screen, (10, 10, 14), (int(self.x + 6), int(self.y - 5)), 3)
