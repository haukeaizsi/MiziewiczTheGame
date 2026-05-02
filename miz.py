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

# Stany gry
MENU = 0
GAME = 1
SETTINGS = 2

# Ustawienia audio
music_volume = 0.2
sound_volume = 1.0

# Czcionki
font = pygame.font.SysFont("Arial", 36)
small_font = pygame.font.SysFont("Arial", 20)

# Ścieżki do zasobów
base_path = getattr(sys, '_MEIPASS', os.path.dirname(__file__))
ASSET_DIR = os.path.join(base_path, "assets")
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

win_sound = load_sound(os.path.join(SFX_DIR, "win.mp3"))
lose_sound = load_sound(os.path.join(SFX_DIR, "lose.mp3"))

music_path = os.path.join(SFX_DIR, "music.mp3")
if os.path.isfile(music_path):
    try:
        pygame.mixer.music.load(music_path)
        pygame.mixer.music.set_volume(music_volume)
        pygame.mixer.music.play(-1)
    except pygame.error:
        pass


def play_random_sound(sounds):
    sounds = [sound for sound in sounds if sound]
    if sounds:
        sound = random.choice(sounds)
        sound.set_volume(sound_volume)
        sound.play()

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
            surface.blit(ammo_img, (self.x - ammo_img.get_width() // 2, self.y - ammo_img.get_height() // 2))
        else:
            pygame.draw.circle(surface, YELLOW, (int(self.x), int(self.y)), self.radius)


class Button:
    def __init__(self, x, y, width, height, text, color=BLUE, hover_color=GREEN):
        self.rect = pygame.Rect(x, y, width, height)
        self.text = text
        self.color = color
        self.hover_color = hover_color
        self.is_hovered = False

    def draw(self, surface):
        color = self.hover_color if self.is_hovered else self.color
        pygame.draw.rect(surface, color, self.rect)
        pygame.draw.rect(surface, BLACK, self.rect, 2)
        text_surf = small_font.render(self.text, True, BLACK)
        text_rect = text_surf.get_rect(center=self.rect.center)
        surface.blit(text_surf, text_rect)

    def check_hover(self, mouse_pos):
        self.is_hovered = self.rect.collidepoint(mouse_pos)

    def is_clicked(self, mouse_pos, mouse_click):
        return self.rect.collidepoint(mouse_pos) and mouse_click


def main():
    global music_volume, sound_volume
    state = MENU

    # Przyciski menu
    start_button = Button(WIDTH // 2 - 100, HEIGHT // 2 - 50, 200, 50, "Start Game")
    settings_button = Button(WIDTH // 2 - 100, HEIGHT // 2, 200, 50, "Settings")
    quit_button = Button(WIDTH // 2 - 100, HEIGHT // 2 + 50, 200, 50, "Quit")

    # Przyciski settings
    music_up_button = Button(WIDTH // 2 - 100, HEIGHT // 2 - 80, 50, 50, "+")
    music_down_button = Button(WIDTH // 2, HEIGHT // 2 - 80, 50, 50, "-")
    sound_up_button = Button(WIDTH // 2 - 100, HEIGHT // 2, 50, 50, "+")
    sound_down_button = Button(WIDTH // 2, HEIGHT // 2, 50, 50, "-")
    back_button = Button(WIDTH // 2 - 100, HEIGHT // 2 + 100, 200, 50, "Back")

    # Zmienne gry
    player = None
    boss = None
    bullets = []
    last_shot_time = 0
    shoot_delay = 200
    game_over = False
    message = ""
    last_hit_sound_time = 0
    hit_sound_delay = 500  # 0.5 sekundy

    running = True
    while running:
        current_time = pygame.time.get_ticks()
        screen.fill(WHITE)
        mouse_pos = pygame.mouse.get_pos()
        mouse_click = False

        # Obsługa zdarzeń
        for event in pygame.event.get():
            if event.type == pygame.QUIT:
                running = False
            elif event.type == pygame.MOUSEBUTTONDOWN and event.button == 1:
                mouse_click = True

        if state == MENU:
            # Rysowanie menu
            title = font.render("MIZIEWICZ THE GAME", True, BLACK)
            title_rect = title.get_rect(center=(WIDTH // 2, HEIGHT // 2 - 150))
            screen.blit(title, title_rect)

            start_button.check_hover(mouse_pos)
            start_button.draw(screen)
            settings_button.check_hover(mouse_pos)
            settings_button.draw(screen)
            quit_button.check_hover(mouse_pos)
            quit_button.draw(screen)

            if start_button.is_clicked(mouse_pos, mouse_click):
                state = GAME
                player = Miziewicz()
                boss = GrubyMocko()
                bullets = []
                last_shot_time = 0
                game_over = False
                message = ""
            elif settings_button.is_clicked(mouse_pos, mouse_click):
                state = SETTINGS
            elif quit_button.is_clicked(mouse_pos, mouse_click):
                running = False

        elif state == SETTINGS:
            # Rysowanie settings
            title = font.render("AUDIO SETTINGS", True, BLACK)
            title_rect = title.get_rect(center=(WIDTH // 2, HEIGHT // 2 - 150))
            screen.blit(title, title_rect)

            music_label = small_font.render(f"Music Volume: {int(music_volume * 100)}%", True, BLACK)
            screen.blit(music_label, (WIDTH // 2 - 300, HEIGHT // 2 - 110))
            music_up_button.check_hover(mouse_pos)
            music_up_button.draw(screen)
            music_down_button.check_hover(mouse_pos)
            music_down_button.draw(screen)

            sound_label = small_font.render(f"Sound Volume: {int(sound_volume * 100)}%", True, BLACK)
            screen.blit(sound_label, (WIDTH // 2 - 300, HEIGHT // 2 + 10))
            sound_up_button.check_hover(mouse_pos)
            sound_up_button.draw(screen)
            sound_down_button.check_hover(mouse_pos)
            sound_down_button.draw(screen)

            back_button.check_hover(mouse_pos)
            back_button.draw(screen)

            if music_up_button.is_clicked(mouse_pos, mouse_click):
                music_volume = min(1.0, music_volume + 0.1)
                pygame.mixer.music.set_volume(music_volume)
            elif music_down_button.is_clicked(mouse_pos, mouse_click):
                music_volume = max(0.0, music_volume - 0.1)
                pygame.mixer.music.set_volume(music_volume)
            elif sound_up_button.is_clicked(mouse_pos, mouse_click):
                sound_volume = min(1.0, sound_volume + 0.1)
            elif sound_down_button.is_clicked(mouse_pos, mouse_click):
                sound_volume = max(0.0, sound_volume - 0.1)
            elif back_button.is_clicked(mouse_pos, mouse_click):
                state = MENU

        elif state == GAME:
            if not game_over:
                keys = pygame.key.get_pressed()
                player.move(keys)
                
                # Strzelanie (Spacja)
                if keys[pygame.K_SPACE] and current_time - last_shot_time > shoot_delay:
                    bullets.append(Bullet(player.x + player.size // 2, player.y))
                    last_shot_time = current_time
                    if shoot_sound:
                        shoot_sound.set_volume(sound_volume)
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
                    if current_time - last_hit_sound_time > hit_sound_delay:
                        play_random_sound(player_hit_sounds)
                        last_hit_sound_time = current_time

                # Sprawdzenie warunków wygranej / przegranej
                if boss.health <= 0:
                    game_over = True
                    message = "WYGRAŁEŚ! POKONAŁEŚ GRUBEGO MOĆKA!"
                    pygame.mixer.music.stop()
                    if win_sound:
                        win_sound.set_volume(sound_volume)
                        win_sound.play()
                    if mocko_death_sound:
                        mocko_death_sound.set_volume(sound_volume)
                        mocko_death_sound.play()
                elif player.health <= 0:
                    game_over = True
                    message = "PRZEGRAŁEŚ! GRUBY MOĆKO CIĘ ZMIAŻDŻYŁ!"
                    pygame.mixer.music.stop()
                    if lose_sound:
                        lose_sound.set_volume(sound_volume)
                        lose_sound.play()
                    if miziewicz_death_sound:
                        miziewicz_death_sound.set_volume(sound_volume)
                        miziewicz_death_sound.play()

            # Rysowanie elementów gry
            player.draw(screen)
            if boss.health > 0:
                boss.draw(screen)
                
            for bullet in bullets:
                bullet.draw(screen)

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
                    last_hit_sound_time = 0
                    pygame.mixer.music.play(-1)

        pygame.display.flip()
        clock.tick(60)

    pygame.quit()
    sys.exit()

if __name__ == "__main__":
    main()
