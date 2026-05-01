import pygame
import sys
import math
import os
import random

# Inicjalizacja Pygame i Mixera
pygame.init()
try:
    pygame.mixer.init()
except pygame.error:
    pass

# Ustawienia ekranu
WIDTH, HEIGHT = 800, 600
screen = pygame.display.set_mode((WIDTH, HEIGHT))
pygame.display.set_caption("Miziewicz The Game")
clock = pygame.time.Clock()

# Kolory
WHITE = (255, 255, 255)
BLACK = (0, 0, 0)
RED = (200, 0, 0)
BLUE = (0, 0, 255)
YELLOW = (255, 255, 0)
GREEN = (0, 200, 0)

# Czcionki
font = pygame.font.SysFont("Arial", 36)
small_font = pygame.font.SysFont("Arial", 20)

# Ścieżki do zasobów
ASSET_DIR = os.path.join(os.path.dirname(__file__), "assets")
IMG_DIR = os.path.join(ASSET_DIR, "imgs")
AUDIO_DIR = os.path.join(ASSET_DIR, "audios")
SFX_DIR = os.path.join(AUDIO_DIR, "sfx")
MIZ_DIR = os.path.join(AUDIO_DIR, "miziewicz")
MOCKO_DIR = os.path.join(AUDIO_DIR, "mocko")

# Pomocnicy do ładowania zasobów

def load_image(filename, size=None):
    path = os.path.join(IMG_DIR, filename)
    if not os.path.isfile(path):
        return None
    image = pygame.image.load(path).convert_alpha()
    return pygame.transform.scale(image, size) if size else image


def load_sound(path):
    if not os.path.isfile(path):
        return None
    try:
        return pygame.mixer.Sound(path)
    except pygame.error:
        return None


music_volume = 0.2
sfx_volume = 0.2

def set_music_volume(level):
    global music_volume
    music_volume = max(0.0, min(1.0, level))
    try:
        pygame.mixer.music.set_volume(music_volume)
    except pygame.error:
        pass

def set_sfx_volume(level):
    global sfx_volume
    sfx_volume = max(0.0, min(1.0, level))
    apply_volume_to_sounds()

def apply_volume_to_sounds():
    for sound in [shoot_sound] + hit_sounds + player_hit_sounds + [mocko_death_sound, miziewicz_death_sound]:
        if sound:
            try:
                sound.set_volume(sfx_volume)
            except pygame.error:
                pass


miziewicz_img = load_image("miziewicz.png", (40, 40))
mocko_img = load_image("mocko.png", (100, 100))
ammo_img = load_image("ammo.png", (24, 24))

shoot_sound = load_sound(os.path.join(MIZ_DIR, "miziewiczshoot.mp3"))
hit_sounds = [
    load_sound(os.path.join(MOCKO_DIR, "mockodmg1.mp3")),
    load_sound(os.path.join(MOCKO_DIR, "mockodmg2.mp3")),
    load_sound(os.path.join(MOCKO_DIR, "mockodmg3.mp3")),
]
player_hit_sounds = [
    load_sound(os.path.join(MIZ_DIR, "miziewiczdmg1.mp3")),
    load_sound(os.path.join(MIZ_DIR, "miziewiczdmg2.mp3")),
    load_sound(os.path.join(MIZ_DIR, "miziewiczdmg3.mp3")),
]
mocko_death_sound = load_sound(os.path.join(MOCKO_DIR, "mockodeath.mp3"))
miziewicz_death_sound = load_sound(os.path.join(MIZ_DIR, "miziewiczdeath.mp3"))
apply_volume_to_sounds()

music_path = os.path.join(SFX_DIR, "music.mp3")
if os.path.isfile(music_path):
    try:
        pygame.mixer.music.load(music_path)
        set_music_volume(music_volume)
        pygame.mixer.music.play(-1)
    except pygame.error:
        pass


def play_random_sound(sounds):
    sounds = [sound for sound in sounds if sound]
    if sounds:
        random.choice(sounds).play()

class Miziewicz:
    def __init__(self):
        self.size = 40
        self.x = WIDTH // 2
        self.y = HEIGHT - 100
        self.speed = 5
        self.health = 100
        self.max_health = 100
        self.rect = pygame.Rect(self.x, self.y, self.size, self.size)

    def move(self, keys):
        if keys[pygame.K_LEFT] or keys[pygame.K_a]:
            self.x -= self.speed
        if keys[pygame.K_RIGHT] or keys[pygame.K_d]:
            self.x += self.speed
        if keys[pygame.K_UP] or keys[pygame.K_w]:
            self.y -= self.speed
        if keys[pygame.K_DOWN] or keys[pygame.K_s]:
            self.y += self.speed

        # Ograniczenie ruchu do ekranu
        self.x = max(0, min(WIDTH - self.size, self.x))
        self.y = max(0, min(HEIGHT - self.size, self.y))
        self.rect.topleft = (self.x, self.y)

    def draw(self, surface):
        if miziewicz_img:
            surface.blit(miziewicz_img, self.rect)
        else:
            pygame.draw.rect(surface, BLUE, self.rect)
        # Pasek zdrowia Miziewicza
        pygame.draw.rect(surface, RED, (self.x, self.y - 15, self.size, 10))
        health_width = (self.health / self.max_health) * self.size
        pygame.draw.rect(surface, GREEN, (self.x, self.y - 15, health_width, 10))

