# Miziewicz Multiplayer

Wieloosobowa wersja gry na 1600x1200 arenie. Max 4 graczy, wspólnie walczą z Grubym Moćką.

## Uruchomienie

### 1. Zainstaluj zależności
```bash
pip install -r requirements.txt
```

### 2. Uruchom serwer (na komputerze-hoście)
```bash
python server.py
```

Serwer będzie nasłuchiwać na:
```
ws://0.0.0.0:5000
```

### 3. Uruchom klientów (gracze)

Na tym samym komputerze:
```bash
python miz.py
```

**Na innym komputerze przez VPN/Internet:**
1. Dowiedz się IP hosta: `ipconfig` (szukaj IPv4 Address)
2. Zmień w `miz.py` linię:
```python
server_ip = "192.168.1.10"  # Twoje IP
```
3. Uruchom:
```bash
python miz.py
```

## Sterowanie

- **Strzałki/WASD** — ruch
- **Spacja** — strzał
- **ESC** — powrót do menu

## Kolory graczy

1. 🔵 Niebieski (Player 1)
2. 🔴 Czerwony (Player 2)
3. 🟡 Żółty (Player 3)
4. 🟢 Zielony (Player 4)

## Pliki

- `server.py` — Serwer WebSocket zarządzający grą
- `miz.py` — Klient Pygame dla graczy
- `miz_single_backup.py` — Backup oryginalnej gry single-player

## Mechanika

- Arena: 1600x1200
- Gracze się nawzajem nie eliminują
- Wszyscy razem walczą z Grubym Moćką
- Wygrana: Boss = 0 HP
- Przegrana: Wszyscy gracze = 0 HP

## Debugowanie

Jeśli serwer mówi "port już używany":
```bash
netstat -ano | findstr :5000
taskkill /PID <PID> /F
```

Zmień port w `server.py` linię:
```python
"5000"  → "5001"
```
