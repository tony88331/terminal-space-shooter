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
INITIAL_LIVES = 5
EXPLOSION_DURATION = 0.18

SOUND_FILES = {
    "start": "/System/Library/Sounds/Hero.aiff",
    "gun_swap": "/System/Library/Sounds/Glass.aiff",
    "shoot_rapid": "/System/Library/Sounds/Pop.aiff",
    "shoot_spread": "/System/Library/Sounds/Ping.aiff",
    "shoot_cannon": "/System/Library/Sounds/Bottle.aiff",
    "hit_scout": "/System/Library/Sounds/Tink.aiff",
    "destroy_scout": "/System/Library/Sounds/Frog.aiff",
    "hit_spinner": "/System/Library/Sounds/Glass.aiff",
    "destroy_spinner": "/System/Library/Sounds/Purr.aiff",
    "hit_brute": "/System/Library/Sounds/Basso.aiff",
    "destroy_brute": "/System/Library/Sounds/Blow.aiff",
    "damage": "/System/Library/Sounds/Submarine.aiff",
    "game_over": "/System/Library/Sounds/Funk.aiff",
}

GUN_TYPES = [
    {
        "id": "rapid",
        "name": "Rapid",
        "hotkey": "1",
        "cooldown": 0.04,
        "sound": "shoot_rapid",
        "projectiles": [
            {"offset_y": 0, "dx": 2, "damage": 1, "char": ".", "color": 3},
        ],
    },
    {
        "id": "spread",
        "name": "Spread",
        "hotkey": "2",
        "cooldown": 0.10,
        "sound": "shoot_spread",
        "projectiles": [
            {"offset_y": -2, "dx": 1, "damage": 1, "char": "|", "color": 3},
            {"offset_y": -1, "dx": 1, "damage": 1, "char": "|", "color": 3},
            {"offset_y": 0, "dx": 1, "damage": 1, "char": "|", "color": 3},
            {"offset_y": 1, "dx": 1, "damage": 1, "char": "|", "color": 3},
            {"offset_y": 2, "dx": 1, "damage": 1, "char": "|", "color": 3},
        ],
    },
    {
        "id": "cannon",
        "name": "Cannon",
        "hotkey": "3",
        "cooldown": 0.18,
        "sound": "shoot_cannon",
        "projectiles": [
            {"offset_y": -1, "dx": 1, "damage": 2, "char": "=", "color": 5},
            {"offset_y": 0, "dx": 1, "damage": 3, "char": "=", "color": 5},
            {"offset_y": 1, "dx": 1, "damage": 2, "char": "=", "color": 5},
        ],
    },
]

ENEMY_TYPES = [
    {
        "id": "scout",
        "name": "Scout",
        "shape": "<",
        "cells": {
            (0, 0): ("<", 2),
            (1, -1): ("<", 2),
            (1, 1): ("<", 2),
        },
        "color": 2,
        "health": 1,
        "score": 10,
        "spawn_weight": 0.50,
        "speed": 1.20,
        "hit_sound": "hit_scout",
        "destroy_sound": "destroy_scout",
        "hit_effect": "spark",
        "destroy_effect": "burst",
    },
    {
        "id": "spinner",
        "name": "Spinner",
        "shape": "@",
        "color": 6,
        "health": 2,
        "score": 20,
        "spawn_weight": 0.30,
        "speed": 1.45,
        "hit_sound": "hit_spinner",
        "destroy_sound": "destroy_spinner",
        "hit_effect": "nova",
        "destroy_effect": "nova",
    },
    {
        "id": "brute",
        "name": "Brute",
        "shape": "#",
        "color": 5,
        "health": 4,
        "score": 40,
        "spawn_weight": 0.20,
        "speed": 0.85,
        "hit_sound": "hit_brute",
        "destroy_sound": "destroy_brute",
        "hit_effect": "chunk",
        "destroy_effect": "shock",
    },
]