class GrubyMocko:
    def __init__(self):
        self.size = 100
        self.x = WIDTH // 2 - 50
        self.y = 50
        self.speed = 1.5
        self.health = 500
        self.max_health = 500
        self.rect = pygame.Rect(self.x, self.y, self.size, self.size)

    def update(self, target_x, target_y):
        # Gruby Moćko podąża za Miziewiczem
        dx = target_x - self.x
        dy = target_y - self.y
        dist = math.hypot(dx, dy)
        
        if dist > 0:
            self.x += (dx / dist) * self.speed
            self.y += (dy / dist) * self.speed
            
        self.rect.topleft = (self.x, self.y)

    def draw(self, surface):
        if mocko_img:
            surface.blit(mocko_img, self.rect)
        else:
            pygame.draw.rect(surface, RED, self.rect)
        # Pasek zdrowia Mocka
        pygame.draw.rect(surface, BLACK, (self.x, self.y - 20, self.size, 15))
        health_width = (self.health / self.max_health) * self.size
        pygame.draw.rect(surface, GREEN, (self.x, self.y - 20, health_width, 15))
        
        label = small_font.render("GRUBY MOĆKO", True, BLACK)
        surface.blit(label, (self.x, self.y - 45))

class Bullet:
    def __init__(self, x, y):
        self.x = x
        self.y = y
        self.radius = 5
        self.speed = 10
        self.rect = pygame.Rect(self.x - self.radius, self.y - self.radius, self.radius*2, self.radius*2)

    def update(self):
        self.y -= self.speed
        self.rect.center = (self.x, self.y)

    def draw(self, surface):
        if ammo_img:
            img_rect = ammo_img.get_rect(center=(int(self.x), int(self.y)))
            surface.blit(ammo_img, img_rect)
        else:
            pygame.draw.circle(surface, YELLOW, (int(self.x), int(self.y)), self.radius)

