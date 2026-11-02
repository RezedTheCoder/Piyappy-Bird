import sys
import time
import random
import colorsys
import math
from pathlib import Path

import pygame


# ============================================================
# PATHS
# ============================================================

BASE_DIR = Path(__file__).resolve().parent
DATA_DIR = BASE_DIR / "data"


def asset(*parts):
    return str(DATA_DIR.joinpath(*parts))


# ============================================================
# CONSTANTS
# ============================================================

DISPLAY_WIDTH = 640
DISPLAY_HEIGHT = 480
HUD_HEIGHT = 90


# ============================================================
# UTILITY
# ============================================================

def clamp(value, minimum, maximum):
    return max(minimum, min(value, maximum))


def checkCollisions(
    a_x, a_y, a_width, a_height,
    b_x, b_y, b_width, b_height
):
    return (
        a_x + a_width > b_x
        and a_x < b_x + b_width
        and a_y + a_height > b_y
        and a_y < b_y + b_height
    )


# ============================================================
# BACKGROUND
# ============================================================

class Background:

    def __init__(self):
        self.uncoloredSprite = pygame.image.load(
            asset("gfx", "bg.png")
        ).convert()

        self.sprite = self.uncoloredSprite.copy()
        self.position = 0

    def setSprite(self, tint):
        copy = self.uncoloredSprite.copy()

        color = colorsys.hsv_to_rgb(
            tint,
            1,
            1
        )

        rgb = tuple(
            int(c * 255)
            for c in color
        )

        copy.fill(
            rgb,
            special_flags=pygame.BLEND_ADD
        )

        self.sprite = copy


# ============================================================
# BEAN
# ============================================================

class Bean:

    def __init__(self, golden=False, value=1, is_critical=False):
        self.sprite = pygame.image.load(
            asset("gfx", "bean.png")
        ).convert_alpha()

        self.position = pygame.Vector2(0, 0)
        self.golden = golden
        self.value = value
        self.is_critical = is_critical
        self.pulse = random.random() * math.tau


# ============================================================
# SHOP BUTTON
# ============================================================

class Button:

    def __init__(self):
        self.price = 5
        self.level = 1

        self.sprite = pygame.image.load(
            asset("gfx", "button.png")
        ).convert_alpha()

        self.typeIndicatorSprite = pygame.image.load(
            asset("gfx", "null_indicator.png")
        ).convert_alpha()


# ============================================================
# PLAYER
# ============================================================

class Player:

    def __init__(self):
        self.position = pygame.Vector2(295, 100)
        self.velocity = pygame.Vector2(10, 0)
        self.acceleration = 0.1

        self.rightSprite = pygame.image.load(
            asset("gfx", "player.png")
        ).convert_alpha()

        self.leftSprite = pygame.transform.flip(
            self.rightSprite,
            True,
            False
        )

        self.currentSprite = self.rightSprite


# ============================================================
# BOSS
# ============================================================

class Boss:

    def __init__(self):
        self.phase = 1

        original_sprite1 = pygame.image.load(
            asset("gfx", "boss_1.png")
        ).convert_alpha()

        original_sprite2 = pygame.image.load(
            asset("gfx", "boss_2.png")
        ).convert_alpha()

        BOSS_SIZE = 80

        self.sprite1 = self.scale_boss(original_sprite1, BOSS_SIZE)
        self.sprite2 = self.scale_boss(original_sprite2, 115)
        self.sprite = self.sprite1

        self.position = pygame.Vector2(320, -200)
        self.direction = 1

        self.max_health = 600
        self.health = 600
        self.speed = 3.5

        self.damage_cooldown = 0

        # ATTACK SYSTEM & TIMERS
        self.attack_timer = 110
        self.max_attack_timer = 110
        self.attack_warning_timer = 0
        self.attack_warning_max = 30

        self.attack_type = None
        self.next_attack_type = "dash"
        self.attack_index = 0

        self.charge_timer = 0
        self.charge_speed = 0
        self.is_charging = False

        self.shockwave_timer = 0
        self.shockwave_y = 0

        self.bean_storm_timer = 0
        self.bean_storm_spawn_timer = 0

        self.meteor_timer = 0
        self.meteors = []

        self.flash_timer = 0
        self.pulse = 0
        self.rage = False

        self.stun_timer = 0.0

        # Attack patterns
        self.phase_1_pattern = ["dash", "dash", "shockwave"]
        self.phase_2_pattern = ["dash", "meteor_rain", "shockwave", "bean_storm"]
        self.rage_pattern = ["dash", "meteor_rain", "shockwave", "bean_storm"]

    def scale_boss(self, sprite, maximum_size):
        width = sprite.get_width()
        height = sprite.get_height()

        scale = min(
            maximum_size / width,
            maximum_size / height
        )

        new_width = max(1, int(width * scale))
        new_height = max(1, int(height * scale))

        return pygame.transform.smoothscale(
            sprite,
            (new_width, new_height)
        )

    def start_phase_1(self, player):
        self.phase = 1
        self.sprite = self.sprite1

        self.max_health = 800
        self.health = self.max_health
        self.speed = 4.2

        self.direction = random.choice([-1, 1])
        self.position.x = DISPLAY_WIDTH / 2 - self.sprite.get_width() / 2
        self.position.y = player.position.y - 220

        self.damage_cooldown = 0
        self.attack_timer = 60
        self.max_attack_timer = 60
        self.attack_warning_timer = 0
        self.attack_type = None
        self.attack_index = 0
        self.next_attack_type = self.phase_1_pattern[0]

        self.charge_timer = 0
        self.charge_speed = 0
        self.is_charging = False
        self.shockwave_timer = 0
        self.shockwave_y = 0
        self.bean_storm_timer = 0
        self.bean_storm_spawn_timer = 0
        self.meteor_timer = 0
        self.meteors.clear()

        self.flash_timer = 0
        self.pulse = 0
        self.rage = False
        self.stun_timer = 0.0

    def start_phase_2(self, player):
        self.phase = 2
        self.sprite = self.sprite2

        # Increased Phase 2 HP from 1800 to 2600
        self.max_health = 2600
        self.health = self.max_health
        self.speed = 7.0

        self.direction = random.choice([-1, 1])
        self.position.x = DISPLAY_WIDTH / 2 - self.sprite.get_width() / 2
        self.position.y = player.position.y - 225

        self.damage_cooldown = 0
        self.attack_timer = 30
        self.max_attack_timer = 30
        self.attack_warning_timer = 0
        self.attack_type = None
        self.attack_index = 0
        self.next_attack_type = self.phase_2_pattern[0]

        self.charge_timer = 0
        self.charge_speed = 0
        self.is_charging = False
        self.shockwave_timer = 0
        self.shockwave_y = 0
        self.bean_storm_timer = 0
        self.bean_storm_spawn_timer = 0
        self.meteor_timer = 0
        self.meteors.clear()

        self.flash_timer = 0
        self.pulse = 0
        self.rage = False
        self.stun_timer = 0.0

    def get_pattern(self):
        if self.rage:
            return self.rage_pattern
        if self.phase == 2:
            return self.phase_2_pattern
        return self.phase_1_pattern

    def trigger_rage(self):
        if self.rage:
            return False

        self.rage = True
        self.attack_index = 0
        self.attack_timer = 8
        self.max_attack_timer = 8
        self.attack_warning_timer = 0
        
        # Increase HP dynamically during rage/final stage boost
        self.max_health += 600
        self.health += 600

        return True

    def start_next_attack(self, player):
        pattern = self.get_pattern()
        self.attack_type = pattern[self.attack_index % len(pattern)]
        self.attack_index += 1
        self.next_attack_type = pattern[self.attack_index % len(pattern)]

        warning = 28 if self.phase == 1 else 20
        if self.rage:
            warning = 14

        self.attack_warning_timer = warning
        self.attack_warning_max = warning

        if player.position.x > self.position.x:
            self.direction = 1
        else:
            self.direction = -1

    def activate_attack(self):
        if self.attack_type == "dash":
            self.is_charging = True
            self.charge_timer = 28 if self.phase == 1 else 36
            self.charge_speed = 14 if self.phase == 1 else 18
            if self.rage:
                self.charge_speed *= 1.4

        elif self.attack_type == "shockwave":
            self.shockwave_timer = 50 if not self.rage else 40
            self.shockwave_y = self.position.y + self.sprite.get_height() - 5

        elif self.attack_type == "bean_storm":
            self.bean_storm_timer = 60 if not self.rage else 45
            self.bean_storm_spawn_timer = 0

        elif self.attack_type == "meteor_rain":
            self.meteor_timer = 90
            self.meteors.clear()
            for _ in range(5 if not self.rage else 8):
                self.meteors.append({
                    "x": random.randint(30, DISPLAY_WIDTH - 30),
                    "y": self.position.y - 350,
                    "target_y": self.position.y + random.randint(100, 350),
                    "delay": random.randint(0, 35),
                    "active": False,
                    "radius": 22
                })

    def finish_attack(self):
        self.attack_type = None

        if self.rage:
            self.attack_timer = 15
        elif self.phase == 2:
            self.attack_timer = 32
        else:
            self.attack_timer = 65

        self.max_attack_timer = self.attack_timer

    def update(self, dt, player):
        self.pulse += 0.18 * dt

        if self.damage_cooldown > 0:
            self.damage_cooldown -= dt
        if self.flash_timer > 0:
            self.flash_timer -= dt

        if self.stun_timer > 0:
            self.stun_timer -= dt
            return

        if self.attack_warning_timer > 0:
            self.attack_warning_timer -= dt
            if player.position.x > self.position.x:
                self.direction = 1
            else:
                self.direction = -1

            if self.attack_warning_timer <= 0:
                self.activate_attack()

        if self.is_charging:
            self.position.x += self.direction * self.charge_speed * dt
            self.position.y += (player.position.y - 220 - self.position.y) * 0.18 * dt
            self.charge_timer -= dt

            if self.charge_timer <= 0:
                self.is_charging = False
                self.finish_attack()

        elif self.shockwave_timer > 0:
            self.shockwave_timer -= dt
            self.shockwave_y += 9.0 * dt * (1.25 if self.rage else 1.0)
            self.position.x += self.speed * self.direction * 0.45 * dt

            if self.shockwave_timer <= 0:
                self.finish_attack()

        elif self.bean_storm_timer > 0:
            self.bean_storm_timer -= dt
            self.position.x += self.speed * self.direction * 0.65 * dt * (1.35 if self.rage else 1.0)

            if self.bean_storm_timer <= 0:
                self.finish_attack()

        elif self.meteor_timer > 0:
            self.meteor_timer -= dt
            for m in self.meteors:
                if m["delay"] > 0:
                    m["delay"] -= dt
                else:
                    m["active"] = True
                    m["y"] += 12 * dt

            if self.meteor_timer <= 0:
                self.finish_attack()

        else:
            health_ratio = self.health / self.max_health if self.max_health > 0 else 0
            rage_multiplier = 1.0

            if health_ratio < 0.66:
                rage_multiplier = 1.25
            if health_ratio < 0.33:
                rage_multiplier = 1.50
            if self.phase == 2:
                rage_multiplier *= 1.25
            if self.rage:
                rage_multiplier *= 1.60

            self.position.x += self.speed * rage_multiplier * self.direction * dt

            if self.position.x <= 0:
                self.position.x = 0
                self.direction = 1

            right_edge = DISPLAY_WIDTH - self.sprite.get_width()
            if self.position.x >= right_edge:
                self.position.x = right_edge
                self.direction = -1

            target_y = player.position.y - (225 if self.phase == 2 else 220)
            difference = target_y - self.position.y
            follow_strength = 0.20 if self.phase == 2 else 0.14

            self.position.y += difference * follow_strength * dt

            self.attack_timer -= dt
            if self.attack_timer <= 0:
                self.start_next_attack(player)

        if self.position.x <= 0:
            self.position.x = 0
            self.direction = 1

        right_edge = DISPLAY_WIDTH - self.sprite.get_width()
        if self.position.x >= right_edge:
            self.position.x = right_edge
            self.direction = -1

    def hit(self, damage):
        self.health -= damage
        self.flash_timer = 8
        if self.health < 0:
            self.health = 0

    def is_dead(self):
        return self.health <= 0


