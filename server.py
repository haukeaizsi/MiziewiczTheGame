import asyncio
import websockets
import json
import uuid
import math
from enum import Enum
from dataclasses import dataclass, asdict
from typing import Dict, Set

class GameState(Enum):
    WAITING = "waiting"
    PLAYING = "playing"
    GAME_OVER = "game_over"

@dataclass
class Player:
    id: str
    name: str
    color: tuple
    x: float
    y: float
    health: int = 100
    max_health: int = 100
    bullets: list = None
    
    def __post_init__(self):
        if self.bullets is None:
            self.bullets = []

@dataclass
class GameData:
    players: Dict[str, dict]
    bosses: list
    state: str
    time: int

class GameServer:
    def __init__(self, width=1600, height=1200, max_players=4):
        self.width = width
        self.height = height
        self.max_players = max_players
        self.clients: Dict[str, websockets.WebSocketServerProtocol] = {}
        self.players: Dict[str, dict] = {}
        self.game_state = GameState.WAITING
        self.colors = [
            (0, 100, 255),    # Niebieski
            (255, 0, 0),      # Czerwony
            (255, 255, 0),    # Żółty
            (0, 200, 0)       # Zielony
        ]
        self.game_time = 0
        self.boss = {
            "x": width // 2 - 50,
            "y": 150,
            "size": 100,
            "health": 500,
            "max_health": 500,
            "speed": 1.5
        }
    
    async def register_player(self, websocket, player_name):
        player_id = str(uuid.uuid4())[:8]
        
        if len(self.players) >= self.max_players:
            await websocket.send(json.dumps({
                "type": "error",
                "message": "Serwer pełny!"
            }))
            return None
        
        color_idx = len(self.players)
        spawn_x = 200 + color_idx * 300
        spawn_y = self.height - 150
        
        self.clients[player_id] = websocket
        self.players[player_id] = {
            "id": player_id,
            "name": player_name,
            "color": self.colors[color_idx],
            "x": spawn_x,
            "y": spawn_y,
            "health": 100,
            "max_health": 100,
            "bullets": [],
            "score": 0
        }
        
        if len(self.players) == self.max_players or len(self.players) >= 2:
            self.game_state = GameState.PLAYING
        
        return player_id
    
    async def unregister_player(self, player_id):
        if player_id in self.clients:
            del self.clients[player_id]
        if player_id in self.players:
            del self.players[player_id]
    
    async def broadcast(self, message):
        """Wyślij do wszystkich klientów"""
        if self.clients:
            await asyncio.gather(
                *[client.send(json.dumps(message)) for client in self.clients.values()],
                return_exceptions=True
            )
    
    async def handle_player_input(self, player_id, data):
        if player_id not in self.players:
            return
        
        player = self.players[player_id]
        
        # Ruch
        if data.get("move"):
            move = data["move"]
            speed = 5
            if move == "left":
                player["x"] -= speed
            elif move == "right":
                player["x"] += speed
            elif move == "up":
                player["y"] -= speed
            elif move == "down":
                player["y"] += speed
            
            player["x"] = max(0, min(self.width - 40, player["x"]))
            player["y"] = max(0, min(self.height - 40, player["y"]))
        
        # Strzał
        if data.get("shoot"):
            bullet = {
                "x": player["x"] + 20,
                "y": player["y"],
                "speed": 10,
                "owner": player_id
            }
            player["bullets"].append(bullet)
    
    async def update_game(self):
        """Główna pętla gry"""
        while True:
            if self.game_state == GameState.PLAYING:
                self.game_time += 1
                
                # Update pocisków
                for player_id in list(self.players.keys()):
                    player = self.players[player_id]
                    bullets_to_remove = []
                    
                    for i, bullet in enumerate(player["bullets"]):
                        bullet["y"] -= bullet["speed"]
                        
                        # Kolizja z bosem
                        if self.check_collision_circle(
                            bullet["x"], bullet["y"], 5,
                            self.boss["x"], self.boss["y"], self.boss["size"] // 2
                        ):
                            self.boss["health"] -= 10
                            bullets_to_remove.append(i)
                        
                        # Pocisk poza ekranem
                        elif bullet["y"] < 0:
                            bullets_to_remove.append(i)
                    
                    for i in reversed(bullets_to_remove):
                        player["bullets"].pop(i)
                
                # Boss podąża za graczami
                if self.players:
                    avg_x = sum(p["x"] for p in self.players.values()) / len(self.players)
                    avg_y = sum(p["y"] for p in self.players.values()) / len(self.players)
                    
                    dx = avg_x - self.boss["x"]
                    dy = avg_y - self.boss["y"]
                    dist = math.hypot(dx, dy)
                    
                    if dist > 0:
                        self.boss["x"] += (dx / dist) * self.boss["speed"]
                        self.boss["y"] += (dy / dist) * self.boss["speed"]
                
                # Kolizja graczy z bosem
                for player_id in list(self.players.keys()):
                    player = self.players[player_id]
                    if self.check_collision_square(
                        player["x"], player["y"], 40,
                        self.boss["x"], self.boss["y"], self.boss["size"]
                    ):
                        player["health"] -= 1
                
                # Sprawdzenie warunku wygranej
                if self.boss["health"] <= 0:
                    self.game_state = GameState.GAME_OVER
                
                # Sprawdzenie przegranej
                alive = any(p["health"] > 0 for p in self.players.values())
                if not alive:
                    self.game_state = GameState.GAME_OVER
                
                # Wysyłanie stanu do klientów
                await self.broadcast({
                    "type": "game_state",
                    "players": self.players,
                    "boss": self.boss,
                    "game_state": self.game_state.value,
                    "time": self.game_time
                })
            
            await asyncio.sleep(0.016)  # ~60 FPS
    
    def check_collision_circle(self, x1, y1, r1, x2, y2, r2):
        dist = math.hypot(x1 - x2, y1 - y2)
        return dist < r1 + r2
    
    def check_collision_square(self, x1, y1, size1, x2, y2, size2):
        return not (x1 + size1 < x2 or x1 > x2 + size2 or
                    y1 + size1 < y2 or y1 > y2 + size2)

async def handle_client(websocket, game_server):
    player_id = None
    try:
        async for message in websocket:
            data = json.loads(message)
            
            if data["type"] == "join":
                player_id = await game_server.register_player(websocket, data.get("name", "Player"))
                if player_id:
                    await websocket.send(json.dumps({
                        "type": "join_success",
                        "player_id": player_id,
                        "players": game_server.players,
                        "boss": game_server.boss,
                        "arena_width": game_server.width,
                        "arena_height": game_server.height
                    }))
            
            elif data["type"] == "input" and player_id:
                await game_server.handle_player_input(player_id, data)
    
    except websockets.exceptions.ConnectionClosed:
        pass
    finally:
        if player_id:
            await game_server.unregister_player(player_id)

async def main():
    game_server = GameServer(width=1600, height=1200, max_players=4)
    
    # Uruchom pętlę gry
    asyncio.create_task(game_server.update_game())
    
    # Uruchom serwer WebSocket
    async with websockets.serve(
        lambda ws: handle_client(ws, game_server),
        "0.0.0.0",
        5000
    ):
        print("🎮 Serwer Miziewicz Multiplayer uruchomiony!")
        print("📍 Nasłuchuje na: 0.0.0.0:5000")
        print("⏳ Czekam na graczy...")
        await asyncio.Future()

if __name__ == "__main__":
    asyncio.run(main())
