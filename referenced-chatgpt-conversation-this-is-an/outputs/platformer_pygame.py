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
JUMP_SPEED = -14
ASSET_DIR = Path(__file__).resolve().parent
CHARACTER_IMAGE = ASSET_DIR / "dog_character.png"
SPRITE_DIR = ASSET_DIR / "jack_russell_sprites"
SPRITE_SIZE = (112, 92)
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


def load_character_animations():
    def sprite(name):
        image = pygame.image.load(SPRITE_DIR / name).convert_alpha()
        return pygame.transform.scale(image, SPRITE_SIZE)

    idle = sprite("idle_0.png")

    return AnimationSet(
        {
            "idle": [
                place_on_canvas(idle, offset=(0, 0)),
                place_on_canvas(idle, offset=(0, -1)),
                place_on_canvas(idle, offset=(0, 0)),
                place_on_canvas(idle, offset=(0, 1)),
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
                make_pose(idle, angle=-75, offset=(0, 6), tint=(190, 190, 190, 255)),
                make_pose(idle, angle=-90, offset=(0, 8), tint=(150, 150, 150, 230)),
            ],
        },
        frame_times={"idle": 0.16, "walk": 0.09, "bark": 0.08, "land": 0.07, "dead": 0.12},
        default_frame_time=0.1,
    )


class Player(pygame.sprite.Sprite):
    def __init__(self, x, y):
        super().__init__()
        self.animations = load_character_animations()
        self.image = self.animations.current_frame()
        self.rect = pygame.Rect(x, y, 44, 48)
        self.velocity = pygame.Vector2(0, 0)
        self.on_ground = False
        self.spawn = pygame.Vector2(x, y)
        self.facing_right = True
        self.state = "idle"
        self.dead_timer = 0
        self.jump_prepare_timer = 0
        self.landing_timer = 0
        self.bark_timer = 0
        self.crouching = False
        self.looking_up = False
        self.jump_key_was_down = False
        self.bark_key_was_down = False

    def handle_input(self):
        if self.state == "dead":
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

        if bark_key_is_down and not self.bark_key_was_down and self.on_ground:
            self.bark_timer = 0.28
            self.jump_prepare_timer = 0
            self.landing_timer = 0

        if down_key_is_down and self.on_ground and self.bark_timer <= 0:
            self.crouching = True
        elif look_up_key_is_down and self.on_ground and self.bark_timer <= 0:
            self.looking_up = True

        can_move = self.bark_timer <= 0 and not self.crouching and self.jump_prepare_timer <= 0
        if can_move and (keys[pygame.K_LEFT] or keys[pygame.K_a]):
            self.velocity.x = -MOVE_SPEED
            self.facing_right = False
        if can_move and (keys[pygame.K_RIGHT] or keys[pygame.K_d]):
            self.velocity.x = MOVE_SPEED
            self.facing_right = True

        can_prepare_jump = (
            self.on_ground
            and self.jump_prepare_timer <= 0
            and self.bark_timer <= 0
            and not self.crouching
        )
        if jump_key_is_down and not self.jump_key_was_down and can_prepare_jump:
            self.jump_prepare_timer = 0.12
            self.landing_timer = 0
            self.velocity.x = 0

        self.jump_key_was_down = jump_key_is_down
        self.bark_key_was_down = bark_key_is_down

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
                    self.velocity.y = 0

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
                self.velocity.y = JUMP_SPEED
                self.on_ground = False

        self.apply_gravity()
        landed = self.move_and_collide(platforms)

        if landed:
            self.landing_timer = 0.16
        elif self.landing_timer > 0:
            self.landing_timer -= dt

        if self.bark_timer > 0:
            self.bark_timer -= dt

        if self.rect.top > DEATH_LINE:
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

    def draw(self, screen):
        image_rect = self.image.get_rect(midbottom=self.rect.midbottom)
        image_rect.y += 4
        screen.blit(self.image, image_rect)

    def reset(self):
        self.rect.topleft = self.spawn
        self.velocity.update(0, 0)
        self.state = "idle"
        self.dead_timer = 0
        self.jump_prepare_timer = 0
        self.landing_timer = 0
        self.bark_timer = 0
        self.crouching = False
        self.looking_up = False
        self.jump_key_was_down = False
        self.bark_key_was_down = False
        self.on_ground = False


class Platform(pygame.sprite.Sprite):
    def __init__(self, x, y, width, height=32):
        super().__init__()
        self.image = pygame.Surface((width, height))
        self.image.fill(GROUND)
        pygame.draw.rect(self.image, DIRT, (0, height - 8, width, 8))
        self.rect = self.image.get_rect(topleft=(x, y))


class Item(pygame.sprite.Sprite):
    def __init__(self, x, y):
        super().__init__()
        self.image = pygame.Surface((22, 22), pygame.SRCALPHA)
        pygame.draw.circle(self.image, ITEM_COLOR, (11, 11), 10)
        pygame.draw.circle(self.image, (255, 245, 150), (8, 7), 4)
        self.rect = self.image.get_rect(center=(x, y))


def build_level():
    platforms = pygame.sprite.Group()
    items = pygame.sprite.Group()

    platform_data = [
        (0, 470, 260, 70),
        (330, 470, 210, 70),
        (610, 470, 360, 70),
        (190, 375, 130, 28),
        (430, 330, 150, 28),
        (670, 285, 150, 28),
        (830, 395, 110, 28),
    ]

    item_data = [
        (235, 340),
        (505, 295),
        (745, 250),
        (885, 360),
    ]

    for data in platform_data:
        platforms.add(Platform(*data))

    for data in item_data:
        items.add(Item(*data))

    return platforms, items


def draw_hud(screen, font, score, state):
    help_text = "Mover: A/D ou setas | Espaco: pular | Cima: olhar | Baixo: abaixar | X: latir | R: reiniciar"
    score_text = f"Itens coletados: {score}"
    state_text = f"Movimento: {STATE_LABELS[state]}"

    screen.blit(font.render(score_text, True, TEXT_COLOR), (24, 18))
    screen.blit(font.render(help_text, True, TEXT_COLOR), (24, 46))
    screen.blit(font.render(state_text, True, TEXT_COLOR), (24, 74))


def main():
    pygame.init()
    screen = pygame.display.set_mode((WIDTH, HEIGHT))
    pygame.display.set_caption("Protótipo de Plataforma 2D")
    clock = pygame.time.Clock()
    font = pygame.font.SysFont("arial", 20)

    platforms, items = build_level()
    player = Player(55, 420)
    score = 0
    running = True

    while running:
        clock.tick(FPS)

        for event in pygame.event.get():
            if event.type == pygame.QUIT:
                running = False
            if event.type == pygame.KEYDOWN and event.key == pygame.K_r:
                platforms, items = build_level()
                player.reset()
                score = 0

        dt = clock.get_time() / 1000
        player.update(platforms, dt)

        if player.state != "dead":
            collected = pygame.sprite.spritecollide(player, items, dokill=True)
            score += len(collected)

        screen.fill(SKY)
        platforms.draw(screen)
        items.draw(screen)
        player.draw(screen)
        draw_hud(screen, font, score, player.animations.state)

        if not items:
            message = font.render("Voce coletou todos os itens!", True, TEXT_COLOR)
            screen.blit(message, (WIDTH // 2 - message.get_width() // 2, 100))

        pygame.display.flip()

    pygame.quit()


if __name__ == "__main__":
    main()
