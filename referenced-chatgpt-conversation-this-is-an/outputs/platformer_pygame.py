import json
from pathlib import Path

import pygame


WIDTH = 960
HEIGHT = 540
FPS = 60

SKY = (92, 178, 255)
GROUND = (70, 150, 78)
DIRT = (126, 84, 49)
ITEM_COLOR = (255, 214, 64)
TEXT_COLOR = (30, 42, 56)

GRAVITY = 0.65
MOVE_SPEED = 5
DASH_SPEED = 12
DASH_DURATION = 0.22
DOUBLE_TAP_WINDOW = 280
BARK_COLLISION_MULTIPLIER = 2.5
BARK_SWITCH_COOLDOWN_MS = 1000
JUMP_SPEED = -14
ASSET_DIR = Path(__file__).resolve().parent
CHARACTER_IMAGE = ASSET_DIR / "dog_character.png"
SPRITE_DIRS = {
    "character_1": ASSET_DIR / "character1_sprites",
    "character_2": ASSET_DIR / "character2_sprites",
    "character_3": ASSET_DIR / "character3_sprites",
}
LEVEL_FILE = ASSET_DIR / "level_01.json"
LEVEL_WIDTH = 1600
LEVEL_HEIGHT = 620
PLAYER_SPAWN = (55, 420)
LEVEL_END = (900, 420)
LEVEL_CHARACTERS = []
SPRITE_SIZE = (112, 92)
CHARACTER_CONFIG = {
    "character_1": {"size": (112, 92), "collision": (44, 48), "move_speed": 5, "jump_speed": -14, "double_jump": True, "dash": True, "outline": None},
    "character_2": {"size": (132, 108), "collision": (58, 70), "move_speed": 2.5, "jump_speed": -14, "double_jump": False, "dash": False, "outline": None},
    "character_3": {"size": (61, 50), "collision": (25, 29), "move_speed": 15, "jump_speed": -14, "double_jump": False, "dash": False, "outline": None},
}
CHARACTER_TYPE_ALIASES = {
    "character_player": "character_1",
    "character_enemy": "character_2",
    "character_npc": "character_3",
}
DEATH_LINE = HEIGHT - 20
STATE_LABELS = {
    "idle": "Parado",
    "walk": "Andando",
    "crouch": "Abaixado",
    "look_up": "Olhando para cima",
    "bark": "Latindo",
    "jump_prepare": "Preparando salto",
    "jump": "Pulando",
    "fall": "Caindo",
    "land": "Amortecendo",
    "dead": "Morrendo",
}


def place_on_canvas(surface, size=SPRITE_SIZE, offset=(0, 0)):
    canvas = pygame.Surface(size, pygame.SRCALPHA)
    x = (size[0] - surface.get_width()) // 2 + offset[0]
    y = (size[1] - surface.get_height()) // 2 + offset[1]
    canvas.blit(surface, (x, y))
    return canvas


def make_pose(base, *, scale=(1.0, 1.0), angle=0, offset=(0, 0), tint=None):
    width = max(1, int(base.get_width() * scale[0]))
    height = max(1, int(base.get_height() * scale[1]))
    image = pygame.transform.scale(base, (width, height))

    if tint:
        overlay = pygame.Surface(image.get_size(), pygame.SRCALPHA)
        overlay.fill(tint)
        image.blit(overlay, (0, 0), special_flags=pygame.BLEND_RGBA_MULT)

    if angle:
        image = pygame.transform.rotate(image, angle)

    return place_on_canvas(image, offset=offset)


class AnimationSet:
    def __init__(self, animations, frame_times=None, default_frame_time=0.12):
        self.animations = animations
        self.frame_times = frame_times or {}
        self.default_frame_time = default_frame_time
        self.state = "idle"
        self.frame_index = 0
        self.timer = 0

    def set_state(self, state):
        if state == self.state:
            return
        self.state = state
        self.frame_index = 0
        self.timer = 0

    def update(self, dt):
        frames = self.animations[self.state]
        if len(frames) == 1:
            return

        self.timer += dt
        frame_time = self.frame_times.get(self.state, self.default_frame_time)
        if self.timer >= frame_time:
            self.timer = 0
            self.frame_index = (self.frame_index + 1) % len(frames)

    def current_frame(self, facing_right=True):
        frame = self.animations[self.state][self.frame_index]
        if facing_right:
            return frame
        return pygame.transform.flip(frame, True, False)


