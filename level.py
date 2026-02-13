from __future__ import annotations

import os
import pygame

from player import Player
from obstacle import Lane, Obstacle
from road_bg import ScrollingRoadBackground


# Levels are generated from 1..10 with increasing difficulty.
# Difficulty increases via:
# - more lanes
# - higher obstacle speed
# - faster spawns (lower spawn_every)
# - slightly smaller min gaps
# - tighter 3-star / 2-star time thresholds

def _make_level(level_num: int) -> dict:
    # Clamp within 1..10
    n = max(1, min(10, int(level_num)))

    lane_height = 70 - (n - 1)  # 70 down to 61
    lane_count = 5 + n  # 6..15 (we will only create this many lanes)

    # Star thresholds: later levels expect faster completion.
    # These are tuned for step-based movement; adjust if you want.
    three_star = max(8.0, 13.0 - (n - 1) * 0.4)  # decreases with level
    two_star = max(12.0, 20.0 - (n - 1) * 0.45)

    # Build lane configs
    lanes = []
    for i in range(lane_count):
        direction = 1 if (i % 2 == 0) else -1

        # Speed ramps up each level and slightly by lane index
        speed = 170 + (n - 1) * 28 + i * 6

        # Spawn gets quicker with level (but keep reasonable lower bound)
        spawn_every = max(0.55, 1.25 - (n - 1) * 0.06 - i * 0.01)

        # Obstacle size
        width = 120 - (n - 1) * 3
        width = max(70, min(130, width))

        # Minimum gap reduces slightly with difficulty (harder)
        gap_min = max(95, 165 - (n - 1) * 6 - i * 1)

        lanes.append(
            {
                "direction": direction,
                "speed": float(speed),
                "spawn_every": float(spawn_every),
                "width": int(width),
                "gap_min": int(gap_min),
            }
        )

    return {
        "name": f"Level {n}",
        "lane_count": lane_count,
        "lane_height": lane_height,
        "finish_padding": max(22, 32 - n),
        "player_step": lane_height,
        "player_speed": 420 + (n - 1) * 10,
        "star_times": {"3": float(three_star), "2": float(two_star)},
        "lanes": lanes,
    }


LEVELS = [_make_level(i) for i in range(1, 6)]


