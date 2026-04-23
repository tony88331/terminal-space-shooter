#!/usr/bin/env python3
import curses
import random
import shutil
import subprocess
import time


FRAME_DELAY = 0.03
ENEMY_STEP_INTERVAL = 0.35
MIN_ENEMY_STEP_INTERVAL = 0.08
MAX_ENEMY_STEP_INTERVAL = 0.8
ENEMY_SPEED_STEP = 0.03
ENEMY_SPAWN_CHANCE = 0.12
MAX_ENEMIES = 12
SHOT_COOLDOWN = 0.05
INITIAL_LIVES = 5

SOUND_FILES = {
    "start": "/System/Library/Sounds/Hero.aiff",
    "shoot": "/System/Library/Sounds/Pop.aiff",
    "hit": "/System/Library/Sounds/Tink.aiff",
    "damage": "/System/Library/Sounds/Basso.aiff",
    "game_over": "/System/Library/Sounds/Funk.aiff",
}


def clamp(value, low, high):
    return max(low, min(high, value))


def draw_center(stdscr, y, text):
    height, width = stdscr.getmaxyx()
    x = max(0, (width - len(text)) // 2)
    try:
        stdscr.addstr(y, x, text)
    except curses.error:
        pass


class SoundEngine:
    def __init__(self):
        self.afplay_available = shutil.which("afplay") is not None
        self.last_played = {}

    def play(self, event, min_interval=0.0):
        now = time.time()
        if now - self.last_played.get(event, 0.0) < min_interval:
            return
        self.last_played[event] = now

        sound_file = SOUND_FILES.get(event)
        if self.afplay_available and sound_file:
            try:
                subprocess.Popen(
                    ["afplay", sound_file],
                    stdout=subprocess.DEVNULL,
                    stderr=subprocess.DEVNULL,
                )
                return
            except OSError:
                self.afplay_available = False

        curses.beep()


def ship_cells(player_x, player_y):
    return {
        (player_x, player_y - 2): ">",
        (player_x, player_y - 1): ">",
        (player_x, player_y): ">",
        (player_x, player_y + 1): ">",
        (player_x, player_y + 2): ">",
        (player_x + 1, player_y - 1): "=",
        (player_x + 1, player_y): "=",
        (player_x + 1, player_y + 1): "=",
        (player_x + 2, player_y - 1): "]",
        (player_x + 2, player_y): "]",
        (player_x + 2, player_y + 1): "]",
    }


def start_screen(stdscr):
    stdscr.clear()
    draw_center(stdscr, 3, "=== TERMINAL SPACE SHOOTER ===")
    draw_center(stdscr, 5, "Move: W/S or Up/Down")
    draw_center(stdscr, 6, "Shoot: Space")
    draw_center(stdscr, 7, "Enemy speed: Left/Right arrows")
    draw_center(stdscr, 8, "Quit: Q")
    draw_center(stdscr, 9, "Press any key to start")
    stdscr.refresh()
    stdscr.nodelay(False)
    stdscr.getch()
    stdscr.nodelay(True)


def game_over_screen(stdscr, score):
    stdscr.clear()
    draw_center(stdscr, 5, "GAME OVER")
    draw_center(stdscr, 7, f"Final score: {score}")
    draw_center(stdscr, 9, "Press R to restart or Q to quit")
    stdscr.refresh()

    stdscr.nodelay(False)
    while True:
        key = stdscr.getch()
        if key in (ord("q"), ord("Q")):
            return False
        if key in (ord("r"), ord("R")):
            return True


def run_game(stdscr):
    curses.curs_set(0)
    curses.start_color()
    curses.use_default_colors()
    curses.init_pair(1, curses.COLOR_CYAN, -1)
    curses.init_pair(2, curses.COLOR_RED, -1)
    curses.init_pair(3, curses.COLOR_YELLOW, -1)
    curses.init_pair(4, curses.COLOR_GREEN, -1)
    sound = SoundEngine()
    stdscr.nodelay(True)
    stdscr.timeout(0)

    while True:
        height, width = stdscr.getmaxyx()
        if height < 16 or width < 40:
            stdscr.clear()
            draw_center(stdscr, 2, "Window too small")
            draw_center(stdscr, 4, "Resize to at least 40x16")
            draw_center(stdscr, 6, "Press Q to quit")
            stdscr.refresh()
            key = stdscr.getch()
            if key in (ord("q"), ord("Q")):
                return
            time.sleep(0.05)
            continue

        start_screen(stdscr)
        sound.play("start", min_interval=0.3)

        player_x = width // 2
        player_y = height // 2
        bullets = []
        enemies = []
        score = 0
        lives = INITIAL_LIVES
        last_shot_time = 0.0
        enemy_step_interval = ENEMY_STEP_INTERVAL
        enemy_step_timer = 0.0
        last_frame_time = time.time()

        while lives > 0:
            frame_start = time.time()
            now = time.time()
            delta = now - last_frame_time
            last_frame_time = now

            height, width = stdscr.getmaxyx()
            player_x = 2
            player_y = clamp(player_y, 3, max(3, height - 4))

            key = stdscr.getch()
            if key in (ord("q"), ord("Q")):
                return
            if key in (ord("w"), ord("W"), curses.KEY_UP):
                player_y -= 1
            elif key in (ord("s"), ord("S"), curses.KEY_DOWN):
                player_y += 1
            elif key == curses.KEY_RIGHT:
                enemy_step_interval = max(MIN_ENEMY_STEP_INTERVAL, enemy_step_interval - ENEMY_SPEED_STEP)
            elif key == curses.KEY_LEFT:
                enemy_step_interval = min(MAX_ENEMY_STEP_INTERVAL, enemy_step_interval + ENEMY_SPEED_STEP)
            elif key == ord(" "):
                now = time.time()
                if now - last_shot_time >= SHOT_COOLDOWN:
                    bullets.append([player_x + 3, player_y - 2])
                    bullets.append([player_x + 3, player_y - 1])
                    bullets.append([player_x + 3, player_y])
                    bullets.append([player_x + 3, player_y + 1])
                    bullets.append([player_x + 3, player_y + 2])
                    last_shot_time = now
                    sound.play("shoot", min_interval=0.04)

            player_y = clamp(player_y, 3, max(3, height - 4))

            if len(enemies) < MAX_ENEMIES and random.random() < ENEMY_SPAWN_CHANCE:
                enemies.append([max(1, width - 2), random.randint(1, max(1, height - 2))])

            for bullet in bullets:
                bullet[0] += 1
            bullets = [b for b in bullets if b[0] < width - 1]

            enemy_step_timer += delta
            if enemy_step_timer >= enemy_step_interval:
                for enemy in enemies:
                    enemy[0] -= 1
                enemy_step_timer = 0.0

            bullets_to_remove = set()
            enemies_to_remove = set()
            for b_idx, bullet in enumerate(bullets):
                for e_idx, enemy in enumerate(enemies):
                    if bullet[0] == enemy[0] and bullet[1] == enemy[1]:
                        bullets_to_remove.add(b_idx)
                        enemies_to_remove.add(e_idx)
                        score += 10
                        break

            if enemies_to_remove:
                sound.play("hit", min_interval=0.05)

            bullets = [b for idx, b in enumerate(bullets) if idx not in bullets_to_remove]
            enemies = [e for idx, e in enumerate(enemies) if idx not in enemies_to_remove]

            filtered_enemies = []
            took_damage = False
            for enemy_x, enemy_y in enemies:
                if enemy_x <= player_x:
                    lives -= 1
                    took_damage = True
                else:
                    filtered_enemies.append([enemy_x, enemy_y])
            enemies = filtered_enemies

            ship_hit_cells = set(ship_cells(player_x, player_y).keys())
            remaining_enemies = []
            for enemy_x, enemy_y in enemies:
                if (enemy_x, enemy_y) in ship_hit_cells:
                    lives -= 1
                    took_damage = True
                else:
                    remaining_enemies.append([enemy_x, enemy_y])
            enemies = remaining_enemies

            if took_damage:
                sound.play("damage", min_interval=0.12)

            stdscr.erase()

            enemy_speed_percent = int(
                (MAX_ENEMY_STEP_INTERVAL - enemy_step_interval)
                / (MAX_ENEMY_STEP_INTERVAL - MIN_ENEMY_STEP_INTERVAL)
                * 100
            )
            top_bar = f" Score: {score}   Lives: {lives}   Enemy speed: {enemy_speed_percent}%   Q: Quit "
            try:
                stdscr.addstr(0, 0, top_bar[: max(0, width - 1)], curses.color_pair(4) | curses.A_BOLD)
            except curses.error:
                pass

            for bullet_x, bullet_y in bullets:
                if 0 < bullet_y < height and 0 < bullet_x < width:
                    try:
                        stdscr.addch(bullet_y, bullet_x, "|", curses.color_pair(3) | curses.A_BOLD)
                    except curses.error:
                        pass

            for enemy_x, enemy_y in enemies:
                if 0 < enemy_y < height and 0 < enemy_x < width:
                    try:
                        stdscr.addch(enemy_y, enemy_x, "<", curses.color_pair(2) | curses.A_BOLD)
                    except curses.error:
                        pass

            for (ship_x, ship_y), ship_char in ship_cells(player_x, player_y).items():
                if 0 < ship_y < height and 0 < ship_x < width:
                    try:
                        stdscr.addch(ship_y, ship_x, ship_char, curses.color_pair(1) | curses.A_BOLD)
                    except curses.error:
                        pass

            stdscr.refresh()

            elapsed = time.time() - frame_start
            delay = FRAME_DELAY - elapsed
            if delay > 0:
                time.sleep(delay)

        sound.play("game_over", min_interval=0.5)
        restart = game_over_screen(stdscr, score)
        if not restart:
            return


def main():
    curses.wrapper(run_game)


if __name__ == "__main__":
    main()
