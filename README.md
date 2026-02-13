# Chicken Hit (Cross Road Game) — Full Documentation

This document explains the entire application architecture, modules, and key functions. It is written to help you understand how the game works end-to-end and to serve as a guide for extending or modifying the project.

Contents:
- Overview
- Project Structure
- Game Flow and States
- Module-by-Module Reference
  - main.py
  - level.py
  - player.py
  - obstacle.py
  - ui.py
  - road_bg.py (if present)
  - assets/ and sounds/
- Configuration and Level Generation
- Collision Model and Hitboxes
- Rendering and UI
- Common Customizations
- Troubleshooting

---

## Overview

Chicken Hit is an arcade-style "crossy road" game built with Pygame. The player controls a character that moves in discrete steps up/down/left/right across horizontally moving lanes of obstacles (cars). The goal is to reach the finish zone at the top without colliding with any obstacle. Difficulty scales by increasing speeds, lane count, and spawn rates.

Core ideas:
- Step-based movement (grid-like) for the player with a small input cooldown.
- Multiple obstacle lanes, each with a direction, speed, and spawn behavior.
- Rect-based collisions between a slightly-shrunken player hitbox and obstacles (also slightly adjusted for fairness).
- Simple UI for home screen, HUD (in-game), and end-of-level overlays.

---

## Project Structure

```
c:\Atmiya Coding\Chicken_Hit\
  assets/                        # images for road background, finish line, player/chicken, cars
  sounds/                        # sound effects (optional)
  level.py                       # Level configuration, state, update/draw, collisions
  main.py                        # Entry point, game loop, state machine, input routing
  obstacle.py                    # Lane & Obstacle classes (car images, spawn/update/draw)
  player.py                      # Player character, movement, collision rectangle, draw
  road_bg.py                     # Scrolling road background (optional/fallback safe)
  ui.py                          # Buttons, HUD overlay, end-of-level overlays
  requirements.txt               # Python dependencies (Pygame)
  DOCUMENTATION.md               # This document
```

---

## Game Flow and States

The game is driven by a simple state machine in `main.py`:
- HOME: Title screen with Start/Quit buttons.
- PLAYING: The active game; updates the current `Level` each frame and draws HUD.
- WIN: Win overlay after reaching the finish line.
- LOSE: Lose overlay after collision.

Transitions:
- From HOME → PLAYING by clicking Start (starts Level 1 by default).
- From PLAYING → WIN/LOSE based on Level flags (`is_won`, `is_lost`).
- From WIN/LOSE → PLAYING via Reattempt or Next Level (if applicable), or → HOME.

---

## Module-by-Module Reference

### main.py (Entry point and State Machine)

Key responsibilities:
- Initialize Pygame and audio.
- Create a `UI` instance and manage the game state loop at target FPS.
- Create and start levels from `LEVELS` (generated in `level.py`).
- Dispatch events to UI buttons and Level.

Important functions and variables:
- `resource_path(*parts)`
  - Returns an absolute path for assets that works in both dev and bundled (PyInstaller) environments.
- `main()`
  - Initializes display, audio, and the main loop.
  - Manages states `STATE_HOME`, `STATE_PLAYING`, `STATE_WIN`, `STATE_LOSE`.
  - Creates and positions UI `Button`s for Start/Quit (home) and Home/Reattempt/Next Level (end overlays).
  - `start_level(idx)` nested function creates a new `Level` from `LEVELS[idx]`, calls `start()`, and switches to PLAYING.
  - In PLAYING, listens for Esc (go home) and R (restart current level).
  - Plays optional SFX on win/lose.

How rendering works:
- Each frame clears the screen, then based on state, draws either the home UI, the active level, or the end overlay with buttons.

### level.py (Level model, configuration, update/draw, collisions)

Key responsibilities:
- Define a function `_make_level(level_num)` that returns a configuration dictionary for a given level of difficulty.
- Define a list `LEVELS` of multiple levels precomputed from `_make_level`.
- Provide the `Level` class that:
  - Initializes the player, lanes, scrolling background, and finish line.
  - Updates player, lanes, and background each frame.
  - Checks win/loss conditions.
  - Draws the playfield: background, safe zones, lanes, finish line, obstacles, and player.