def add_outline(image, color):
    mask = pygame.mask.from_surface(image)
    outline = mask.to_surface(setcolor=color, unsetcolor=(0, 0, 0, 0))
    result = pygame.Surface(image.get_size(), pygame.SRCALPHA)
    for offset_x in (-2, -1, 0, 1, 2):
        for offset_y in (-2, -1, 0, 1, 2):
            result.blit(outline, (offset_x, offset_y))
    result.blit(image, (0, 0))
    return result


def load_character_animations(character_type="character_1"):
    config = CHARACTER_CONFIG[character_type]
    sprite_dir = SPRITE_DIRS[character_type]

    def sprite(name):
        image = pygame.image.load(sprite_dir / name).convert_alpha()
        image = pygame.transform.scale(image, config["size"])
        if config["outline"]:
            image = add_outline(image, config["outline"])
        return image

    idle = sprite("idle_0.png")

    return AnimationSet(
        {
            "idle": [
                place_on_canvas(idle, size=config["size"], offset=(0, 0)),
                place_on_canvas(idle, size=config["size"], offset=(0, -1)),
                place_on_canvas(idle, size=config["size"], offset=(0, 0)),
                place_on_canvas(idle, size=config["size"], offset=(0, 1)),
            ],
            "walk": [
                sprite("walk_0.png"),
                sprite("walk_1.png"),
            ],
            "crouch": [sprite("crouch_0.png")],
            "look_up": [sprite("look_up_0.png")],
            "bark": [
                sprite("bark_0.png"),
                sprite("bark_1.png"),
            ],
            "jump_prepare": [sprite("jump_prepare_0.png")],
            "jump": [
                sprite("jump_0.png"),
            ],
            "fall": [
                sprite("fall_0.png"),
            ],
            "land": [
                sprite("land_0.png"),
                sprite("land_1.png"),
            ],
            "dead": [
                place_on_canvas(make_pose(idle, angle=-75, offset=(0, 6), tint=(190, 190, 190, 255)), size=config["size"]),
                place_on_canvas(make_pose(idle, angle=-90, offset=(0, 8), tint=(150, 150, 150, 230)), size=config["size"]),
            ],
        },
        frame_times={"idle": 0.16, "walk": 0.09, "bark": 0.08, "land": 0.07, "dead": 0.12},
        default_frame_time=0.1,
    )


