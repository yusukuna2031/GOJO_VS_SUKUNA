import pygame
import random
import math
import sys

pygame.init()

try:
    pygame.mixer.init()
except:
    pass

# ================= НАСТРОЙКИ =================

WIDTH, HEIGHT = 1000, 600
FULLSCREEN = False
DISPLAY_FLAGS = pygame.SCALED
screen = pygame.display.set_mode((WIDTH, HEIGHT), DISPLAY_FLAGS)
pygame.display.set_caption("GOJO VS SUKUNA")
clock = pygame.time.Clock()

GROUND_Y = 530
PLAYER_W = 150
PLAYER_H = 230

MAX_HP = 100
MAX_ENERGY = 100
ENERGY_SPEED = 40

PURPLE_COOLDOWN = 30
FUGA_COOLDOWN = 30
DOMAIN_DURATION = 35
DOMAIN_CLASH_MULTIPLIER = 5

font = pygame.font.SysFont("arial", 30, bold=True)
big_font = pygame.font.SysFont("arial", 65, bold=True)
small_font = pygame.font.SysFont("arial", 19, bold=True)


# ================= ЗАГРУЗКА ФАЙЛОВ =================

def load_image(names, size=None):
    for name in names:
        try:
            img = pygame.image.load(name).convert_alpha()
            if size:
                img = pygame.transform.scale(img, size)
            return img
        except:
            pass
    return None


background = load_image(["arena.png"], (WIDTH, HEIGHT))
gojo_img = load_image(["gojo.png", "gojo.png.png"], (PLAYER_W, PLAYER_H))
sukuna_img = load_image(["sukuna.png", "sukuna.png.png"], (PLAYER_W, PLAYER_H))

music_loaded = False
try:
    pygame.mixer.music.load("judas.mp3")
    music_loaded = True
except:
    pass

gojo_domain_sound = None
sukuna_domain_sound = None

try:
    gojo_domain_sound = pygame.mixer.Sound("gojo_domain.mp3")
    gojo_domain_sound.set_volume(1.0)
except:
    pass

try:
    sukuna_domain_sound = pygame.mixer.Sound("sukuna_domain.mp3")
    sukuna_domain_sound.set_volume(1.0)
except:
    pass


# ================= СОСТОЯНИЕ ИГРЫ =================

game_state = "menu"  # menu, mode_select, character_select, difficulty_select, fight
game_mode = "2p"  # 2p or bot
human_character = "GOJO"  # GOJO or SUKUNA in bot mode
bot_character = "SUKUNA"
bot_difficulty = "medium"  # easy, medium, hard
bot_decision_timer = 0.0
bot_jump_timer = 0.0

gojo_x = 150
sukuna_x = 700
gojo_jump = 0
sukuna_jump = 0
gojo_velocity = 0
sukuna_velocity = 0

gojo_hp = 100
sukuna_hp = 100
gojo_energy = 0
sukuna_energy = 0

gojo_facing = 1
sukuna_facing = -1

gojo_roll_timer = 0
sukuna_roll_timer = 0
gojo_roll_cooldown = 0
sukuna_roll_cooldown = 0
gojo_invincible = 0
sukuna_invincible = 0

gojo_attack_cooldown = 0
sukuna_attack_cooldown = 0

# HOLLOW PURPLE
gojo_purple_animation = 0
gojo_purple_direction = 1
gojo_purple_cooldown = 0

# FUGA
sukuna_fuga_animation = 0
sukuna_fuga_direction = -1
sukuna_fuga_cooldown = 0

# DOMAINS
gojo_domain_active = False
sukuna_domain_active = False
gojo_domain_timer = 0.0
sukuna_domain_timer = 0.0
sukuna_domain_damage_timer = 0.0

domain_clash = False
domain_winner = None
gojo_domain_power = 0
sukuna_domain_power = 0

projectiles = []
slashes = []
explosions = []
black_flash_effects = []


# ================= ВСПОМОГАТЕЛЬНЫЕ ФУНКЦИИ =================

def draw_text(text, font_obj, color, x, y, center=True):
    img = font_obj.render(text, True, color)
    rect = img.get_rect()
    if center:
        rect.center = (x, y)
    else:
        rect.topleft = (x, y)
    screen.blit(img, rect)


def draw_glow(x, y, radius, color):
    radius = max(1, int(radius))
    for r in range(radius, 0, -5):
        alpha = int(25 + 100 * (r / radius))
        glow = pygame.Surface((r * 2, r * 2), pygame.SRCALPHA)
        pygame.draw.circle(glow, (*color, alpha), (r, r), r)
        screen.blit(glow, (int(x) - r, int(y) - r))


def draw_energy_bar(x, y, energy, color):
    pygame.draw.rect(screen, (30, 30, 40), (x, y, 300, 16))
    pygame.draw.rect(screen, color, (x, y, int(300 * energy / 100), 16))
    pygame.draw.rect(screen, (255, 255, 255), (x, y, 300, 16), 2)


def draw_hp_bar(x, y, hp, color):
    pygame.draw.rect(screen, (35, 35, 35), (x, y, 300, 25))
    pygame.draw.rect(screen, color, (x, y, int(300 * max(0, hp) / 100), 25))
    pygame.draw.rect(screen, (255, 255, 255), (x, y, 300, 25), 2)