Important parts:
- `_make_level(level_num: int) -> dict`
  - Produces parameters like lane count, lane height, obstacle speeds, spawn times, and gap sizes.
  - Also sets star time thresholds to earn 1–3 stars on completion.
- `LEVELS = [_make_level(i) for i in range(1, 6)]`
  - Builds five level configurations (1..5) by default.
- `class Level` constructor
  - Stores screen size and level config.
  - Creates `Player` with step size equal to `lane_height` for a grid-like feel.
  - Creates multiple `Lane` instances (from `obstacle.py`), spacing them vertically above a bottom safe zone.
  - Tries to create a `ScrollingRoadBackground` instance from `road_bg.py` if the asset exists.
  - Sets initial state flags and timers.
- `start()`
  - Resets timers, state flags.
  - Resets the player and all lanes (spawns seed obstacles so the road is not empty at start).
- `update(dt, events)`
  - Updates timer, player (movement/cooldown), background, and lanes.
  - Collision detection between `player.rect` and each obstacle hitbox (see Collision Model below).
  - Win condition: if the player's y-position crosses `_finish_line_y()`.
- `draw(screen)`
  - Paints background, safe zones, finish line banner (or fallback lines), lanes with dividers, obstacles, and player.

Finish line geometry:
- `_finish_line_y()` returns the y coordinate at the top edge of the road section, i.e., above the last lane and below the top safe zone.

Collisions:
- The `Level.update()` method iterates through each lane and obstacle, building a slightly shrunken hitbox from `obs.rect` and checking `player_rect.colliderect(hitbox)`. This softens unfair pixel collisions near transparent edges.

Stars:
- `stars_earned` uses the time thresholds in the level config to assign 1–3 stars on win.

### player.py (Player movement, collision box, draw)

Key responsibilities:
- Manage the player’s position, step-based movement, and collision rectangle.
- Draw the player sprite centered around its logical position.

Important functions and properties:
- `_resource_path(*parts)`
  - Works like `resource_path` in main.py, but scoped to the module.
- `class Player` constructor
  - `x, y`: starting position (center of sprite/rect).
  - `radius`: used for fallback drawing when no sprite is available.
  - `speed, step`: movement speed (continuous) and step size (used on key presses for grid-like hops).
  - `bounds`: screen bounds to clamp the player’s position.
  - Attempts to load `assets/Chicken.png` and scale it to `_sprite_size`.
- `reset()`
  - Restores `x, y` and cooldown when (re)starting a level.
- `rect` (property)
  - Computes a collision rectangle centered at `(x, y)`. If a sprite is available, it shrinks the collision bounds by a percentage to be more forgiving than the full sprite footprint. Fallback is a circle-sized rect.
- `update(dt, events)`
  - Applies a short input cooldown to create discrete step movement on keydown events (Arrow Keys / WASD).
  - Clamps the player to the provided `bounds`.
- `draw(screen)`
  - If a sprite is loaded, draws it centered on `(x, y)`.
  - If no sprite is available, draws a stylized circle with eyes as a fallback.

### obstacle.py (Obstacle sprite, Lane spawn logic)

Key responsibilities:
- Load top-view car images as Pygame Surfaces.
- Define `Obstacle` objects that move horizontally and draw as cars (or rectangles if assets are missing).
- Define `Lane`: a moving band of obstacles with spawn timing and min-gap logic.

Important parts:
- `_load_car_images()`
  - Loads car pngs from `assets/`. If it fails, returns an empty list; obstacles will draw as rectangles with fallback colors.
- `class Obstacle`
  - Stores `rect`, `speed`, and `direction` (1 for right, -1 for left).
  - `update(dt)`: moves the obstacle horizontally according to speed and direction.
  - `draw(screen)`: if a car image is available, scales and rotates it to match horizontal lanes, flipping if needed based on direction; otherwise, draws a rounded rectangle.