class Level:
    def __init__(self, config: dict, screen_size: tuple[int, int]):
        self.config = config
        self.screen_width, self.screen_height = screen_size

        # Assets
        self._assets_dir = os.path.join(os.path.dirname(os.path.abspath(__file__)), "assets")
        self._road_bg_path = os.path.join(self._assets_dir, "1.png")
        self._finish_img_path = os.path.join(self._assets_dir, "finish line.jpg")

        # Lazy-loaded finish line image (may be None if missing)
        self._finish_img: pygame.Surface | None = None

        self.lane_height = int(config["lane_height"])
        self.lane_count = int(config["lane_count"])
        self.finish_padding = int(config.get("finish_padding", 30))

        # Layout:
        # bottom safe zone, then road lanes, then top finish/safe zone
        self.safe_zone_height = self.lane_height

        # Player
        start_x = self.screen_width // 2
        start_y = self.screen_height - (self.safe_zone_height // 2)
        self.player = Player(
            x=start_x,
            y=start_y,
            radius=18,
            speed=float(config.get("player_speed", 420)),
            step=self.lane_height,
            bounds=(0, 0, self.screen_width, self.screen_height),
        )

        # Lanes
        self.lanes: list[Lane] = []
        # road lanes occupy y from bottom safe zone upwards
        for i, lane_cfg in enumerate(config["lanes"]):
            # lane index 0 is just above bottom safe zone
            lane_y_center = self.screen_height - self.safe_zone_height - (i + 0.5) * self.lane_height
            lane_rect = pygame.Rect(0, int(lane_y_center - self.lane_height / 2), self.screen_width, self.lane_height)
            # Better car proportions for the provided top-view car sprites:
            # make them longer (along x) and slightly taller so they feel less squished.
            car_height = max(26, int(self.lane_height * 1.15))
            car_width = max(90, int(car_height * 1.49))

            lane = Lane(
                rect=lane_rect,
                direction=int(lane_cfg["direction"]),
                speed=float(lane_cfg["speed"]),
                spawn_every=float(lane_cfg["spawn_every"]),
                obstacle_width=car_width,
                obstacle_height=car_height,
                min_gap=int(lane_cfg.get("gap_min", 140)),
            )
            self.lanes.append(lane)

        # Scrolling road background behind lanes
        try:
            lane_rects = [lane.rect for lane in self.lanes]
            self.road_bg = ScrollingRoadBackground(
                image_path=self._road_bg_path,
                screen_size=(self.screen_width, self.screen_height),
                lane_rects=lane_rects,
                scroll_speed=float(config.get("road_scroll_speed", 140.0)),
            )
        except Exception:
            # If asset missing or fails to load, fall back to solid colors.
            self.road_bg = None

        # State
        self._time_elapsed = 0.0
        self._running = False
        self._won = False
        self._lost = False

    def start(self):
        self._time_elapsed = 0.0
        self._running = True
        self._won = False
        self._lost = False
        self.player.reset()
        for lane in self.lanes:
            lane.reset()

    @property
    def time_elapsed(self) -> float:
        return self._time_elapsed

    @property
    def is_won(self) -> bool:
        return self._won

    @property
    def is_lost(self) -> bool:
        return self._lost

    @property
    def stars_earned(self) -> int:
        if not self._won:
            return 0
        t = self._time_elapsed
        t3 = float(self.config["star_times"]["3"])
        t2 = float(self.config["star_times"]["2"])
        if t <= t3:
            return 3
        if t <= t2:
            return 2
        return 1

    def _finish_line_y(self) -> int:
        # Place finish line exactly at the top edge of the road section,
        # i.e. right after all obstacle lanes end.
        #
        # Layout from bottom:
        #   bottom safe zone
        #   lane_count * lane_height (road lanes)
        #   remaining top area is safe/finish zone
        road_top = self.screen_height - self.safe_zone_height - (self.lane_count * self.lane_height)
        # Add a small padding so the banner sits nicely within the top zone.
        # return max(8, int(road_top + 10))
        return road_top

    def update(self, dt: float, events: list[pygame.event.Event]):
        if not self._running or self._won or self._lost:
            return

        self._time_elapsed += dt

        self.player.update(dt, events)

        if self.road_bg:
            self.road_bg.update(dt)

        for lane in self.lanes:
            lane.update(dt, self.screen_width)

        # Collisions
        player_rect = self.player.rect
        for lane in self.lanes:
            for obs in lane.obstacles:
                # Use a slightly shrunken hitbox for obstacles to match visible car body
                pad_x = max(6, int(obs.rect.width * 0.16))
                pad_y = max(4, int(obs.rect.height * 0.20))
                hitbox = obs.rect.inflate(-pad_x, -pad_y)
                if player_rect.colliderect(hitbox):
                    self._lost = True
                    self._running = False
                    return

        # Win condition: reach finish line near top
        if self.player.y <= self._finish_line_y():
            self._won = True
            self._running = False

    def draw(self, screen: pygame.Surface):
        # Background
        screen.fill((18, 20, 26))

        # Top safe zone
        pygame.draw.rect(screen, (34, 40, 52), pygame.Rect(0, 0, self.screen_width, self.safe_zone_height))
        # Bottom safe zone
        pygame.draw.rect(
            screen,
            (34, 40, 52),
            pygame.Rect(0, self.screen_height - self.safe_zone_height, self.screen_width, self.safe_zone_height),
        )

        # Finish line (image if available)
        fy = self._finish_line_y()
        if self._finish_img is None:
            try:
                self._finish_img = pygame.image.load(self._finish_img_path).convert_alpha()
            except Exception:
                self._finish_img = False  # sentinel: failed

        if self._finish_img not in (None, False):
            # Draw a cleaner "banner" finish line with subtle shadow and top/bottom highlights.
            banner_h = 98
            y = max(0, fy - banner_h // 2)

            # Shadow behind banner
            shadow = pygame.Surface((self.screen_width, banner_h), pygame.SRCALPHA)
            shadow.fill((0, 0, 0, 70))
            screen.blit(shadow, (0, y + 2))

            banner = pygame.transform.smoothscale(self._finish_img, (self.screen_width, banner_h))
            screen.blit(banner, (0, y))

            # Elegant highlights
            pygame.draw.line(screen, (255, 255, 255, 120), (0, y + 1), (self.screen_width, y + 1), 2)
            pygame.draw.line(screen, (0, 0, 0, 120), (0, y + banner_h - 2), (self.screen_width, y + banner_h - 2), 2)
        else:
            # Fallback: double-line finish marker
            pygame.draw.line(screen, (255, 210, 90), (0, fy), (self.screen_width, fy), 5)
            pygame.draw.line(screen, (10, 10, 14), (0, fy + 6), (self.screen_width, fy + 6), 2)

        # Road lanes
        if self.road_bg:
            self.road_bg.draw(screen)

        for i, lane in enumerate(self.lanes):
            if not self.road_bg:
                lane_color = (26, 28, 34) if i % 2 == 0 else (30, 32, 38)
                pygame.draw.rect(screen, lane_color, lane.rect)

            # lane divider line
            pygame.draw.line(
                screen,
                (55, 58, 66),
                (0, lane.rect.bottom),
                (self.screen_width, lane.rect.bottom),
                2,
            )

            lane.draw(screen)

        self.player.draw(screen)