class Player(pygame.sprite.Sprite):
    def __init__(self, x, y, character_type="character_1", controllable=True):
        super().__init__()
        config = CHARACTER_CONFIG[character_type]
        self.character_type = character_type
        self.controllable = controllable
        self.move_speed = config["move_speed"]
        self.speed_multiplier = 1.0
        self.jump_speed = config["jump_speed"]
        self.double_jump_enabled = config["double_jump"]
        self.dash_enabled = config["dash"]
        self.animations = load_character_animations(character_type)
        self.image = self.animations.current_frame()
        self.rect = pygame.Rect(x, y, *config["collision"])
        self.velocity = pygame.Vector2(0, 0)
        self.on_ground = False
        self.spawn = pygame.Vector2(x, y)
        self.facing_right = True
        self.state = "idle"
        self.dead_timer = 0
        self.jump_prepare_timer = 0
        self.jumps_used = 0
        self.landing_timer = 0
        self.bark_timer = 0
        self.bark_requested = False
        self.dash_timer = 0
        self.dash_direction = 0
        self.last_tap_time = {"left": -DOUBLE_TAP_WINDOW * 2, "right": -DOUBLE_TAP_WINDOW * 2}
        self.crouching = False
        self.looking_up = False
        self.bark_requested = False
        self.jump_key_was_down = False
        self.bark_key_was_down = False
        self.left_key_was_down = False
        self.right_key_was_down = False

    def handle_input(self):
        if not self.controllable or self.state == "dead":
            self.velocity.x = 0
            return

        keys = pygame.key.get_pressed()
        self.velocity.x = 0
        self.crouching = False
        self.looking_up = False

        jump_key_is_down = keys[pygame.K_SPACE]
        look_up_key_is_down = keys[pygame.K_UP] or keys[pygame.K_w]
        down_key_is_down = keys[pygame.K_DOWN] or keys[pygame.K_s]
        bark_key_is_down = keys[pygame.K_x]
        left_key_is_down = keys[pygame.K_LEFT] or keys[pygame.K_a]
        right_key_is_down = keys[pygame.K_RIGHT] or keys[pygame.K_d]
        now = pygame.time.get_ticks()

        if bark_key_is_down and not self.bark_key_was_down and self.on_ground:
            self.bark_timer = 0.28
            self.bark_requested = True
            self.jump_prepare_timer = 0
            self.landing_timer = 0

        if down_key_is_down and self.on_ground and self.bark_timer <= 0:
            self.crouching = True
        elif look_up_key_is_down and self.on_ground and self.bark_timer <= 0:
            self.looking_up = True

        can_move = self.bark_timer <= 0 and not self.crouching and self.jump_prepare_timer <= 0
        if can_move and self.on_ground and self.dash_enabled:
            for direction_name, is_down, was_down, direction in (
                ("left", left_key_is_down, self.left_key_was_down, -1),
                ("right", right_key_is_down, self.right_key_was_down, 1),
            ):
                if is_down and not was_down:
                    if now - self.last_tap_time[direction_name] <= DOUBLE_TAP_WINDOW:
                        self.dash_timer = DASH_DURATION
                        self.dash_direction = direction
                    self.last_tap_time[direction_name] = now

        if can_move and self.dash_enabled and self.dash_timer > 0:
            self.velocity.x = self.dash_direction * self.move_speed * self.speed_multiplier * 2.4
            self.facing_right = self.dash_direction > 0
        elif can_move and left_key_is_down:
            self.velocity.x = -self.move_speed * self.speed_multiplier
            self.facing_right = False
        elif can_move and right_key_is_down:
            self.velocity.x = self.move_speed * self.speed_multiplier
            self.facing_right = True

        can_prepare_jump = (
            self.on_ground
            and self.jump_prepare_timer <= 0
            and self.bark_timer <= 0
            and not self.crouching
        )
        if jump_key_is_down and not self.jump_key_was_down:
            if can_prepare_jump and self.jumps_used == 0:
                self.jump_prepare_timer = 0.12
                self.landing_timer = 0
                self.velocity.x = 0
            elif (
                self.double_jump_enabled
                and not self.on_ground
                and self.jumps_used == 1
                and self.bark_timer <= 0
            ):
                self.velocity.y = self.jump_speed
                self.jumps_used = 2
                self.landing_timer = 0

        self.jump_key_was_down = jump_key_is_down
        self.bark_key_was_down = bark_key_is_down
        self.left_key_was_down = left_key_is_down
        self.right_key_was_down = right_key_is_down

    def apply_gravity(self):
        if self.jump_prepare_timer > 0:
            return

        self.velocity.y += GRAVITY
        if self.velocity.y > 18:
            self.velocity.y = 18

    def move_and_collide(self, platforms):
        landed = False
        falling_speed = self.velocity.y

        self.rect.x += self.velocity.x
        for platform in platforms:
            if self.rect.colliderect(platform.rect):
                if self.velocity.x > 0:
                    self.rect.right = platform.rect.left
                elif self.velocity.x < 0:
                    self.rect.left = platform.rect.right

        self.rect.y += self.velocity.y
        self.on_ground = False
        for platform in platforms:
            if self.rect.colliderect(platform.rect):
                if self.velocity.y > 0:
                    self.rect.bottom = platform.rect.top
                    self.velocity.y = 0
                    self.on_ground = True
                    if falling_speed > 7:
                        landed = True
                elif self.velocity.y < 0:
                    self.rect.top = platform.rect.bottom
                    self.velocity.y = GRAVITY
                    break

        return landed

    def choose_animation_state(self):
        if self.state == "dead":
            return "dead"
        if self.bark_timer > 0:
            return "bark"
        if self.jump_prepare_timer > 0:
            return "jump_prepare"
        if self.landing_timer > 0:
            return "land"
        if self.velocity.y < -1:
            return "jump"
        if self.velocity.y > 1 and not self.on_ground:
            return "fall"
        if self.crouching:
            return "crouch"
        if self.looking_up:
            return "look_up"
        if self.velocity.x != 0:
            return "walk"
        return "idle"

    def update(self, platforms, dt):
        self.handle_input()

        if self.jump_prepare_timer > 0:
            self.jump_prepare_timer -= dt
            if self.jump_prepare_timer <= 0:
                self.velocity.y = self.jump_speed
                self.jumps_used = 1
                self.on_ground = False

        self.apply_gravity()
        landed = self.move_and_collide(platforms)

        if self.on_ground:
            self.jumps_used = 0

        if landed:
            self.landing_timer = 0.16
        elif self.landing_timer > 0:
            self.landing_timer -= dt

        if self.bark_timer > 0:
            self.bark_timer -= dt

        if self.dash_timer > 0:
            self.dash_timer -= dt

        if self.rect.top > LEVEL_HEIGHT - 20:
            self.die()

        if self.state == "dead":
            self.dead_timer += dt
            if self.dead_timer >= 0.7:
                self.reset()

        self.animations.set_state(self.choose_animation_state())
        self.animations.update(dt)
        self.image = self.animations.current_frame(self.facing_right)

    def die(self):
        if self.state != "dead":
            self.state = "dead"
            self.dead_timer = 0
            self.velocity.update(0, -7)

    def draw(self, screen, camera_x=0, camera_y=0):
        image_rect = self.image.get_rect(midbottom=self.rect.midbottom)
        image_rect.y += 4
        image_rect.x -= camera_x
        image_rect.y -= camera_y
        screen.blit(self.image, image_rect)

    def reset(self):
        self.rect.topleft = self.spawn
        self.velocity.update(0, 0)
        self.speed_multiplier = 1.0
        self.state = "idle"
        self.dead_timer = 0
        self.jump_prepare_timer = 0
        self.jumps_used = 0
        self.landing_timer = 0
        self.bark_timer = 0
        self.bark_requested = False
        self.dash_timer = 0
        self.dash_direction = 0
        self.crouching = False
        self.looking_up = False
        self.jump_key_was_down = False
        self.bark_key_was_down = False
        self.left_key_was_down = False
        self.right_key_was_down = False
        self.last_tap_time = {"left": -DOUBLE_TAP_WINDOW * 2, "right": -DOUBLE_TAP_WINDOW * 2}
        self.on_ground = False


