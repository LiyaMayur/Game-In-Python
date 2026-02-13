from __future__ import annotations

import os
import random
import pygame


_CAR_IMAGE_FILES = [
    "top-view-blue-car-outline-600nw-2582505797.png",
    "top-view-dark-grey-car-600nw-2582507361.png",
    "top-view-green-car-outline-600nw-2582506973.png",
    "top-view-white-car-outline-600nw-2582505535.png",
]


def _load_car_images() -> list[pygame.Surface]:
    """Load car images from assets folder.

    Fail-safe: if loading fails, return empty list and obstacles will draw as rectangles.
    """
    try:
        base_dir = os.path.dirname(os.path.abspath(__file__))
        assets_dir = os.path.join(base_dir, "assets")
        images: list[pygame.Surface] = []
        for fname in _CAR_IMAGE_FILES:
            path = os.path.join(assets_dir, fname)
            images.append(pygame.image.load(path).convert_alpha())
        return images
    except Exception:
        return []


# Loaded lazily on first Obstacle creation (after pygame init)
_CAR_IMAGES: list[pygame.Surface] | None = None


class Obstacle:
    def __init__(self, rect: pygame.Rect, speed: float, direction: int):
        global _CAR_IMAGES

        self.rect = rect
        self.speed = float(speed)
        self.direction = 1 if direction >= 0 else -1

        if _CAR_IMAGES is None:
            _CAR_IMAGES = _load_car_images()

        self._base_image: pygame.Surface | None = random.choice(_CAR_IMAGES) if _CAR_IMAGES else None

        # Fallback color if images are unavailable
        self.color = random.choice([(255, 92, 92), (255, 165, 70), (255, 120, 210), (120, 255, 160)])

    def update(self, dt: float):
        self.rect.x += int(self.direction * self.speed * dt)

    def draw(self, screen: pygame.Surface):
        if self._base_image is None:
            pygame.draw.rect(screen, self.color, self.rect, border_radius=10)
            pygame.draw.rect(screen, (10, 10, 14), self.rect, width=2, border_radius=10)
            return

        img = pygame.transform.smoothscale(self._base_image, (self.rect.width, self.rect.height))

        # The source assets are top-view cars oriented vertically.
        # Our lanes move horizontally, so rotate to face sideways first.
        # Rotate 90deg clockwise: car points right.
        img = pygame.transform.rotate(img, -90)

        # If moving left, flip horizontally so the front faces left.
        if self.direction < 0:
            img = pygame.transform.flip(img, True, False)

        # After rotation, the surface size is swapped; re-scale to our rect.
        img = pygame.transform.smoothscale(img, (self.rect.width, self.rect.height))

        screen.blit(img, self.rect.topleft)


class Lane:
    def __init__(
        self,
        rect: pygame.Rect,
        direction: int,
        speed: float,
        spawn_every: float,
        obstacle_width: int,
        obstacle_height: int,
        min_gap: int = 140,
    ):
        self.rect = rect
        self.direction = 1 if direction >= 0 else -1
        self.speed = float(speed)
        self.spawn_every = float(spawn_every)
        self.obstacle_width = int(obstacle_width)
        self.obstacle_height = int(obstacle_height)
        self.min_gap = int(min_gap)

        self.obstacles: list[Obstacle] = []
        self._spawn_timer = 0.0

    def reset(self):
        self.obstacles.clear()
        self._spawn_timer = 0.0

        # Seed the lane with a couple obstacles so it doesn't start empty.
        # Place them with enforced min_gap so they never overlap.
        seed_count = random.randint(1, 3)

        candidates = [random.randint(0, max(0, self.rect.width - self.obstacle_width)) for _ in range(40)]
        candidates.sort()

        placed: list[pygame.Rect] = []
        y = self.rect.centery - self.obstacle_height // 2
        for x in candidates:
            if len(placed) >= seed_count:
                break
            r = pygame.Rect(x, y, self.obstacle_width, self.obstacle_height)
            if all(r.right + self.min_gap <= p.left or r.left >= p.right + self.min_gap for p in placed):
                placed.append(r)

        for r in placed:
            self.obstacles.append(Obstacle(r, self.speed, self.direction))

        self.obstacles.sort(key=lambda o: o.rect.x)

    def _can_spawn(self, screen_width: int) -> bool:
        # Spawn at offscreen edge in movement direction.
        if self.direction > 0:
            spawn_x = -self.obstacle_width - 20
            nearest = min(self.obstacles, key=lambda o: o.rect.left, default=None)
            if nearest is None:
                return True
            return (nearest.rect.left - spawn_x) >= self.min_gap
        else:
            spawn_x = screen_width + 20
            nearest = max(self.obstacles, key=lambda o: o.rect.right, default=None)
            if nearest is None:
                return True
            return (spawn_x - nearest.rect.right) >= self.min_gap

    def _spawn(self, screen_width: int):
        y = self.rect.centery - self.obstacle_height // 2

        if self.direction > 0:
            base_x = -self.obstacle_width - 20
            nearest = min(self.obstacles, key=lambda o: o.rect.left, default=None)
            if nearest is not None:
                x = min(base_x, nearest.rect.left - self.min_gap - self.obstacle_width)
            else:
                x = base_x
        else:
            base_x = screen_width + 20
            nearest = max(self.obstacles, key=lambda o: o.rect.right, default=None)
            if nearest is not None:
                x = max(base_x, nearest.rect.right + self.min_gap)
            else:
                x = base_x

        rect = pygame.Rect(int(x), y, self.obstacle_width, self.obstacle_height)
        self.obstacles.append(Obstacle(rect, self.speed, self.direction))

    def update(self, dt: float, screen_width: int):
        # Update existing
        for o in self.obstacles:
            o.update(dt)

        # Prevent overlaps: if obstacles get too close due to dt/rounding,
        # push the trailing one back to preserve min_gap.
        if len(self.obstacles) > 1:
            self.obstacles.sort(key=lambda o: o.rect.x)

            if self.direction > 0:
                # Moving right: rightmost is front.
                for i in range(len(self.obstacles) - 2, -1, -1):
                    front = self.obstacles[i + 1]
                    back = self.obstacles[i]
                    desired_right = front.rect.left - self.min_gap
                    if back.rect.right > desired_right:
                        back.rect.right = desired_right
            else:
                # Moving left: leftmost is front.
                for i in range(1, len(self.obstacles)):
                    front = self.obstacles[i - 1]
                    back = self.obstacles[i]
                    desired_left = front.rect.right + self.min_gap
                    if back.rect.left < desired_left:
                        back.rect.left = desired_left

        # Remove offscreen
        if self.direction > 0:
            self.obstacles = [o for o in self.obstacles if o.rect.left < screen_width + 200]
        else:
            self.obstacles = [o for o in self.obstacles if o.rect.right > -200]

        # Spawn new
        self._spawn_timer += dt
        if self._spawn_timer >= self.spawn_every:
            self._spawn_timer = 0.0
            if self._can_spawn(screen_width):
                self._spawn(screen_width)

    def draw(self, screen: pygame.Surface):
        for o in self.obstacles:
            o.draw(screen)
