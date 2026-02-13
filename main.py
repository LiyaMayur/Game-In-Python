import os
import sys
import pygame

from level import Level, LEVELS
from ui import UI, Button


SCREEN_WIDTH = 900
SCREEN_HEIGHT = 700
FPS = 60


STATE_HOME = "HOME"
STATE_PLAYING = "PLAYING"
STATE_WIN = "WIN"
STATE_LOSE = "LOSE"


def resource_path(*parts: str) -> str:
    """Get absolute path to resource, works for dev and for PyInstaller."""
    base_path = getattr(sys, "_MEIPASS", os.path.dirname(os.path.abspath(__file__)))
    return os.path.join(base_path, *parts)


def main():
    pygame.init()
    pygame.mixer.init()
    pygame.display.set_caption("Cross Road Game")

    screen = pygame.display.set_mode((SCREEN_WIDTH, SCREEN_HEIGHT))
    clock = pygame.time.Clock()

    ui = UI(screen)

    # Load sounds (optional)
    sfx_win = None
    sfx_hit = None
    try:
        sfx_win = pygame.mixer.Sound(resource_path("sounds", "win.wav"))
    except Exception:
        sfx_win = None
    try:
        sfx_hit = pygame.mixer.Sound(resource_path("sounds", "hit.wav"))
    except Exception:
        sfx_hit = None

    state = STATE_HOME
    running = True

    level_index = 0
    level = None

    def start_level(idx: int):
        nonlocal level_index, level, state
        level_index = max(0, min(idx, len(LEVELS) - 1))
        level = Level(LEVELS[level_index], (SCREEN_WIDTH, SCREEN_HEIGHT))
        level.start()
        state = STATE_PLAYING

    # HOME buttons
    btn_start = Button("Start", center=(SCREEN_WIDTH // 2, 360), size=(220, 55))
    btn_quit = Button("Quit", center=(SCREEN_WIDTH // 2, 430), size=(220, 55))

    # END screen buttons
    btn_home = Button("Home", center=(SCREEN_WIDTH // 2, 430), size=(220, 55))
    btn_retry = Button("Reattempt", center=(SCREEN_WIDTH // 2, 495), size=(220, 55))
    btn_next = Button("Next Level", center=(SCREEN_WIDTH // 2, 560), size=(220, 55))

    while running:
        dt = clock.tick(FPS) / 1000.0

        events = pygame.event.get()
        for event in events:
            if event.type == pygame.QUIT:
                running = False

        screen.fill((18, 20, 26))

        if state == STATE_HOME:
            ui.draw_title("CROSS ROAD GAME")
            ui.draw_subtitle("Use Arrow Keys / WASD to move. Reach the top without hitting obstacles.")
            ui.draw_subtitle(f"Levels: {len(LEVELS)}", y=250)

            for event in events:
                if btn_start.handle_event(event):
                    # Always start from the beginning when starting a new run
                    start_level(0)
                if btn_quit.handle_event(event):
                    running = False

            btn_start.draw(screen)
            btn_quit.draw(screen)

        elif state == STATE_PLAYING:
            assert level is not None

            # Allow quick restart/exit
            for event in events:
                if event.type == pygame.KEYDOWN:
                    if event.key == pygame.K_ESCAPE:
                        state = STATE_HOME
                    elif event.key == pygame.K_r:
                        start_level(level_index)

            level.update(dt, events)
            level.draw(screen)
            ui.draw_hud(level_name=LEVELS[level_index]["name"], time_elapsed=level.time_elapsed)

            if level.is_won:
                if sfx_win:
                    try:
                        sfx_win.play()
                    except Exception:
                        pass
                state = STATE_WIN
            elif level.is_lost:
                if sfx_hit:
                    try:
                        sfx_hit.play()
                    except Exception:
                        pass
                state = STATE_LOSE

        elif state in (STATE_WIN, STATE_LOSE):
            assert level is not None

            # Draw last frame of level behind overlay
            level.draw(screen)

            if state == STATE_WIN:
                stars = level.stars_earned
                ui.draw_end_overlay(
                    title="CONGRATULATIONS!",
                    subtitle=f"You cleared all obstacles!  Time: {level.time_elapsed:.2f}s",
                    stars=stars,
                    level_name=LEVELS[level_index]["name"],
                )
            else:
                ui.draw_end_overlay(
                    title="OOPS!",
                    subtitle="You got hit. Try again!",
                    stars=0,
                    level_name=LEVELS[level_index]["name"],
                )

            # Next level is ONLY allowed after completing (winning) the current level.
            has_next = (state == STATE_WIN) and (level_index < (len(LEVELS) - 1))
            btn_next.enabled = has_next

            for event in events:
                if btn_home.handle_event(event):
                    state = STATE_HOME
                if btn_retry.handle_event(event):
                    start_level(level_index)
                if btn_next.handle_event(event) and has_next:
                    start_level(level_index + 1)

            btn_home.draw(screen)
            btn_retry.draw(screen)
            btn_next.draw(screen)

        pygame.display.flip()

    pygame.quit()


if __name__ == "__main__":
    main()