class Platform(pygame.sprite.Sprite):
    def __init__(self, x, y, width, height=32):
        super().__init__()
        self.image = pygame.Surface((width, height))
        self.image.fill(GROUND)
        pygame.draw.rect(self.image, DIRT, (0, height - 8, width, 8))
        self.rect = self.image.get_rect(topleft=(x, y))


class MovingPlatform(Platform):
    def __init__(self, x, y, width, height=32):
        super().__init__(x, y, width, height)
        self.image.fill((22, 75, 135))
        pygame.draw.rect(self.image, (113, 53, 166), (0, height - 8, width, 8))
        self.velocity = pygame.Vector2(0, 0)

    def update(self, platforms, pusher, dt):
        self.velocity.y = min(self.velocity.y + GRAVITY, 18)
        if pusher is not None:
            push_area = pusher.rect.inflate(8, 8)
            if push_area.colliderect(self.rect):
                direction = 1 if pusher.velocity.x >= 0 else -1
                self.velocity.x = direction * max(1.0, abs(pusher.velocity.x) * 0.5)
                pusher.velocity.x *= 0.35
            else:
                self.velocity.x *= 0.85
        else:
            self.velocity.x *= 0.85

        self.rect.x += int(self.velocity.x)
        for platform in platforms:
            if platform is self or isinstance(platform, MovingPlatform):
                continue
            if self.rect.colliderect(platform.rect):
                if self.velocity.x > 0:
                    self.rect.right = platform.rect.left
                elif self.velocity.x < 0:
                    self.rect.left = platform.rect.right
                self.velocity.x = 0

        self.rect.y += int(self.velocity.y)
        supported = False
        for platform in platforms:
            if platform is self or isinstance(platform, MovingPlatform):
                continue
            if self.rect.colliderect(platform.rect):
                if self.velocity.y > 0:
                    self.rect.bottom = platform.rect.top
                    self.velocity.y = 0
                    supported = True
                elif self.velocity.y < 0:
                    self.rect.top = platform.rect.bottom
                    self.velocity.y = GRAVITY
        return supported