# ============================================================
# SOUND HELPERS
# ============================================================

def play_sound(sound):
    if sound is not None:
        sound.play()


def load_sound(filename):
    try:
        return pygame.mixer.Sound(asset("sfx", filename))
    except pygame.error:
        return None


def play_music(filename, loop=-1):
    try:
        pygame.mixer.music.load(asset("sfx", filename))
        pygame.mixer.music.play(loop)
    except pygame.error:
        pass


def stop_music():
    try:
        pygame.mixer.music.stop()
    except pygame.error:
        pass


# ============================================================
# SHOP CREATION
# ============================================================

def create_buttons():
    buttons = [Button(), Button(), Button()]

    buttons[0].typeIndicatorSprite = pygame.image.load(
        asset("gfx", "flap_indicator.png")
    ).convert_alpha()
    buttons[0].price = 5

    buttons[1].typeIndicatorSprite = pygame.image.load(
        asset("gfx", "speed_indicator.png")
    ).convert_alpha()
    buttons[1].price = 5

    buttons[2].typeIndicatorSprite = pygame.image.load(
        asset("gfx", "beanup_indicator.png")
    ).convert_alpha()
    buttons[2].price = 5

    return buttons


# ============================================================
# BEAN CREATION
# ============================================================

def create_beans(player, count=12, display_width=DISPLAY_WIDTH):
    beans = [Bean() for _ in range(count)]
    spacing = max(95, int(DISPLAY_HEIGHT * 0.58))

    for i, bean in enumerate(beans):
        max_x = max(0, display_width - bean.sprite.get_width())
        bean.position.xy = (
            random.randrange(max_x + 1),
            player.position.y - 160 - i * spacing
        )

    return beans


def add_boss_bean(beans, x, y, golden=False, value=1, is_critical=False):
    bean = Bean(golden=golden, value=value, is_critical=is_critical)
    max_x = max(0, DISPLAY_WIDTH - bean.sprite.get_width())
    bean.position.xy = (clamp(x, 0, max_x), y)
    beans.append(bean)


def spawn_boss_bean_pattern(beans, player, pattern=None):
    if pattern is None:
        pattern = random.choice(["normal", "line", "zigzag", "cluster", "golden"])

    base_y = player.position.y - random.randint(280, 560)

    if pattern == "normal":
        for _ in range(random.randint(4, 7)):
            is_crit = random.random() < 0.15
            add_boss_bean(
                beans,
                random.randint(20, DISPLAY_WIDTH - 40),
                base_y + random.randint(-55, 55),
                is_critical=is_crit
            )

    elif pattern == "line":
        left = random.randint(30, 120)
        right = random.randint(360, DISPLAY_WIDTH - 30)

        for i in range(6):
            t = i / 5
            x = left + (right - left) * t
            add_boss_bean(beans, x, base_y)

    elif pattern == "zigzag":
        for i in range(7):
            x = 25 + i * 88
            y = base_y + (65 if i % 2 == 0 else -65)
            add_boss_bean(beans, x, y)

    elif pattern == "cluster":
        center_x = random.randint(80, DISPLAY_WIDTH - 80)
        for _ in range(9):
            add_boss_bean(
                beans,
                center_x + random.randint(-65, 65),
                base_y + random.randint(-65, 65)
            )

    elif pattern == "golden":
        add_boss_bean(
            beans,
            random.randint(70, DISPLAY_WIDTH - 90),
            base_y,
            golden=True,
            value=5
        )

        for _ in range(5):
            add_boss_bean(
                beans,
                random.randint(40, DISPLAY_WIDTH - 60),
                base_y + random.randint(-85, 85)
            )