EXPLOSION_STYLES = {
    "spark": [
        {"char": "+", "color": 3, "offsets": [(-1, 0), (1, 0), (0, -1), (0, 1)]},
        {"char": ".", "color": 3, "offsets": [(-1, 0), (1, 0), (0, -1), (0, 1)]},
        {"char": ".", "color": 2, "offsets": [(0, 0)]},
    ],
    "burst": [
        {
            "char": "+",
            "color": 3,
            "offsets": [
                (-1, 0),
                (1, 0),
                (0, -1),
                (0, 1),
                (-1, -1),
                (-1, 1),
                (1, -1),
                (1, 1),
            ],
        },
        {
            "char": "*",
            "color": 2,
            "offsets": [
                (-2, 0),
                (2, 0),
                (0, -2),
                (0, 2),
                (-1, -2),
                (-1, 2),
                (1, -2),
                (1, 2),
            ],
        },
        {
            "char": ".",
            "color": 3,
            "offsets": [
                (-2, -1),
                (-2, 1),
                (2, -1),
                (2, 1),
                (-3, 0),
                (3, 0),
            ],
        },
    ],
    "nova": [
        {"char": "o", "color": 6, "offsets": [(-1, 0), (1, 0), (0, -1), (0, 1)]},
        {"char": "*", "color": 6, "offsets": [(-1, -1), (-1, 1), (1, -1), (1, 1)]},
        {"char": ".", "color": 3, "offsets": [(-2, 0), (2, 0), (0, -2), (0, 2)]},
    ],
    "chunk": [
        {"char": "%", "color": 5, "offsets": [(0, 0), (-1, 0), (1, 0)]},
        {"char": "x", "color": 5, "offsets": [(-1, -1), (-1, 1), (1, -1), (1, 1)]},
        {"char": ".", "color": 2, "offsets": [(-2, 0), (2, 0), (0, -1), (0, 1)]},
    ],
    "shock": [
        {"char": "#", "color": 5, "offsets": [(0, 0), (-1, 0), (1, 0), (0, -1), (0, 1)]},
        {
            "char": "*",
            "color": 3,
            "offsets": [
                (-2, 0),
                (2, 0),
                (0, -2),
                (0, 2),
                (-1, -1),
                (-1, 1),
                (1, -1),
                (1, 1),
            ],
        },
        {"char": ".", "color": 2, "offsets": [(-3, 0), (3, 0), (0, -2), (0, 2)]},
    ],
}

GUN_BY_KEY = {ord(gun["hotkey"]): index for index, gun in enumerate(GUN_TYPES)}


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
        (player_x, player_y - 2): (">", 1),
        (player_x, player_y - 1): (">", 1),
        (player_x, player_y): (">", 1),
        (player_x, player_y + 1): (">", 1),
        (player_x, player_y + 2): (">", 1),
        (player_x + 1, player_y - 1): ("=", 1),
        (player_x + 1, player_y): ("=", 1),
        (player_x + 1, player_y + 1): ("=", 1),
        (player_x + 2, player_y - 1): ("=", 1),
        (player_x + 2, player_y): ("=", 1),
        (player_x + 2, player_y + 1): ("=", 1),
        (player_x + 3, player_y - 2): ("]", 1),
        (player_x + 3, player_y - 1): ("]", 1),
        (player_x + 3, player_y): ("]", 1),
        (player_x + 3, player_y + 1): ("]", 1),
        (player_x + 3, player_y + 2): ("]", 1),
    }


def enemy_cells(enemy):
    enemy_type = enemy["type"]
    cells = enemy_type.get("cells")
    if cells:
        return {
            (enemy["x"] + offset_x, enemy["y"] + offset_y): (char, color)
            for (offset_x, offset_y), (char, color) in cells.items()
        }

    return {
        (enemy["x"], enemy["y"]): (enemy_type["shape"], enemy_type["color"]),
    }


def select_gun(gun_index, sound, quiet=False):
    gun_index %= len(GUN_TYPES)
    if not quiet:
        sound.play("gun_swap", min_interval=0.05)
    return gun_index