class Item(pygame.sprite.Sprite):
    def __init__(self, x, y):
        super().__init__()
        self.image = pygame.Surface((22, 22), pygame.SRCALPHA)
        pygame.draw.circle(self.image, ITEM_COLOR, (11, 11), 10)
        pygame.draw.circle(self.image, (255, 245, 150), (8, 7), 4)
        self.rect = self.image.get_rect(center=(x, y))


class LevelEnd(pygame.sprite.Sprite):
    def __init__(self, x, y):
        super().__init__()
        self.image = pygame.Surface((38, 58), pygame.SRCALPHA)
        pygame.draw.line(self.image, (45, 35, 28), (8, 4), (8, 54), 4)
        pygame.draw.polygon(self.image, (210, 65, 52), [(10, 6), (34, 14), (10, 24)])
        self.rect = self.image.get_rect(topleft=(x, y))


def build_level():
    global LEVEL_WIDTH, LEVEL_HEIGHT, PLAYER_SPAWN, LEVEL_END, LEVEL_CHARACTERS
    platforms = pygame.sprite.Group()
    items = pygame.sprite.Group()

    with LEVEL_FILE.open(encoding="utf-8") as level_file:
        level_data = json.load(level_file)

    world_data = level_data.get("world", {})
    LEVEL_WIDTH = max(1, int(world_data.get("width", LEVEL_WIDTH)))
    LEVEL_HEIGHT = max(1, int(world_data.get("height", LEVEL_HEIGHT)))
    spawn_data = level_data.get("player_spawn", {})
    end_data = level_data.get("level_end", {})
    LEVEL_END = (int(end_data.get("x", LEVEL_END[0])), int(end_data.get("y", LEVEL_END[1])))
    character_data = []
    for index, data in enumerate(level_data.get("characters", [])):
        normalized = {**data}
        normalized["type"] = "character_2" if index == 0 else "character_3" if index == 1 else CHARACTER_TYPE_ALIASES.get(data.get("type"), data.get("type"))
        character_data.append(normalized)

    LEVEL_CHARACTERS = [
        data for data in character_data
        if data.get("type") in ("character_2", "character_3")
    ]
    PLAYER_SPAWN = (
        int(spawn_data.get("x", PLAYER_SPAWN[0])),
        int(spawn_data.get("y", PLAYER_SPAWN[1])),
    )
    platform_data = level_data["platforms"]
    item_data = level_data["items"]

    for data in platform_data:
        platform_class = MovingPlatform if data.get("type") == "moving_platform" else Platform
        platforms.add(platform_class(data["x"], data["y"], data["width"], data["height"]))

    for data in item_data:
        items.add(Item(data["x"], data["y"]))

    return platforms, items


def draw_hud(screen, font, score, state):
    help_text = "Mover: A/D ou setas | Espaco: pular | Cima: olhar | Baixo: abaixar | X: latir | R: reiniciar"
    score_text = f"Itens coletados: {score}"
    state_text = f"Movimento: {STATE_LABELS[state]}"

    screen.blit(font.render(score_text, True, TEXT_COLOR), (24, 18))
    screen.blit(font.render(help_text, True, TEXT_COLOR), (24, 46))
    screen.blit(font.render(state_text, True, TEXT_COLOR), (24, 74))


def create_players():
    return [
        Player(*PLAYER_SPAWN, controllable=True),
        *[
            Player(data["x"], data["y"], data["type"], controllable=False)
            for data in LEVEL_CHARACTERS
        ],
    ]