def draw_menu_button(rect, label, color=(100, 30, 180)):
    pygame.draw.rect(screen, color, rect, border_radius=15)
    pygame.draw.rect(screen, (230, 200, 255), rect, 3, border_radius=15)
    draw_text(label, font, (255, 255, 255), rect[0] + rect[2] // 2,
              rect[1] + rect[3] // 2)


def is_human(character):
    return game_mode == "2p" or human_character == character


# ================= УРОН =================

def damage_player(target, damage, ignore_invincibility=False):
    global gojo_hp, sukuna_hp
    global gojo_domain_power, sukuna_domain_power
    global domain_clash, domain_winner
    global gojo_domain_active, sukuna_domain_active
    global sukuna_domain_timer, sukuna_domain_damage_timer
    global gojo_domain_timer

    if target == "gojo":
        if gojo_invincible > 0 and not ignore_invincibility:
            return
        actual_damage = min(gojo_hp, damage)
        gojo_hp = max(0, gojo_hp - damage)
        if domain_clash:
            sukuna_domain_power = min(
                100, sukuna_domain_power + actual_damage * DOMAIN_CLASH_MULTIPLIER
            )

    elif target == "sukuna":
        if sukuna_invincible > 0 and not ignore_invincibility:
            return
        actual_damage = min(sukuna_hp, damage)
        sukuna_hp = max(0, sukuna_hp - damage)
        if domain_clash:
            gojo_domain_power = min(
                100, gojo_domain_power + actual_damage * DOMAIN_CLASH_MULTIPLIER
            )

    if domain_clash:
        if gojo_domain_power >= 100:
            domain_winner = "GOJO"
            domain_clash = False
            # Годжо выиграл: домен Сукуны прекращается, урона после победы нет.
            sukuna_domain_active = False
            sukuna_domain_timer = 0.0
            sukuna_domain_damage_timer = 0.0
        elif sukuna_domain_power >= 100:
            domain_winner = "SUKUNA"
            domain_clash = False
            # Сукуна выиграл: его домен остаётся активным и начинает наносить урон.
            gojo_domain_active = False
            gojo_domain_timer = 0.0


# ================= ЧЁРНАЯ МОЛНИЯ =================

def try_black_flash(kind):
    """Второе нажатие H/L включает усиление, если снаряд уже близко к цели."""
    target_type = "purple" if kind == "purple" else "fuga"

    for projectile in projectiles:
        if projectile["type"] != target_type:
            continue
        if projectile.get("black_flash", False):
            continue

        target_x = sukuna_x if kind == "purple" else gojo_x
        target_center = target_x + PLAYER_W // 2
        distance = abs(target_center - projectile["x"])

        # Окно активации: снаряд находится не дальше 180 пикселей от цели.
        if distance <= 180:
            projectile["black_flash"] = True
            return True

    return False


def create_black_flash(x, y):
    black_flash_effects.append({
        "x": int(x),
        "y": int(y),
        "timer": 0.48,
        "max_timer": 0.48
    })


def draw_black_flash_effects(dt):
    for effect in black_flash_effects[:]:
        effect["timer"] -= dt
        x = effect["x"]
        y = effect["y"]
        progress = max(0, effect["timer"] / effect["max_timer"])
        radius = int(115 * progress)

        # Яркая вспышка и красное свечение
        draw_glow(x, y, max(12, radius), (255, 0, 35))
        flash_alpha = int(190 * progress)
        flash = pygame.Surface((WIDTH, HEIGHT), pygame.SRCALPHA)
        pygame.draw.circle(flash, (255, 255, 255, flash_alpha),
                           (x, y), max(2, int(42 * progress)))
        screen.blit(flash, (0, 0))

        # Чёрные молнии с красной обводкой
        for i in range(8):
            angle = (i / 8) * math.tau + 0.25
            length = random.randint(45, 105) * max(0.25, progress)
            end_x = int(x + math.cos(angle) * length)
            end_y = int(y + math.sin(angle) * length)
            mid_x = int((x + end_x) / 2 + random.randint(-18, 18))
            mid_y = int((y + end_y) / 2 + random.randint(-18, 18))
            points = [(x, y), (mid_x, mid_y), (end_x, end_y)]

            pygame.draw.lines(screen, (255, 15, 35), False, points, 9)
            pygame.draw.lines(screen, (0, 0, 0), False, points, 5)

        if effect["timer"] <= 0:
            black_flash_effects.remove(effect)


# ================= СБРОС ИГРЫ =================

def reset_game():
    global gojo_x, sukuna_x, gojo_jump, sukuna_jump
    global gojo_velocity, sukuna_velocity
    global gojo_hp, sukuna_hp, gojo_energy, sukuna_energy
    global gojo_facing, sukuna_facing
    global gojo_roll_timer, sukuna_roll_timer
    global gojo_roll_cooldown, sukuna_roll_cooldown
    global gojo_invincible, sukuna_invincible
    global gojo_attack_cooldown, sukuna_attack_cooldown
    global gojo_purple_animation, gojo_purple_direction, gojo_purple_cooldown
    global sukuna_fuga_animation, sukuna_fuga_direction, sukuna_fuga_cooldown
    global gojo_domain_active, sukuna_domain_active
    global gojo_domain_timer, sukuna_domain_timer, sukuna_domain_damage_timer
    global domain_clash, domain_winner, gojo_domain_power, sukuna_domain_power
    global projectiles, slashes, explosions, black_flash_effects
    global bot_decision_timer, bot_jump_timer

    bot_decision_timer = 0.0
    bot_jump_timer = 0.0
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

    gojo_purple_animation = 0
    gojo_purple_direction = 1
    gojo_purple_cooldown = 0

    sukuna_fuga_animation = 0
    sukuna_fuga_direction = -1
    sukuna_fuga_cooldown = 0

    gojo_domain_active = sukuna_domain_active = False
    gojo_domain_timer = sukuna_domain_timer = 0.0
    sukuna_domain_damage_timer = 0.0

    domain_clash = False
    domain_winner = None
    gojo_domain_power = sukuna_domain_power = 0

    projectiles = []
    slashes = []
    explosions = []
    black_flash_effects = []


# ================= АТАКИ ГОДЖО =================

def gojo_attack(kind):
    global gojo_attack_cooldown

    if gojo_attack_cooldown > 0 or gojo_purple_animation > 0:
        return

    if kind == "blue":
        projectiles.append({
            "x": gojo_x + PLAYER_W // 2,
            "y": GROUND_Y - 125 + gojo_jump,
            "direction": gojo_facing,
            "speed": 850,
            "radius": 17,
            "damage": 4,
            "color": (30, 100, 255),
            "type": "blue"
        })

    elif kind == "red":
        projectiles.append({
            "x": gojo_x + PLAYER_W // 2,
            "y": GROUND_Y - 125 + gojo_jump,
            "direction": gojo_facing,
            "speed": 700,
            "radius": 22,
            "damage": 6,
            "color": (255, 35, 35),
            "type": "red"
        })

    gojo_attack_cooldown = 0.35


# ================= HOLLOW PURPLE =================

def start_purple():
    global gojo_energy, gojo_purple_animation
    global gojo_purple_direction, gojo_purple_cooldown

    if gojo_energy < 50:
        return
    if gojo_purple_animation > 0 or gojo_purple_cooldown > 0:
        return

    gojo_energy -= 50
    gojo_purple_direction = gojo_facing
    gojo_purple_animation = 2.0
    gojo_purple_cooldown = PURPLE_COOLDOWN


def fire_purple():
    projectiles.append({
        "x": gojo_x + PLAYER_W // 2,
        "y": GROUND_Y - 125 + gojo_jump,
        "direction": gojo_purple_direction,
        "speed": 650,
        "radius": 38,
        "damage": 15,
        "color": (160, 40, 255),
        "type": "purple",
        "black_flash": False
    })


# ================= РАЗРЕЗЫ СУКУНЫ =================

def sukuna_attack():
    global sukuna_attack_cooldown

    if (gojo_domain_active and not domain_clash) or sukuna_attack_cooldown > 0:
        return

    slashes.append({
        "x": sukuna_x + PLAYER_W // 2,
        "y": GROUND_Y - 125 + sukuna_jump,
        "direction": sukuna_facing,
        "speed": 850,
        "distance": 0,
        "max_distance": 500
    })
    sukuna_attack_cooldown = 0.55


# ================= FUGA =================

def start_fuga():
    global sukuna_energy, sukuna_fuga_animation
    global sukuna_fuga_direction, sukuna_fuga_cooldown

    if (gojo_domain_active and not domain_clash) or sukuna_energy < 50:
        return
    if sukuna_fuga_animation > 0 or sukuna_fuga_cooldown > 0:
        return

    sukuna_energy -= 50
    sukuna_fuga_direction = sukuna_facing
    sukuna_fuga_animation = 2.0
    sukuna_fuga_cooldown = FUGA_COOLDOWN


def fire_fuga():
    projectiles.append({
        "x": sukuna_x + PLAYER_W // 2,
        "y": GROUND_Y - 125 + sukuna_jump,
        "direction": sukuna_fuga_direction,
        "speed": 600,
        "radius": 30,
        "damage": 25,
        "color": (255, 100, 10),
        "type": "fuga",
        "black_flash": False
    })


# ================= ДОМЕНЫ =================

def start_gojo_domain():
    global gojo_energy, gojo_domain_active, gojo_domain_timer
    global domain_winner
    global sukuna_velocity, sukuna_roll_timer, sukuna_fuga_animation
    global projectiles, slashes, domain_clash
    global gojo_domain_power, sukuna_domain_power

    if gojo_energy < 100 or gojo_domain_active:
        return

    gojo_energy -= 100
    gojo_domain_active = True
    gojo_domain_timer = DOMAIN_DURATION

    if gojo_domain_sound is not None:
        gojo_domain_sound.play()

    sukuna_velocity = 0
    sukuna_roll_timer = 0
    sukuna_fuga_animation = 0
    slashes.clear()
    projectiles[:] = [p for p in projectiles if p.get("type") != "fuga"]

    if sukuna_domain_active:
        domain_clash = True
        domain_winner = None
        gojo_domain_power = 0
        sukuna_domain_power = 0


def start_sukuna_domain():
    global sukuna_energy, sukuna_domain_active, sukuna_domain_timer
    global domain_winner
    global sukuna_domain_damage_timer, domain_clash
    global gojo_domain_power, sukuna_domain_power

    if sukuna_energy < 100 or sukuna_domain_active:
        return

    sukuna_energy -= 100
    sukuna_domain_active = True
    sukuna_domain_timer = DOMAIN_DURATION
    sukuna_domain_damage_timer = 0.0

    if sukuna_domain_sound is not None:
        sukuna_domain_sound.play()

    if gojo_domain_active:
        domain_clash = True
        domain_winner = None
        gojo_domain_power = 0
        sukuna_domain_power = 0


# ================= РИСОВАНИЕ ПЕРСОНАЖЕЙ =================

def draw_player(img, x, jump, facing, invincible, fallback_color):
    y = GROUND_Y - PLAYER_H + jump
    if invincible > 0 and int(invincible * 15) % 2 == 0:
        return

    if img:
        sprite = pygame.transform.flip(img, facing == -1, False)
        screen.blit(sprite, (int(x), int(y)))
    else:
        pygame.draw.rect(
            screen, fallback_color,
            (int(x), int(y), PLAYER_W, PLAYER_H),
            border_radius=15
        )


# ================= АНИМАЦИЯ PURPLE =================

def draw_purple_animation():
    if gojo_purple_animation <= 0:
        return

    elapsed = 2.0 - gojo_purple_animation
    center_x = gojo_x + PLAYER_W // 2
    center_y = GROUND_Y - PLAYER_H + 100 + gojo_jump

    if elapsed < 0.65:
        draw_text("BLUE + RED", small_font, (255, 255, 255),
                  center_x, center_y - 75)
        blue_x = center_x - 45 * gojo_purple_direction
        red_x = center_x + 45 * gojo_purple_direction
        draw_glow(int(blue_x), center_y, 38, (30, 100, 255))
        pygame.draw.circle(screen, (30, 100, 255), (int(blue_x), int(center_y)), 20)
        draw_glow(int(red_x), center_y, 38, (255, 30, 30))
        pygame.draw.circle(screen, (255, 30, 30), (int(red_x), int(center_y)), 20)

    elif elapsed < 1.15:
        progress = (elapsed - 0.65) / 0.5
        distance = 45 * (1 - progress)
        blue_x = center_x - distance * gojo_purple_direction
        red_x = center_x + distance * gojo_purple_direction
        draw_glow(int(blue_x), center_y, 40, (30, 100, 255))
        pygame.draw.circle(screen, (30, 100, 255), (int(blue_x), int(center_y)), 21)
        draw_glow(int(red_x), center_y, 40, (255, 30, 30))
        pygame.draw.circle(screen, (255, 30, 30), (int(red_x), int(center_y)), 21)
        draw_glow(center_x, center_y, 45, (160, 40, 255))

    else:
        radius = int(28 + 18 * math.sin(elapsed * 15))
        draw_glow(center_x, center_y, 75, (170, 40, 255))
        pygame.draw.circle(screen, (120, 20, 220), (int(center_x), int(center_y)), radius + 8)
        pygame.draw.circle(screen, (210, 160, 255), (int(center_x), int(center_y)), radius)
        pygame.draw.circle(screen, (255, 255, 255), (int(center_x), int(center_y)), 9)
        draw_text("HOLLOW PURPLE!", font, (210, 140, 255), center_x, center_y - 80)


# ================= АНИМАЦИЯ FUGA =================

def draw_fuga_animation():
    if sukuna_fuga_animation <= 0:
        return

    elapsed = 2.0 - sukuna_fuga_animation
    center_x = sukuna_x + PLAYER_W // 2
    center_y = GROUND_Y - PLAYER_H + 105 + sukuna_jump

    if elapsed < 0.7:
        draw_text("FUGA...", font, (255, 150, 40), center_x, center_y - 75)
        for i in range(8):
            angle = elapsed * 8 + i * math.pi / 4
            px = center_x + math.cos(angle) * 45
            py = center_y + math.sin(angle) * 45
            draw_glow(int(px), int(py), 22, (255, 80, 10))
            pygame.draw.circle(
                screen, (255, random.randint(80, 180), 10),
                (int(px), int(py)), random.randint(5, 10)
            )
    else:
        radius = int(25 + 12 * math.sin(elapsed * 18))
        draw_glow(center_x, center_y, 75, (255, 65, 5))
        pygame.draw.circle(screen, (190, 20, 0), (int(center_x), int(center_y)), radius + 12)
        pygame.draw.circle(screen, (255, 90, 0), (int(center_x), int(center_y)), radius)
        pygame.draw.circle(screen, (255, 220, 90), (int(center_x), int(center_y)), radius // 2)
        draw_text("FUGA!", font, (255, 120, 20), center_x, center_y - 80)


# ================= ВИЗУАЛЬНЫЕ ДОМЕНЫ =================

def draw_domains():
    if not gojo_domain_active and not sukuna_domain_active:
        return

    overlay = pygame.Surface((WIDTH, HEIGHT), pygame.SRCALPHA)

    if gojo_domain_active:
        overlay.fill((35, 70, 180, 65))
        for i in range(18):
            x = (i * 137 + pygame.time.get_ticks() // 25) % WIDTH
            y = (i * 79 + pygame.time.get_ticks() // 35) % HEIGHT
            pygame.draw.circle(overlay, (160, 210, 255, 150),
                               (x, y), random.randint(2, 5))
        draw_text("UNLIMITED VOID", font, (140, 200, 255), WIDTH // 2, 145)

    if sukuna_domain_active:
        overlay.fill((130, 10, 20, 65))
        for i in range(14):
            x = (i * 173 + pygame.time.get_ticks() // 30) % WIDTH
            y = (i * 97 + pygame.time.get_ticks() // 40) % HEIGHT
            pygame.draw.line(overlay, (255, 50, 50, 170),
                             (x, y), (x + 35, y - 25), 3)
        draw_text("MALEVOLENT SHRINE", font, (255, 100, 100), WIDTH // 2, 180)

    screen.blit(overlay, (0, 0))


# ================= ШКАЛА СТОЛКНОВЕНИЯ ДОМЕНОВ =================

def draw_domain_clash_bar():
    if not domain_clash and not domain_winner:
        return

    bar_x, bar_y = 250, 490
    bar_width, bar_height = 500, 30

    draw_text("DOMAIN CLASH!", font, (255, 255, 255), WIDTH // 2, 455)
    pygame.draw.rect(screen, (20, 20, 30),
                     (bar_x, bar_y, bar_width, bar_height), border_radius=8)

    blue_width = int(bar_width * gojo_domain_power / 100)
    if blue_width > 0:
        pygame.draw.rect(screen, (30, 120, 255),
                         (bar_x, bar_y, blue_width, bar_height), border_radius=8)
        draw_glow(bar_x + blue_width, bar_y + bar_height // 2, 20, (30, 120, 255))

    red_width = int(bar_width * sukuna_domain_power / 100)
    if red_width > 0:
        pygame.draw.rect(screen, (255, 35, 45),
                         (bar_x + bar_width - red_width, bar_y, red_width, bar_height),
                         border_radius=8)
        draw_glow(bar_x + bar_width - red_width,
                  bar_y + bar_height // 2, 20, (255, 35, 45))

    pygame.draw.rect(screen, (255, 255, 255),
                     (bar_x, bar_y, bar_width, bar_height), 2, border_radius=8)

    draw_text(f"GOJO {int(gojo_domain_power)}%", small_font,
              (100, 180, 255), 160, 505)
    draw_text(f"{int(sukuna_domain_power)}% SUKUNA", small_font,
              (255, 100, 100), 840, 505)

    if domain_winner == "GOJO":
        draw_text("GOJO WON THE DOMAIN CLASH!", font,
                  (100, 180, 255), WIDTH // 2, 410)
    elif domain_winner == "SUKUNA":
        draw_text("SUKUNA WON THE DOMAIN CLASH!", font,
                  (255, 70, 70), WIDTH // 2, 410)


# ================= ВЗРЫВЫ =================

def create_explosion(x, y):
    explosions.append({"x": x, "y": y, "timer": 0.55, "max_timer": 0.55})


def draw_explosions(dt):
    for explosion in explosions[:]:
        explosion["timer"] -= dt
        progress = 1 - (explosion["timer"] / explosion["max_timer"])
        radius = int(25 + progress * 110)
        x, y = int(explosion["x"]), int(explosion["y"])

        draw_glow(x, y, radius + 25, (255, 65, 5))
        pygame.draw.circle(screen, (255, 60, 0), (x, y), radius)
        pygame.draw.circle(screen, (255, 170, 20), (x, y), int(radius * 0.65))
        pygame.draw.circle(screen, (255, 240, 120), (x, y), int(radius * 0.3))

        if explosion["timer"] <= 0:
            explosions.remove(explosion)


# ================= ПОЛНОЭКРАННЫЙ РЕЖИМ =================

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
    dt = clock.tick(60) / 1000
    dt = min(dt, 0.04)

    for event in pygame.event.get():
        if event.type == pygame.QUIT:
            running = False

        if event.type == pygame.KEYDOWN:
            # F11 работает и в меню, и во время боя
            if event.key == pygame.K_F11:
                toggle_fullscreen()
                continue

            if game_state == "fight":
                if is_human("GOJO"):
                    if event.key == pygame.K_w and gojo_jump == 0:
                        gojo_velocity = -720
                    if event.key == pygame.K_s and gojo_roll_cooldown <= 0:
                        gojo_roll_timer = 0.55
                        gojo_roll_cooldown = 1.0
                        gojo_invincible = 0.7
                    if event.key == pygame.K_f:
                        gojo_attack("blue")
                    if event.key == pygame.K_g:
                        gojo_attack("red")
                    if event.key == pygame.K_h:
                        if not try_black_flash("purple"):
                            start_purple()
                    if event.key == pygame.K_j:
                        start_gojo_domain()

                if is_human("SUKUNA"):
                    if event.key == pygame.K_UP and sukuna_jump == 0 and (not gojo_domain_active or domain_clash):
                        sukuna_velocity = -720
                    if event.key == pygame.K_DOWN and sukuna_roll_cooldown <= 0 and (not gojo_domain_active or domain_clash):
                        sukuna_roll_timer = 0.55
                        sukuna_roll_cooldown = 1.0
                        sukuna_invincible = 0.7
                    if event.key == pygame.K_k:
                        sukuna_attack()
                    if event.key == pygame.K_l:
                        if not try_black_flash("fuga"):
                            start_fuga()
                    if event.key == pygame.K_o:
                        start_sukuna_domain()

                if event.key == pygame.K_ESCAPE:
                    game_state = "menu"
                    pygame.mixer.music.stop()

            elif game_state == "menu":
                if event.key in (pygame.K_RETURN, pygame.K_SPACE):
                    game_state = "mode_select"

            elif game_state == "mode_select":
                if event.key == pygame.K_1:
                    game_mode = "2p"
                    reset_game()
                    game_state = "fight"
                    if music_loaded: pygame.mixer.music.play(-1)
                elif event.key == pygame.K_2:
                    game_mode = "bot"
                    game_state = "character_select"
                elif event.key == pygame.K_ESCAPE:
                    game_state = "menu"

            elif game_state == "character_select":
                if event.key == pygame.K_1:
                    human_character, bot_character = "GOJO", "SUKUNA"
                    game_state = "difficulty_select"
                elif event.key == pygame.K_2:
                    human_character, bot_character = "SUKUNA", "GOJO"
                    game_state = "difficulty_select"
                elif event.key == pygame.K_ESCAPE:
                    game_state = "mode_select"

            elif game_state == "difficulty_select":
                if event.key in (pygame.K_1, pygame.K_KP1):
                    bot_difficulty = "easy"
                elif event.key in (pygame.K_2, pygame.K_KP2):
                    bot_difficulty = "medium"
                elif event.key in (pygame.K_3, pygame.K_KP3):
                    bot_difficulty = "hard"
                else:
                    bot_difficulty = None
                if bot_difficulty:
                    reset_game()
                    game_state = "fight"
                    if music_loaded: pygame.mixer.music.play(-1)
                elif event.key == pygame.K_ESCAPE:
                    game_state = "character_select"

        if event.type == pygame.MOUSEBUTTONDOWN and event.button == 1:
            mx, my = event.pos
            if game_state == "menu" and pygame.Rect(350, 280, 300, 75).collidepoint(mx, my):
                game_state = "mode_select"
            elif game_state == "mode_select":
                if pygame.Rect(250, 260, 500, 75).collidepoint(mx, my):
                    game_mode = "2p"
                    reset_game()
                    game_state = "fight"
                    if music_loaded: pygame.mixer.music.play(-1)
                elif pygame.Rect(250, 360, 500, 75).collidepoint(mx, my):
                    game_mode = "bot"
                    game_state = "character_select"
            elif game_state == "character_select":
                if pygame.Rect(250, 260, 500, 75).collidepoint(mx, my):
                    human_character, bot_character = "GOJO", "SUKUNA"
                    game_state = "difficulty_select"
                elif pygame.Rect(250, 360, 500, 75).collidepoint(mx, my):
                    human_character, bot_character = "SUKUNA", "GOJO"
                    game_state = "difficulty_select"
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
                    if music_loaded: pygame.mixer.music.play(-1)

    keys = pygame.key.get_pressed()

    # ================= МЕНЮ =================

    if game_state in ("menu", "mode_select", "character_select", "difficulty_select"):
        screen.fill((12, 5, 30))
        if background:
            screen.blit(background, (0, 0))
        draw_text("GOJO VS SUKUNA", big_font, (220, 180, 255), WIDTH // 2, 155)

        if game_state == "menu":
            draw_menu_button((350, 280, 300, 75), "НАЧАТЬ БОЙ")
            draw_text("Нажми ENTER или кнопку мышью", small_font,
                      (220, 220, 220), WIDTH // 2, 400)
            draw_text("F11 - ПОЛНЫЙ ЭКРАН", small_font,
                      (220, 220, 220), WIDTH // 2, 445)
        elif game_state == "mode_select":
            draw_text("ВЫБЕРИ РЕЖИМ ИГРЫ", font, (255, 255, 255), WIDTH // 2, 220)
            draw_menu_button((250, 260, 500, 75), "2 PLAYERS")
            draw_menu_button((250, 360, 500, 75), "1 PLAYER WITH BOT", (120, 35, 145))
            draw_text("1 - 2 Players     2 - With Bot     ESC - Назад",
                      small_font, (230, 230, 230), WIDTH // 2, 475)
        elif game_state == "character_select":
            draw_text("КЕМ ТЫ ХОЧЕШЬ ИГРАТЬ?", font,
                      (255, 255, 255), WIDTH // 2, 220)
            draw_menu_button((250, 260, 500, 75), "GOJO", (35, 75, 180))
            draw_menu_button((250, 360, 500, 75), "SUKUNA", (150, 25, 35))
            draw_text("1 - Gojo     2 - Sukuna     ESC - Назад",
                      small_font, (230, 230, 230), WIDTH // 2, 475)
        elif game_state == "difficulty_select":
            draw_text("ВЫБЕРИ СЛОЖНОСТЬ БОТА", font,
                      (255, 255, 255), WIDTH // 2, 175)
            draw_menu_button((250, 230, 500, 65), "ЛЁГКИЙ", (35, 130, 65))
            draw_menu_button((250, 315, 500, 65), "СРЕДНИЙ", (150, 105, 25))
            draw_menu_button((250, 400, 500, 65), "СЛОЖНЫЙ", (155, 35, 45))
            draw_text("1 - Лёгкий     2 - Средний     3 - Сложный     ESC - Назад",
                      small_font, (230, 230, 230), WIDTH // 2, 500)

    # ================= БОЙ =================

    elif game_state == "fight":
        if background:
            screen.blit(background, (0, 0))
        else:
            screen.fill((45, 20, 65))

        # ДВИЖЕНИЕ ГОДЖО
        if is_human("GOJO") and gojo_purple_animation <= 0:
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

        # ДВИЖЕНИЕ СУКУНЫ
        if is_human("SUKUNA") and sukuna_fuga_animation <= 0 and (not gojo_domain_active or domain_clash):
            if sukuna_roll_timer > 0:
                sukuna_x += sukuna_facing * 1100 * dt
                sukuna_roll_timer -= dt
            else:
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
                gojo_jump = 0
                gojo_velocity = 0

        if (sukuna_jump < 0 or sukuna_velocity < 0) and (not gojo_domain_active or domain_clash):
            sukuna_jump += sukuna_velocity * dt
            sukuna_velocity += 1800 * dt
            if sukuna_jump >= 0:
                sukuna_jump = 0
                sukuna_velocity = 0

        # ЗАРЯД ЭНЕРГИИ
        if is_human("GOJO") and keys[pygame.K_e]:
            gojo_energy = min(100, gojo_energy + ENERGY_SPEED * dt)
        if is_human("SUKUNA") and keys[pygame.K_RSHIFT]:
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

        # ================= ИИ ПРОТИВНИКА: 3 УРОВНЯ =================
        if game_mode == "bot":
            bot_settings = {
                "easy":   {"think": (0.65, 0.90), "energy": 7,  "speed": 105, "attack_chance": 0.45, "dodge": 0.00},
                "medium": {"think": (0.32, 0.48), "energy": 13, "speed": 165, "attack_chance": 0.72, "dodge": 0.12},
                "hard":   {"think": (0.16, 0.25), "energy": 18, "speed": 225, "attack_chance": 0.95, "dodge": 0.42},
            }
            cfg = bot_settings.get(bot_difficulty, bot_settings["medium"])
            bot_decision_timer -= dt
            bot_jump_timer = max(0, bot_jump_timer - dt)

            # Бот заряжает энергию постепенно, а не огромными скачками.
            if bot_character == "GOJO":
                gojo_energy = min(100, gojo_energy + cfg["energy"] * dt)
            else:
                sukuna_energy = min(100, sukuna_energy + cfg["energy"] * dt)

            if bot_decision_timer <= 0:
                bot_decision_timer = random.uniform(*cfg["think"])
                if bot_character == "GOJO":
                    distance = abs((gojo_x + PLAYER_W / 2) - (sukuna_x + PLAYER_W / 2))
                    gojo_facing = 1 if sukuna_x > gojo_x else -1
                    if gojo_energy >= 100 and not gojo_domain_active and not domain_clash:
                        start_gojo_domain()
                    elif gojo_energy >= 50 and gojo_purple_cooldown <= 0 and gojo_purple_animation <= 0 and distance > 210:
                        start_purple()
                    elif distance > 205:
                        gojo_x += gojo_facing * cfg["speed"] * dt
                    elif distance < 125 and random.random() < cfg["dodge"]:
                        gojo_x -= gojo_facing * cfg["speed"] * 0.75 * dt
                    elif gojo_attack_cooldown <= 0 and random.random() < cfg["attack_chance"]:
                        gojo_attack(random.choice(["blue", "red", "blue"]))
                    if gojo_jump == 0 and random.random() < cfg["dodge"]:
                        gojo_velocity = -720
                else:
                    distance = abs((sukuna_x + PLAYER_W / 2) - (gojo_x + PLAYER_W / 2))
                    sukuna_facing = -1 if gojo_x < sukuna_x else 1
                    if sukuna_energy >= 100 and not sukuna_domain_active and not domain_clash:
                        start_sukuna_domain()
                    elif sukuna_energy >= 50 and sukuna_fuga_cooldown <= 0 and sukuna_fuga_animation <= 0 and distance > 190:
                        start_fuga()
                    elif not gojo_domain_active or domain_clash:
                        if distance > 205:
                            sukuna_x += sukuna_facing * cfg["speed"] * dt
                        elif distance < 125 and random.random() < cfg["dodge"]:
                            sukuna_x -= sukuna_facing * cfg["speed"] * 0.75 * dt
                        elif sukuna_attack_cooldown <= 0 and random.random() < cfg["attack_chance"]:
                            sukuna_attack()
                        if sukuna_jump == 0 and random.random() < cfg["dodge"]:
                            sukuna_velocity = -720

                gojo_x = max(0, min(WIDTH - PLAYER_W, gojo_x))
                sukuna_x = max(0, min(WIDTH - PLAYER_W, sukuna_x))

        # ТАЙМЕРЫ ДОМЕНОВ
        if gojo_domain_active:
            gojo_domain_timer = max(0, gojo_domain_timer - dt)
            if gojo_domain_timer <= 0:
                gojo_domain_active = False
                if domain_clash:
                    domain_clash = False
                    gojo_domain_power = sukuna_domain_power = 0

        if sukuna_domain_active:
            sukuna_domain_timer = max(0, sukuna_domain_timer - dt)
            if sukuna_domain_timer <= 0:
                sukuna_domain_active = False
                sukuna_domain_damage_timer = 0
                if domain_clash:
                    domain_clash = False
                    gojo_domain_power = sukuna_domain_power = 0

        if sukuna_domain_active and not domain_clash:
            sukuna_domain_damage_timer += dt
            while sukuna_domain_damage_timer >= 2.0:
                sukuna_domain_damage_timer -= 2.0
                damage_player("gojo", 5, ignore_invincibility=True)

        # PURPLE: запуск снаряда в нужный момент анимации
        if gojo_purple_animation > 0:
            old_time = gojo_purple_animation
            gojo_purple_animation -= dt
            if old_time > 0.85 and gojo_purple_animation <= 0.85:
                fire_purple()

        # FUGA: запуск снаряда в нужный момент анимации
        if sukuna_fuga_animation > 0:
            old_time = sukuna_fuga_animation
            sukuna_fuga_animation -= dt
            if old_time > 0.85 and sukuna_fuga_animation <= 0.85:
                fire_fuga()

        # СНАРЯДЫ
        for p in projectiles[:]:
            p["x"] += p["direction"] * p["speed"] * dt
            color = p["color"]
            radius = p["radius"]

            draw_glow(int(p["x"]), int(p["y"]), radius * 2, color)
            pygame.draw.circle(screen, color, (int(p["x"]), int(p["y"])), radius)
            pygame.draw.circle(screen, (255, 255, 255),
                               (int(p["x"]), int(p["y"])), max(3, radius // 3))

            if p["type"] == "fuga":
                for i in range(4):
                    flame_x = int(p["x"] - p["direction"] * (i * 13))
                    flame_y = int(p["y"] + random.randint(-18, 18))
                    pygame.draw.circle(
                        screen, (255, random.randint(70, 180), 0),
                        (flame_x, flame_y), random.randint(5, 12)
                    )

            gojo_rect = pygame.Rect(
                gojo_x, GROUND_Y - PLAYER_H + gojo_jump, PLAYER_W, PLAYER_H
            )
            sukuna_rect = pygame.Rect(
                sukuna_x, GROUND_Y - PLAYER_H + sukuna_jump, PLAYER_W, PLAYER_H
            )
            projectile_rect = pygame.Rect(
                int(p["x"] - radius), int(p["y"] - radius), radius * 2, radius * 2
            )

            # PURPLE ПОПАЛ В СУКУНУ
            if p["type"] != "fuga" and projectile_rect.colliderect(sukuna_rect):
                if p["type"] == "purple" and p.get("black_flash", False):
                    damage_player("sukuna", 20)
                    create_black_flash(p["x"], p["y"])
                else:
                    damage_player("sukuna", p["damage"])
                projectiles.remove(p)
                continue

            # FUGA ПОПАЛА В ГОДЖО
            if p["type"] == "fuga" and projectile_rect.colliderect(gojo_rect):
                create_explosion(p["x"], p["y"])
                if p.get("black_flash", False):
                    damage_player("gojo", 30)
                    create_black_flash(p["x"], p["y"])
                else:
                    damage_player("gojo", p["damage"])
                projectiles.remove(p)
                continue

            if p["x"] < -100 or p["x"] > WIDTH + 100:
                if p["type"] == "fuga":
                    create_explosion(p["x"], p["y"])
                projectiles.remove(p)

        # РАЗРЕЗЫ СУКУНЫ
        for slash in slashes[:]:
            move = slash["speed"] * dt
            slash["x"] += slash["direction"] * move
            slash["distance"] += move
            sx, sy = int(slash["x"]), int(slash["y"])

            points = [
                (sx - 32, sy - 12), (sx - 10, sy - 5), (sx + 28, sy - 22),
                (sx + 12, sy), (sx + 35, sy + 10), (sx - 5, sy + 7)
            ]
            if slash["direction"] == -1:
                points = [(2 * sx - x, y) for x, y in points]
            pygame.draw.polygon(screen, (255, 20, 30), points)

            inner_points = [
                (sx - 25, sy - 9), (sx - 8, sy - 3), (sx + 20, sy - 17),
                (sx + 8, sy), (sx + 25, sy + 7), (sx - 4, sy + 5)
            ]
            if slash["direction"] == -1:
                inner_points = [(2 * sx - x, y) for x, y in inner_points]
            pygame.draw.polygon(screen, (5, 5, 10), inner_points)

            gojo_rect = pygame.Rect(
                gojo_x, GROUND_Y - PLAYER_H + gojo_jump, PLAYER_W, PLAYER_H
            )
            slash_rect = pygame.Rect(sx - 30, sy - 20, 60, 40)

            if slash_rect.colliderect(gojo_rect):
                damage_player("gojo", 2)
                slashes.remove(slash)
                continue

            if slash["distance"] >= slash["max_distance"]:
                slashes.remove(slash)

        # ВИЗУАЛЬНЫЕ ЭФФЕКТЫ
        draw_explosions(dt)
        draw_black_flash_effects(dt)

        # ДОМЕНЫ
        draw_domains()

        # ПЕРСОНАЖИ
        draw_player(gojo_img, gojo_x, gojo_jump, gojo_facing,
                    gojo_invincible, (50, 100, 255))
        draw_player(sukuna_img, sukuna_x, sukuna_jump, sukuna_facing,
                    sukuna_invincible, (180, 30, 30))

        draw_purple_animation()
        draw_fuga_animation()

        # HP И ЭНЕРГИЯ
        draw_text("GOJO", font, (100, 170, 255), 150, 25)
        draw_text("SUKUNA", font, (255, 80, 80), 850, 25)
        if game_mode == "bot":
            difficulty_label = {"easy": "ЛЁГКИЙ", "medium": "СРЕДНИЙ", "hard": "СЛОЖНЫЙ"}.get(bot_difficulty, "СРЕДНИЙ")
            draw_text(f"YOU: {human_character}  |  BOT: {bot_character}  |  {difficulty_label}",
                      small_font, (255, 255, 255), WIDTH // 2, 115)
        draw_hp_bar(30, 50, gojo_hp, (40, 120, 255))
        draw_hp_bar(670, 50, sukuna_hp, (220, 30, 30))
        draw_energy_bar(30, 85, gojo_energy, (50, 130, 255))
        draw_energy_bar(670, 85, sukuna_energy, (170, 50, 220))
        draw_text(f"{int(gojo_energy)}%", small_font, (255, 255, 255), 340, 93)
        draw_text(f"{int(sukuna_energy)}%", small_font, (255, 255, 255), 980, 93)

        # PURPLE ИНФОРМАЦИЯ
        if gojo_purple_cooldown > 0:
            purple_text = f"PURPLE: {math.ceil(gojo_purple_cooldown)}s"
        elif gojo_energy < 50:
            purple_text = "PURPLE: NEED 50 ENERGY"
        else:
            purple_text = "PURPLE READY! H"
        draw_text(purple_text, small_font, (210, 150, 255), WIDTH // 2, 25)

        # FUGA ИНФОРМАЦИЯ
        if sukuna_fuga_animation > 0:
            fuga_text = "FUGA ACTIVATING!"
        elif sukuna_fuga_cooldown > 0:
            fuga_text = f"FUGA COOLDOWN: {math.ceil(sukuna_fuga_cooldown)}s"
        elif sukuna_energy < 50:
            fuga_text = "FUGA: NEED 50 ENERGY"
        else:
            fuga_text = "FUGA READY! L"
        draw_text(fuga_text, small_font, (255, 130, 20), WIDTH // 2, 55)

        # ПОДСКАЗКА ЧЁРНОЙ МОЛНИИ
        purple_armed = any(p["type"] == "purple" and p.get("black_flash", False)
                           for p in projectiles)
        fuga_armed = any(p["type"] == "fuga" and p.get("black_flash", False)
                         for p in projectiles)
        if purple_armed:
            draw_text("BLACK FLASH READY!", small_font, (255, 40, 60), 360, 155)
        if fuga_armed:
            draw_text("BLACK FLASH READY!", small_font, (255, 40, 60), 640, 155)

        # ДОМЕНЫ ИНФОРМАЦИЯ
        if not gojo_domain_active:
            gojo_domain_text = "DOMAIN READY! J" if gojo_energy >= 100 else "DOMAIN: NEED 100"
            draw_text(gojo_domain_text, small_font, (100, 180, 255), 150, 125)
        elif gojo_domain_active:
            draw_text(f"GOJO DOMAIN: {math.ceil(gojo_domain_timer)}s",
                      small_font, (100, 180, 255), 150, 125)

        if not sukuna_domain_active:
            sukuna_domain_text = "DOMAIN READY! O" if sukuna_energy >= 100 else "DOMAIN: NEED 100"
            draw_text(sukuna_domain_text, small_font, (255, 100, 100), 850, 125)
        elif sukuna_domain_active:
            draw_text(f"SUKUNA DOMAIN: {math.ceil(sukuna_domain_timer)}s",
                      small_font, (255, 100, 100), 850, 125)

        draw_domain_clash_bar()
        if game_mode == "2p":
            draw_text("GOJO: A/D W F/G H J | SUKUNA: arrows K/L O",
                      small_font, (235, 235, 235), WIDTH // 2, 575)
        elif human_character == "GOJO":
            draw_text("YOU: A/D move, W jump, F/G attacks, H Purple, J Domain, E charge",
                      small_font, (235, 235, 235), WIDTH // 2, 575)
        else:
            draw_text("YOU: arrows move, UP jump, K slash, L Fuga, O Domain, RIGHT SHIFT charge",
                      small_font, (235, 235, 235), WIDTH // 2, 575)

        # ПОБЕДА В БОЮ
        if gojo_hp <= 0 or sukuna_hp <= 0:
            winner = "SUKUNA WINS!" if gojo_hp <= 0 else "GOJO WINS!"
            pygame.draw.rect(screen, (10, 5, 20), (250, 220, 500, 150),
                             border_radius=20)
            draw_text(winner, big_font, (220, 150, 255), WIDTH // 2, 270)
            draw_text("ESC - MENU", font, (255, 255, 255), WIDTH // 2, 330)

    pygame.display.flip()

pygame.quit()
sys.exit()