# ============================================================
# PARTICLES & EFFECTS
# ============================================================

def spawn_particles(
    particles, x, y, count, color,
    speed_min=1.0, speed_max=5.0, size_min=2, size_max=7,
    life_min=20, life_max=55
):
    for _ in range(count):
        angle = random.uniform(0, math.tau)
        speed = random.uniform(speed_min, speed_max)

        particles.append({
            "x": x,
            "y": y,
            "vx": math.cos(angle) * speed,
            "vy": math.sin(angle) * speed,
            "life": random.uniform(life_min, life_max),
            "max_life": life_max,
            "size": random.randint(size_min, size_max),
            "color": color
        })


def spawn_ring(rings, x, y, start_radius=15, growth=7, life=25, color=(255, 70, 20)):
    rings.append({
        "x": x,
        "y": y,
        "radius": start_radius,
        "growth": growth,
        "life": life,
        "max_life": life,
        "color": color
    })


def update_effects(particles, rings, dt):
    for particle in particles[:]:
        particle["x"] += particle["vx"] * dt
        particle["y"] += particle["vy"] * dt
        particle["vy"] += 0.06 * dt
        particle["vx"] *= 0.995
        particle["life"] -= dt

        if particle["life"] <= 0:
            particles.remove(particle)

    for ring in rings[:]:
        ring["radius"] += ring["growth"] * dt
        ring["life"] -= dt

        if ring["life"] <= 0:
            rings.remove(ring)


def draw_effects(surface, particles, rings, cam_offset):
    for particle in particles:
        life_ratio = clamp(particle["life"] / particle["max_life"], 0, 1)
        alpha = int(255 * life_ratio)
        size = max(1, int(particle["size"] * life_ratio + 1))

        particle_surface = pygame.Surface(
            (size * 2 + 4, size * 2 + 4),
            pygame.SRCALPHA
        )

        pygame.draw.circle(
            particle_surface,
            (*particle["color"], alpha),
            (size + 2, size + 2),
            size
        )

        surface.blit(
            particle_surface,
            (
                int(particle["x"] - size - 2),
                int(particle["y"] + cam_offset - size - 2)
            )
        )

    for ring in rings:
        ratio = clamp(ring["life"] / ring["max_life"], 0, 1)
        alpha = int(220 * ratio)

        ring_surface = pygame.Surface(
            surface.get_size(),
            pygame.SRCALPHA
        )

        pygame.draw.circle(
            ring_surface,
            (*ring["color"], alpha),
            (int(ring["x"]), int(ring["y"] + cam_offset)),
            max(1, int(ring["radius"])),
            3
        )

        surface.blit(ring_surface, (0, 0))


# ============================================================
# MAIN
# ============================================================

