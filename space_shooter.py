#!/usr/bin/env python3
import curses
import json
import os
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
TREASURE_SPAWN_CHANCE = 0.012
MAX_TREASURES = 2
TREASURE_STEP_INTERVAL = 0.15
STATUS_MESSAGE_DURATION = 1.8
SHIELD_DURATION = 1.2
SHIELD_COOLDOWN = 7.0
MAX_ENEMY_BULLETS = 28
BOOST_DURATION = 5.0
BOOST_POWER_MULTIPLIER = 2.0
BOSS_SCORE_STEP = 300
HIGH_SCORE_LIMIT = 10
HIGH_SCORE_FILE = os.path.join(os.path.dirname(__file__), "high_scores.json")

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
    "treasure": "/System/Library/Sounds/Hero.aiff",
    "shield_up": "/System/Library/Sounds/Blow.aiff",
    "shield_block": "/System/Library/Sounds/Tink.aiff",
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
        "cells": {
            (0, 0): ("<", 2),
            (1, -1): ("<", 2),
            (1, 0): ("=", 2),
            (1, 1): ("<", 2),
            (2, 0): ("<", 2),
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
        "fire_cooldown": 1.9,
        "shot": {"char": ":", "color": 2, "damage": 1, "speed": 1},
    },
    {
        "id": "spinner",
        "name": "Spinner",
        "cells": {
            (0, 0): ("<", 6),
            (1, -1): ("/", 6),
            (1, 0): ("O", 3),
            (1, 1): ("\\", 6),
            (2, 0): (">", 6),
        },
        "color": 6,
        "health": 2,
        "score": 20,
        "spawn_weight": 0.30,
        "speed": 1.45,
        "hit_sound": "hit_spinner",
        "destroy_sound": "destroy_spinner",
        "hit_effect": "nova",
        "destroy_effect": "nova",
        "fire_cooldown": 1.45,
        "shot": {"char": "*", "color": 6, "damage": 1, "speed": 1},
    },
    {
        "id": "brute",
        "name": "Brute",
        "cells": {
            (0, -1): ("[", 5),
            (0, 0): ("{", 5),
            (0, 1): ("[", 5),
            (1, -1): ("#", 5),
            (1, 0): ("#", 3),
            (1, 1): ("#", 5),
            (2, -1): ("#", 5),
            (2, 0): ("#", 5),
            (2, 1): ("#", 5),
            (3, -1): ("]", 5),
            (3, 0): (">", 5),
            (3, 1): ("]", 5),
        },
        "color": 5,
        "health": 4,
        "score": 40,
        "spawn_weight": 0.20,
        "speed": 0.85,
        "hit_sound": "hit_brute",
        "destroy_sound": "destroy_brute",
        "hit_effect": "chunk",
        "destroy_effect": "shock",
        "fire_cooldown": 2.4,
        "shot": {"char": "o", "color": 5, "damage": 2, "speed": 1},
    },
]

BOSS_TYPE = {
    "id": "boss",
    "name": "Dreadnought",
    "cells": {
        (0, -2): ("[", 5),
        (0, -1): ("[", 5),
        (0, 0): ("<", 5),
        (0, 1): ("[", 5),
        (0, 2): ("[", 5),
        (1, -2): ("#", 5),
        (1, -1): ("#", 5),
        (1, 0): ("#", 3),
        (1, 1): ("#", 5),
        (1, 2): ("#", 5),
        (2, -2): ("#", 5),
        (2, -1): ("#", 5),
        (2, 0): ("O", 3),
        (2, 1): ("#", 5),
        (2, 2): ("#", 5),
        (3, -2): ("#", 5),
        (3, -1): ("#", 5),
        (3, 0): ("#", 3),
        (3, 1): ("#", 5),
        (3, 2): ("#", 5),
        (4, -2): ("]", 5),
        (4, -1): ("]", 5),
        (4, 0): (">", 5),
        (4, 1): ("]", 5),
        (4, 2): ("]", 5),
    },
    "color": 5,
    "health": 26,
    "score": 260,
    "speed": 0.55,
    "hit_sound": "hit_brute",
    "destroy_sound": "destroy_brute",
    "hit_effect": "shock",
    "destroy_effect": "shock",
    "fire_cooldown": 0.85,
    "shot": {"char": "~", "color": 5, "damage": 2, "speed": 1},
}

