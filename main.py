import pygame
import random
import math
import sys

pygame.init()

try:
    pygame.mixer.init()
except:
    pass

WIDTH, HEIGHT = 1000, 600
GROUND_Y = 530
PLAYER_W, PLAYER_H = 150, 230
MAX_HP = 100
MAX_ENERGY = 100
ENERGY_SPEED = 40

DOMAIN_DURATION = 30
SPECIAL_COOLDOWN = 30

screen = pygame.display.set_mode((WIDTH, HEIGHT), pygame.SCALED)
pygame.display.set_caption("GOJO VS SUKUNA")
clock = pygame.time.Clock()

font = pygame.font.SysFont("arial", 30, bold=True)
big_font = pygame.font.SysFont("arial", 65, bold=True)
small_font = pygame.font.SysFont("arial", 18, bold=True)


# ================= ФАЙЛЫ =================

def load_image(names, size=None):
    if isinstance(names, str):
        names = [names]

    for name in names:
        try:
            img = pygame.image.load(name).convert_alpha()
            if size:
                img = pygame.transform.scale(img, size)
            return img
        except:
            pass

    return None


background = load_image("arena.png", (WIDTH, HEIGHT))

images = {
    "GOJO": load_image(["gojo.png", "gojo.png.png"], (PLAYER_W, PLAYER_H)),
    "SUKUNA": load_image(["sukuna.png", "sukuna.png.png"], (PLAYER_W, PLAYER_H)),
    "YUJI": load_image("yuji.png", (PLAYER_W, PLAYER_H)),
    "MEGUMI": load_image("megumi.png", (PLAYER_W, PLAYER_H)),
    "YUTA": load_image("yuta_rika.png", (PLAYER_W, PLAYER_H)),
    "MAHITO": load_image("mahito.png", (PLAYER_W, PLAYER_H))
}

skins = {
    "GOJO": [
        ("Обычный Годжо", images["GOJO"]),
        ("Годжо-ученик", load_image("gojo_sunglasses.png", (PLAYER_W, PLAYER_H))),
        ("Годжо без повязки", load_image("gojo_teacher.png", (PLAYER_W, PLAYER_H))),
        ("Годжо из манги", load_image("gojo_manga.png", (PLAYER_W, PLAYER_H)))
    ],
    "SUKUNA": [
        ("Обычный Сукуна", images["SUKUNA"]),
        ("Сукуна в своей одежде", load_image("sukuna_clothes.png", (PLAYER_W, PLAYER_H))),
        ("Хейан Сукуна", load_image("sukuna_hiean.png", (PLAYER_W, PLAYER_H)))
    ],
    "YUJI": [("Юдзи Итадори", images["YUJI"])],
    "MEGUMI": [("Мегуми Фушигуро", images["MEGUMI"])],
    "YUTA": [("Юта Оккоцу и Рика", images["YUTA"])],
    "MAHITO": [("Махито", images["MAHITO"])]
}

skin_index = {c: 0 for c in skins}


# ================= ЗВУКИ =================

def load_sound(filename):
    try:
        sound = pygame.mixer.Sound(filename)
        sound.set_volume(1.0)
        return sound
    except:
        print("Не удалось загрузить:", filename)
        return None


sounds = {
    "gojo_domain": load_sound("gojo_domain.mp3"),
    "sukuna_domain": load_sound("sukuna_domain.mp3"),
    "gojo_purple": load_sound("gojo_purple.mp3"),
    "sukuna_fuga": load_sound("sukuna_fuga.mp3"),
    "yuji_bf": load_sound("yuji_bf.mp3"),
    "yuji_domain": load_sound("yuji_domain.mp3"),
    "mahoraga": load_sound("mahoraga_megumi.mp3"),
    "megumi_domain": load_sound("megumi_domain.mp3"),
    "victory": load_sound("light_victory.mp3")
}

music_loaded = False
try:
    pygame.mixer.music.load("judas.mp3")
    music_loaded = True
except:
    pass


def play_sound(name):
    # После завершения раунда разрешена только финальная речь Лайта.
    if round_over and name != "victory":
        return
    sound = sounds.get(name)
    if sound:
        sound.play()


# ================= МЕНЮ И ПЕРСОНАЖИ =================

game_state = "menu"
game_mode = "2p"
left_character = "GOJO"
right_character = "SUKUNA"
human_character = "GOJO"
bot_character = "SUKUNA"
bot_difficulty = "medium"

character_select_side = "left"
character_select_index = 0
CHARACTER_CHOICES = ["GOJO", "SUKUNA", "YUJI", "MEGUMI", "YUTA", "MAHITO"]
skin_queue = []
skin_step = 0
skin_after = "fight"

FULLSCREEN = False


def draw_text(text, f, color, x, y, center=True):
    image = f.render(str(text), True, color)
    rect = image.get_rect()
    if center:
        rect.center = (x, y)
    else:
        rect.topleft = (x, y)
    screen.blit(image, rect)