def main():
    pygame.init()

    try:
        pygame.mixer.init()
    except pygame.error:
        pass

    DISPLAY = pygame.display.set_mode((DISPLAY_WIDTH, DISPLAY_HEIGHT))
    pygame.display.set_caption("Flappuccino")

    shop = pygame.image.load(asset("gfx", "shop.png")).convert_alpha()
    shop_bg = pygame.image.load(asset("gfx", "shop_bg.png")).convert_alpha()
    retry_button = pygame.image.load(asset("gfx", "retry_button.png")).convert_alpha()
    logo = pygame.image.load(asset("gfx", "logo.png")).convert_alpha()

    title_bg = pygame.image.load(asset("gfx", "bg.png")).convert()
    title_bg.fill((255, 31, 0), special_flags=pygame.BLEND_ADD)
    shadow = pygame.image.load(asset("gfx", "shadow.png")).convert_alpha()

    font = pygame.font.Font(asset("fonts", "font.otf"), 100)
    font_small = pygame.font.Font(asset("fonts", "font.otf"), 32)
    font_20 = pygame.font.Font(asset("fonts", "font.otf"), 20)

    # SOUND EFFECTS
    flapfx = load_sound("flap.wav")
    upgradefx = load_sound("upgrade.wav")
    beanfx = load_sound("bean.wav")
    deadfx = load_sound("dead.wav")

    phase1fx = load_sound("phase1.wav")
    phase2fx = load_sound("phase2.wav")
    bossAttackfx = load_sound("boss_attack.wav")
    ragefx = load_sound("rage.wav")
    victoryfx = load_sound("victory.wav")

    WHITE = (255, 255, 255)

    player = Player()
    beans = create_beans(player, count=12)
    buttons = create_buttons()

    bg = [Background(), Background(), Background()]
    boss = Boss()

    beanCount = 0
    startingHeight = player.position.y
    height = 0
    max_health = 100.0
    health = 100.0

    # STATS & CAPS
    NORMAL_START_FLAP = 4.2
    NORMAL_START_SPEED = 10.0
    NORMAL_MAX_FLAP = 30.0
    NORMAL_MAX_SPEED = 30.0

    flapForce = NORMAL_START_FLAP
    beanMultiplier = 20

    BOSS_START_FLAP = 3.0
    BOSS_START_SPEED = 6.0
    BOSS_MAX_FLAP = 25.0
    BOSS_MAX_SPEED = 20.0

    # Adjusted Bean Spawn Constants per Phase
    BOSS_PHASE_1_MAX_BEANS = 55  # Slightly increased spawn in phase 1
    BOSS_PHASE_2_MAX_BEANS = 30  # Slightly decreased spawn in phase 2

    BOSS_MAX_FLAP_LEVEL = 20
    BOSS_MAX_SPEED_LEVEL = 20
    BOSS_MAX_BEAN_LEVEL = 20

    dead = False
    boss_fight = False
    boss_defeated = False
    game_finished = False

    boss_phase_message_timer = 0
    final_message_timer = 0

    screen_shake = 0.0
    screen_flash = 0.0
    boss_hit_flash = 0.0
    boss_warning_pulse = 0.0
    victory_timer = 0.0

    phase_transition = False
    phase_transition_timer = 0.0
    player_invuln_timer = 0.0

    combo = 0
    combo_timer = 0.0
    combo_flash_timer = 0.0

    boss_rage_triggered = False
    boss_rage_message_timer = 0.0

    victory_sequence = False
    victory_sequence_timer = 0.0

    no_hit_bean_streak = 0
    stun_banner_timer = 0.0
    crit_banner_timer = 0.0

    intro_card_timer = 0.0
    intro_card_title = ""
    intro_card_subtitle = ""

    stats_time = 0.0
    stats_beans = 0
    stats_best_combo = 0
    stats_damage_taken = 0
    stats_golden_beans = 0

    particles = []
    rings = []

    last_time = time.perf_counter()

    play_sound(flapfx)
    splashScreenTimer = 0.0

    while splashScreenTimer < 100:
        now = time.perf_counter()
        dt = (now - last_time) * 60
        last_time = now
        dt = min(dt, 5)

        for event in pygame.event.get():
            if event.type == pygame.QUIT:
                pygame.quit()
                return

        DISPLAY.fill((231, 205, 183))
        startMessage = font_small.render("POLYMARS", True, (171, 145, 123))

        DISPLAY.blit(
            startMessage,
            (
                DISPLAY.get_width() / 2 - startMessage.get_width() / 2,
                DISPLAY.get_height() / 2 - startMessage.get_height() / 2
            )
        )

        pygame.display.flip()
        splashScreenTimer += dt
        pygame.time.delay(10)

    titleScreen = True
    play_sound(flapfx)

    while titleScreen:
        now = time.perf_counter()
        dt = (now - last_time) * 60
        last_time = now
        dt = min(dt, 5)

        clicked = False
        mouseX, mouseY = pygame.mouse.get_pos()

        for event in pygame.event.get():
            if event.type == pygame.QUIT:
                pygame.quit()
                return

            if event.type == pygame.MOUSEBUTTONDOWN and event.button == 1:
                clicked = True

        start_x = DISPLAY.get_width() / 2 - retry_button.get_width() / 2
        start_y = 288

        if clicked and checkCollisions(
            mouseX, mouseY, 3, 3,
            start_x, start_y, retry_button.get_width(), retry_button.get_height()
        ):
            play_sound(upgradefx)
            titleScreen = False

        DISPLAY.fill(WHITE)
        DISPLAY.blit(title_bg, (0, 0))
        DISPLAY.blit(shadow, (0, 0))

        logo_y = (
            DISPLAY.get_height() / 2
            - logo.get_height() / 2
            + math.sin(time.time() * 5) * 5
            - 25
        )

        DISPLAY.blit(logo, (DISPLAY.get_width() / 2 - logo.get_width() / 2, logo_y))
        DISPLAY.blit(retry_button, (start_x, start_y))

        startMessage = font_small.render("START", True, (0, 0, 0))
        DISPLAY.blit(
            startMessage,
            (DISPLAY.get_width() / 2 - startMessage.get_width() / 2, 292)
        )

        pygame.display.flip()
        pygame.time.delay(10)

    running = True

    while running:
        now = time.perf_counter()
        dt = (now - last_time) * 60
        last_time = now
        dt = min(dt, 5)

        mouseX, mouseY = pygame.mouse.get_pos()

        jump = False
        clicked = False

        if screen_shake > 0:
            screen_shake = max(0, screen_shake - 0.65 * dt)
        if screen_flash > 0:
            screen_flash = max(0, screen_flash - dt)
        if boss_hit_flash > 0:
            boss_hit_flash = max(0, boss_hit_flash - dt)
        if boss_warning_pulse > 0:
            boss_warning_pulse = max(0, boss_warning_pulse - dt)
        if player_invuln_timer > 0:
            player_invuln_timer = max(0, player_invuln_timer - dt)

        if stun_banner_timer > 0:
            stun_banner_timer = max(0, stun_banner_timer - dt)
        if crit_banner_timer > 0:
            crit_banner_timer = max(0, crit_banner_timer - dt)
        if intro_card_timer > 0:
            intro_card_timer = max(0, intro_card_timer - dt)

        if combo_timer > 0:
            combo_timer -= dt
            if combo_timer <= 0:
                combo = 0

        if combo_flash_timer > 0:
            combo_flash_timer = max(0, combo_flash_timer - dt)
        if boss_rage_message_timer > 0:
            boss_rage_message_timer = max(0, boss_rage_message_timer - dt)

        if boss_fight and not dead and not game_finished:
            stats_time += (dt / 60.0)

        for event in pygame.event.get():
            if event.type == pygame.QUIT:
                running = False
            elif event.type == pygame.KEYDOWN:
                if event.key == pygame.K_ESCAPE:
                    running = False
                elif event.key == pygame.K_SPACE:
                    jump = True
            elif event.type == pygame.MOUSEBUTTONDOWN:
                if event.button == 1:
                    clicked = True

        if game_finished:
            DISPLAY.fill((10, 10, 12))

            if stats_damage_taken == 0 and stats_best_combo >= 15:
                rank = "S"
                rank_color = (255, 215, 0)
            elif stats_damage_taken < 100:
                rank = "A"
                rank_color = (0, 255, 120)
            elif stats_damage_taken < 250:
                rank = "B"
                rank_color = (100, 180, 255)
            elif stats_damage_taken < 450:
                rank = "C"
                rank_color = (255, 165, 0)
            else:
                rank = "D"
                rank_color = (220, 50, 50)

            title_txt = font_small.render("BOSS DEFEATED!", True, (255, 215, 0))
            DISPLAY.blit(title_txt, (DISPLAY_WIDTH / 2 - title_txt.get_width() / 2, 30))

            m, s = divmod(int(stats_time), 60)
            time_str = f"{m:02d}:{s:02d}"

            s1 = font_20.render(f"Time: {time_str}", True, WHITE)
            s2 = font_20.render(f"Beans Collected: {stats_beans}", True, WHITE)
            s3 = font_20.render(f"Best Combo: x{stats_best_combo}", True, WHITE)
            s4 = font_20.render(f"Damage Taken: {stats_damage_taken}", True, WHITE)
            s5 = font_20.render(f"Golden Beans: {stats_golden_beans}", True, WHITE)
            s_rank = font_small.render(f"RANK: {rank}", True, rank_color)

            DISPLAY.blit(s1, (DISPLAY_WIDTH / 2 - 140, 90))
            DISPLAY.blit(s2, (DISPLAY_WIDTH / 2 - 140, 120))
            DISPLAY.blit(s3, (DISPLAY_WIDTH / 2 - 140, 150))
            DISPLAY.blit(s4, (DISPLAY_WIDTH / 2 - 140, 180))
            DISPLAY.blit(s5, (DISPLAY_WIDTH / 2 - 140, 210))
            DISPLAY.blit(s_rank, (DISPLAY_WIDTH / 2 - s_rank.get_width() / 2, 250))

            pygame.draw.line(DISPLAY, (60, 60, 60), (40, 310), (DISPLAY_WIDTH - 40, 310), 2)

            troll_text = font_small.render("I JUST WASTED YOUR TIME", True, (255, 255, 255))
            DISPLAY.blit(troll_text, (DISPLAY_WIDTH / 2 - troll_text.get_width() / 2, 345))

            pygame.display.flip()
            victory_timer += dt

            if victory_timer >= 260:
                running = False

            pygame.time.delay(10)
            continue

        if clicked and mouseY < DISPLAY.get_height() - HUD_HEIGHT:
            jump = True

        player_height = player.currentSprite.get_height()
        camOffset = (
            -player.position.y
            + DISPLAY.get_height() / 2
            - player_height / 2
        )

        WORLD = pygame.Surface((DISPLAY_WIDTH, DISPLAY_HEIGHT), pygame.SRCALPHA)
        WORLD.fill(WHITE)

        tint = ((player.position.y / 50) % 100) / 100

        for background in bg:
            background.setSprite(tint)
            WORLD.blit(background.sprite, (0, background.position + camOffset))

        height = round(-(player.position.y - startingHeight) / DISPLAY.get_height())

        if (
            height >= 100
            and not boss_fight
            and not boss_defeated
        ):
            boss_fight = True
            boss_defeated = False

            boss.start_phase_1(player)
            play_music("phase1.wav")

            flapForce = BOSS_START_FLAP
            player.velocity.x = BOSS_START_SPEED
            buttons = create_buttons()

            health = max_health

            # Slightly increased Phase 1 bean count
            beans = create_beans(player, count=BOSS_PHASE_1_MAX_BEANS)

            boss_phase_message_timer = 180
            screen_shake = 12
            screen_flash = 18
            boss_warning_pulse = 30

            intro_card_timer = 120
            intro_card_title = "LEVEL 100"
            intro_card_subtitle = "PHASE 1: THE HUNTER"

            spawn_particles(
                particles, DISPLAY_WIDTH / 2, boss.position.y,
                45, (255, 70, 20), 1, 6, 2, 8, 20, 70
            )
            spawn_ring(
                rings, DISPLAY_WIDTH / 2, boss.position.y,
                20, 8, 30, (255, 40, 20)
            )

            phase_transition = False
            phase_transition_timer = 0
            player_invuln_timer = 0
            combo = 0
            combo_timer = 0
            combo_flash_timer = 0
            boss_rage_triggered = False
            boss_rage_message_timer = 0
            victory_sequence = False
            victory_sequence_timer = 0
            no_hit_bean_streak = 0

            stats_time = 0.0
            stats_beans = 0
            stats_best_combo = 0
            stats_damage_taken = 0
            stats_golden_beans = 0

        color = colorsys.hsv_to_rgb(tint, 0.5, 0.5)
        currentHeightMarker = font.render(
            str(height),
            True,
            tuple(int(c * 255) for c in color)
        )

        marker_y = (
            camOffset
            + round((player.position.y - startingHeight) / DISPLAY.get_height()) * DISPLAY.get_height()
            + player_height
            - 40
        )

        WORLD.blit(
            currentHeightMarker,
            (DISPLAY.get_width() / 2 - currentHeightMarker.get_width() / 2, marker_y)
        )

        for bean in beans:
            WORLD.blit(bean.sprite, (bean.position.x, bean.position.y + camOffset))

        player_angle = clamp(player.velocity.y, -10, 5) * (-5 if player.velocity.x >= 0 else 5)
        rotated_player = pygame.transform.rotate(player.currentSprite, player_angle)

        if player_invuln_timer <= 0 or int(player_invuln_timer * 4) % 2 == 0:
            WORLD.blit(
                rotated_player,
                (player.position.x, player.position.y + camOffset)
            )

        if (
            boss_fight
            and not boss_defeated
            and not phase_transition
            and not victory_sequence
        ):
            boss_center_x = boss.position.x + boss.sprite.get_width() / 2
            boss_center_y = boss.position.y + boss.sprite.get_height() / 2

            aura = pygame.Surface(DISPLAY.get_size(), pygame.SRCALPHA)
            aura_radius = int(48 + math.sin(boss.pulse) * 8 + (12 if boss.phase == 2 else 0))
            aura_alpha = 55 if boss.phase == 1 else 85

            pygame.draw.circle(
                aura,
                (255, 25, 15, aura_alpha),
                (int(boss_center_x), int(boss_center_y + camOffset)),
                aura_radius,
                6
            )
            WORLD.blit(aura, (0, 0))

            boss_sprite = boss.sprite
            if boss.flash_timer > 0:
                boss_sprite = boss.sprite.copy()
                boss_sprite.fill((255, 255, 255, 220), special_flags=pygame.BLEND_RGBA_ADD)

            WORLD.blit(boss_sprite, (boss.position.x, boss.position.y + camOffset))

            if boss.is_charging:
                for trail in range(5):
                    trail_alpha = max(10, 90 - trail * 15)
                    trail_surface = pygame.Surface(boss.sprite.get_size(), pygame.SRCALPHA)
                    trail_surface.blit(boss_sprite, (0, 0))
                    trail_surface.set_alpha(trail_alpha)
                    trail_x = boss.position.x - boss.direction * (trail + 1) * 14
                    trail_y = boss.position.y + camOffset
                    WORLD.blit(trail_surface, (trail_x, trail_y))

            if boss.shockwave_timer > 0:
                wave_y = boss.shockwave_y + camOffset
                pygame.draw.rect(WORLD, (255, 35, 15), (0, int(wave_y - 11), DISPLAY_WIDTH, 22))
                pygame.draw.line(WORLD, (255, 225, 100), (0, int(wave_y)), (DISPLAY_WIDTH, int(wave_y)), 4)

            if boss.meteor_timer > 0:
                for m in boss.meteors:
                    if m["active"]:
                        pygame.draw.circle(WORLD, (255, 90, 20), (int(m["x"]), int(m["y"] + camOffset)), m["radius"])
                    else:
                        pygame.draw.circle(WORLD, (255, 40, 20), (int(m["x"]), int(m["target_y"] + camOffset)), m["radius"], 2)

            boss_bar_width = 400
            boss_bar_height = 22
            boss_bar_x = DISPLAY.get_width() / 2 - boss_bar_width / 2
            boss_bar_y = 15

            pygame.draw.rect(WORLD, (35, 35, 35), (boss_bar_x, boss_bar_y, boss_bar_width, boss_bar_height))
            boss_health_width = int(boss_bar_width * boss.health / boss.max_health)
            pygame.draw.rect(WORLD, (200, 0, 0), (boss_bar_x, boss_bar_y, boss_health_width, boss_bar_height))

            rage_indicator_x = boss_bar_x + boss_bar_width * 0.25
            pygame.draw.line(WORLD, (255, 50, 50), (int(rage_indicator_x), boss_bar_y - 4), (int(rage_indicator_x), boss_bar_y + boss_bar_height + 4), 3)

            for marker_ratio in (0.66, 0.33):
                marker_x = boss_bar_x + boss_bar_width * marker_ratio
                pygame.draw.line(WORLD, (255, 180, 80), (int(marker_x), boss_bar_y), (int(marker_x), boss_bar_y + boss_bar_height), 2)

            pygame.draw.rect(WORLD, (255, 255, 255), (boss_bar_x, boss_bar_y, boss_bar_width, boss_bar_height), 2)

            phase_text = font_20.render("BOSS PHASE " + str(boss.phase), True, (255, 255, 255))
            WORLD.blit(phase_text, (DISPLAY.get_width() / 2 - phase_text.get_width() / 2, 40))

            cd_width = 200
            cd_height = 8
            cd_x = DISPLAY_WIDTH / 2 - cd_width / 2
            cd_y = 65

            pygame.draw.rect(WORLD, (40, 40, 40), (cd_x, cd_y, cd_width, cd_height))

            if boss.attack_warning_timer > 0:
                fill_ratio = boss.attack_warning_timer / boss.attack_warning_max
                pygame.draw.rect(WORLD, (255, 40, 40), (cd_x, cd_y, int(cd_width * fill_ratio), cd_height))
            else:
                fill_ratio = max(0, boss.attack_timer / boss.max_attack_timer)
                pygame.draw.rect(WORLD, (255, 200, 50), (cd_x, cd_y, int(cd_width * fill_ratio), cd_height))

            next_atk_name = boss.next_attack_type.replace("_", " ").upper()
            next_txt = font_20.render(f"NEXT: {next_atk_name}", True, (240, 240, 240))
            WORLD.blit(next_txt, (DISPLAY_WIDTH / 2 - next_txt.get_width() / 2, 76))

            tip_str = ""
            if boss.attack_warning_timer > 0:
                if boss.attack_type == "dash":
                    tip_str = "DODGE SIDEWAYS!"
                elif boss.attack_type == "shockwave":
                    tip_str = "FLAP HIGH!"
                elif boss.attack_type == "bean_storm":
                    tip_str = "WEAVE BETWEEN BEANS!"
                elif boss.attack_type == "meteor_rain":
                    tip_str = "WATCH TARGET RINGS!"

            if tip_str:
                tip_txt = font_20.render(tip_str, True, (255, 230, 80))
                WORLD.blit(tip_txt, (DISPLAY_WIDTH / 2 - tip_txt.get_width() / 2, 98))

        draw_effects(WORLD, particles, rings, camOffset)

        shake_x = 0
        shake_y = 0
        if screen_shake > 0:
            shake_amount = int(screen_shake)
            shake_x = random.randint(-shake_amount, shake_amount)
            shake_y = random.randint(-shake_amount, shake_amount)

        DISPLAY.fill(WHITE)
        DISPLAY.blit(WORLD, (shake_x, shake_y))

        if boss_fight and not boss_defeated:
            overlay = pygame.Surface(DISPLAY.get_size(), pygame.SRCALPHA)
            pulse_alpha = int(24 + math.sin(time.time() * 5) * 10)

            if boss.phase == 1:
                overlay.fill((100, 0, 0, max(10, pulse_alpha)))
            else:
                overlay.fill((180, 0, 0, max(15, pulse_alpha + 15)))

            DISPLAY.blit(overlay, (0, 0))

        if stun_banner_timer > 0:
            stun_t = font_small.render("BOSS STUNNED!", True, (255, 215, 0))
            DISPLAY.blit(stun_t, (DISPLAY_WIDTH / 2 - stun_t.get_width() / 2, 125))

        if crit_banner_timer > 0:
            crit_t = font_20.render("CRITICAL HIT! x2 DAMAGE", True, (255, 100, 50))
            DISPLAY.blit(crit_t, (DISPLAY_WIDTH / 2 - crit_t.get_width() / 2, 155))

        if intro_card_timer > 0:
            card_surface = pygame.Surface(DISPLAY.get_size(), pygame.SRCALPHA)
            card_surface.fill((0, 0, 0, 180))
            t1 = font.render(intro_card_title, True, (255, 215, 0))
            t2 = font_small.render(intro_card_subtitle, True, (255, 255, 255))

            card_surface.blit(t1, (DISPLAY_WIDTH / 2 - t1.get_width() / 2, 140))
            card_surface.blit(t2, (DISPLAY_WIDTH / 2 - t2.get_width() / 2, 240))
            DISPLAY.blit(card_surface, (0, 0))

        if boss_fight and combo >= 2 and combo_timer > 0:
            combo_text = font_small.render("COMBO x" + str(combo), True, (255, 220, 70))
            DISPLAY.blit(combo_text, (DISPLAY_WIDTH / 2 - combo_text.get_width() / 2, 180))

            streak_desc = ""
            if combo >= 20:
                streak_desc = "COMBO x20: MASSIVE DAMAGE!"
            elif combo >= 10:
                streak_desc = "COMBO x10: +25 HP RESTORED!"
            elif combo >= 5:
                streak_desc = "COMBO x5: +10 HP RESTORED!"

            if streak_desc:
                bonus_text = font_20.render(streak_desc, True, (255, 245, 150))
                DISPLAY.blit(bonus_text, (DISPLAY_WIDTH / 2 - bonus_text.get_width() / 2, 212))

        if boss_fight and boss_rage_message_timer > 0:
            rage_text = font_small.render("BOSS ENRAGED!", True, (255, 45, 20))
            DISPLAY.blit(rage_text, (DISPLAY_WIDTH / 2 - rage_text.get_width() / 2, 245))

        if phase_transition:
            dark = pygame.Surface(DISPLAY.get_size(), pygame.SRCALPHA)
            ratio = clamp(phase_transition_timer / 70, 0, 1)
            alpha = int(100 + 100 * (1 - abs(ratio - 0.5) * 2))
            dark.fill((45, 0, 0, clamp(alpha, 90, 220)))
            DISPLAY.blit(dark, (0, 0))

            phase2_text = font.render("PHASE 2", True, (255, 60, 25))
            phase2_scale = 1 + 0.08 * math.sin(time.time() * 10)
            phase2_scaled = pygame.transform.smoothscale(
                phase2_text,
                (int(phase2_text.get_width() * phase2_scale), int(phase2_text.get_height() * phase2_scale))
            )

            DISPLAY.blit(
                phase2_scaled,
                (DISPLAY_WIDTH / 2 - phase2_scaled.get_width() / 2, DISPLAY_HEIGHT / 2 - phase2_scaled.get_height() / 2)
            )

        if player_invuln_timer > 0:
            invuln_text = font_20.render("INVULNERABLE", True, (255, 230, 80))
            DISPLAY.blit(invuln_text, (20, 370))

        if victory_sequence:
            victory_alpha = int(clamp(victory_sequence_timer * 2, 0, 130))
            victory_overlay = pygame.Surface(DISPLAY.get_size(), pygame.SRCALPHA)
            victory_overlay.fill((255, 80, 10, victory_alpha))
            DISPLAY.blit(victory_overlay, (0, 0))

            if victory_sequence_timer >= 18:
                victory_text = font_small.render("BOSS DEFEATED!", True, (255, 235, 80))
                pulse = 1 + 0.08 * math.sin(time.time() * 8)
                victory_scaled = pygame.transform.smoothscale(
                    victory_text,
                    (int(victory_text.get_width() * pulse), int(victory_text.get_height() * pulse))
                )
                DISPLAY.blit(victory_scaled, (DISPLAY_WIDTH / 2 - victory_scaled.get_width() / 2, 250))

            if victory_sequence_timer >= 90:
                released_text = font_20.render("THE BEANS HAVE BEEN RELEASED", True, (255, 245, 180))
                DISPLAY.blit(released_text, (DISPLAY_WIDTH / 2 - released_text.get_width() / 2, 295))

        DISPLAY.blit(shop_bg, (0, 0))

        health_width = max(0, int(150 * health / max_health))
        pygame.draw.rect(DISPLAY, (81, 48, 20), (21, 437, health_width, 25))
        DISPLAY.blit(shop, (0, 0))

        hp_txt = font_20.render(f"{int(health)}/{int(max_health)}", True, WHITE)
        DISPLAY.blit(hp_txt, (35, 439))

        for index, button in enumerate(buttons):
            button_x = 220 + index * 125
            DISPLAY.blit(button.sprite, (button_x, 393))

            priceDisplay = font_small.render(str(button.price), True, (0, 0, 0))
            DISPLAY.blit(priceDisplay, (262 + index * 125, 408))

            levelDisplay = font_20.render("Lvl. " + str(button.level), True, (200, 200, 200))
            DISPLAY.blit(levelDisplay, (234 + index * 125, 441))

            DISPLAY.blit(button.typeIndicatorSprite, (202 + index * 125, 377))

        beanCountDisplay = font_small.render(str(beanCount).zfill(7), True, (0, 0, 0))
        DISPLAY.blit(beanCountDisplay, (72, 394))

        if dead:
            DISPLAY.blit(retry_button, (4, 4))
            deathMessage = font_small.render("RETRY", True, (0, 0, 0))
            DISPLAY.blit(deathMessage, (24, 8))

        if not dead and not boss_fight:
            player.position.x += player.velocity.x * dt

            if player.position.x + player.currentSprite.get_width() > DISPLAY.get_width():
                player.position.x = DISPLAY.get_width() - player.currentSprite.get_width()
                player.velocity.x = -abs(player.velocity.x)
                player.currentSprite = player.leftSprite
            elif player.position.x < 0:
                player.position.x = 0
                player.velocity.x = abs(player.velocity.x)
                player.currentSprite = player.rightSprite

            if jump:
                player.velocity.y = -flapForce
                play_sound(flapfx)

            player.position.y += player.velocity.y * dt
            player.velocity.y = clamp(player.velocity.y + player.acceleration * dt, -99999999999, 50)
            health -= 0.2 * dt

            if health <= 0:
                health = 0
                dead = True
                stop_music()
                play_sound(deadfx)

        def damage_player(amount):
            nonlocal health, dead, player_invuln_timer, no_hit_bean_streak, stats_damage_taken

            if player_invuln_timer > 0:
                return False

            health -= amount
            stats_damage_taken += int(amount)
            player_invuln_timer = 60
            no_hit_bean_streak = 0

            spawn_particles(
                particles,
                player.position.x + player.currentSprite.get_width() / 2,
                player.position.y + player.currentSprite.get_height() / 2,
                20, (255, 220, 110), 1, 7, 2, 8, 18, 50
            )

            spawn_ring(
                rings,
                player.position.x + player.currentSprite.get_width() / 2,
                player.position.y + player.currentSprite.get_height() / 2,
                12, 8, 22, (255, 70, 20)
            )

            if health <= 0:
                health = 0
                dead = True
                stop_music()
                play_sound(deadfx)

            return True

        if (
            boss_fight
            and not dead
            and not game_finished
            and not phase_transition
            and not victory_sequence
        ):
            player.position.x += player.velocity.x * dt

            if player.position.x + player.currentSprite.get_width() >= DISPLAY_WIDTH:
                player.position.x = DISPLAY_WIDTH - player.currentSprite.get_width()
                player.velocity.x = -abs(player.velocity.x)
                player.currentSprite = player.leftSprite
            elif player.position.x <= 0:
                player.position.x = 0
                player.velocity.x = abs(player.velocity.x)
                player.currentSprite = player.rightSprite

            if jump:
                player.velocity.y = -flapForce
                play_sound(flapfx)
                spawn_particles(
                    particles,
                    player.position.x + player.currentSprite.get_width() / 2,
                    player.position.y + player.currentSprite.get_height() / 2,
                    5, (255, 230, 120), 0.5, 2.5, 2, 4, 10, 25
                )

            player.position.y += player.velocity.y * dt
            player.velocity.y = clamp(player.velocity.y + player.acceleration * dt, -99999999999, 50)
            health -= 0.12 * dt

            if health <= 0:
                health = 0
                dead = True
                stop_music()
                play_sound(deadfx)

            boss.update(dt, player)

            if boss.meteor_timer > 0 and player_invuln_timer <= 0:
                for m in boss.meteors:
                    if m["active"]:
                        if checkCollisions(
                            player.position.x, player.position.y,
                            player.currentSprite.get_width(), player.currentSprite.get_height(),
                            m["x"] - m["radius"], m["y"] - m["radius"],
                            m["radius"] * 2, m["radius"] * 2
                        ):
                            damage_player(35)

            if boss.attack_warning_timer > 0:
                boss_warning_pulse = 10
                if random.random() < 0.55:
                    spawn_particles(
                        particles,
                        boss.position.x + boss.sprite.get_width() / 2,
                        boss.position.y + boss.sprite.get_height() / 2,
                        2 if boss.phase == 1 else 3, (255, 30, 10), 1, 4, 2, 6, 8, 20
                    )

            if boss.is_charging and random.random() < 0.85:
                spawn_particles(
                    particles,
                    boss.position.x + boss.sprite.get_width() / 2,
                    boss.position.y + boss.sprite.get_height() / 2,
                    3, (255, 100, 20), 1, 5, 2, 7, 8, 22
                )

            if boss.bean_storm_timer > 0:
                boss.bean_storm_spawn_timer -= dt
                if boss.bean_storm_spawn_timer <= 0:
                    spawn_boss_bean_pattern(beans, player, random.choice(["normal", "zigzag", "cluster", "golden"]))
                    boss.bean_storm_spawn_timer = 11 if not boss.rage else 7

            if boss.shockwave_timer > 0 and player_invuln_timer <= 0:
                wave_y = boss.shockwave_y
                wave_top = wave_y - 20
                wave_bottom = wave_y + 20
                player_top = player.position.y
                player_bottom = player.position.y + player.currentSprite.get_height()

                if player_bottom > wave_top and player_top < wave_bottom:
                    if damage_player(24 if boss.phase == 1 else 30):
                        player.velocity.y = -flapForce * 0.45
                        screen_shake = max(screen_shake, 12)

            if (
                boss.damage_cooldown <= 0
                and player_invuln_timer <= 0
                and checkCollisions(
                    player.position.x, player.position.y,
                    player.currentSprite.get_width(), player.currentSprite.get_height(),
                    boss.position.x, boss.position.y,
                    boss.sprite.get_width(), boss.sprite.get_height()
                )
            ):
                damage = 30 if boss.phase == 1 else 40
                if boss.is_charging:
                    damage += 15

                if damage_player(damage):
                    boss.damage_cooldown = 40 if boss.rage else 48
                    player.velocity.y = -flapForce
                    screen_shake = max(screen_shake, 18 if boss.is_charging else 10)
                    screen_flash = max(screen_flash, 10)
                    play_sound(deadfx)

            if (
                boss.phase == 2
                and boss.health <= boss.max_health * 0.25
                and not boss_rage_triggered
            ):
                boss_rage_triggered = True
                boss.trigger_rage()

                boss_rage_message_timer = 120
                screen_shake = 18
                screen_flash = 20

                intro_card_timer = 90
                intro_card_title = "FINAL RAGE"
                intro_card_subtitle = "THE DESTROYER IS UNLEASHED!"

                play_sound(ragefx if ragefx is not None else deadfx)
                spawn_particles(
                    particles,
                    boss.position.x + boss.sprite.get_width() / 2,
                    boss.position.y + boss.sprite.get_height() / 2,
                    80, (255, 30, 10), 1, 9, 2, 10, 18, 75
                )
                spawn_ring(
                    rings,
                    boss.position.x + boss.sprite.get_width() / 2,
                    boss.position.y + boss.sprite.get_height() / 2,
                    20, 13, 60, (255, 40, 20)
                )

            if boss.is_dead():
                if boss.phase == 1:
                    phase_transition = True
                    phase_transition_timer = 70

                    boss.attack_type = None
                    boss.attack_warning_timer = 0
                    boss.is_charging = False
                    boss.charge_timer = 0
                    boss.shockwave_timer = 0
                    boss.bean_storm_timer = 0

                    health = max_health
                    combo = 0
                    combo_timer = 0

                    screen_shake = 28
                    screen_flash = 30

                    spawn_particles(
                        particles,
                        boss.position.x + boss.sprite.get_width() / 2,
                        boss.position.y + boss.sprite.get_height() / 2,
                        100, (255, 70, 10), 1, 10, 3, 12, 20, 90
                    )
                    spawn_ring(
                        rings,
                        boss.position.x + boss.sprite.get_width() / 2,
                        boss.position.y + boss.sprite.get_height() / 2,
                        25, 12, 50, (255, 180, 30)
                    )

                    play_music("phase2.wav")

                elif boss.phase == 2:
                    boss_fight = False
                    boss_defeated = True

                    victory_sequence = True
                    victory_sequence_timer = 0

                    screen_shake = 32
                    screen_flash = 45

                    stop_music()
                    play_sound(victoryfx if victoryfx is not None else upgradefx)
                    spawn_particles(
                        particles,
                        boss.position.x + boss.sprite.get_width() / 2,
                        boss.position.y + boss.sprite.get_height() / 2,
                        150, (255, 80, 20), 1, 12, 3, 13, 25, 100
                    )
                    spawn_ring(
                        rings,
                        boss.position.x + boss.sprite.get_width() / 2,
                        boss.position.y + boss.sprite.get_height() / 2,
                        35, 14, 70, (255, 210, 70)
                    )

                    for _ in range(20):
                        add_boss_bean(
                            beans,
                            random.randint(20, DISPLAY_WIDTH - 40),
                            player.position.y - random.randint(50, 450),
                            golden=(random.random() < 0.20),
                            value=5
                        )

        if phase_transition and not dead:
            phase_transition_timer -= dt
            health = min(max_health, health + 0.30 * dt)

            if random.random() < 0.80:
                spawn_particles(
                    particles,
                    DISPLAY_WIDTH / 2 + random.randint(-110, 110),
                    player.position.y + random.randint(-110, 110),
                    4, (255, 45, 15), 1, 8, 2, 9, 12, 40
                )

            if phase_transition_timer <= 0:
                phase_transition = False
                boss.start_phase_2(player)
                health = max_health
                combo = 0
                combo_timer = 0
                boss_rage_triggered = False
                boss_rage_message_timer = 0
                boss_phase_message_timer = 180

                intro_card_timer = 100
                intro_card_title = "PHASE 2"
                intro_card_subtitle = "THE DESTROYER"

                beans = []
                for pattern in ["line", "zigzag", "cluster", "golden", "normal"]:
                    spawn_boss_bean_pattern(beans, player, pattern)

                # Adjusted Phase 2 bean spawn limit
                while len(beans) < BOSS_PHASE_2_MAX_BEANS:
                    spawn_boss_bean_pattern(beans, player, "normal")

                screen_shake = 24
                screen_flash = 25

        if victory_sequence:
            victory_sequence_timer += dt

            if random.random() < 0.70:
                spawn_particles(
                    particles,
                    random.randint(10, DISPLAY_WIDTH - 10),
                    player.position.y + random.randint(-350, 30),
                    3, random.choice([(255, 180, 50), (255, 90, 20), (255, 230, 100)]),
                    0.5, 6, 2, 7, 10, 42
                )

            if victory_sequence_timer >= 175:
                victory_sequence = False
                game_finished = True
                victory_timer = 0

        update_effects(particles, rings, dt)

        for bean in beans:
            if bean.position.y + camOffset + bean.sprite.get_height() > DISPLAY_HEIGHT:
                if boss_fight:
                    bean.position.y = player.position.y - DISPLAY_HEIGHT - random.randrange(0, 1100)
                else:
                    bean.position.y -= DISPLAY_HEIGHT * 2

                max_x = max(0, DISPLAY_WIDTH - bean.sprite.get_width())
                bean.position.x = random.randrange(max_x + 1)
                bean.golden = False
                bean.is_critical = False
                bean.value = 1

            if hasattr(bean, "pulse"):
                bean.pulse += 0.12 * dt

            if (
                not dead
                and not phase_transition
                and not victory_sequence
                and checkCollisions(
                    player.position.x, player.position.y,
                    player.currentSprite.get_width(), player.currentSprite.get_height(),
                    bean.position.x, bean.position.y,
                    bean.sprite.get_width(), bean.sprite.get_height()
                )
            ):
                play_sound(beanfx)
                golden = getattr(bean, "golden", False)
                is_crit = getattr(bean, "is_critical", False)
                value = 5 if golden else getattr(bean, "value", 1)

                beanCount += value

                if golden:
                    stats_golden_beans += 1

                stats_beans += value

                if combo_timer > 0:
                    combo += 1
                else:
                    combo = 1

                stats_best_combo = max(stats_best_combo, combo)

                combo_timer = 100
                combo_flash_timer = 18

                health = min(max_health, health + (max_health * 0.50))

                if combo >= 10:
                    health = min(max_health, health + 25)
                elif combo >= 5:
                    health = min(max_health, health + 10)

                no_hit_bean_streak += 1

                if boss_fight and no_hit_bean_streak >= 10:
                    no_hit_bean_streak = 0
                    boss.stun_timer = 70
                    stun_banner_timer = 60

                if boss_fight:
                    base_damage = 30 if boss.phase == 1 else 25
                    combo_multiplier = 1 + min(combo, 10) * 0.06
                    damage = int(base_damage * combo_multiplier)

                    if combo >= 20:
                        damage += 50

                    if golden:
                        damage = int(damage * 2.5)

                    if is_crit:
                        damage *= 2
                        crit_banner_timer = 30

                    boss.hit(damage)
                    boss_hit_flash = 8
                    screen_shake = max(screen_shake, 5)

                    spawn_particles(
                        particles,
                        boss.position.x + boss.sprite.get_width() / 2,
                        boss.position.y + boss.sprite.get_height() / 2,
                        12 if not golden else 35, (255, 225, 80), 1, 6, 2, 7, 12, 36
                    )
                    spawn_ring(
                        rings,
                        boss.position.x + boss.sprite.get_width() / 2,
                        boss.position.y + boss.sprite.get_height() / 2,
                        7 if not golden else 16, 4 if not golden else 9, 15 if not golden else 28, (255, 230, 100)
                    )

                bean.position.y = player.position.y - DISPLAY_HEIGHT - random.randrange(0, 700)
                max_x = max(0, DISPLAY_WIDTH - bean.sprite.get_width())
                bean.position.x = random.randrange(max_x + 1)
                bean.golden = False
                bean.is_critical = False
                bean.value = 1

        current_target_beans = BOSS_PHASE_1_MAX_BEANS if (boss.phase == 1) else BOSS_PHASE_2_MAX_BEANS
        if (
            boss_fight
            and not boss_defeated
            and not phase_transition
            and not victory_sequence
            and len(beans) < current_target_beans
        ):
            while len(beans) < current_target_beans:
                new_bean = Bean()
                max_x = max(0, DISPLAY.get_width() - new_bean.sprite.get_width())
                new_bean.position.xy = (
                    random.randrange(max_x + 1),
                    player.position.y - DISPLAY_HEIGHT - random.randrange(0, 1600)
                )
                beans.append(new_bean)

        # SHOP INTERACTION (DISABLED DURING BOSS FIFT)
        for index, button in enumerate(buttons):
            buttonX = 220 + index * 125
            buttonY = 393

            if (
                clicked
                and not dead
                and not game_finished
                and mouseY >= DISPLAY.get_height() - HUD_HEIGHT
                and checkCollisions(
                    mouseX, mouseY, 3, 3,
                    buttonX, buttonY, button.sprite.get_width(), button.sprite.get_height()
                )
            ):
                # Completely disable shop upgrades when fighting a boss
                upgrade_allowed = not boss_fight

                if upgrade_allowed and beanCount >= button.price:
                    play_sound(upgradefx)
                    button.level += 1
                    beanCount -= button.price

                    button.price = max(1, round(button.price * 1.5))

                    if index == 0:
                        flapForce = min(NORMAL_MAX_FLAP, flapForce * 1.5)
                    elif index == 1:
                        direction = 1 if player.velocity.x >= 0 else -1
                        new_speed = min(NORMAL_MAX_SPEED, abs(player.velocity.x) * 1.5)
                        player.velocity.x = direction * new_speed
                    elif index == 2:
                        beanMultiplier += 20
                        for _ in range(12):
                            new_bean = Bean()
                            max_x = max(0, DISPLAY_WIDTH - new_bean.sprite.get_width())
                            new_bean.position.xy = (
                                random.randrange(max_x + 1),
                                player.position.y - DISPLAY_HEIGHT - random.randrange(0, 300)
                            )
                            beans.append(new_bean)

        if (
            dead
            and clicked
            and checkCollisions(
                mouseX, mouseY, 3, 3,
                4, 4, retry_button.get_width(), retry_button.get_height()
            )
        ):
            stop_music()
            max_health = 100.0
            health = 100.0

            player.velocity.xy = (NORMAL_START_SPEED, 0)
            player.position.xy = (295, 100)
            player.currentSprite = player.rightSprite

            beanCount = 0
            height = 0
            startingHeight = player.position.y
            flapForce = NORMAL_START_FLAP
            beanMultiplier = 20

            dead = False
            boss_fight = False
            boss_defeated = False
            game_finished = False

            boss_phase_message_timer = 0
            final_message_timer = 0
            victory_timer = 0
            phase_transition = False
            phase_transition_timer = 0
            player_invuln_timer = 0
            combo = 0
            combo_timer = 0
            combo_flash_timer = 0
            boss_rage_triggered = False
            boss_rage_message_timer = 0
            victory_sequence = False
            victory_sequence_timer = 0

            no_hit_bean_streak = 0
            stun_banner_timer = 0
            crit_banner_timer = 0
            intro_card_timer = 0

            screen_shake = 0
            screen_flash = 0
            boss_hit_flash = 0

            particles.clear()
            rings.clear()

            boss = Boss()
            buttons = create_buttons()
            beans = create_beans(player, count=12)

            play_sound(upgradefx)

        background_height = DISPLAY_HEIGHT
        base_background_y = round(player.position.y / background_height) * background_height

        bg[0].position = base_background_y
        bg[1].position = base_background_y + background_height
        bg[2].position = base_background_y - background_height

        if screen_flash > 0:
            flash_alpha = int(clamp(screen_flash / 45 * 170, 0, 170))
            flash = pygame.Surface(DISPLAY.get_size(), pygame.SRCALPHA)
            flash.fill((255, 70, 20, flash_alpha))
            DISPLAY.blit(flash, (0, 0))

        pygame.display.flip()
        pygame.time.delay(10)

    pygame.quit()


if __name__ == "__main__":
    main()