- `class Lane`
  - Constructor takes a lane rect, direction, speed, spawn interval, obstacle size, and minimum gap.
  - `reset()`: clears obstacles and seeds 1–3 obstacles, ensuring `min_gap` spacing to avoid overlaps at the start.
  - `_can_spawn(screen_width)`: checks if spawning a new obstacle at the lane edge would maintain spacing.
  - `_spawn(screen_width)`: creates a new obstacle at the correct offscreen edge with proper spacing relative to the nearest obstacle.
  - `update(dt, screen_width)`: updates obstacle positions; performs ordering correction to keep `min_gap` if rounding pushes objects too close; removes offscreen obstacles; accumulates spawn timer and spawns when ready.
  - `draw(screen)`: draws every obstacle in the lane.

### ui.py (Buttons, HUD, and End-of-Level overlay)

Key responsibilities:
- Define a simple `Button` with hover state, enabled/disabled handling, and click detection.
- Draw text labels for title and subtitles on the home screen.
- Draw a HUD with level name, time, and help hints.
- Draw an end overlay with a panel and stars.

Important parts:
- `class Button`
  - `handle_event(event) -> bool`: returns True if left-mouse clicked within bounds and the button is enabled.
  - `draw(screen)`: paints a rounded rectangle button with simple hover and disabled states, then renders text.
- `class UI`
  - Fonts are created in the constructor.
  - `draw_title(text)`: draws the main title centered near the top.
  - `draw_subtitle(text, y)`: draws a subtitle under the title.
  - `draw_hud(level_name, time_elapsed)`: draws a translucent black box with HUD text: current level, elapsed time, and controls.
  - `draw_end_overlay(title, subtitle, stars, level_name)`: draws a centered panel with the title, level name, message, and stars; the background is dimmed with a translucent overlay.
  - `_draw_stars(center, stars)` and `_draw_star(...)`: helpers to render three stars with filled/outlined styles.

### road_bg.py (Optional scrolling background)

If present, this module provides `ScrollingRoadBackground`, a parallax-like background image that scrolls gently to add depth while lanes and obstacles animate on top. If asset loading fails, `level.py` falls back to plain colored lanes.

---

## Configuration and Level Generation

Levels are generated in `level.py` via `_make_level(level_num)`. For a given `n`:
- `lane_height`: decreases slightly with level to make lanes a bit tighter.
- `lane_count`: increases with level (more lanes = harder).
- `speed`: base car speed increases with level and slightly by lane index.
- `spawn_every`: time between spawns per lane, lower with higher levels (faster spawns).
- `gap_min`: minimum distance between obstacles to avoid impossible scenarios.
- `player_step`: matches `lane_height` for consistent grid moves.
- `star_times`: lower thresholds for higher levels to earn 2–3 stars.

You can adjust difficulty by modifying formulas in `_make_level`:
- Slower cars: reduce the base speed and per-lane increment.
- Fewer cars: increase `spawn_every` or increase `gap_min`.
- Bigger/smaller cars: change the scaling in the `Level` constructor when creating `Lane` with `obstacle_width/height`.

---

## Collision Model and Hitboxes

Collisions are checked in `Level.update()`:
- `player_rect` is obtained from `Player.rect`. This rectangle is intentionally shrunken relative to the visual sprite, making the game feel fair (avoiding collisions on transparent edges or tiny overlaps).
- Each obstacle provides a rectangle `obs.rect`. The level computes a slightly shrunken `hitbox` using `inflate(-pad_x, -pad_y)`. The padding fractions are tuned based on sprite proportions.
- Collision check uses `player_rect.colliderect(hitbox)`.

If collisions feel too early or too late:
- Make collisions more forgiving: increase player rect shrink, or increase obstacle shrink (larger `pad_x/pad_y`).
- Make collisions stricter: decrease the shrink percentages or reduce the minimum padding.

The player sprite is drawn centered on `(x, y)` so that visuals and collision box are aligned, preventing perceived gaps.

---

## Rendering and UI

