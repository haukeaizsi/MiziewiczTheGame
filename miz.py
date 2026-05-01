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

music_path = os.path.join(SFX_DIR, "music.mp3")
if os.path.isfile(music_path):
    try:
        pygame.mixer.music.load(music_path)
        pygame.mixer.music.set_volume(0.2)
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

    while running:
        current_time = pygame.time.get_ticks()
        screen.fill(WHITE)

        # Obsługa zdarzeń
        for event in pygame.event.get():
            if event.type == pygame.QUIT:
                running = False

        if not game_over:
            keys = pygame.key.get_pressed()
            player.move(keys)
            
            # Strzelanie (Spacja)
            if keys[pygame.K_SPACE] and current_time - last_shot_time > shoot_delay:
                bullets.append(Bullet(player.x + player.size // 2, player.y))
                last_shot_time = current_time
                if shoot_sound:
                    shoot_sound.play()

            boss.update(player.x, player.y)

            # Aktualizacja pocisków
            for bullet in bullets[:]:
                bullet.update()
                if bullet.y < 0:
                    bullets.remove(bullet)
                elif bullet.rect.colliderect(boss.rect):
                    boss.health -= 10
                    play_random_sound(hit_sounds)
                    if bullet in bullets:
                        bullets.remove(bullet)

            # Kolizja Moćka z Miziewiczem
            if player.rect.colliderect(boss.rect):
                player.health -= 2
                play_random_sound(player_hit_sounds)

            # Sprawdzenie warunków wygranej / przegranej
            if boss.health <= 0:
                game_over = True
                message = "WYGRAŁEŚ! POKONAŁEŚ GRUBEGO MOĆKA!"
                if mocko_death_sound:
                    mocko_death_sound.play()
            elif player.health <= 0:
                game_over = True
                message = "PRZEGRAŁEŚ! GRUBY MOĆKO CIĘ ZMIAŻDŻYŁ!"
                if miziewicz_death_sound:
                    miziewicz_death_sound.play()

        # Rysowanie elementów gry
        player.draw(screen)
        if boss.health > 0:
            boss.draw(screen)
            
        for bullet in bullets:
            bullet.draw(screen)

        if ammo_img:
            screen.blit(ammo_img, (20, 20))
            ammo_label = small_font.render("STRZAŁY", True, BLACK)
            screen.blit(ammo_label, (50, 20))

        # Wyświetlanie napisów końcowych
        if game_over:
            text = font.render(message, True, BLACK)
            text_rect = text.get_rect(center=(WIDTH // 2, HEIGHT // 2))
            screen.blit(text, text_rect)
            
            restart_text = small_font.render("Naciśnij 'R', aby zagrać ponownie", True, BLACK)
            restart_rect = restart_text.get_rect(center=(WIDTH // 2, HEIGHT // 2 + 50))
            screen.blit(restart_text, restart_rect)
            
            keys = pygame.key.get_pressed()
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