def spawn_enemy(width, height):
    enemy_type = random.choices(
        ENEMY_TYPES,
        weights=[enemy["spawn_weight"] for enemy in ENEMY_TYPES],
        k=1,
    )[0]
    return {
        "x": max(1, width - 2),
        "y": random.randint(2, max(2, height - 2)),
        "type": enemy_type,
        "hp": enemy_type["health"],
        "move_timer": 0.0,
    }


def fire_gun(bullets, player_x, player_y, gun, now):
    for projectile in gun["projectiles"]:
        bullets.append(
            {
                "x": player_x + 4,
                "y": player_y + projectile["offset_y"],
                "dx": projectile["dx"],
                "damage": projectile["damage"],
                "char": projectile["char"],
                "color": projectile["color"],
                "fired": now,
            }
        )


def make_explosion(x, y, style, duration_multiplier=1.0):
    return {
        "x": x,
        "y": y,
        "style": style,
        "started": time.time(),
        "duration": EXPLOSION_DURATION * duration_multiplier,
    }


def explosion_cells(effect, age):
    style = EXPLOSION_STYLES.get(effect["style"], EXPLOSION_STYLES["spark"])
    if effect["duration"] <= 0:
        phase_index = len(style) - 1
    else:
        phase_index = min(len(style) - 1, int((age / effect["duration"]) * len(style)))

    phase = style[phase_index]
    cells = {(effect["x"], effect["y"]): (phase["char"], phase["color"])}
    for offset_x, offset_y in phase["offsets"]:
        cells[(effect["x"] + offset_x, effect["y"] + offset_y)] = (
            phase["char"],
            phase["color"],
        )
    return cells


def start_screen(stdscr):
    stdscr.clear()
    draw_center(stdscr, 2, "=== TERMINAL SPACE SHOOTER ===")
    draw_center(stdscr, 4, "Move: W/S or Up/Down")
    draw_center(stdscr, 5, "Shoot: Space")
    draw_center(stdscr, 6, "Switch guns: Left/Right arrows")
    draw_center(stdscr, 7, "Enemy speed: - slower   + faster")
    draw_center(stdscr, 8, "Pause: P    Quit: Q")
    draw_center(stdscr, 10, "Enemies: <<< Scout (1 HP / 10)   @ Spinner (2 HP / 20)   # Brute (4 HP / 40)")
    draw_center(stdscr, 12, "Press any key to start")
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


