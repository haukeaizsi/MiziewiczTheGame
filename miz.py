import pygame
import sys
import asyncio
import websockets
import json
import math
import os
import threading
from dataclasses import dataclass

# Inicjalizacja Pygame
pygame.init()
try:
    pygame.mixer.init()
except pygame.error:
    pass

# Ustawienia ekranu
WIDTH, HEIGHT = 1200, 800
screen = pygame.display.set_mode((WIDTH, HEIGHT))
pygame.display.set_caption("Miziewicz The Game - Multiplayer")
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

def start_multiplayer_game(server_ip, server_port, player_name):
    """Główna pętla klienta multiplayer"""
    
<<<<<<< HEAD
    async def run_game():
        async with websockets.connect(f"ws://{server_ip}:{server_port}", ping_interval=None) as websocket:
            # Wysłanie żądania dołączenia
            await websocket.send(json.dumps({
                "type": "join",
                "name": player_name
            }))
            
            # Odbierz dane gracza
            join_msg = json.loads(await websocket.recv())
            if join_msg["type"] != "join_success":
                print("Błąd: Nie udało się dołączyć do gry")
                return
            
            player_id = join_msg["player_id"]
            players = join_msg["players"]
            boss = join_msg["boss"]
            arena_width = join_msg["arena_width"]
            arena_height = join_msg["arena_height"]
            
            camera_x = 0
            camera_y = 0
            last_shot_time = 0
            shoot_delay = 200
            running = True
            in_menu = False
            game_state = "playing"
            
            # Nasłuchiwanie wiadomości od serwera w osobnym wątku
            async def listen_server():
                nonlocal players, boss, game_state
                try:
                    async for message in websocket:
                        data = json.loads(message)
                        if data["type"] == "game_state":
                            players = data["players"]
                            boss = data["boss"]
                            game_state = data["game_state"]
                except:
                    pass
            
            asyncio.create_task(listen_server())
            
            # Pętla gry
            while running:
                current_time = pygame.time.get_ticks()
                screen.fill(WHITE)
                
                # Obsługa zdarzeń
                for event in pygame.event.get():
                    if event.type == pygame.QUIT:
                        running = False
                    elif event.type == pygame.KEYDOWN:
                        if event.key == pygame.K_ESCAPE:
                            running = False
                
                # Wejście gracza
                keys = pygame.key.get_pressed()
                move = None
                if keys[pygame.K_LEFT] or keys[pygame.K_a]:
                    move = "left"
                elif keys[pygame.K_RIGHT] or keys[pygame.K_d]:
                    move = "right"
                elif keys[pygame.K_UP] or keys[pygame.K_w]:
                    move = "up"
                elif keys[pygame.K_DOWN] or keys[pygame.K_s]:
                    move = "down"
                
                shoot = keys[pygame.K_SPACE] and current_time - last_shot_time > shoot_delay
                if shoot:
                    last_shot_time = current_time
                
                # Wyślij dane do serwera
                try:
                    await websocket.send(json.dumps({
                        "type": "input",
                        "move": move,
                        "shoot": shoot
                    }))
                except:
                    running = False
                
                # Rysowanie
                if player_id in players:
                    my_player = players[player_id]
                    camera_x = my_player["x"] - WIDTH // 2
                    camera_y = my_player["y"] - HEIGHT // 2
                    camera_x = max(0, min(arena_width - WIDTH, camera_x))
                    camera_y = max(0, min(arena_height - HEIGHT, camera_y))
                    
                    # Rysuj graczy
                    for pid, player in players.items():
                        px = player["x"] - camera_x
                        py = player["y"] - camera_y
                        
                        if -50 < px < WIDTH + 50 and -50 < py < HEIGHT + 50:
                            pygame.draw.rect(screen, player["color"], (px, py, 40, 40))
                            
                            # Pasek zdrowia
                            pygame.draw.rect(screen, RED, (px, py - 15, 40, 8))
                            hw = (player["health"] / player["max_health"]) * 40
                            pygame.draw.rect(screen, GREEN, (px, py - 15, hw, 8))
                            
                            # Nazwa
                            name_text = tiny_font.render(player["name"], True, BLACK)
                            screen.blit(name_text, (px - 10, py - 30))
                            
                            # Pociski
                            for bullet in player["bullets"]:
                                bx = bullet["x"] - camera_x
                                by = bullet["y"] - camera_y
                                if -10 < bx < WIDTH + 10 and -10 < by < HEIGHT + 10:
                                    if ammo_img:
                                        img_rect = ammo_img.get_rect(center=(int(bx), int(by)))
                                        screen.blit(ammo_img, img_rect)
                                    else:
                                        pygame.draw.circle(screen, YELLOW, (int(bx), int(by)), 5)
                    
                    # Rysuj bossa
                    bx = boss["x"] - camera_x
                    by = boss["y"] - camera_y
                    
                    if -150 < bx < WIDTH + 150 and -150 < by < HEIGHT + 150:
                        pygame.draw.rect(screen, RED, (bx, by, boss["size"], boss["size"]))
                        
                        pygame.draw.rect(screen, BLACK, (bx, by - 25, boss["size"], 15))
                        bhw = (boss["health"] / boss["max_health"]) * boss["size"]
                        pygame.draw.rect(screen, GREEN, (bx, by - 25, bhw, 15))
                        
                        boss_label = small_font.render("GRUBY MOĆKO", True, BLACK)
                        screen.blit(boss_label, (bx - 30, by - 55))
                    
                    # UI
                    pygame.draw.rect(screen, GRAY, (10, 10, 300, 120), 2)
                    
                    for i, (pid, player) in enumerate(players.items()):
                        y_offset = 20 + i * 25
                        player_ui = tiny_font.render(f"{player['name']}: {player['health']}/{player['max_health']}", True, player["color"])
                        screen.blit(player_ui, (20, y_offset))
                    
                    # Koniec gry
                    if game_state == "game_over":
                        overlay = pygame.Surface((WIDTH, HEIGHT))
                        overlay.set_alpha(200)
                        overlay.fill(BLACK)
                        screen.blit(overlay, (0, 0))
                        
                        if boss["health"] <= 0:
                            msg = "ZWYCIĘSTWO!"
                            color = GREEN
                        else:
                            msg = "PORAŻKA!"
                            color = RED
                        
                        end_text = font.render(msg, True, color)
                        end_rect = end_text.get_rect(center=(WIDTH // 2, HEIGHT // 2))
                        screen.blit(end_text, end_rect)
                
                pygame.display.flip()
                clock.tick(60)
                await asyncio.sleep(0.001)
    
    asyncio.run(run_game())

# Font dla UI
tiny_font = pygame.font.SysFont("Arial", 14)
GRAY = (100, 100, 100)

def main():
    print("🎮 Miziewicz Multiplayer Client")
    print("=====================================")
    print("Podaj dane serwera:")
    
    # Domyślnie localhost
    server_ip = input("IP serwera (domyślnie localhost): ").strip() or "localhost"
    server_port = int(input("Port serwera (domyślnie 5000): ").strip() or "5000")
    player_name = input("Twoja nazwa gracza: ").strip() or "Player"
    
    print(f"\n⏳ Łączenie z {server_ip}:{server_port}...")
    print("Wciśnij ESC w grze, aby zakończyć.\n")
    
    try:
        start_multiplayer_game(server_ip, server_port, player_name)
    except Exception as e:
        print(f"❌ Błąd: {e}")
    finally:
        pygame.quit()
        sys.exit()
=======
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
>>>>>>> parent of 3f5509b (Miziewicz 1.0.1)

if __name__ == "__main__":
    main()