EXPLOSION_STYLES = {
    "spark": [
        {"char": "+", "color": 3, "offsets": [(-1, 0), (1, 0), (0, -1), (0, 1)]},
        {"char": "*", "color": 3, "offsets": [(-1, -1), (-1, 1), (1, -1), (1, 1)]},
        {"char": ".", "color": 2, "offsets": [(0, 0), (-2, 0), (2, 0)]},
    ],
    "burst": [
        {
            "char": "*",
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
            "char": "+",
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
                (-3, 0),
                (3, 0),
                (-2, -1),
                (-2, 1),
                (2, -1),
                (2, 1),
            ],
        },
    ],
    "nova": [
        {"char": "o", "color": 6, "offsets": [(-1, 0), (1, 0), (0, -1), (0, 1)]},
        {"char": "+", "color": 3, "offsets": [(-1, -1), (-1, 1), (1, -1), (1, 1)]},
        {"char": ".", "color": 6, "offsets": [(-2, 0), (2, 0), (0, -2), (0, 2)]},
    ],
    "chunk": [
        {"char": "#", "color": 5, "offsets": [(0, 0), (-1, 0), (1, 0)]},
        {"char": "x", "color": 3, "offsets": [(-1, -1), (-1, 1), (1, -1), (1, 1)]},
        {"char": ".", "color": 2, "offsets": [(-2, 0), (2, 0), (0, -1), (0, 1)]},
    ],
    "shock": [
        {"char": "#", "color": 5, "offsets": [(0, 0), (-1, 0), (1, 0), (0, -1), (0, 1)]},
        {
            "char": "+",
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
    "treasure": [
        {"char": "$", "color": 3, "offsets": [(0, 0), (-1, 0), (1, 0), (0, -1), (0, 1)]},
        {"char": "+", "color": 4, "offsets": [(-1, -1), (-1, 1), (1, -1), (1, 1)]},
        {"char": ".", "color": 3, "offsets": [(-2, 0), (2, 0), (0, -2), (0, 2)]},
    ],
}

GUN_BY_KEY = {ord(gun["hotkey"]): index for index, gun in enumerate(GUN_TYPES)}

DIFFICULTY_LEVELS = [
    {
        "id": "easy",
        "name": "Easy",
        "key": ord("1"),
        "enemy_spawn_chance": 0.09,
        "enemy_speed_scale": 0.88,
        "starting_lives": 6,
        "treasure_spawn_chance": 0.018,
        "bonus_life_chance": 0.60,
        "score_multiplier": 1.0,
        "description": "6 lives, fewer enemies, more treasure",
    },
    {
        "id": "normal",
        "name": "Normal",
        "key": ord("2"),
        "enemy_spawn_chance": ENEMY_SPAWN_CHANCE,
        "enemy_speed_scale": 1.0,
        "starting_lives": INITIAL_LIVES,
        "treasure_spawn_chance": TREASURE_SPAWN_CHANCE,
        "bonus_life_chance": 0.45,
        "score_multiplier": 1.15,
        "description": "Balanced pace with a small score bonus",
    },
    {
        "id": "hard",
        "name": "Hard",
        "key": ord("3"),
        "enemy_spawn_chance": 0.16,
        "enemy_speed_scale": 1.18,
        "starting_lives": 4,
        "treasure_spawn_chance": 0.008,
        "bonus_life_chance": 0.28,
        "score_multiplier": 1.4,
        "description": "4 lives, faster swarms, rarer treasure",
    },
]


def clamp(value, low, high):
    return max(low, min(high, value))


def draw_center(stdscr, y, text):
    height, width = stdscr.getmaxyx()
    x = max(0, (width - len(text)) // 2)
    try:
        stdscr.addstr(y, x, text)
    except curses.error:
        pass


def draw_center_colored(stdscr, y, text, attributes=0):
    height, width = stdscr.getmaxyx()
    x = max(0, (width - len(text)) // 2)
    try:
        stdscr.addstr(y, x, text, attributes)
    except curses.error:
        pass


def load_high_scores():
    try:
        with open(HIGH_SCORE_FILE, "r", encoding="utf-8") as file:
            scores = json.load(file)
    except (OSError, json.JSONDecodeError):
        return []

    if not isinstance(scores, list):
        return []

    cleaned = []
    for entry in scores:
        if not isinstance(entry, dict):
            continue
        score = entry.get("score")
        difficulty = entry.get("difficulty", "Unknown")
        timestamp = entry.get("timestamp", "-")
        if isinstance(score, int):
            cleaned.append(
                {
                    "score": score,
                    "difficulty": str(difficulty),
                    "timestamp": str(timestamp),
                }
            )

    cleaned.sort(key=lambda item: item["score"], reverse=True)
    return cleaned[:HIGH_SCORE_LIMIT]


def save_high_scores(scores):
    trimmed = scores[:HIGH_SCORE_LIMIT]
    with open(HIGH_SCORE_FILE, "w", encoding="utf-8") as file:
        json.dump(trimmed, file, indent=2)


def record_high_score(scores, score, difficulty_name):
    entry = {
        "score": score,
        "difficulty": difficulty_name,
        "timestamp": time.strftime("%Y-%m-%d %H:%M"),
    }
    scores.append(entry)
    scores.sort(key=lambda item: item["score"], reverse=True)
    rank = scores.index(entry) + 1
    scores = scores[:HIGH_SCORE_LIMIT]
    try:
        save_high_scores(scores)
    except OSError:
        pass

    if rank > HIGH_SCORE_LIMIT:
        rank = None
    return scores, rank


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


def ship_cells(player_x, player_y, boosted=False):
    cells = {
        (player_x, player_y - 2): (">", 1),
        (player_x, player_y - 1): (">", 1),
        (player_x, player_y): (">", 1),
        (player_x, player_y + 1): (">", 1),
        (player_x, player_y + 2): (">", 1),
        (player_x + 1, player_y - 2): ("/", 1),
        (player_x + 1, player_y - 1): ("=", 1),
        (player_x + 1, player_y): ("=", 1),
        (player_x + 1, player_y + 1): ("=", 1),
        (player_x + 1, player_y + 2): ("\\", 1),
        (player_x + 2, player_y - 1): ("[", 1),
        (player_x + 2, player_y): ("#", 1),
        (player_x + 2, player_y + 1): ("[", 1),
        (player_x + 3, player_y - 2): ("}", 1),
        (player_x + 3, player_y - 1): ("]", 1),
        (player_x + 3, player_y): ("]", 1),
        (player_x + 3, player_y + 1): ("]", 1),
        (player_x + 3, player_y + 2): ("}", 1),
        (player_x + 4, player_y): ("]", 1),
    }

    if boosted:
        cells.update(
            {
                (player_x - 1, player_y - 3): ("+", 3),
                (player_x - 1, player_y + 3): ("+", 3),
                (player_x, player_y - 3): (">", 3),
                (player_x, player_y + 3): (">", 3),
                (player_x + 1, player_y - 3): ("/", 3),
                (player_x + 1, player_y + 3): ("\\", 3),
                (player_x + 2, player_y - 3): ("[", 3),
                (player_x + 2, player_y + 3): ("[", 3),
                (player_x + 3, player_y - 3): ("}", 3),
                (player_x + 3, player_y + 3): ("}", 3),
                (player_x + 4, player_y - 1): ("]", 3),
                (player_x + 4, player_y + 1): ("]", 3),
                (player_x + 5, player_y): ("]", 3),
            }
        )

    return cells


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


def treasure_cells(treasure):
    return {
        (treasure["x"], treasure["y"] - 1): ("+", 3),
        (treasure["x"] + 1, treasure["y"] - 1): ("-", 3),
        (treasure["x"] + 2, treasure["y"] - 1): ("+", 3),
        (treasure["x"], treasure["y"]): ("[", 3),
        (treasure["x"] + 1, treasure["y"]): ("$", 4),
        (treasure["x"] + 2, treasure["y"]): ("]", 3),
        (treasure["x"], treasure["y"] + 1): ("+", 3),
        (treasure["x"] + 1, treasure["y"] + 1): ("-", 3),
        (treasure["x"] + 2, treasure["y"] + 1): ("+", 3),
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
        "fire_timer": random.uniform(0.0, enemy_type["fire_cooldown"] * 0.6),
    }


def spawn_boss(width, height):
    center_y = random.randint(6, max(6, height - 7))
    return {
        "x": max(6, width - 9),
        "y": center_y,
        "type": BOSS_TYPE,
        "hp": BOSS_TYPE["health"],
        "move_timer": 0.0,
        "fire_timer": random.uniform(0.0, BOSS_TYPE["fire_cooldown"] * 0.6),
        "drift": random.choice((-1, 1)),
        "drift_timer": 0.0,
    }


def spawn_treasure(width, height):
    return {
        "x": max(6, width - 6),
        "y": random.randint(3, max(3, height - 4)),
        "move_timer": 0.0,
        "fall_timer": 0.0,
        "drift": random.choice((-1, 1)),
    }


def spawn_enemy_bullet(enemy, lane_shift=0):
    enemy_type = enemy["type"]
    shot = enemy_type["shot"]
    return {
        "x": enemy["x"] - 1,
        "y": enemy["y"] + lane_shift,
        "dx": shot["speed"],
        "damage": shot["damage"],
        "char": shot["char"],
        "color": shot["color"],
    }


def fire_gun(bullets, player_x, player_y, gun, now, power_level, damage_multiplier=1.0, muzzle_offset=5):
    projectiles = list(gun["projectiles"])

    if gun["id"] == "rapid" and power_level >= 1:
        projectiles.extend(
            [
                {"offset_y": -1, "dx": 2, "damage": 1, "char": ".", "color": 3},
                {"offset_y": 1, "dx": 2, "damage": 1, "char": ".", "color": 3},
            ]
        )
    elif gun["id"] == "spread" and power_level >= 1:
        projectiles.extend(
            [
                {"offset_y": -3, "dx": 1, "damage": 1, "char": "|", "color": 3},
                {"offset_y": 3, "dx": 1, "damage": 1, "char": "|", "color": 3},
            ]
        )
    elif gun["id"] == "cannon" and power_level >= 1:
        projectiles = [
            {
                **projectile,
                "damage": projectile["damage"] + power_level,
                "char": "@",
                "color": 5,
            }
            for projectile in projectiles
        ]

    for projectile in projectiles:
        boosted_damage = max(1, int(round(projectile["damage"] * damage_multiplier)))
        bullets.append(
            {
                "x": player_x + muzzle_offset,
                "y": player_y + projectile["offset_y"],
                "dx": projectile["dx"],
                "damage": boosted_damage,
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


def set_status_message(message, now):
    return {"text": message, "expires": now + STATUS_MESSAGE_DURATION}


def award_treasure(lives, power_level, difficulty):
    if random.random() < difficulty["bonus_life_chance"]:
        return lives + 1, power_level, "VIGOR UP +1 life"
    if power_level < 2:
        return lives, power_level + 1, f"POWER UP Lv{power_level + 2}"
    return lives + 1, power_level, "BONUS VIGOR +1 life"


def explosion_cells(effect, age):
    style = EXPLOSION_STYLES.get(effect["style"], EXPLOSION_STYLES["spark"])
    if not isinstance(style, list) or not style:
        return {(effect["x"], effect["y"]): ("*", 3)}

    if effect["duration"] <= 0:
        phase_index = len(style) - 1
    else:
        phase_index = min(len(style) - 1, int((age / effect["duration"]) * len(style)))

    phase = style[max(0, phase_index)]
    phase_char = phase.get("char", "*")
    phase_color = phase.get("color", 3)
    phase_offsets = phase.get("offsets", [])

    cells = {(effect["x"], effect["y"]): (phase_char, phase_color)}
    for offset_x, offset_y in phase_offsets:
        cells[(effect["x"] + offset_x, effect["y"] + offset_y)] = (
            phase_char,
            phase_color,
        )
    return cells


def start_screen(stdscr, high_scores):
    selected_index = 1
    stdscr.nodelay(False)

    while True:
        stdscr.clear()
        draw_center(stdscr, 2, "=== TERMINAL SPACE SHOOTER ===")
        draw_center(stdscr, 4, "Move: W/S or Up/Down")
        draw_center(stdscr, 5, "Shoot: Space")
        draw_center(stdscr, 6, "Switch guns: Left/Right arrows")
        draw_center(stdscr, 7, "Enemy speed: - slower   + faster")
        draw_center(stdscr, 8, "Shield: X    Pause: P    Quit: Q")
        if high_scores:
            best = high_scores[0]
            draw_center(stdscr, 3, f"High Score: {best['score']} ({best['difficulty']})")
        draw_center(stdscr, 10, "Enemies: scout dart   spinner core   brute block")
        draw_center(stdscr, 11, "Treasure: 5s Titan Boost (ship grows + 2x damage)")
        draw_center(stdscr, 12, "Choose difficulty:")

        for index, difficulty in enumerate(DIFFICULTY_LEVELS):
            prefix = ">" if index == selected_index else " "
            line = (
                f"{prefix} {index + 1}. {difficulty['name']}  "
                f"x{difficulty['score_multiplier']:.2f} score  "
                f"{difficulty['description']}"
            )
            attributes = curses.color_pair(3) | curses.A_BOLD if index == selected_index else curses.A_DIM
            draw_center_colored(stdscr, 14 + index, line, attributes)

        draw_center(stdscr, 17, "Use Up/Down or 1-3, then press Enter")
        stdscr.refresh()

        key = stdscr.getch()
        if key in (ord("q"), ord("Q")):
            return None
        if key in (curses.KEY_UP, ord("w"), ord("W")):
            selected_index = (selected_index - 1) % len(DIFFICULTY_LEVELS)
        elif key in (curses.KEY_DOWN, ord("s"), ord("S")):
            selected_index = (selected_index + 1) % len(DIFFICULTY_LEVELS)
        elif key in (curses.KEY_ENTER, 10, 13, ord(" ")):
            stdscr.nodelay(True)
            return DIFFICULTY_LEVELS[selected_index]
        else:
            for index, difficulty in enumerate(DIFFICULTY_LEVELS):
                if key == difficulty["key"]:
                    stdscr.nodelay(True)
                    return difficulty


def game_over_screen(stdscr, score, difficulty, high_scores, rank):
    stdscr.clear()
    draw_center(stdscr, 3, "GAME OVER")
    draw_center(stdscr, 5, f"Final score: {score} ({difficulty['name']})")
    if rank:
        draw_center(stdscr, 6, f"New leaderboard rank: #{rank}")
    else:
        draw_center(stdscr, 6, "No leaderboard entry this run")

    draw_center(stdscr, 8, "Top Scores")
    for index, entry in enumerate(high_scores[:5]):
        draw_center(
            stdscr,
            9 + index,
            f"{index + 1:>2}. {entry['score']:>5}  {entry['difficulty']:<6}  {entry['timestamp']}",
        )

    draw_center(stdscr, 15, "Press R to restart or Q to quit")
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
    high_scores = load_high_scores()
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

        difficulty = start_screen(stdscr, high_scores)
        if difficulty is None:
            return
        sound.play("start", min_interval=0.3)

        player_x = 2
        player_y = height // 2
        gun_index = 1
        bullets = []
        enemies = []
        enemy_bullets = []
        treasures = []
        explosions = []
        score = 0
        lives = difficulty["starting_lives"]
        power_level = 0
        status_message = None
        last_shot_time = 0.0
        enemy_step_interval = ENEMY_STEP_INTERVAL
        shield_until = 0.0
        shield_ready_at = 0.0
        boost_until = 0.0
        boss_next_score = BOSS_SCORE_STEP
        last_frame_time = time.time()

        while lives > 0:
            frame_start = time.time()
            now = time.time()
            delta = now - last_frame_time
            last_frame_time = now
            boost_active = now < boost_until
            ship_span = 3 if boost_active else 2

            height, width = stdscr.getmaxyx()
            player_y = clamp(player_y, 1 + ship_span, max(1 + ship_span, height - (2 + ship_span)))
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
            elif key in (ord("x"), ord("X")):
                if now >= shield_ready_at:
                    shield_until = now + SHIELD_DURATION
                    shield_ready_at = now + SHIELD_COOLDOWN
                    status_message = set_status_message("AEGIS ONLINE", now)
                    sound.play("shield_up", min_interval=0.1)
            elif key == ord(" "):
                if now - last_shot_time >= gun["cooldown"]:
                    fire_gun(
                        bullets,
                        player_x,
                        player_y,
                        gun,
                        now,
                        power_level,
                        damage_multiplier=BOOST_POWER_MULTIPLIER if boost_active else 1.0,
                        muzzle_offset=6 if boost_active else 5,
                    )
                    last_shot_time = now
                    sound.play(gun["sound"], min_interval=0.03)

            player_y = clamp(player_y, 1 + ship_span, max(1 + ship_span, height - (2 + ship_span)))

            boss_alive = any(enemy["type"]["id"] == "boss" for enemy in enemies)
            if score >= boss_next_score and not boss_alive:
                enemies.append(spawn_boss(width, height))
                status_message = set_status_message("BOSS WAVE INBOUND", now)
                boss_next_score += BOSS_SCORE_STEP
                boss_alive = True

            spawn_chance = difficulty["enemy_spawn_chance"] * (0.35 if boss_alive else 1.0)
            if len(enemies) < MAX_ENEMIES and random.random() < spawn_chance:
                enemies.append(spawn_enemy(width, height))
            if len(treasures) < MAX_TREASURES and random.random() < difficulty["treasure_spawn_chance"]:
                treasures.append(spawn_treasure(width, height))

            for bullet in bullets:
                bullet["x"] += bullet["dx"]
            bullets = [bullet for bullet in bullets if bullet["x"] < width - 1]

            for enemy in enemies:
                enemy["move_timer"] += delta
                enemy["fire_timer"] += delta
                move_threshold = max(
                    MIN_ENEMY_STEP_INTERVAL / 2,
                    enemy_step_interval
                    / (enemy["type"]["speed"] * difficulty["enemy_speed_scale"]),
                )
                if enemy["move_timer"] >= move_threshold:
                    enemy["x"] -= 1
                    enemy["move_timer"] = 0.0

                if enemy["type"]["id"] == "boss":
                    enemy["drift_timer"] += delta
                    if enemy["drift_timer"] >= 0.12:
                        enemy["y"] += enemy["drift"]
                        if enemy["y"] <= 6 or enemy["y"] >= height - 6:
                            enemy["drift"] *= -1
                            enemy["y"] = clamp(enemy["y"], 6, max(6, height - 6))
                        enemy["drift_timer"] = 0.0

                fire_threshold = enemy["type"]["fire_cooldown"] / difficulty["enemy_speed_scale"]
                while enemy["fire_timer"] >= fire_threshold:
                    enemy["fire_timer"] -= fire_threshold
                    if len(enemy_bullets) >= MAX_ENEMY_BULLETS or enemy["x"] <= player_x + 5:
                        continue
                    if enemy["type"]["id"] == "boss":
                        for lane_shift in (-2, 0, 2):
                            if len(enemy_bullets) < MAX_ENEMY_BULLETS and random.random() < 0.92:
                                enemy_bullets.append(spawn_enemy_bullet(enemy, lane_shift=lane_shift))
                    elif random.random() < 0.82:
                        enemy_bullets.append(spawn_enemy_bullet(enemy))

            for enemy_bullet in enemy_bullets:
                enemy_bullet["x"] -= enemy_bullet["dx"]
            enemy_bullets = [
                enemy_bullet
                for enemy_bullet in enemy_bullets
                if enemy_bullet["x"] > 0
            ]

            for treasure in treasures:
                treasure["move_timer"] += delta
                treasure["fall_timer"] += delta
                if treasure["move_timer"] >= TREASURE_STEP_INTERVAL:
                    treasure["x"] -= 1
                    treasure["move_timer"] = 0.0
                if treasure["fall_timer"] >= TREASURE_STEP_INTERVAL * 1.5:
                    treasure["y"] += treasure["drift"]
                    if treasure["y"] <= 3 or treasure["y"] >= height - 4:
                        treasure["drift"] *= -1
                        treasure["y"] = clamp(treasure["y"], 3, max(3, height - 4))
                    treasure["fall_timer"] = 0.0

            bullets_to_remove = set()
            enemy_bullets_to_remove = set()
            destroyed_enemy_ids = set()
            destroyed_treasure_ids = set()
            for bullet_index, bullet in enumerate(bullets):
                for enemy in enemies:
                    if (bullet["x"], bullet["y"]) in enemy_cells(enemy):
                        bullets_to_remove.add(bullet_index)
                        enemy["hp"] -= bullet["damage"]
                        enemy_type = enemy["type"]
                        if enemy["hp"] <= 0:
                            destroyed_enemy_ids.add(id(enemy))
                            score += int(enemy_type["score"] * difficulty["score_multiplier"])
                            explosions.append(
                                make_explosion(
                                    enemy["x"],
                                    enemy["y"],
                                    enemy_type["destroy_effect"],
                                    duration_multiplier=1.35,
                                )
                            )
                            sound.play(enemy_type["destroy_sound"], min_interval=0.03)
                            if enemy_type["id"] == "boss":
                                lives += 1
                                status_message = set_status_message("BOSS DOWN +1 LIFE", now)
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
                else:
                    for enemy_bullet_index, enemy_bullet in enumerate(enemy_bullets):
                        if bullet["x"] == enemy_bullet["x"] and bullet["y"] == enemy_bullet["y"]:
                            bullets_to_remove.add(bullet_index)
                            enemy_bullets_to_remove.add(enemy_bullet_index)
                            explosions.append(
                                make_explosion(
                                    bullet["x"],
                                    bullet["y"],
                                    "spark",
                                    duration_multiplier=0.65,
                                )
                            )
                            break
                    else:
                        for treasure in treasures:
                            if (bullet["x"], bullet["y"]) in treasure_cells(treasure):
                                bullets_to_remove.add(bullet_index)
                                destroyed_treasure_ids.add(id(treasure))
                                lives, power_level, reward_text = award_treasure(
                                    lives, power_level, difficulty
                                )
                                boost_until = now + BOOST_DURATION
                                explosions.append(
                                    make_explosion(
                                        treasure["x"] + 1,
                                        treasure["y"],
                                        "treasure",
                                        duration_multiplier=1.1,
                                    )
                                )
                                status_message = set_status_message(
                                    f"{reward_text} + TITAN BOOST x2",
                                    now,
                                )
                                sound.play("treasure", min_interval=0.05)
                                break

            bullets = [
                bullet for index, bullet in enumerate(bullets) if index not in bullets_to_remove
            ]
            enemy_bullets = [
                enemy_bullet
                for index, enemy_bullet in enumerate(enemy_bullets)
                if index not in enemy_bullets_to_remove
            ]
            enemies = [enemy for enemy in enemies if id(enemy) not in destroyed_enemy_ids]
            treasures = [treasure for treasure in treasures if id(treasure) not in destroyed_treasure_ids]

            explosions = [
                effect
                for effect in explosions
                if now - effect["started"] < effect["duration"]
            ]
            if status_message and now >= status_message["expires"]:
                status_message = None

            filtered_enemies = []
            took_damage = False
            for enemy in enemies:
                if any(cell_x <= player_x for cell_x, _ in enemy_cells(enemy)):
                    lives -= 1
                    took_damage = True
                else:
                    filtered_enemies.append(enemy)
            enemies = filtered_enemies

            treasures = [
                treasure
                for treasure in treasures
                if all(cell_x > 0 for cell_x, _ in treasure_cells(treasure))
            ]

            boost_active = now < boost_until
            ship_hit_cells = set(ship_cells(player_x, player_y, boosted=boost_active).keys())
            shield_active = now < shield_until
            remaining_enemies = []
            for enemy in enemies:
                if ship_hit_cells.intersection(enemy_cells(enemy).keys()):
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

            remaining_enemy_bullets = []
            for enemy_bullet in enemy_bullets:
                if (enemy_bullet["x"], enemy_bullet["y"]) in ship_hit_cells:
                    if shield_active:
                        explosions.append(
                            make_explosion(
                                enemy_bullet["x"],
                                enemy_bullet["y"],
                                "spark",
                                duration_multiplier=0.7,
                            )
                        )
                        sound.play("shield_block", min_interval=0.02)
                    else:
                        lives -= enemy_bullet["damage"]
                        took_damage = True
                else:
                    remaining_enemy_bullets.append(enemy_bullet)
            enemy_bullets = remaining_enemy_bullets

            if took_damage:
                sound.play("damage", min_interval=0.12)

            stdscr.erase()

            enemy_speed_percent = int(
                (MAX_ENEMY_STEP_INTERVAL - enemy_step_interval)
                / (MAX_ENEMY_STEP_INTERVAL - MIN_ENEMY_STEP_INTERVAL)
                * 100
            )
            hud = (
                f" Score: {score}   Lives: {lives}   Power: {power_level + 1}"
                f"   Difficulty: {difficulty['name']} x{difficulty['score_multiplier']:.2f}"
                f"   Gun: {gun['name']} [Left/Right]"
                f"   Boost: {'ON' if boost_active else 'OFF'}"
                f"   Shield: {'ON' if shield_active else 'RDY' if now >= shield_ready_at else f'{max(0.0, shield_ready_at - now):.1f}s'} [X]"
                f"   Enemy speed: {enemy_speed_percent}% [+/-]   P: Pause   Q: Quit "
            )
            try:
                stdscr.addstr(0, 0, hud[: max(0, width - 1)], curses.color_pair(4) | curses.A_BOLD)
            except curses.error:
                pass

            gun_line = " Guns: Left/Right cycle   Rapid   Spread   Cannon   Shoot [$] crates for Vigor/Power "
            try:
                stdscr.addstr(1, 0, gun_line[: max(0, width - 1)], curses.color_pair(1) | curses.A_BOLD)
            except curses.error:
                pass
            if status_message:
                try:
                    stdscr.addstr(
                        2,
                        0,
                        f" Status: {status_message['text']} "[: max(0, width - 1)],
                        curses.color_pair(3) | curses.A_BOLD,
                    )
                except curses.error:
                    pass

            if boost_active:
                try:
                    stdscr.addstr(
                        3,
                        0,
                        f" Titan Boost: {max(0.0, boost_until - now):.1f}s   Damage x{BOOST_POWER_MULTIPLIER:.1f} "[
                            : max(0, width - 1)
                        ],
                        curses.color_pair(5) | curses.A_BOLD,
                    )
                except curses.error:
                    pass

            boss = next((enemy for enemy in enemies if enemy["type"]["id"] == "boss"), None)
            if boss:
                try:
                    stdscr.addstr(
                        4,
                        0,
                        f" BOSS {boss['type']['name']} HP: {boss['hp']} "[: max(0, width - 1)],
                        curses.color_pair(2) | curses.A_BOLD,
                    )
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

            for enemy_bullet in enemy_bullets:
                bullet_x = enemy_bullet["x"]
                bullet_y = enemy_bullet["y"]
                if 0 < bullet_y < height and 0 < bullet_x < width:
                    try:
                        stdscr.addch(
                            bullet_y,
                            bullet_x,
                            enemy_bullet["char"],
                            curses.color_pair(enemy_bullet["color"]) | curses.A_BOLD,
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

            for treasure in treasures:
                for (cell_x, cell_y), (cell_char, color_pair) in treasure_cells(treasure).items():
                    if 2 < cell_y < height and 0 < cell_x < width:
                        try:
                            stdscr.addch(
                                cell_y,
                                cell_x,
                                cell_char,
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

            for (ship_x, ship_y), (ship_char, color_pair) in ship_cells(player_x, player_y, boosted=boost_active).items():
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

            if shield_active:
                aura_points = [
                    (player_x - 1, player_y - 2),
                    (player_x - 1, player_y + 2),
                    (player_x + 1, player_y - 3),
                    (player_x + 1, player_y + 3),
                    (player_x + 3, player_y - 3),
                    (player_x + 3, player_y + 3),
                    (player_x + 5, player_y - 2),
                    (player_x + 5, player_y + 2),
                ]
                for aura_x, aura_y in aura_points:
                    if 1 < aura_y < height and 0 < aura_x < width:
                        try:
                            stdscr.addch(
                                aura_y,
                                aura_x,
                                "*",
                                curses.color_pair(6) | curses.A_BOLD,
                            )
                        except curses.error:
                            pass

            stdscr.refresh()

            elapsed = time.time() - frame_start
            delay = FRAME_DELAY - elapsed
            if delay > 0:
                time.sleep(delay)

        sound.play("game_over", min_interval=0.5)
        high_scores, rank = record_high_score(high_scores, score, difficulty["name"])
        restart = game_over_screen(stdscr, score, difficulty, high_scores, rank)
        if not restart:
            return


def main():
    curses.wrapper(run_game)


if __name__ == "__main__":
    main()