def main():
    player = Miziewicz()
    boss = GrubyMocko()
    bullets = []
    
    last_shot_time = 0
    shoot_delay = 200  # Opóźnienie między strzałami w milisekundach

    running = True
    game_over = False
    message = ""
    in_menu = True
    dragging_slider = None
    music_slider_rect = pygame.Rect(200, 240, 400, 20)
    sfx_slider_rect = pygame.Rect(200, 310, 400, 20)
    music_handle_rect = pygame.Rect(0, 0, 16, 32)
    sfx_handle_rect = pygame.Rect(0, 0, 16, 32)
    music_handle_rect.center = (music_slider_rect.left + int(music_volume * music_slider_rect.width), music_slider_rect.centery)
    sfx_handle_rect.center = (sfx_slider_rect.left + int(sfx_volume * sfx_slider_rect.width), sfx_slider_rect.centery)
    start_button = pygame.Rect(WIDTH // 2 - 100, 380, 200, 50)

    while running:
        current_time = pygame.time.get_ticks()
        screen.fill(WHITE)

        for event in pygame.event.get():
            if event.type == pygame.QUIT:
                running = False

            if in_menu:
                if event.type == pygame.MOUSEBUTTONDOWN and event.button == 1:
                    if start_button.collidepoint(event.pos):
                        in_menu = False
                        game_over = False
                        message = ""
                        player = Miziewicz()
                        boss = GrubyMocko()
                        bullets = []
                        last_shot_time = 0
                    elif music_slider_rect.collidepoint(event.pos) or music_handle_rect.collidepoint(event.pos):
                        dragging_slider = "music"
                    elif sfx_slider_rect.collidepoint(event.pos) or sfx_handle_rect.collidepoint(event.pos):
                        dragging_slider = "sfx"
                elif event.type == pygame.MOUSEBUTTONUP and event.button == 1:
                    dragging_slider = None
                elif event.type == pygame.MOUSEMOTION and dragging_slider:
                    if dragging_slider == "music":
                        mx = max(music_slider_rect.left, min(event.pos[0], music_slider_rect.right))
                        set_music_volume((mx - music_slider_rect.left) / music_slider_rect.width)
                        music_handle_rect.centerx = mx
                    elif dragging_slider == "sfx":
                        mx = max(sfx_slider_rect.left, min(event.pos[0], sfx_slider_rect.right))
                        set_sfx_volume((mx - sfx_slider_rect.left) / sfx_slider_rect.width)
                        sfx_handle_rect.centerx = mx
            else:
                if event.type == pygame.KEYDOWN and event.key == pygame.K_ESCAPE:
                    in_menu = True

        if in_menu:
            title = font.render("Miziewicz The Game", True, BLACK)
            title_rect = title.get_rect(center=(WIDTH // 2, 110))
            screen.blit(title, title_rect)

            info = small_font.render("Ustaw głośność muzyki i efektów", True, BLACK)
            info_rect = info.get_rect(center=(WIDTH // 2, 150))
            screen.blit(info, info_rect)

            pygame.draw.rect(screen, BLACK, music_slider_rect, 2)
            music_filled = pygame.Rect(music_slider_rect.left, music_slider_rect.top, int(music_volume * music_slider_rect.width), music_slider_rect.height)
            pygame.draw.rect(screen, GREEN, music_filled)
            music_handle_rect.center = (music_slider_rect.left + int(music_volume * music_slider_rect.width), music_slider_rect.centery)
            pygame.draw.rect(screen, BLACK, music_handle_rect)
            music_label = small_font.render(f"Muzyka: {int(music_volume * 100)}%", True, BLACK)
            screen.blit(music_label, (music_slider_rect.left, music_slider_rect.top - 25))

            pygame.draw.rect(screen, BLACK, sfx_slider_rect, 2)
            sfx_filled = pygame.Rect(sfx_slider_rect.left, sfx_slider_rect.top, int(sfx_volume * sfx_slider_rect.width), sfx_slider_rect.height)
            pygame.draw.rect(screen, GREEN, sfx_filled)
            sfx_handle_rect.center = (sfx_slider_rect.left + int(sfx_volume * sfx_slider_rect.width), sfx_slider_rect.centery)
            pygame.draw.rect(screen, BLACK, sfx_handle_rect)
            sfx_label = small_font.render(f"SFX: {int(sfx_volume * 100)}%", True, BLACK)
            screen.blit(sfx_label, (sfx_slider_rect.left, sfx_slider_rect.top - 25))

            pygame.draw.rect(screen, BLUE, start_button)
            start_text = font.render("START", True, WHITE)
            start_text_rect = start_text.get_rect(center=start_button.center)
            screen.blit(start_text, start_text_rect)

            controls_text = small_font.render("Spacja = strzał, ESC = menu", True, BLACK)
            controls_rect = controls_text.get_rect(center=(WIDTH // 2, 460))
            screen.blit(controls_text, controls_rect)
        else:
            keys = pygame.key.get_pressed()
            if not game_over:
                player.move(keys)

                if keys[pygame.K_SPACE] and current_time - last_shot_time > shoot_delay:
                    bullets.append(Bullet(player.x + player.size // 2, player.y))
                    last_shot_time = current_time
                    if shoot_sound:
                        shoot_sound.play()

                boss.update(player.x, player.y)

                for bullet in bullets[:]:
                    bullet.update()
                    if bullet.y < 0:
                        bullets.remove(bullet)
                    elif bullet.rect.colliderect(boss.rect):
                        boss.health -= 10
                        play_random_sound(hit_sounds)
                        if bullet in bullets:
                            bullets.remove(bullet)

                if player.rect.colliderect(boss.rect):
                    previous_health = player.health
                    player.health -= 2
                    if player.health <= 0:
                        player.health = 0
                        game_over = True
                        message = "PRZEGRAŁEŚ! GRUBY MOĆKO CIĘ ZMIAŻDŻYŁ!"
                        if miziewicz_death_sound:
                            miziewicz_death_sound.play()
                    elif previous_health > 0:
                        play_random_sound(player_hit_sounds)

                if not game_over and boss.health <= 0:
                    game_over = True
                    message = "WYGRAŁEŚ! POKONAŁEŚ GRUBEGO MOĆKA!"
                    if mocko_death_sound:
                        mocko_death_sound.play()

            player.draw(screen)
            if boss.health > 0:
                boss.draw(screen)

            for bullet in bullets:
                bullet.draw(screen)

            if game_over:
                text = font.render(message, True, BLACK)
                text_rect = text.get_rect(center=(WIDTH // 2, HEIGHT // 2))
                screen.blit(text, text_rect)

                restart_text = small_font.render("Naciśnij 'R', aby zagrać ponownie", True, BLACK)
                restart_rect = restart_text.get_rect(center=(WIDTH // 2, HEIGHT // 2 + 50))
                screen.blit(restart_text, restart_rect)

                if keys[pygame.K_r]:
                    player = Miziewicz()
                    boss = GrubyMocko()
                    bullets = []
                    last_shot_time = 0
                    game_over = False
                    message = ""

        pygame.display.flip()
        clock.tick(60)

    pygame.quit()
    sys.exit()

if __name__ == "__main__":
    main()