- Background and safe zones are drawn in `Level.draw()`.
- Lanes are rectangles with divider lines; obstacles are drawn in their lanes.
- Finish line: if an image is available, it is drawn near the top of the road; otherwise, a fallback line is rendered.
- Player: If the chicken sprite is loaded, it is drawn centered at `(x, y)`; otherwise, a stylized circle is drawn.
- UI overlays:
  - HOME: Title/subtitles and Start/Quit buttons.
  - HUD: Level name, time, and shortcuts.
  - End overlay: Dimmed background with a centered panel displaying the result, stars, and buttons for navigation.

---

## Common Customizations

- Change player step size: in `level.py` where `Player` is created, change `step=self.lane_height`.
- Change lane speeds: tweak the `speed` formula in `_make_level`.
- Change spawn rates: modify `spawn_every` and/or lane `min_gap`.
- Adjust car sizes: in `Level.__init__`, tune `car_height` and `car_width` when creating each `Lane`.
- Tweak collision feel: edit `Player.rect` shrink values and obstacle hitbox padding in `Level.update()`.
- Add more levels: extend `LEVELS` by generating more configs.
- UI look: modify colors, sizes, and fonts in `ui.py`.

---

## Troubleshooting

- Game window not opening / errors on import:
  - Ensure Pygame is installed (`pip install -r requirements.txt`).
- Assets not found / rectangles instead of images:
  - Verify image files exist under `assets/` and have correct names.
  - The game gracefully falls back to basic shapes if assets are missing.
- Collisions feel unfair:
  - Adjust shrink parameters in `player.rect` and obstacle padding in `level.update()`.
- Performance issues:
  - Reduce obstacle spawn frequency or speeds.
  - Avoid extremely large images; convert images to optimized PNGs.

---

## Appendix: Function-by-Function Pointers

Below is a quick pointer map to find functions and what they do:

- main.py
  - `main()`: Initializes game, runs loop, manages states, draws UI, delegates to `Level`.
  - `resource_path()`: Utility to build absolute asset paths.

- level.py
  - `_make_level(level_num)`: Builds config dict for the given level difficulty.
  - `LEVELS`: Pre-generated list of configs.
  - `Level.__init__`: Sets up player, lanes, background, finish line params, timers, and state flags.
  - `Level.start()`: Resets state and seeds lanes.
  - `Level.update(dt, events)`: Updates entities, checks collisions and win condition.
  - `Level.draw(screen)`: Renders background, lanes, finish line, obstacles, and player.
  - `Level.stars_earned`: Returns stars based on completion time.

- player.py
  - `Player.__init__`: Initializes player properties and attempts to load sprite.
  - `Player.reset()`: Restores starting position.
  - `Player.rect` (property): Computes shrunken collision rectangle.
  - `Player.update(dt, events)`: Processes step movement and clamps to bounds.
  - `Player.draw(screen)`: Renders sprite or fallback circle centered at `(x, y)`.

- obstacle.py
  - `_load_car_images()`: Loads car sprites from assets.
  - `Obstacle.__init__`: Stores rect, speed, direction, and optionally a base image.
  - `Obstacle.update(dt)`: Integrates horizontal position.
  - `Obstacle.draw(screen)`: Draws rotated/scaled car sprite (or a rectangle fallback).
  - `Lane.__init__`: Stores all lane parameters and state.
  - `Lane.reset()`: Seeds lane with non-overlapping obstacles.
  - `Lane._can_spawn(screen_width)`: Determines if spacing allows a new spawn.
  - `Lane._spawn(screen_width)`: Adds a new obstacle offscreen with correct spacing.
  - `Lane.update(dt, screen_width)`: Updates movement, spacing, culls offscreen, and spawns.
  - `Lane.draw(screen)`: Draws all lane obstacles.

- ui.py
  - `Button.__init__/handle_event/draw`: Rectangle button with text and hover/disabled states.
  - `UI.draw_title/draw_subtitle`: Title/subtitle for home screen.
  - `UI.draw_hud`: HUD box with level/time and controls.
  - `UI.draw_end_overlay`: Dimmed overlay panel with title, subtitle, and star rating.
  - `UI._draw_stars/_draw_star`: Helpers for rendering three stars.

---

This README-style document should equip you to navigate and extend the project. For further improvements, consider adding saved best times, a settings menu, or visual polish (shadows/gradients/particles) while keeping performance constraints in mind.