def pause_screen(stdscr):
    height, _ = stdscr.getmaxyx()
    draw_center(stdscr, max(3, height // 2 - 1), "PAUSED")
    draw_center(stdscr, max(4, height // 2 + 1), "Press P to resume or Q to quit")
    stdscr.refresh()

    stdscr.nodelay(False)
    while True:
        key = stdscr.getch()
        if key in (ord("p"), ord("P")):
            stdscr.nodelay(True)
            stdscr.timeout(0)
            return True
        if key in (ord("q"), ord("Q")):
            stdscr.nodelay(True)
            stdscr.timeout(0)
            return False


def run_game(stdscr):
    curses.curs_set(0)
    curses.start_color()
    curses.use_default_colors()
    curses.init_pair(1, curses.COLOR_CYAN, -1)
    curses.init_pair(2, curses.COLOR_RED, -1)
    curses.init_pair(3, curses.COLOR_YELLOW, -1)
    curses.init_pair(4, curses.COLOR_GREEN, -1)
    curses.init_pair(5, curses.COLOR_MAGENTA, -1)
    curses.init_pair(6, curses.COLOR_BLUE, -1)
    sound = SoundEngine()
    stdscr.nodelay(True)
    stdscr.timeout(0)

    while True:
        height, width = stdscr.getmaxyx()
        if height < 18 or width < 60:
            stdscr.clear()
            draw_center(stdscr, 2, "Window too small")
            draw_center(stdscr, 4, "Resize to at least 60x18")
            draw_center(stdscr, 6, "Press Q to quit")
            stdscr.refresh()
            key = stdscr.getch()
            if key in (ord("q"), ord("Q")):
                return
            time.sleep(0.05)
            continue

        start_screen(stdscr)
        sound.play("start", min_interval=0.3)

        player_x = 2
        player_y = height // 2
        gun_index = 1
        bullets = []
        enemies = []
        explosions = []
        score = 0
        lives = INITIAL_LIVES
        last_shot_time = 0.0
        enemy_step_interval = ENEMY_STEP_INTERVAL
        last_frame_time = time.time()

        while lives > 0:
            frame_start = time.time()
            now = time.time()
            delta = now - last_frame_time
            last_frame_time = now

            height, width = stdscr.getmaxyx()
            player_y = clamp(player_y, 3, max(3, height - 4))
            gun = GUN_TYPES[gun_index]

            key = stdscr.getch()
            if key in (ord("q"), ord("Q")):
                return
            if key in (ord("p"), ord("P")):
                if not pause_screen(stdscr):
                    return
                last_frame_time = time.time()
                continue
            if key in (ord("w"), ord("W"), curses.KEY_UP):
                player_y -= 1
            elif key in (ord("s"), ord("S"), curses.KEY_DOWN):
                player_y += 1
            elif key == curses.KEY_RIGHT:
                gun_index = select_gun(gun_index + 1, sound)
                gun = GUN_TYPES[gun_index]
            elif key == curses.KEY_LEFT:
                gun_index = select_gun(gun_index - 1, sound)
                gun = GUN_TYPES[gun_index]
            elif key in (ord("+"), ord("=")):
                enemy_step_interval = max(
                    MIN_ENEMY_STEP_INTERVAL,
                    enemy_step_interval - ENEMY_SPEED_STEP,
                )
            elif key in (ord("-"), ord("_")):
                enemy_step_interval = min(
                    MAX_ENEMY_STEP_INTERVAL,
                    enemy_step_interval + ENEMY_SPEED_STEP,
                )
            elif key in GUN_BY_KEY:
                gun_index = select_gun(GUN_BY_KEY[key], sound)
                gun = GUN_TYPES[gun_index]
            elif key == ord(" "):
                if now - last_shot_time >= gun["cooldown"]:
                    fire_gun(bullets, player_x, player_y, gun, now)
                    last_shot_time = now
                    sound.play(gun["sound"], min_interval=0.03)

            player_y = clamp(player_y, 3, max(3, height - 4))

            if len(enemies) < MAX_ENEMIES and random.random() < ENEMY_SPAWN_CHANCE:
                enemies.append(spawn_enemy(width, height))

            for bullet in bullets:
                bullet["x"] += bullet["dx"]
            bullets = [bullet for bullet in bullets if bullet["x"] < width - 1]

            for enemy in enemies:
                enemy["move_timer"] += delta
                move_threshold = max(MIN_ENEMY_STEP_INTERVAL / 2, enemy_step_interval / enemy["type"]["speed"])
                if enemy["move_timer"] >= move_threshold:
                    enemy["x"] -= 1
                    enemy["move_timer"] = 0.0

            bullets_to_remove = set()
            destroyed_enemy_ids = set()
            for bullet_index, bullet in enumerate(bullets):
                for enemy in enemies:
                    if enemy["x"] == bullet["x"] and enemy["y"] == bullet["y"]:
                        bullets_to_remove.add(bullet_index)
                        enemy["hp"] -= bullet["damage"]
                        enemy_type = enemy["type"]
                        if enemy["hp"] <= 0:
                            destroyed_enemy_ids.add(id(enemy))
                            score += enemy_type["score"]
                            explosions.append(
                                make_explosion(
                                    enemy["x"],
                                    enemy["y"],
                                    enemy_type["destroy_effect"],
                                    duration_multiplier=1.35,
                                )
                            )
                            sound.play(enemy_type["destroy_sound"], min_interval=0.03)
                        else:
                            explosions.append(
                                make_explosion(
                                    enemy["x"],
                                    enemy["y"],
                                    enemy_type["hit_effect"],
                                    duration_multiplier=0.75,
                                )
                            )
                            sound.play(enemy_type["hit_sound"], min_interval=0.03)
                        break

            bullets = [
                bullet for index, bullet in enumerate(bullets) if index not in bullets_to_remove
            ]
            enemies = [enemy for enemy in enemies if id(enemy) not in destroyed_enemy_ids]

            explosions = [
                effect
                for effect in explosions
                if now - effect["started"] < effect["duration"]
            ]

            filtered_enemies = []
            took_damage = False
            for enemy in enemies:
                if enemy["x"] <= player_x:
                    lives -= 1
                    took_damage = True
                else:
                    filtered_enemies.append(enemy)
            enemies = filtered_enemies

            ship_hit_cells = set(ship_cells(player_x, player_y).keys())
            remaining_enemies = []
            for enemy in enemies:
                if (enemy["x"], enemy["y"]) in ship_hit_cells:
                    lives -= 1
                    took_damage = True
                    explosions.append(
                        make_explosion(
                            enemy["x"],
                            enemy["y"],
                            enemy["type"]["destroy_effect"],
                            duration_multiplier=1.0,
                        )
                    )
                else:
                    remaining_enemies.append(enemy)
            enemies = remaining_enemies

            if took_damage:
                sound.play("damage", min_interval=0.12)

            stdscr.erase()

            enemy_speed_percent = int(
                (MAX_ENEMY_STEP_INTERVAL - enemy_step_interval)
                / (MAX_ENEMY_STEP_INTERVAL - MIN_ENEMY_STEP_INTERVAL)
                * 100
            )
            hud = (
                f" Score: {score}   Lives: {lives}   Gun: {gun['name']} [Left/Right]"
                f"   Enemy speed: {enemy_speed_percent}% [+/-]   P: Pause   Q: Quit "
            )
            try:
                stdscr.addstr(0, 0, hud[: max(0, width - 1)], curses.color_pair(4) | curses.A_BOLD)
            except curses.error:
                pass

            gun_line = " Guns: Left/Right cycle   Rapid (fast)   Spread (wide)   Cannon (heavy) "
            try:
                stdscr.addstr(1, 0, gun_line[: max(0, width - 1)], curses.color_pair(1) | curses.A_BOLD)
            except curses.error:
                pass

            for bullet in bullets:
                bullet_x = bullet["x"]
                bullet_y = bullet["y"]
                if 0 < bullet_y < height and 0 < bullet_x < width:
                    try:
                        stdscr.addch(
                            bullet_y,
                            bullet_x,
                            bullet["char"],
                            curses.color_pair(bullet["color"]) | curses.A_BOLD,
                        )
                    except curses.error:
                        pass

            for effect in explosions:
                age = now - effect["started"]
                for (effect_x, effect_y), (effect_char, color_pair) in explosion_cells(effect, age).items():
                    if 1 < effect_y < height and 0 < effect_x < width:
                        try:
                            stdscr.addch(
                                effect_y,
                                effect_x,
                                effect_char,
                                curses.color_pair(color_pair) | curses.A_BOLD,
                            )
                        except curses.error:
                            pass

            for enemy in enemies:
                enemy_x = enemy["x"]
                enemy_y = enemy["y"]
                enemy_type = enemy["type"]
                if 1 < enemy_y < height and 0 < enemy_x < width:
                    for (cell_x, cell_y), (cell_char, color_pair) in enemy_cells(enemy).items():
                        if 1 < cell_y < height and 0 < cell_x < width:
                            try:
                                stdscr.addch(
                                    cell_y,
                                    cell_x,
                                    cell_char,
                                    curses.color_pair(color_pair) | curses.A_BOLD,
                                )
                            except curses.error:
                                pass

                    if enemy["hp"] > 1 and enemy_x + 1 < width:
                        try:
                            stdscr.addstr(
                                enemy_y,
                                enemy_x + 1,
                                str(enemy["hp"]),
                                curses.color_pair(enemy_type["color"]) | curses.A_DIM,
                            )
                        except curses.error:
                            pass

            for (ship_x, ship_y), (ship_char, color_pair) in ship_cells(player_x, player_y).items():
                if 1 < ship_y < height and 0 < ship_x < width:
                    try:
                        stdscr.addch(
                            ship_y,
                            ship_x,
                            ship_char,
                            curses.color_pair(color_pair) | curses.A_BOLD,
                        )
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