def draw_button(rect, label, color=(100, 30, 180)):
    pygame.draw.rect(screen, color, rect, border_radius=15)
    pygame.draw.rect(screen, (230, 200, 255), rect, 3, border_radius=15)
    draw_text(label, font, (255, 255, 255),
              rect[0] + rect[2] // 2,
              rect[1] + rect[3] // 2)


def get_image(character):
    return skins[character][skin_index[character]][1]


def is_human(side):
    if game_mode == "2p":
        return True
    if side == "left":
        return human_character in ("GOJO", "YUJI", "YUTA")
    return human_character in ("SUKUNA", "MEGUMI", "MAHITO")


def start_skin_selection(queue, after):
    global skin_queue, skin_step, skin_after, game_state
    skin_queue = queue[:]
    skin_step = 0
    skin_after = after
    game_state = "skin_select"


def finish_skin_selection():
    global game_state
    if skin_after == "difficulty":
        game_state = "difficulty_select"
    else:
        reset_game()
        game_state = "fight"
        if music_loaded:
            pygame.mixer.music.play(-1)


def choose_bot_character(character):
    global human_character, bot_character
    global left_character, right_character

    human_character = character

    if character in ("GOJO", "YUJI", "YUTA"):
        left_character = character
        bot_character = "SUKUNA"
        right_character = "SUKUNA"
    else:
        right_character = character
        bot_character = "GOJO"
        left_character = "GOJO"

    start_skin_selection([character], "difficulty")


def choose_2p_character(character):
    global left_character, right_character, character_select_side

    if character_select_side == "left":
        left_character = character
        character_select_side = "right"
    else:
        right_character = character
        # Один и тот же персонаж использует общий выбранный скин,
        # поэтому не нужно показывать экран выбора скина дважды.
        queue = list(dict.fromkeys([left_character, right_character]))
        start_skin_selection(queue, "fight")


# ================= ИГРОВОЕ СОСТОЯНИЕ =================

def reset_game():
    global gojo_x, sukuna_x, gojo_jump, sukuna_jump
    global gojo_velocity, sukuna_velocity
    global gojo_hp, sukuna_hp, gojo_energy, sukuna_energy
    global gojo_facing, sukuna_facing
    global gojo_roll_timer, sukuna_roll_timer
    global gojo_roll_cooldown, sukuna_roll_cooldown
    global gojo_invincible, sukuna_invincible
    global gojo_attack_cooldown, sukuna_attack_cooldown
    global gojo_purple_animation, sukuna_fuga_animation
    global gojo_purple_cooldown, sukuna_fuga_cooldown
    global gojo_domain_active, sukuna_domain_active
    global gojo_domain_timer, sukuna_domain_timer
    global gojo_domain_damage_timer, sukuna_domain_damage_timer
    global domain_clash, domain_winner
    global gojo_domain_power, sukuna_domain_power
    global projectiles, slashes, explosions, black_flash_effects
    global yuji_next_attack, megumi_next_attack
    global mahoraga_timer, left_mahoraga_timer, bot_decision_timer, bot_jump_timer
    global victory_sound_played, round_over
    global yuta_swords, yuta_sword_timer, mahito_attack_index, mahito_ball, mahito_ball_hit, mahito_domain_hits, mahito_domain_failed

    try:
        pygame.mixer.stop()
        pygame.mixer.music.stop()
    except pygame.error:
        pass

    gojo_x, sukuna_x = 150, 700
    gojo_jump = sukuna_jump = 0
    gojo_velocity = sukuna_velocity = 0
    gojo_hp = sukuna_hp = 100
    gojo_energy = sukuna_energy = 0
    gojo_facing, sukuna_facing = 1, -1

    gojo_roll_timer = sukuna_roll_timer = 0
    gojo_roll_cooldown = sukuna_roll_cooldown = 0
    gojo_invincible = sukuna_invincible = 0
    gojo_attack_cooldown = sukuna_attack_cooldown = 0

    gojo_purple_animation = sukuna_fuga_animation = 0
    gojo_purple_cooldown = sukuna_fuga_cooldown = 0

    gojo_domain_active = sukuna_domain_active = False
    gojo_domain_timer = sukuna_domain_timer = 0
    gojo_domain_damage_timer = sukuna_domain_damage_timer = 0

    domain_clash = False
    domain_winner = None
    gojo_domain_power = sukuna_domain_power = 0

    projectiles = []
    slashes = []
    explosions = []
    black_flash_effects = []

    yuji_next_attack = "slash"
    megumi_next_attack = "dogs"
    side_next_attack["left"] = side_next_attack["right"] = "slash"
    side_megumi_attack["left"] = side_megumi_attack["right"] = "dogs"
    mahoraga_timer = 0
    left_mahoraga_timer = 0

    bot_decision_timer = 0
    bot_jump_timer = 0
    victory_sound_played = False
    round_over = False
    yuta_swords = {"left": 5, "right": 5}
    yuta_sword_timer = {"left": 0, "right": 0}
    mahito_attack_index = {"left": 0, "right": 0}
    mahito_ball = {"left": 0, "right": 0}
    mahito_ball_hit = {"left": False, "right": False}
    mahito_domain_hits = {"left": 0, "right": 0}
    mahito_domain_failed = {"left": False, "right": False}


gojo_x = 150
sukuna_x = 700
gojo_jump = sukuna_jump = 0
gojo_velocity = sukuna_velocity = 0
gojo_hp = sukuna_hp = 100
gojo_energy = sukuna_energy = 0
gojo_facing, sukuna_facing = 1, -1

gojo_roll_timer = sukuna_roll_timer = 0
gojo_roll_cooldown = sukuna_roll_cooldown = 0
gojo_invincible = sukuna_invincible = 0
gojo_attack_cooldown = sukuna_attack_cooldown = 0

gojo_purple_animation = sukuna_fuga_animation = 0
gojo_purple_cooldown = sukuna_fuga_cooldown = 0

gojo_domain_active = sukuna_domain_active = False
gojo_domain_timer = sukuna_domain_timer = 0
gojo_domain_damage_timer = sukuna_domain_damage_timer = 0

domain_clash = False
domain_winner = None
gojo_domain_power = sukuna_domain_power = 0

projectiles = []
slashes = []
explosions = []
black_flash_effects = []

yuji_next_attack = "slash"
megumi_next_attack = "dogs"
mahoraga_timer = 0
left_mahoraga_timer = 0

bot_decision_timer = 0
bot_jump_timer = 0
victory_sound_played = False
round_over = False
yuta_swords = {"left": 5, "right": 5}
yuta_sword_timer = {"left": 0, "right": 0}
mahito_attack_index = {"left": 0, "right": 0}
mahito_ball = {"left": 0, "right": 0}
mahito_ball_hit = {"left": False, "right": False}
mahito_domain_hits = {"left": 0, "right": 0}
mahito_domain_failed = {"left": False, "right": False}


def check_round_over():
    """Замораживает бой и отключает все звуки, кроме речи о победе."""
    global round_over

    if gojo_hp <= 0 or sukuna_hp <= 0:
        if not round_over:
            round_over = True
            projectiles.clear()
            slashes.clear()
            try:
                pygame.mixer.music.stop()
                pygame.mixer.stop()
            except pygame.error:
                pass
        return True

    return False


# ================= ЭФФЕКТЫ =================

def glow(x, y, radius, color):
    for r in range(radius, 0, -6):
        surf = pygame.Surface((r * 2, r * 2), pygame.SRCALPHA)
        pygame.draw.circle(surf, (*color, 30), (r, r), r)
        screen.blit(surf, (int(x - r), int(y - r)))


def create_explosion(x, y):
    explosions.append({"x": x, "y": y, "timer": 0.5})


def draw_explosions(dt):
    for e in explosions[:]:
        e["timer"] -= dt
        progress = 1 - max(0, e["timer"] / 0.5)
        radius = int(20 + progress * 90)
        glow(e["x"], e["y"], radius + 20, (255, 80, 5))
        pygame.draw.circle(screen, (255, 90, 0),
                           (int(e["x"]), int(e["y"])), radius)
        pygame.draw.circle(screen, (255, 220, 80),
                           (int(e["x"]), int(e["y"])), max(2, radius // 3))
        if e["timer"] <= 0:
            explosions.remove(e)


def create_black_flash(x, y):
    black_flash_effects.append({"x": x, "y": y, "timer": 0.5})


def draw_black_flashes(dt):
    for e in black_flash_effects[:]:
        e["timer"] -= dt
        p = max(0, e["timer"] / 0.5)
        glow(e["x"], e["y"], int(100 * p), (255, 0, 35))

        for i in range(8):
            angle = i * math.tau / 8
            length = 80 * p
            end = (int(e["x"] + math.cos(angle) * length),
                   int(e["y"] + math.sin(angle) * length))
            pygame.draw.line(screen, (255, 0, 30),
                             (int(e["x"]), int(e["y"])), end, 6)
            pygame.draw.line(screen, (0, 0, 0),
                             (int(e["x"]), int(e["y"])), end, 2)

        if e["timer"] <= 0:
            black_flash_effects.remove(e)


# ================= УРОН =================

def damage_player(target, damage, ignore_invincibility=False, source_side=None):
    global gojo_hp, sukuna_hp, gojo_domain_power, sukuna_domain_power
    global domain_clash, domain_winner
    global gojo_domain_active, sukuna_domain_active

    if round_over:
        return False

    # МАХОРАГА: МЕГУМИ НЕУЯЗВИМ КО ВСЕМУ УРОНУ 5 СЕКУНД
    # Проверка выполняется даже для урона от доменов.
    if target == "sukuna":
        if right_character == "MEGUMI" and mahoraga_timer > 0:
            return

        if sukuna_invincible > 0 and not ignore_invincibility:
            return

        actual = min(sukuna_hp, damage)
        if actual <= 0:
            return False
        sukuna_hp = max(0, sukuna_hp - damage)
        if domain_clash:
            gojo_domain_power = min(100, gojo_domain_power + actual * 5)

    else:
        if left_character == "MEGUMI" and left_mahoraga_timer > 0:
            return
        if gojo_invincible > 0 and not ignore_invincibility:
            return

        actual = min(gojo_hp, damage)
        if actual <= 0:
            return False
        gojo_hp = max(0, gojo_hp - damage)
        if domain_clash:
            sukuna_domain_power = min(100, sukuna_domain_power + actual * 5)

    # Считаем только успешные попадания самого Махито во время его домена.
    if source_side in ("left", "right") and side_character(source_side) == "MAHITO":
        active = gojo_domain_active if source_side == "left" else sukuna_domain_active
        timer = gojo_domain_timer if source_side == "left" else sukuna_domain_timer
        if active and timer > 0:
            mahito_domain_hits[source_side] += 1
            if mahito_domain_hits[source_side] >= 5:
                if target == "sukuna":
                    sukuna_hp = 0
                else:
                    gojo_hp = 0

    if domain_clash:
        if gojo_domain_power >= 100:
            domain_winner = left_character
            domain_clash = False
            sukuna_domain_active = False

        elif sukuna_domain_power >= 100:
            domain_winner = right_character
            domain_clash = False
            gojo_domain_active = False

    check_round_over()
    return True


# ================= СПОСОБНОСТИ ДЛЯ ОБОИХ СЛОТОВ =================

# Все способности определяются персонажем в конкретном слоте,
# а не тем, слева он стоит или справа.
side_next_attack = {"left": "slash", "right": "slash"}
side_megumi_attack = {"left": "dogs", "right": "dogs"}


def side_prefix(side):
    return "gojo" if side == "left" else "sukuna"


def side_character(side):
    return left_character if side == "left" else right_character


def side_attack(side, key=None):
    prefix = side_prefix(side)
    x = globals()[prefix + "_x"]
    jump = globals()[prefix + "_jump"]
    facing = globals()[prefix + "_facing"]
    cooldown_name = prefix + "_attack_cooldown"
    if globals()[cooldown_name] > 0:
        return

    character = side_character(side)
    if character == "GOJO":
        kind = key or "blue"
        if kind == "blue":
            data = (850, 17, 4, (30, 100, 255), "blue")
        else:
            data = (700, 22, 6, (255, 35, 35), "red")
        speed, radius, damage, color, ptype = data
        projectiles.append({"x": x + 75, "y": GROUND_Y - 125 + jump,
                            "direction": facing, "speed": speed,
                            "radius": radius, "damage": damage,
                            "color": color, "type": ptype})
        globals()[cooldown_name] = 0.35

    elif character == "YUJI":
        if side_next_attack[side] == "slash":
            speed, radius, damage, color, ptype = 900, 24, 8, (190, 15, 35), "yuji_slash"
            side_next_attack[side] = "blood"
        else:
            speed, radius, damage, color, ptype = 650, 17, 11, (255, 0, 55), "yuji_blood"
            side_next_attack[side] = "slash"
        projectiles.append({"x": x + 75, "y": GROUND_Y - 125 + jump,
                            "direction": facing, "speed": speed,
                            "radius": radius, "damage": damage,
                            "color": color, "type": ptype})
        globals()[cooldown_name] = 0.55

    elif character == "MEGUMI":
        if side_megumi_attack[side] == "dogs":
            speed, radius, damage, color, ptype, yoff = 800, 27, 9, (25, 20, 35), "megumi_dogs", 75
            side_megumi_attack[side] = "nue"
        else:
            speed, radius, damage, color, ptype, yoff = 950, 22, 10, (150, 180, 255), "megumi_nue", 145
            side_megumi_attack[side] = "dogs"
        projectiles.append({"x": x + 75, "y": GROUND_Y - yoff + jump,
                            "direction": facing, "speed": speed,
                            "radius": radius, "damage": damage,
                            "color": color, "type": ptype})
        globals()[cooldown_name] = 0.65

    elif character == "YUTA":
        if (gojo_domain_active if side == "left" else sukuna_domain_active):
            if yuta_swords[side] <= 0:
                return
            yuta_swords[side] -= 1
            copied = random.choice(["speech", "mini_slash", "black_flash"])
            if copied == "speech":
                projectiles.append({"x": x + 75, "y": GROUND_Y - 125 + jump, "direction": facing, "speed": 1200, "radius": 28, "damage": 0, "color": (220, 220, 255), "type": "yuta_speech", "side": side})
            elif copied == "mini_slash":
                slashes.append({"x": x + 75, "y": GROUND_Y - 125 + jump, "direction": facing, "speed": 1050, "distance": 0, "max_distance": 560, "damage": 7, "side": side, "yuta": True})
            else:
                projectiles.append({"x": x + 75, "y": GROUND_Y - 125 + jump, "direction": facing, "speed": 1050, "radius": 30, "damage": 12, "color": (180, 80, 255), "type": "yuta_black_flash", "side": side})
        else:
            # Меч Юты — быстрый удар на короткой дистанции.
            target = "sukuna" if side == "left" else "gojo"
            tx = sukuna_x if side == "left" else gojo_x
            if abs((x + 75) - (tx + 75)) < 185:
                damage_player(target, 9)
            else:
                projectiles.append({"x": x + 75, "y": GROUND_Y - 125 + jump, "direction": facing, "speed": 900, "radius": 20, "damage": 9, "color": (220, 220, 255), "type": "yuta_sword", "side": side})
        globals()[cooldown_name] = 0.45

    elif character == "MAHITO":
        idx = mahito_attack_index[side]
        mahito_attack_index[side] = (idx + 1) % 3
        target = "sukuna" if side == "left" else "gojo"
        tx = sukuna_x if side == "left" else gojo_x
        if idx == 0:  # рука
            if abs(x - tx) < 205:
                damage_player(target, 8, source_side=side)
            else:
                projectiles.append({"x": x + 75, "y": GROUND_Y - 125 + jump, "direction": facing, "speed": 850, "radius": 22, "damage": 8, "color": (160, 90, 190), "type": "mahito_hand", "side": side})
        elif idx == 1:  # рука-меч
            if abs(x - tx) < 230:
                damage_player(target, 11, source_side=side)
            else:
                projectiles.append({"x": x + 75, "y": GROUND_Y - 125 + jump, "direction": facing, "speed": 1150, "radius": 17, "damage": 11, "color": (190, 210, 255), "type": "mahito_sword", "side": side})
        else:  # огромный молот
            projectiles.append({"x": x + 75, "y": GROUND_Y - 125 + jump, "direction": facing, "speed": 650, "radius": 36, "damage": 15, "color": (110, 55, 145), "type": "mahito_hammer", "side": side})
        globals()[cooldown_name] = 0.6 if idx != 2 else 0.85

    elif character == "SUKUNA":
        slashes.append({"x": x + 75, "y": GROUND_Y - 125 + jump,
                        "direction": facing, "speed": 850,
                        "distance": 0, "max_distance": 500,
                        "damage": 2, "side": side})
        globals()[cooldown_name] = 0.55


def summon_mahoraga(side):
    global mahoraga_timer, left_mahoraga_timer
    prefix = side_prefix(side)
    energy_name = prefix + "_energy"
    cooldown_name = prefix + ("_purple_cooldown" if side == "left" else "_fuga_cooldown")
    if globals()[energy_name] < 50 or globals()[cooldown_name] > 0:
        return
    globals()[energy_name] -= 50
    globals()[cooldown_name] = SPECIAL_COOLDOWN
    if side == "left":
        left_mahoraga_timer = 5.0
    else:
        mahoraga_timer = 5.0
    play_sound("mahoraga")


def activate_special(side):
    character = side_character(side)
    prefix = side_prefix(side)
    energy_name = prefix + "_energy"
    cooldown_name = prefix + ("_purple_cooldown" if side == "left" else "_fuga_cooldown")
    animation_name = prefix + ("_purple_animation" if side == "left" else "_fuga_animation")

    if character == "MEGUMI":
        summon_mahoraga(side)
        return
    if character == "MAHITO":
        if globals()[energy_name] < 50 or globals()[cooldown_name] > 0:
            return
        globals()[energy_name] -= 50
        globals()[cooldown_name] = SPECIAL_COOLDOWN
        mahito_ball[side] = 1.0
        mahito_ball_hit[side] = False
        return
    if character == "YUTA":
        if globals()[energy_name] < 50 or globals()[cooldown_name] > 0:
            return
        globals()[energy_name] -= 50
        globals()[cooldown_name] = SPECIAL_COOLDOWN
        globals()[animation_name] = 1.7
        return
    if globals()[energy_name] < 50 or globals()[cooldown_name] > 0:
        return

    globals()[energy_name] -= 50
    globals()[cooldown_name] = SPECIAL_COOLDOWN
    if character == "YUJI":
        globals()[animation_name] = 1.5
        play_sound("yuji_bf")
    elif character == "GOJO":
        globals()[animation_name] = 2.0
        play_sound("gojo_purple")
    elif character == "SUKUNA":
        globals()[animation_name] = 2.0
        play_sound("sukuna_fuga")


def fire_special(side):
    character = side_character(side)
    prefix = side_prefix(side)
    x = globals()[prefix + "_x"] + 75
    y = GROUND_Y - 125 + globals()[prefix + "_jump"]
    direction = globals()[prefix + "_facing"]

    if character == "YUTA":
        data = (700, 42, 22, (170, 90, 255), "yuta_beam")
    elif character == "YUJI":
        data = (1000, 35, 23, (255, 0, 35), "yuji_black_flash")
    elif character == "GOJO":
        data = (650, 38, 15, (160, 40, 255), "purple")
    elif character == "SUKUNA":
        data = (600, 30, 25, (255, 100, 10), "fuga")
    else:
        return
    speed, radius, damage, color, ptype = data
    projectiles.append({"x": x, "y": y, "direction": direction,
                        "speed": speed, "radius": radius,
                        "damage": damage, "color": color, "type": ptype})


def start_domain(side):
    global gojo_energy, sukuna_energy
    global gojo_domain_active, sukuna_domain_active
    global gojo_domain_timer, sukuna_domain_timer
    global gojo_domain_damage_timer, sukuna_domain_damage_timer
    global domain_clash, domain_winner, gojo_domain_power, sukuna_domain_power
    global sukuna_velocity, gojo_velocity, sukuna_roll_timer, gojo_roll_timer

    prefix = side_prefix(side)
    energy_name = prefix + "_energy"
    if globals()[energy_name] < 100:
        return
    if side == "left" and gojo_domain_active:
        return
    if side == "right" and sukuna_domain_active:
        return

    globals()[energy_name] -= 100
    mahito_domain_hits[side] = 0
    mahito_domain_failed[side] = False
    if side_character(side) == "YUTA": yuta_swords[side] = 5
    if side == "left":
        gojo_domain_active = True
        gojo_domain_timer = DOMAIN_DURATION
        gojo_domain_damage_timer = 0
        gojo_velocity = 0
        gojo_roll_timer = 0
    else:
        sukuna_domain_active = True
        sukuna_domain_timer = DOMAIN_DURATION
        sukuna_domain_damage_timer = 0
        sukuna_velocity = 0
        sukuna_roll_timer = 0

    sound_by_character = {"GOJO": "gojo_domain", "YUJI": "yuji_domain",
                          "SUKUNA": "sukuna_domain", "MEGUMI": "megumi_domain"}
    # Для Юты и Махито звуки пока не добавлены — домен должен запускаться без них.
    domain_sound = sound_by_character.get(side_character(side))
    if domain_sound:
        play_sound(domain_sound)

    if gojo_domain_active and sukuna_domain_active:
        domain_clash = True
        domain_winner = None
        gojo_domain_power = sukuna_domain_power = 0


def start_gojo_domain():
    start_domain("left")


def start_sukuna_domain():
    start_domain("right")


# ================= РИСОВАНИЕ ПЕРСОНАЖЕЙ =================

def draw_player(character, x, jump, facing, invincible, fallback):
    y = GROUND_Y - PLAYER_H + jump

    if invincible > 0 and int(invincible * 15) % 2 == 0:
        return

    img = get_image(character)

    if img:
        screen.blit(pygame.transform.flip(img, facing == -1, False),
                    (int(x), int(y)))
    else:
        pygame.draw.rect(screen, fallback,
                         (int(x), int(y), PLAYER_W, PLAYER_H),
                         border_radius=15)


def draw_special_animations():
    for side in ("left", "right"):
        prefix = side_prefix(side)
        timer = globals()[prefix + ("_purple_animation" if side == "left" else "_fuga_animation")]
        if timer <= 0:
            continue
        x = globals()[prefix + "_x"] + 75
        y = GROUND_Y - 125 + globals()[prefix + "_jump"]
        character = side_character(side)
        if character == "YUJI":
            glow(x, y, 90, (255, 0, 30))
            pygame.draw.circle(screen, (20, 0, 10), (x, y), 35)
            pygame.draw.circle(screen, (255, 0, 40), (x, y), 22)
            draw_text("BLACK FLASH!", font, (255, 30, 50), x, y - 75)
        elif character == "GOJO":
            glow(x, y, 85, (160, 40, 255))
            pygame.draw.circle(screen, (150, 40, 255), (x, y), 35)
            pygame.draw.circle(screen, (255, 255, 255), (x, y), 10)
            draw_text("HOLLOW PURPLE!", font, (210, 140, 255), x, y - 75)
        elif character == "SUKUNA":
            glow(x, y, 80, (255, 70, 5))
            pygame.draw.circle(screen, (255, 100, 0), (x, y), 30)
            draw_text("FUGA!", font, (255, 120, 20), x, y - 75)


def draw_mahoraga():
    for side in ("left", "right"):
        timer = left_mahoraga_timer if side == "left" else mahoraga_timer
        if timer <= 0 or side_character(side) != "MEGUMI":
            continue
        prefix = side_prefix(side)
        cx = globals()[prefix + "_x"] + 75
        cy = GROUND_Y - PLAYER_H + globals()[prefix + "_jump"]
        glow(cx, cy + 65, 100, (100, 70, 160))
        pygame.draw.circle(screen, (100, 90, 115), (cx, cy + 35), 28)
        pygame.draw.rect(screen, (75, 65, 95), (cx - 24, cy + 60, 48, 95), border_radius=15)
        pygame.draw.line(screen, (75, 65, 95), (cx - 15, cy + 85), (cx - 48, cy + 135), 13)
        pygame.draw.line(screen, (75, 65, 95), (cx + 15, cy + 85), (cx + 48, cy + 135), 13)
        pygame.draw.line(screen, (75, 65, 95), (cx - 12, cy + 150), (cx - 28, cy + 205), 14)
        pygame.draw.line(screen, (75, 65, 95), (cx + 12, cy + 150), (cx + 28, cy + 205), 14)
        wheel_y = cy - 15
        pygame.draw.circle(screen, (220, 190, 100), (cx, wheel_y), 35, 7)
        pygame.draw.circle(screen, (245, 220, 150), (cx, wheel_y), 8)
        for i in range(8):
            angle = i * math.tau / 8
            px = int(cx + math.cos(angle) * 23)
            py = int(wheel_y + math.sin(angle) * 23)
            pygame.draw.line(screen, (245, 220, 150), (cx, wheel_y), (px, py), 3)
        draw_text("MAHORAGA!", small_font, (230, 210, 150), cx, cy - 55)
        draw_text(f"{math.ceil(timer)}s", small_font, (255, 255, 255), cx, cy - 85)


# ================= ДОМЕНЫ: ВИЗУАЛ =================

def draw_anime_slash(x, y, size, angle, color, core_color=(255, 245, 245)):
    """Острый многосегментный разрез с ярким внутренним следом."""
    ca, sa = math.cos(angle), math.sin(angle)

    # Ломаная форма разреза — не круг и не прямая палка.
    shape = [
        (-1.00, -0.10), (-0.52, -0.30), (-0.18, -0.13),
        (0.16, -0.42), (0.05, -0.08), (0.92, 0.18),
        (0.34, 0.14), (0.02, 0.39), (0.10, 0.10),
        (-0.48, 0.18)
    ]

    points = []
    for px, py in shape:
        px *= size
        py *= size
        rx = px * ca - py * sa
        ry = px * sa + py * ca
        points.append((int(x + rx), int(y + ry)))

    pygame.draw.polygon(screen, color, points)

    # Тонкий белый разлом внутри красного/розового следа.
    inner = []
    for px, py in [(-0.72, -0.12), (-0.28, -0.04),
                   (0.10, -0.22), (0.55, 0.10)]:
        px *= size
        py *= size
        rx = px * ca - py * sa
        ry = px * sa + py * ca
        inner.append((int(x + rx), int(y + ry)))
    if len(inner) > 1:
        pygame.draw.lines(screen, core_color, False, inner,
                          max(1, int(size * 0.045)))


def draw_black_lightning(x, y, size, angle):
    """Чёрная зигзагообразная молния для домена Юдзи."""
    ca, sa = math.cos(angle), math.sin(angle)
    path = [(-1.0, -0.15), (-0.35, -0.05), (-0.05, -0.75),
            (0.12, -0.10), (0.85, 0.05), (0.20, 0.22),
            (0.02, 0.85), (-0.12, 0.20)]
    points = []
    for px, py in path:
        px *= size
        py *= size
        points.append((int(x + px * ca - py * sa),
                       int(y + px * sa + py * ca)))
    pygame.draw.lines(screen, (0, 0, 0), False, points,
                      max(2, int(size * 0.12)))
    pygame.draw.lines(screen, (45, 0, 12), False, points,
                      max(1, int(size * 0.035)))


def draw_gojo_black_hole(ticks):
    """Большая чёрная дыра с вращающимся светящимся кольцом."""
    cx, cy = WIDTH // 2, 315
    pulse = 1.0 + 0.035 * math.sin(ticks / 180)

    # Мягкое синее свечение за дырой.
    glow(cx, cy, int(205 * pulse), (55, 95, 255))
    glow(cx, cy, int(165 * pulse), (115, 55, 255))

    # Вращающийся аккреционный диск.
    points_outer = []
    points_inner = []
    rotation = ticks / 650
    for i in range(81):
        a = math.tau * i / 80 + rotation
        wobble = 1 + 0.08 * math.sin(a * 3 + ticks / 250)
        points_outer.append((
            int(cx + math.cos(a) * 155 * pulse * wobble),
            int(cy + math.sin(a) * 58 * pulse * wobble)
        ))
        points_inner.append((
            int(cx + math.cos(a) * 105 * pulse),
            int(cy + math.sin(a) * 34 * pulse)
        ))

    pygame.draw.lines(screen, (70, 110, 255), True, points_outer, 12)
    pygame.draw.lines(screen, (190, 145, 255), True, points_inner, 7)
    pygame.draw.ellipse(screen, (225, 235, 255),
                        (cx - 132, cy - 25, 264, 50), 3)

    # Сама чёрная сфера и тонкий светлый край.
    pygame.draw.ellipse(screen, (5, 3, 15),
                        (cx - 91, cy - 91, 182, 182))
    pygame.draw.ellipse(screen, (20, 12, 45),
                        (cx - 96, cy - 96, 192, 192), 4)


def draw_domains():
    if not gojo_domain_active and not sukuna_domain_active:
        return

    ticks = pygame.time.get_ticks()
    overlay = pygame.Surface((WIDTH, HEIGHT), pygame.SRCALPHA)

    # ГОДЖО / ЮДЗИ — левый игрок.
    if gojo_domain_active:
        if left_character == "YUTA":
            overlay.fill((85, 35, 125, 150)); screen.blit(overlay, (0, 0))
            for i in range(5):
                sx = 120 + i * 190
                pygame.draw.line(screen, (210, 210, 225), (sx, GROUND_Y-15), (sx+30, GROUND_Y-125), 5)
                pygame.draw.line(screen, (120, 70, 170), (sx+30, GROUND_Y-125), (sx+38, GROUND_Y-145), 3)
            draw_text("ИСТИННАЯ И ВЗАИМНАЯ ЛЮБОВЬ", small_font, (240, 220, 255), WIDTH//2, 150)
            draw_text(f"МЕЧЕЙ: {yuta_swords['left']}/5", small_font, (255,255,255), WIDTH//2, 178)
        elif left_character == "MAHITO":
            overlay.fill((100, 0, 145, 170)); screen.blit(overlay, (0,0))
            for i in range(45):
                x=(i*137)%WIDTH; y=(i*83)%GROUND_Y
                pygame.draw.circle(screen,(155,95,180),(x,y),12,3)
                pygame.draw.line(screen,(155,95,180),(x,y+10),(x+random.randint(-12,12),y+35),4)
            draw_text("САМОВОПЛОЩЕНИЕ СОВЕРШЕНСТВА", small_font,(245,210,255),WIDTH//2,150)
            draw_text(f"ПОПАДАНИЯ: {mahito_domain_hits['left']}/5", small_font,(255,255,255),WIDTH//2,178)
        elif left_character == "YUJI":
            overlay.fill((75, 0, 18, 105))
            screen.blit(overlay, (0, 0))

            # Небольшие острые разрезы по всей карте + чёрные молнии.
            for i in range(22):
                x = (i * 173 + ticks * (0.075 + (i % 4) * 0.012)) % (WIDTH + 100) - 50
                y = (i * 97 + ticks * (0.035 + (i % 3) * 0.009)) % HEIGHT
                size = 15 + (i % 4) * 4
                angle = -0.45 + (i % 5) * 0.18
                draw_anime_slash(x, y, size, angle,
                                 (205, 12, 42), (255, 185, 195))
                if i % 2 == 0:
                    draw_black_lightning(x + 5, y - 2, size * 0.8,
                                         angle + 0.35)

            draw_text("РАЗРЕЗ ДУШИ", font, (255, 50, 75),
                      WIDTH // 2, 150)
        elif left_character == "GOJO":
            overlay.fill((15, 25, 95, 85))
            screen.blit(overlay, (0, 0))
            draw_gojo_black_hole(ticks)

            # Редкие частицы вокруг чёрной дыры.
            for i in range(24):
                x = (i * 137 + ticks // 9) % WIDTH
                y = (i * 79 + ticks // 13) % HEIGHT
                pygame.draw.circle(screen, (175, 210, 255),
                                   (int(x), int(y)), 2)

            draw_text("UNLIMITED VOID", font, (165, 205, 255),
                      WIDTH // 2, 150)
        elif left_character == "MEGUMI":
            overlay.fill((8, 5, 20, 175))
            screen.blit(overlay, (0, 0))
            pygame.draw.rect(screen, (0, 0, 0), (0, GROUND_Y, WIDTH, HEIGHT - GROUND_Y))
            for i in range(1, 13):
                x = int(i * WIDTH / 13)
                pygame.draw.line(screen, (75, 75, 85), (WIDTH // 2, GROUND_Y), (x, HEIGHT), 2)
            for j in range(1, 5):
                y = GROUND_Y + j * 14
                pygame.draw.line(screen, (65, 65, 75), (0, y), (WIDTH, y), 2)
            draw_text("ХИМЕРИЧЕСКИЙ ТЕНЕВОЙ САД", small_font, (190, 175, 220), WIDTH // 2, 185)
        else:  # SUKUNA
            overlay.fill((105, 0, 10, 95))
            screen.blit(overlay, (0, 0))
            for i in range(27):
                x = (i * 149 + ticks * (0.11 + (i % 5) * 0.018)) % (WIDTH + 120) - 60
                y = (i * 83 + ticks * (0.055 + (i % 4) * 0.013)) % HEIGHT
                size = 27 + (i % 5) * 8
                angle = -0.55 + (i % 6) * 0.19
                draw_anime_slash(x, y, size, angle, (190, 5, 20), (255, 225, 225))
            draw_text("MALEVOLENT SHRINE", font, (255, 100, 100), WIDTH // 2, 185)

    # СУКУНА / МЕГУМИ — правый игрок.
    if sukuna_domain_active:
        if right_character == "YUTA":
            overlay.fill((85, 35, 125, 150)); screen.blit(overlay,(0,0))
            for i in range(5):
                sx=120+i*190
                pygame.draw.line(screen,(210,210,225),(sx,GROUND_Y-15),(sx+30,GROUND_Y-125),5)
            draw_text("ИСТИННАЯ И ВЗАИМНАЯ ЛЮБОВЬ",small_font,(240,220,255),WIDTH//2,150)
            draw_text(f"МЕЧЕЙ: {yuta_swords['right']}/5",small_font,(255,255,255),WIDTH//2,178)
        elif right_character == "MAHITO":
            overlay.fill((100,0,145,170)); screen.blit(overlay,(0,0))
            for i in range(45):
                x=(i*137)%WIDTH; y=(i*83)%GROUND_Y
                pygame.draw.circle(screen,(155,95,180),(x,y),12,3)
                pygame.draw.line(screen,(155,95,180),(x,y+10),(x+random.randint(-12,12),y+35),4)
            draw_text("САМОВОПЛОЩЕНИЕ СОВЕРШЕНСТВА",small_font,(245,210,255),WIDTH//2,150)
            draw_text(f"ПОПАДАНИЯ: {mahito_domain_hits['right']}/5",small_font,(255,255,255),WIDTH//2,178)
        elif right_character == "MEGUMI":
            overlay.fill((8, 5, 20, 175))
            screen.blit(overlay, (0, 0))

            # Пол становится полностью чёрным.
            pygame.draw.rect(screen, (0, 0, 0),
                             (0, GROUND_Y, WIDTH, HEIGHT - GROUND_Y))

            # Серые линии на теневом полу.
            for i in range(1, 13):
                x = int(i * WIDTH / 13)
                pygame.draw.line(screen, (75, 75, 85),
                                 (WIDTH // 2, GROUND_Y),
                                 (x, HEIGHT), 2)
            for j in range(1, 5):
                y = GROUND_Y + j * 14
                pygame.draw.line(screen, (65, 65, 75),
                                 (0, y), (WIDTH, y), 2)

            # Тусклые фиолетовые тени по всему фону.
            for i in range(14):
                x = (i * 173 + ticks // 22) % WIDTH
                y = (i * 97 + ticks // 29) % GROUND_Y
                pygame.draw.circle(screen, (45, 30, 70),
                                   (int(x), int(y)), 16, 2)

            draw_text("ХИМЕРИЧЕСКИЙ ТЕНЕВОЙ САД",
                      small_font, (190, 175, 220), WIDTH // 2, 185)
        elif right_character == "YUJI":
            overlay.fill((75, 0, 18, 105))
            screen.blit(overlay, (0, 0))
            for i in range(22):
                x = (i * 173 + ticks * (0.075 + (i % 4) * 0.012)) % (WIDTH + 100) - 50
                y = (i * 97 + ticks * (0.035 + (i % 3) * 0.009)) % HEIGHT
                size = 15 + (i % 4) * 4
                angle = -0.45 + (i % 5) * 0.18
                draw_anime_slash(x, y, size, angle, (205, 12, 42), (255, 185, 195))
                if i % 2 == 0:
                    draw_black_lightning(x + 5, y - 2, size * 0.8, angle + 0.35)
            draw_text("РАЗРЕЗ ДУШИ", font, (255, 50, 75), WIDTH // 2, 185)
        elif right_character == "GOJO":
            overlay.fill((15, 25, 95, 85))
            screen.blit(overlay, (0, 0))
            draw_gojo_black_hole(ticks)
            draw_text("UNLIMITED VOID", font, (165, 205, 255), WIDTH // 2, 185)
        else:
            overlay.fill((105, 0, 10, 95))
            screen.blit(overlay, (0, 0))

            # Крупные, острые, неровные разрезы по всей карте.
            for i in range(27):
                x = (i * 149 + ticks * (0.11 + (i % 5) * 0.018)) % (WIDTH + 120) - 60
                y = (i * 83 + ticks * (0.055 + (i % 4) * 0.013)) % HEIGHT
                size = 27 + (i % 5) * 8
                angle = -0.55 + (i % 6) * 0.19
                draw_anime_slash(x, y, size, angle,
                                 (190, 5, 20), (255, 225, 225))

            draw_text("MALEVOLENT SHRINE", font, (255, 100, 100),
                      WIDTH // 2, 185)


# ================= ИНТЕРФЕЙС =================

def draw_hp_bar(x, y, hp, color):
    pygame.draw.rect(screen, (35, 35, 35), (x, y, 300, 25))
    pygame.draw.rect(screen, color,
                     (x, y, int(300 * max(0, hp) / 100), 25))
    pygame.draw.rect(screen, (255, 255, 255), (x, y, 300, 25), 2)


def draw_energy_bar(x, y, energy, color):
    pygame.draw.rect(screen, (30, 30, 40), (x, y, 300, 16))
    pygame.draw.rect(screen, color,
                     (x, y, int(300 * energy / 100), 16))
    pygame.draw.rect(screen, (255, 255, 255), (x, y, 300, 16), 2)


def draw_domain_clash():
    if not domain_clash and not domain_winner:
        return

    draw_text("DOMAIN CLASH!", font, (255, 255, 255), 500, 455)

    pygame.draw.rect(screen, (20, 20, 30), (250, 490, 500, 30),
                     border_radius=8)

    pygame.draw.rect(screen, (30, 120, 255),
                     (250, 490, int(500 * gojo_domain_power / 100), 30),
                     border_radius=8)

    red_width = int(500 * sukuna_domain_power / 100)
    pygame.draw.rect(screen, (255, 35, 45),
                     (750 - red_width, 490, red_width, 30),
                     border_radius=8)

    pygame.draw.rect(screen, (255, 255, 255), (250, 490, 500, 30), 2,
                     border_radius=8)

    draw_text(f"{left_character} {int(gojo_domain_power)}%",
              small_font, (100, 180, 255), 150, 505)
    draw_text(f"{int(sukuna_domain_power)}% {right_character}",
              small_font, (255, 100, 100), 850, 505)

    if domain_winner:
        draw_text(f"{domain_winner} WON THE DOMAIN CLASH!",
                  font, (255, 220, 100), 500, 420)


# ================= ПОЛНЫЙ ЭКРАН =================

def toggle_fullscreen():
    global FULLSCREEN, screen
    FULLSCREEN = not FULLSCREEN
    flags = pygame.SCALED
    if FULLSCREEN:
        flags |= pygame.FULLSCREEN
    screen = pygame.display.set_mode((WIDTH, HEIGHT), flags)


# ================= ГЛАВНЫЙ ЦИКЛ =================

running = True

while running:
    dt = min(clock.tick(60) / 1000, 0.04)
    check_round_over()
    if round_over:
        dt = 0

    for event in pygame.event.get():

        if event.type == pygame.QUIT:
            running = False

        if event.type == pygame.KEYDOWN:

            if event.key == pygame.K_F11:
                toggle_fullscreen()

            elif game_state == "menu":
                if event.key in (pygame.K_RETURN, pygame.K_SPACE):
                    game_state = "mode_select"

            elif game_state == "mode_select":
                if event.key == pygame.K_1:
                    game_mode = "2p"
                    character_select_side = "left"
                    character_select_index = 0
                    left_character, right_character = "GOJO", "SUKUNA"
                    skin_index = {c: 0 for c in skins}
                    game_state = "character_select_2p"
                elif event.key == pygame.K_2:
                    game_mode = "bot"
                    character_select_index = 0
                    game_state = "character_select"
                elif event.key == pygame.K_ESCAPE:
                    game_state = "menu"

            elif game_state in ("character_select_2p", "character_select"):
                if event.key == pygame.K_LEFT:
                    character_select_index = (character_select_index - 1) % len(CHARACTER_CHOICES)
                elif event.key == pygame.K_RIGHT:
                    character_select_index = (character_select_index + 1) % len(CHARACTER_CHOICES)
                elif event.key == pygame.K_RETURN:
                    selected = CHARACTER_CHOICES[character_select_index]
                    if game_state == "character_select_2p":
                        choose_2p_character(selected)
                    else:
                        choose_bot_character(selected)
                elif event.key == pygame.K_ESCAPE:
                    game_state = "mode_select"

            elif game_state == "skin_select":
                character = skin_queue[skin_step]
                if event.key == pygame.K_LEFT:
                    skin_index[character] = (skin_index[character] - 1) % len(skins[character])
                elif event.key == pygame.K_RIGHT:
                    skin_index[character] = (skin_index[character] + 1) % len(skins[character])
                elif event.key == pygame.K_RETURN:
                    skin_step += 1
                    if skin_step >= len(skin_queue):
                        finish_skin_selection()
                elif event.key == pygame.K_ESCAPE:
                    game_state = "menu"

            elif game_state == "difficulty_select":
                if event.key in (pygame.K_1, pygame.K_KP1):
                    bot_difficulty = "easy"
                elif event.key in (pygame.K_2, pygame.K_KP2):
                    bot_difficulty = "medium"
                elif event.key in (pygame.K_3, pygame.KP3):
                    bot_difficulty = "hard"
                else:
                    bot_difficulty = None

                if bot_difficulty:
                    reset_game()
                    game_state = "fight"
                    if music_loaded:
                        pygame.mixer.music.play(-1)
                elif event.key == pygame.K_ESCAPE:
                    game_state = "character_select"

            elif game_state == "fight":

                if round_over:
                    if event.key == pygame.K_ESCAPE:
                        game_state = "menu"
                        pygame.mixer.music.stop()
                    else:
                        continue

                if event.key == pygame.K_ESCAPE:
                    game_state = "menu"
                    pygame.mixer.music.stop()

                if is_human("left"):

                    if event.key == pygame.K_w and gojo_jump == 0:
                        gojo_velocity = -720

                    if event.key == pygame.K_s and gojo_roll_cooldown <= 0:
                        gojo_roll_timer = 0.55
                        gojo_roll_cooldown = 1
                        gojo_invincible = 0.7

                    if event.key in (pygame.K_f, pygame.K_g):
                        side_attack("left", "blue" if event.key == pygame.K_f else "red")

                    if event.key == pygame.K_h:
                        activate_special("left")

                    if event.key == pygame.K_j:
                        start_domain("left")

                if is_human("right"):

                    if event.key == pygame.K_UP and sukuna_jump == 0:
                        if not gojo_domain_active or domain_clash:
                            sukuna_velocity = -720

                    if event.key == pygame.K_DOWN and sukuna_roll_cooldown <= 0:
                        if not gojo_domain_active or domain_clash:
                            sukuna_roll_timer = 0.55
                            sukuna_roll_cooldown = 1
                            sukuna_invincible = 0.7

                    if event.key == pygame.K_k:
                        side_attack("right")

                    if event.key == pygame.K_l:
                        activate_special("right")

                    if event.key == pygame.K_o:
                        start_domain("right")

        if event.type == pygame.MOUSEBUTTONDOWN and event.button == 1:
            mx, my = event.pos

            if game_state == "menu":
                if pygame.Rect(350, 280, 300, 75).collidepoint(mx, my):
                    game_state = "mode_select"

            elif game_state == "mode_select":
                if pygame.Rect(250, 260, 500, 75).collidepoint(mx, my):
                    game_mode = "2p"
                    character_select_side = "left"
                    character_select_index = 0
                    left_character, right_character = "GOJO", "SUKUNA"
                    skin_index = {c: 0 for c in skins}
                    game_state = "character_select_2p"
                elif pygame.Rect(250, 360, 500, 75).collidepoint(mx, my):
                    game_mode = "bot"
                    character_select_index = 0
                    game_state = "character_select"

            elif game_state in ("character_select_2p", "character_select"):
                if pygame.Rect(260, 345, 100, 75).collidepoint(mx, my):
                    character_select_index = (character_select_index - 1) % len(CHARACTER_CHOICES)
                elif pygame.Rect(640, 345, 100, 75).collidepoint(mx, my):
                    character_select_index = (character_select_index + 1) % len(CHARACTER_CHOICES)
                elif pygame.Rect(350, 490, 300, 65).collidepoint(mx, my):
                    selected = CHARACTER_CHOICES[character_select_index]
                    if game_state == "character_select_2p":
                        choose_2p_character(selected)
                    else:
                        choose_bot_character(selected)

            elif game_state == "skin_select":
                character = skin_queue[skin_step]
                if pygame.Rect(300, 300, 150, 80).collidepoint(mx, my):
                    skin_index[character] = (skin_index[character] - 1) % len(skins[character])
                elif pygame.Rect(550, 300, 150, 80).collidepoint(mx, my):
                    skin_index[character] = (skin_index[character] + 1) % len(skins[character])
                elif pygame.Rect(350, 500, 300, 60).collidepoint(mx, my):
                    skin_step += 1
                    if skin_step >= len(skin_queue):
                        finish_skin_selection()

            elif game_state == "difficulty_select":
                if pygame.Rect(250, 230, 500, 65).collidepoint(mx, my):
                    bot_difficulty = "easy"
                elif pygame.Rect(250, 315, 500, 65).collidepoint(mx, my):
                    bot_difficulty = "medium"
                elif pygame.Rect(250, 400, 500, 65).collidepoint(mx, my):
                    bot_difficulty = "hard"
                else:
                    bot_difficulty = None

                if bot_difficulty:
                    reset_game()
                    game_state = "fight"
                    if music_loaded:
                        pygame.mixer.music.play(-1)

    keys = pygame.key.get_pressed()

    # ================= ЭКРАНЫ МЕНЮ =================

    if game_state != "fight":

        screen.fill((12, 5, 30))
        if background:
            screen.blit(background, (0, 0))

        draw_text("GOJO VS SUKUNA", big_font, (220, 180, 255), 500, 155)

        if game_state == "menu":
            draw_button((350, 280, 300, 75), "НАЧАТЬ БОЙ")
            draw_text("ENTER - начать", small_font, (230, 230, 230), 500, 400)

        elif game_state == "mode_select":
            draw_text("ВЫБЕРИ РЕЖИМ ИГРЫ", font, (255, 255, 255), 500, 220)
            draw_button((250, 260, 500, 75), "2 PLAYERS")
            draw_button((250, 360, 500, 75), "1 PLAYER WITH BOT")
            draw_text("1 - 2 Players     2 - With Bot     ESC - Назад",
                      small_font, (230, 230, 230), 500, 475)

        elif game_state == "character_select_2p":
            player_label = "ИГРОК 1" if character_select_side == "left" else "ИГРОК 2"
            draw_text(f"{player_label}: ВЫБЕРИ ПЕРСОНАЖА", font, (255, 255, 255), 500, 205)
            selected = CHARACTER_CHOICES[character_select_index]
            colors = {"GOJO": (35, 75, 180), "SUKUNA": (150, 25, 35), "YUJI": (150, 65, 35),
                      "MEGUMI": (45, 45, 100), "YUTA": (90, 45, 130), "MAHITO": (110, 45, 130)}
            draw_button((260, 345, 100, 75), "<")
            draw_button((640, 345, 100, 75), ">")
            draw_text(selected, big_font, (255, 255, 255), 500, 280)
            preview = get_image(selected)
            if preview:
                preview = pygame.transform.scale(preview, (150, 230))
                screen.blit(preview, preview.get_rect(center=(500, 390)))
            else:
                draw_text("IMAGE NOT FOUND", font, (255, 80, 80), 500, 390)
            draw_button((350, 490, 300, 65), "ВЫБРАТЬ", colors[selected])
            draw_text("← → ЛИСТАТЬ     ENTER - ВЫБРАТЬ", small_font, (230, 230, 230), 500, 545)
            draw_text(f"{character_select_index + 1} / {len(CHARACTER_CHOICES)}", small_font, (230, 230, 230), 500, 575)

        elif game_state == "character_select":
            draw_text("КЕМ ТЫ ХОЧЕШЬ ИГРАТЬ?", font, (255, 255, 255), 500, 205)
            selected = CHARACTER_CHOICES[character_select_index]
            colors = {"GOJO": (35, 75, 180), "SUKUNA": (150, 25, 35), "YUJI": (150, 65, 35),
                      "MEGUMI": (45, 45, 100), "YUTA": (90, 45, 130), "MAHITO": (110, 45, 130)}
            draw_button((260, 345, 100, 75), "<")
            draw_button((640, 345, 100, 75), ">")
            draw_text(selected, big_font, (255, 255, 255), 500, 280)
            preview = get_image(selected)
            if preview:
                preview = pygame.transform.scale(preview, (150, 230))
                screen.blit(preview, preview.get_rect(center=(500, 390)))
            else:
                draw_text("IMAGE NOT FOUND", font, (255, 80, 80), 500, 390)
            draw_button((350, 490, 300, 65), "ВЫБРАТЬ", colors[selected])
            draw_text("← → ЛИСТАТЬ     ENTER - ВЫБРАТЬ", small_font, (230, 230, 230), 500, 545)
            draw_text(f"{character_select_index + 1} / {len(CHARACTER_CHOICES)}", small_font, (230, 230, 230), 500, 575)

        elif game_state == "skin_select":
            character = skin_queue[skin_step]
            name, img = skins[character][skin_index[character]]
            draw_text(f"ВЫБОР СКИНА: {character}", font, (255, 255, 255), 500, 220)
            draw_text(f"{skin_index[character] + 1} / {len(skins[character])}",
                      font, (170, 140, 255), 500, 275)

            if img:
                preview = pygame.transform.scale(img, (180, 270))
                screen.blit(preview, preview.get_rect(center=(500, 405)))
            else:
                draw_text("IMAGE NOT FOUND", font, (255, 80, 80), 500, 400)

            draw_text(name, font, (200, 170, 255), 500, 550)
            draw_text("< LEFT       RIGHT >       ENTER - ВЫБРАТЬ",
                      small_font, (255, 255, 255), 500, 585)

        elif game_state == "difficulty_select":
            draw_text("ВЫБЕРИ СЛОЖНОСТЬ БОТА", font, (255, 255, 255), 500, 175)
            draw_button((250, 230, 500, 65), "ЛЁГКИЙ", (35, 130, 65))
            draw_button((250, 315, 500, 65), "СРЕДНИЙ", (150, 105, 25))
            draw_button((250, 400, 500, 65), "СЛОЖНЫЙ", (155, 35, 45))
            draw_text("1 - Лёгкий     2 - Средний     3 - Сложный",
                      small_font, (230, 230, 230), 500, 500)

    # ================= БОЙ =================

    else:

        if background:
            screen.blit(background, (0, 0))
        else:
            screen.fill((45, 20, 65))

        # ДВИЖЕНИЕ

        if is_human("left") and gojo_purple_animation <= 0:
            if gojo_roll_timer > 0:
                gojo_x += gojo_facing * 1100 * dt
                gojo_roll_timer -= dt
            else:
                if keys[pygame.K_a]:
                    gojo_x -= 320 * dt
                    gojo_facing = -1
                if keys[pygame.K_d]:
                    gojo_x += 320 * dt
                    gojo_facing = 1

        if is_human("right") and sukuna_fuga_animation <= 0:
            if sukuna_roll_timer > 0:
                sukuna_x += sukuna_facing * 1100 * dt
                sukuna_roll_timer -= dt
            elif not gojo_domain_active or domain_clash:
                if keys[pygame.K_LEFT]:
                    sukuna_x -= 320 * dt
                    sukuna_facing = -1
                if keys[pygame.K_RIGHT]:
                    sukuna_x += 320 * dt
                    sukuna_facing = 1

        gojo_x = max(0, min(WIDTH - PLAYER_W, gojo_x))
        sukuna_x = max(0, min(WIDTH - PLAYER_W, sukuna_x))

        # ПРЫЖКИ

        if gojo_jump < 0 or gojo_velocity < 0:
            gojo_jump += gojo_velocity * dt
            gojo_velocity += 1800 * dt
            if gojo_jump >= 0:
                gojo_jump = gojo_velocity = 0

        if (sukuna_jump < 0 or sukuna_velocity < 0) and (not gojo_domain_active or domain_clash):
            sukuna_jump += sukuna_velocity * dt
            sukuna_velocity += 1800 * dt
            if sukuna_jump >= 0:
                sukuna_jump = sukuna_velocity = 0

        # ЭНЕРГИЯ

        if is_human("left") and keys[pygame.K_e]:
            gojo_energy = min(100, gojo_energy + ENERGY_SPEED * dt)

        if is_human("right") and keys[pygame.K_RSHIFT]:
            sukuna_energy = min(100, sukuna_energy + ENERGY_SPEED * dt)

        # ТАЙМЕРЫ

        gojo_roll_cooldown = max(0, gojo_roll_cooldown - dt)
        sukuna_roll_cooldown = max(0, sukuna_roll_cooldown - dt)
        gojo_invincible = max(0, gojo_invincible - dt)
        sukuna_invincible = max(0, sukuna_invincible - dt)
        gojo_attack_cooldown = max(0, gojo_attack_cooldown - dt)
        sukuna_attack_cooldown = max(0, sukuna_attack_cooldown - dt)
        gojo_purple_cooldown = max(0, gojo_purple_cooldown - dt)
        sukuna_fuga_cooldown = max(0, sukuna_fuga_cooldown - dt)
        mahoraga_timer = max(0, mahoraga_timer - dt)
        left_mahoraga_timer = max(0, left_mahoraga_timer - dt)

        # ИИ БОТА

        if game_mode == "bot" and not round_over:

            cfgs = {
                "easy": (0.75, 7, 105, 0.45, 0.0),
                "medium": (0.40, 13, 165, 0.72, 0.12),
                "hard": (0.20, 18, 225, 0.95, 0.42)
            }

            think, energy_rate, bot_speed, attack_chance, dodge = cfgs[bot_difficulty]

            bot_decision_timer -= dt

            if bot_character in ("GOJO", "YUJI", "YUTA"):
                gojo_energy = min(100, gojo_energy + energy_rate * dt)
            else:
                sukuna_energy = min(100, sukuna_energy + energy_rate * dt)

            if bot_decision_timer <= 0:
                bot_decision_timer = random.uniform(think * 0.7, think * 1.3)

                if bot_character in ("GOJO", "YUJI", "YUTA"):
                    distance = abs(gojo_x - sukuna_x)
                    gojo_facing = 1 if sukuna_x > gojo_x else -1

                    if gojo_energy >= 100 and not gojo_domain_active:
                        start_gojo_domain()
                    elif gojo_energy >= 50 and gojo_purple_cooldown <= 0 and distance > 200:
                        activate_special("left")
                    elif distance > 180:
                        gojo_x += gojo_facing * bot_speed * dt
                    elif random.random() < attack_chance:
                        side_attack("left", random.choice(["blue", "red"]))
                    if gojo_jump == 0 and random.random() < dodge:
                        gojo_velocity = -720

                else:
                    distance = abs(sukuna_x - gojo_x)
                    sukuna_facing = -1 if gojo_x < sukuna_x else 1

                    if sukuna_energy >= 100 and not sukuna_domain_active:
                        start_sukuna_domain()
                    elif sukuna_energy >= 50 and sukuna_fuga_cooldown <= 0 and distance > 190:
                        activate_special("right")
                    elif not gojo_domain_active or domain_clash:
                        if distance > 180:
                            sukuna_x += sukuna_facing * bot_speed * dt
                        elif random.random() < attack_chance:
                            side_attack("right")
                        if sukuna_jump == 0 and random.random() < dodge:
                            sukuna_velocity = -725

        # ДОМЕНЫ: ТАЙМЕРЫ И УРОН

        if gojo_domain_active:
            gojo_domain_timer = max(0, gojo_domain_timer - dt)
            if gojo_domain_timer <= 0:
                if left_character == "MAHITO" and mahito_domain_hits["left"] < 5 and not mahito_domain_failed["left"]:
                    mahito_domain_failed["left"] = True
                    gojo_hp = max(0, gojo_hp // 2)
                    gojo_energy //= 2
                gojo_domain_active = False
                if domain_clash:
                    domain_clash = False
                    gojo_domain_power = sukuna_domain_power = 0

        if sukuna_domain_active:
            sukuna_domain_timer = max(0, sukuna_domain_timer - dt)
            if sukuna_domain_timer <= 0:
                if right_character == "MAHITO" and mahito_domain_hits["right"] < 5 and not mahito_domain_failed["right"]:
                    mahito_domain_failed["right"] = True
                    sukuna_hp = max(0, sukuna_hp // 2)
                    sukuna_energy //= 4
                sukuna_domain_active = False
                sukuna_domain_damage_timer = 0
                if domain_clash:
                    domain_clash = False
                    gojo_domain_power = sukuna_domain_power = 0

        check_round_over()
        if round_over:
            dt = 0

        if gojo_domain_active and not domain_clash and left_character == "YUJI":
            gojo_domain_damage_timer += dt
            while gojo_domain_damage_timer >= 2:
                gojo_domain_damage_timer -= 2
                damage_player("sukuna", 5, True)

        if sukuna_domain_active and not domain_clash and right_character == "YUJI":
            sukuna_domain_damage_timer += dt
            while sukuna_domain_damage_timer >= 2:
                sukuna_domain_damage_timer -= 2
                damage_player("gojo", 5, True)

        # АНИМАЦИЯ СПЕЦИАЛЬНЫХ АТАК

        if gojo_purple_animation > 0:
            old = gojo_purple_animation
            gojo_purple_animation -= dt
            if old > 0.85 >= gojo_purple_animation:
                fire_special("left")

        if sukuna_fuga_animation > 0:
            old = sukuna_fuga_animation
            sukuna_fuga_animation -= dt
            if old > 0.85 >= sukuna_fuga_animation:
                fire_special("right")

        # ОСОБАЯ ФОРМА МАХИТО: шар едет к противнику и возвращается.
        for side in ("left", "right"):
            if mahito_ball[side] > 0:
                mahito_ball[side] = max(0, mahito_ball[side] - dt)
                prefix = side_prefix(side)
                x0 = globals()[prefix + "_x"] + 75
                direction = globals()[prefix + "_facing"]
                elapsed = 1.0 - mahito_ball[side]
                travel = math.sin(min(1, elapsed) * math.pi) * 260
                bx = x0 + direction * travel
                by = GROUND_Y - 45

                pygame.draw.circle(screen, (105, 55, 135), (int(bx), int(by)), 40)
                pygame.draw.circle(screen, (185, 125, 210), (int(bx), int(by)), 31, 4)
                for a in range(0, 360, 30):
                    rad = math.radians(a)
                    base = (int(bx + math.cos(rad) * 31), int(by + math.sin(rad) * 31))
                    tip = (int(bx + math.cos(rad) * 58), int(by + math.sin(rad) * 58))
                    pygame.draw.line(screen, (225, 205, 240), base, tip, 5)

                # Только одно попадание за одно превращение.
                if not mahito_ball_hit[side] and 0.25 < elapsed < 0.75:
                    enemy_x = sukuna_x if side == "left" else gojo_x
                    enemy_rect = pygame.Rect(enemy_x, GROUND_Y - PLAYER_H, PLAYER_W, PLAYER_H)
                    ball_rect = pygame.Rect(int(bx - 40), int(by - 40), 80, 80)
                    if ball_rect.colliderect(enemy_rect):
                        hit = damage_player(
                            "sukuna" if side == "left" else "gojo",
                            13, source_side=side
                        )
                        if hit:
                            mahito_ball_hit[side] = True

        # ДОМЕН МАХИТО: пять попаданий за 30 секунд или штраф половины HP/энергии.
        for side, active, timer in (("left", gojo_domain_active, gojo_domain_timer), ("right", sukuna_domain_active, sukuna_domain_timer)):
            if side_character(side) == "MAHITO" and active and timer <= 0.05 and not mahito_domain_failed[side] and mahito_domain_hits[side] < 5:
                mahito_domain_failed[side] = True
                hp_name = "gojo_hp" if side == "left" else "sukuna_hp"
                energy_name = side_prefix(side) + "_energy"
                globals()[hp_name] = max(0, globals()[hp_name] // 2)
                globals()[energy_name] = globals()[energy_name] // 2

        check_round_over()
        if round_over:
            dt = 0

        # СНАРЯДЫ

        for p in projectiles[:]:
            p["x"] += p["direction"] * p["speed"] * dt

            x, y = int(p["x"]), int(p["y"])
            r = p["radius"]
            color = p["color"]

            glow(x, y, r * 2, color)
            pygame.draw.circle(screen, color, (x, y), r)
            pygame.draw.circle(screen, (255, 255, 255),
                               (x, y), max(3, r // 3))

            if p["type"] in ("mahito_hammer",):
                pygame.draw.rect(screen, (80, 35, 110), (x-30, y-25, 60, 50), border_radius=8)
            elif p["type"] in ("mahito_sword", "mahito_hand"):
                pygame.draw.line(screen, (225, 190, 240), (x-25, y), (x+25, y), 8)
            elif p["type"] in ("yuta_beam",):
                pygame.draw.circle(screen, (245, 220, 255), (x, y), r+8, 4)
            elif p["type"] == "megumi_dogs":
                pygame.draw.circle(screen, (5, 5, 10), (x - 8, y - 7), 9)
                pygame.draw.circle(screen, (5, 5, 10), (x + 8, y - 7), 9)
                pygame.draw.circle(screen, (255, 255, 255), (x - 4, y - 8), 2)
                pygame.draw.circle(screen, (255, 255, 255), (x + 4, y - 8), 2)

            elif p["type"] == "megumi_nue":
                pygame.draw.polygon(screen, (220, 230, 255),
                                    [(x, y - 25), (x + 25, y),
                                     (x, y + 15), (x - 25, y)])

            elif p["type"] == "yuji_blood":
                for i in range(4):
                    pygame.draw.circle(screen, (180, 0, 25),
                                       (x - p["direction"] * i * 12,
                                        y + random.randint(-10, 10)), 6)

            elif p["type"] == "fuga":
                for i in range(4):
                    pygame.draw.circle(screen, (255, random.randint(70, 180), 0),
                                       (x - p["direction"] * i * 13,
                                        y + random.randint(-18, 18)),
                                       random.randint(5, 12))

            left_rect = pygame.Rect(gojo_x, GROUND_Y - PLAYER_H + gojo_jump,
                                    PLAYER_W, PLAYER_H)
            right_rect = pygame.Rect(sukuna_x, GROUND_Y - PLAYER_H + sukuna_jump,
                                     PLAYER_W, PLAYER_H)
            shot_rect = pygame.Rect(x - r, y - r, r * 2, r * 2)

            if p["direction"] == 1 and shot_rect.colliderect(right_rect):
                if p["type"] == "yuta_speech":
                    sukuna_velocity = 0
                    sukuna_roll_timer = 0
                elif p["type"] == "mahito_hand":
                    damage_player("sukuna", p["damage"], source_side=p.get("side"))
                elif p["type"] == "mahito_sword":
                    damage_player("sukuna", p["damage"], source_side=p.get("side"))
                elif p["type"] == "mahito_hammer":
                    damage_player("sukuna", p["damage"], source_side=p.get("side"))
                elif p["type"] == "yuta_sword":
                    damage_player("sukuna", p["damage"], source_side=p.get("side"))
                elif p["type"] == "yuta_black_flash":
                    damage_player("sukuna", p["damage"], source_side=p.get("side")); create_black_flash(x, y)
                if p["type"] == "yuji_blood":
                    damage_player("sukuna", p["damage"], source_side=p.get("side"))
                elif p["type"] == "yuji_black_flash":
                    damage_player("sukuna", p["damage"], source_side=p.get("side"))
                    create_black_flash(x, y)
                else:
                    damage_player("sukuna", p["damage"], source_side=p.get("side"))

                projectiles[:] = [item for item in projectiles if item is not p]
                continue

            if p["direction"] == -1 and shot_rect.colliderect(left_rect):
                if p["type"] in ("yuta_speech",):
                    gojo_velocity = 0
                    gojo_roll_timer = 0
                elif p["type"] in ("mahito_hand", "mahito_sword", "mahito_hammer", "yuta_sword", "yuta_black_flash"):
                    damage_player("gojo", p["damage"], source_side=p.get("side"))
                    if p["type"] == "yuta_black_flash": create_black_flash(x, y)
                if p["type"] == "fuga":
                    create_explosion(x, y)
                if p["type"] == "fuga":
                    damage_player("gojo", p["damage"], source_side=p.get("side"))
                else:
                    damage_player("gojo", p["damage"], source_side=p.get("side"))
                projectiles[:] = [item for item in projectiles if item is not p]
                continue

            if x < -100 or x > WIDTH + 100:
                projectiles[:] = [item for item in projectiles if item is not p]

        # РАЗРЕЗЫ СУКУНЫ

        for slash in slashes[:]:
            move = slash["speed"] * dt
            slash["x"] += slash["direction"] * move
            slash["distance"] += move

            sx, sy = int(slash["x"]), int(slash["y"])
            points = [(sx - 32, sy - 12), (sx - 10, sy - 5),
                      (sx + 28, sy - 22), (sx + 12, sy),
                      (sx + 35, sy + 10), (sx - 5, sy + 7)]

            if slash["direction"] == -1:
                points = [(2 * sx - x, y) for x, y in points]

            pygame.draw.polygon(screen, (255, 20, 30), points)

            if slash.get("side", "right") == "left":
                target_rect = pygame.Rect(sukuna_x, GROUND_Y - PLAYER_H + sukuna_jump, PLAYER_W, PLAYER_H)
                target_name = "sukuna"
            else:
                target_rect = pygame.Rect(gojo_x, GROUND_Y - PLAYER_H + gojo_jump, PLAYER_W, PLAYER_H)
                target_name = "gojo"
            slash_rect = pygame.Rect(sx - 30, sy - 20, 60, 40)

            if slash_rect.colliderect(target_rect):
                damage_player(target_name, slash["damage"], source_side=slash.get("side"))
                slashes[:] = [item for item in slashes if item is not slash]
                continue

            if slash["distance"] >= slash["max_distance"]:
                slashes[:] = [item for item in slashes if item is not slash]

        # ЭФФЕКТЫ И ПЕРСОНАЖИ

        draw_explosions(dt)
        draw_black_flashes(dt)
        draw_domains()

        draw_player(left_character, gojo_x, gojo_jump, gojo_facing,
                    gojo_invincible, (50, 100, 255))
        draw_player(right_character, sukuna_x, sukuna_jump, sukuna_facing,
                    sukuna_invincible, (180, 30, 30))

        draw_mahoraga()
        draw_special_animations()

        # ПОЛОСКИ HP И ЭНЕРГИИ

        draw_text(left_character, font, (100, 170, 255), 150, 25)
        draw_text(right_character, font, (255, 80, 80), 850, 25)

        draw_hp_bar(30, 50, gojo_hp, (40, 120, 255))
        draw_hp_bar(670, 50, sukuna_hp, (220, 30, 30))

        draw_energy_bar(30, 85, gojo_energy, (50, 130, 255))
        draw_energy_bar(670, 85, sukuna_energy, (170, 50, 220))

        draw_text(f"{int(gojo_energy)}%", small_font, (255, 255, 255), 340, 93)
        draw_text(f"{int(sukuna_energy)}%", small_font, (255, 255, 255), 980, 93)

        # ПОДСКАЗКИ СПОСОБНОСТЕЙ — по выбранному персонажу каждого игрока.
        def ability_labels(character, side):
            if character == "GOJO":
                return "PURPLE", "F - BLUE | G - RED", "UNLIMITED VOID"
            if character == "YUJI":
                next_name = side_next_attack[side]
                return "BLACK FLASH", f"АТАКА: {'РАЗРЕЗ' if next_name == 'slash' else 'КРОВЬ'}", "РАЗРЕЗ ДУШИ"
            if character == "YUTA":
                return "РИКА + ЮТА", (f"МЕЧЕЙ: {yuta_swords[side]}/5" if (gojo_domain_active if side == "left" else sukuna_domain_active) else "F/G - МЕЧ | H - ЛУЧ"), "ИСТИННАЯ И ВЗАИМНАЯ ЛЮБОВЬ"
            if character == "MAHITO":
                return "ШАРООБРАЗНАЯ ФОРМА", f"АТАКА {mahito_attack_index[side]+1}/3", "САМОВОПЛОЩЕНИЕ СОВЕРШЕНСТВА"
            if character == "MEGUMI":
                next_name = side_megumi_attack[side]
                return "МАХОРАГА", f"АТАКА: {'БОЖЕСТВЕННЫЕ ПСЫ' if next_name == 'dogs' else 'НУЭ'}", "ХИМЕРИЧЕСКИЙ ТЕНЕВОЙ САД"
            return "FUGA", "K - SLASH", "MALEVOLENT SHRINE"

        special_left, attack_left, domain_left = ability_labels(left_character, "left")
        special_right, attack_right, domain_right = ability_labels(right_character, "right")

        left_cooldown = gojo_purple_cooldown
        right_cooldown = sukuna_fuga_cooldown
        if left_cooldown > 0:
            left_special_text = f"{special_left}: {math.ceil(left_cooldown)}s"
        elif gojo_energy < 50:
            left_special_text = f"{special_left}: NEED 50 ENERGY"
        else:
            left_special_text = f"{special_left} READY! H"

        if right_cooldown > 0:
            right_special_text = f"{special_right}: {math.ceil(right_cooldown)}s"
        elif sukuna_energy < 50:
            right_special_text = f"{special_right}: NEED 50 ENERGY"
        else:
            right_special_text = f"{special_right} READY! L"

        draw_text(left_special_text, small_font, (210, 150, 255), 260, 125)
        draw_text(right_special_text, small_font, (255, 130, 20), 740, 125)

        draw_text(attack_left, small_font, (255, 255, 255), 250, 155)
        draw_text(attack_right, small_font, (255, 255, 255), 750, 155)

        left_domain_info = (
            f"DOMAIN: {math.ceil(gojo_domain_timer)}s"
            if gojo_domain_active else
            ("DOMAIN READY! J" if gojo_energy >= 100 else "DOMAIN: NEED 100")
        )

        right_domain_info = (
            f"DOMAIN: {math.ceil(sukuna_domain_timer)}s"
            if sukuna_domain_active else
            ("DOMAIN READY! O" if sukuna_energy >= 100 else "DOMAIN: NEED 100")
        )

        draw_text(left_domain_info, small_font, (100, 180, 255), 150, 185)
        draw_text(right_domain_info, small_font, (255, 100, 100), 850, 185)

        draw_domain_clash()

        # УПРАВЛЕНИЕ

        if game_mode == "2p":
            draw_text(
                "P1: A/D W S E F/G H J     |     P2: ARROWS DOWN SHIFT K L O",
                small_font, (235, 235, 235), 500, 575
            )
        elif human_character in ("GOJO", "YUJI", "YUTA"):
            draw_text(
                "YOU: A/D move, W jump, F/G attack, H special, J domain, E energy",
                small_font, (235, 235, 235), 500, 575
            )
        else:
            draw_text(
                "YOU: arrows move, UP jump, K attack, L special, O domain, SHIFT energy",
                small_font, (235, 235, 235), 500, 575
            )

        # ПОБЕДА

        if gojo_hp <= 0 or sukuna_hp <= 0:

            if not victory_sound_played:
                victory_sound_played = True
                try:
                    pygame.mixer.music.stop()
                    pygame.mixer.stop()
                except pygame.error:
                    pass
                play_sound("victory")

            winner = right_character if gojo_hp <= 0 else left_character

            pygame.draw.rect(screen, (10, 5, 20), (250, 220, 500, 150),
                             border_radius=20)
            draw_text(f"{winner} WINS!", big_font, (220, 150, 255), 500, 270)
            draw_text("ESC - MENU", font, (255, 255, 255), 500, 330)

    pygame.display.flip()

pygame.quit()
sys.exit()