def transfer_control(players, active_index, now, last_transfer_time):
    active_player = players[active_index]
    if not active_player.bark_requested:
        return active_index, last_transfer_time
    if now - last_transfer_time < BARK_SWITCH_COOLDOWN_MS:
        active_player.bark_requested = False
        return active_index, last_transfer_time

    active_player.bark_requested = False
    bark_area = active_player.rect.inflate(
        active_player.rect.width * (BARK_COLLISION_MULTIPLIER - 1),
        active_player.rect.height * (BARK_COLLISION_MULTIPLIER - 1),
    )
    for index, target in enumerate(players):
        if index == active_index or target.state == "dead":
            continue
        if bark_area.colliderect(target.rect):
            active_player.controllable = False
            active_player.velocity.x = 0
            active_player.dash_timer = 0
            active_player.bark_timer = 0
            active_player.state = "idle"
            target.controllable = True
            target.bark_timer = 0
            target.bark_requested = False
            target.jump_key_was_down = False
            target.bark_key_was_down = False
            return index, now

    return active_index, last_transfer_time


def main():
    pygame.init()
    screen = pygame.display.set_mode((WIDTH, HEIGHT))
    pygame.display.set_caption("Protótipo de Plataforma 2D")
    clock = pygame.time.Clock()
    font = pygame.font.SysFont("arial", 20)

    platforms, items = build_level()
    players = create_players()
    active_index = 0
    level_end = LevelEnd(*LEVEL_END)
    score = 0
    camera_x = 0
    camera_y = 0
    end_reached = False
    last_transfer_time = -BARK_SWITCH_COOLDOWN_MS
    running = True

    while running:
        clock.tick(FPS)

        for event in pygame.event.get():
            if event.type == pygame.QUIT:
                running = False
            if event.type == pygame.KEYDOWN and event.key == pygame.K_r:
                platforms, items = build_level()
                players = create_players()
                active_index = 0
                level_end = LevelEnd(*LEVEL_END)
                score = 0
                camera_x = 0
                camera_y = 0
                end_reached = False
                last_transfer_time = -BARK_SWITCH_COOLDOWN_MS

        dt = clock.get_time() / 1000
        pusher = next(
            (character for character in players if character.character_type == "character_2"),
            None,
        )
        for character in players:
            character.speed_multiplier = 1.0
        if pusher is not None:
            for platform in platforms:
                if isinstance(platform, MovingPlatform) and pusher.rect.inflate(8, 8).colliderect(platform.rect):
                    pusher.speed_multiplier = 0.35
                    break
        for character in players:
            character.update(platforms, dt)
        for platform in platforms:
            if isinstance(platform, MovingPlatform):
                platform.update(platforms, pusher, dt)
        active_index, last_transfer_time = transfer_control(
            players,
            active_index,
            pygame.time.get_ticks(),
            last_transfer_time,
        )
        player = players[active_index]

        if player.state != "dead":
            collected = pygame.sprite.spritecollide(player, items, dokill=True)
            score += len(collected)
            if pygame.sprite.collide_rect(player, level_end):
                end_reached = True

        target_camera_x = player.rect.centerx - WIDTH * 0.45
        target_camera_y = player.rect.bottom - HEIGHT * 0.88
        camera_x = max(0, min(max(0, LEVEL_WIDTH - WIDTH), target_camera_x))
        camera_y = max(0, min(max(0, LEVEL_HEIGHT - HEIGHT), target_camera_y))

        screen.fill(SKY)
        for platform in platforms:
            screen.blit(platform.image, (platform.rect.x - camera_x, platform.rect.y - camera_y))
        for item in items:
            screen.blit(item.image, (item.rect.x - camera_x, item.rect.y - camera_y))
        for index, character in enumerate(players):
            if index == active_index:
                continue
            character.draw(screen, camera_x, camera_y)
        players[active_index].draw(screen, camera_x, camera_y)
        screen.blit(level_end.image, (level_end.rect.x - camera_x, level_end.rect.y - camera_y))
        draw_hud(screen, font, score, player.animations.state)

        if not items:
            message = font.render("Voce coletou todos os itens!", True, TEXT_COLOR)
            screen.blit(message, (WIDTH // 2 - message.get_width() // 2, 100))
        if end_reached:
            message = font.render("FIM DA TELA", True, TEXT_COLOR)
            screen.blit(message, (WIDTH // 2 - message.get_width() // 2, 135))

        pygame.display.flip()

    pygame.quit()


if __name__ == "__main__":
    main()
