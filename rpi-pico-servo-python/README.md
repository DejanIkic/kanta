# RPi Pico Servo Control Python

Kompletan Python projekat za upravljanje SG90 servo motorom preko USB komunikacije između Raspberry Pi 5 i Raspberry Pi Pico.

## Projekt Struktura

```
rpi-pico-servo-python/
├── rpi_api/                    # FastAPI aplikacija
│   ├── __init__.py
│   ├── main.py                 # FastAPI ruter i endpointi
│   ├── servo_service.py        # Servo kontrola i serijska komunikacija
│   ├── models.py               # SQLAlchemy modeli za bazu
│   ├── database.py             # Database konekcija i konfiguracija
│   ├── config.py               # Konfiguracija i environment varijable
│   ├── requirements.txt        # Python zavisnosti
│   └── Dockerfile              # Docker image za RPi (ARM64)
├── pico_firmware/              # MicroPython kod za Pico
│   ├── main.py                 # Glavna logika i UART komunikacija
│   ├── servo_driver.py         # PWM kontrola serva
│   └── boot.py                 # Boot skripta
├── alembic/                    # Database migracije
│   ├── versions/
│   ├── env.py
│   └── script.py.mako
├── scripts/                    # Helper skripte
│   ├── flash_pico.py          # Skripta za flashing Pico-a
│   ├── setup.sh              # Setup skripta za RPi
│   └── deploy.sh             # Deployment skripta
├── .vscode/                   # VS Code Remote SSH settings
│   ├── settings.json         # Remote development settings
│   ├── launch.json           # Remote debugging configuration
│   └── tasks.json            # SSH task runner
├── docker-compose.yml          # PostgreSQL i RPi API servis
├── requirements.txt            # Global requirements
├── pyproject.toml             # Project konfiguracija
└── README.md                  # Dokumentacija
```

## Hardverski Setup

### Komponente
- **Raspberry Pi 5** - Glavni kontroler
- **Raspberry Pi Pico** - PWM generator za servo
- **SG90 Servo Motor** - 9g mikro servo
- **USB kabel** - Povezivanje RPi i Pico
- **Napajanje** - 5V za servo (može i sa RPi USB-a)

### Povezivanje
```
Pico Pinout:
├── GP0  → Servo Signal (žuto/orange)
├── VBUS → Servo VCC (crveno) - 5V iz USB-a
├── GND  → Servo GND (smeđe/crno)
└── UART pins za komunikaciju sa RPi
```

### USB Konekcija
- Povežite Pico sa RPi preko USB kabela
- Pico će se registrovati kao `/dev/ttyACM0` na RPi

## Softverski Setup

### 1. Priprema Raspberry Pi-ja

```bash
# Clone repozitorijum
git clone <repository-url> rpi-pico-servo-python
cd rpi-pico-servo-python

# Pokreni setup skriptu
chmod +x scripts/setup.sh
sudo ./scripts/setup.sh

# Restartuj sistem
sudo reboot
```

### 2. Flash Pico sa MicroPython

```bash
# Nakon restarta, povežite Pico u BOOTSEL modu
# (držite BOOTSEL taster dok povezujete USB)

# Install rshell za komunikaciju
pip install rshell

# Flash firmware i upload kod
python3 scripts/flash_pico.py
```

### 3. Pokretanje Aplikacije

#### Opcija A: Docker (preporučeno)
```bash
# Pokreni sve servise
docker-compose up -d

# Proveri status
docker-compose ps

# Prikazi logove
docker-compose logs -f api
```

#### Opcija B: Development
```bash
# Install zavisnosti
pip install -r requirements.txt

# Pokreni PostgreSQL (ako nije preko Docker-a)
sudo systemctl start postgresql

# Kreiraj bazu
createdb servo_db

# Pokreni migracije
alembic upgrade head

# Pokreni API server
python -m uvicorn rpi_api.main:app --host 0.0.0.0 --port 8000 --reload
```

## API Endpoint-i

### Kontrola Serva
- `POST /api/servo/{angle}` - Postavi servo na ugao (0-180°)
- `GET /api/servo/status` - Status konekcije sa Pico-om
- `GET /api/servo/history` - Zadnjih 100 pokreta iz baze

### System
- `GET /` - Root endpoint sa informacijama
- `GET /health` - Health check servisa
- `GET /docs` - Swagger dokumentacija

### Primeri
```bash
# Postavi servo na 90 stepeni
curl -X POST http://localhost:8000/api/servo/90

# Proveri status
curl http://localhost:8000/api/servo/status

# Istorija pokreta
curl http://localhost:8000/api/servo/history
```

## VS Code Remote Development

### 1. VS Code Setup
```bash
# Install VS Code na lokalnom računaru
# Install Remote SSH extension
```

### 2. SSH Konekcija
```bash
# VS Code → Command Palette → Remote-SSH: Connect to Host
# Unesite: pi@<RASPBERRY_PI_IP>
```

### 3. Development Workflow
- **F5** - Debug FastAPI aplikacije
- **Ctrl+Shift+P** → Tasks → Run task
- **Terminal** - Automatski se otvara na RPi-u

### Debugging
- Postavite breakpoint-ove u kodu
- Koristite "FastAPI Debug" konfiguraciju
- Remote debugging preko SSH tunela

## Database Setup

### PostgreSQL Konfiguracija
```bash
# Access pgAdmin (opciono)
http://localhost:5050
Email: admin@example.com
Password: admin

# Direct connection
Host: localhost
Port: 5432
Database: servo_db
User: postgres
Password: password
```

### Database Migracije
```bash
# Kreiraj novu migraciju
alembic revision --autogenerate -m "Opis migracije"

# Primeni migracije
alembic upgrade head

# Vrati migraciju
alembic downgrade -1
```

## Monitoring i Logging

### Logovi
```bash
# Docker logovi
docker-compose logs -f api
docker-compose logs -f postgres

# Application logovi
tail -f /var/log/servo-api.log
```

### Health Checks
```bash
# API health
curl http://localhost:8000/health

# Database health
docker-compose exec postgres pg_isready -U postgres
```

## Troubleshooting

### Pico nije pronađen
```bash
# Proveri USB device
lsusb | grep Pico

# Proveri serijski port
ls /dev/ttyACM*

# Proveri prava pristupa
sudo chmod 666 /dev/ttyACM0
```

### Servo ne reaguje
```bash
# Proveri Pico konekciju
minicom -D /dev/ttyACM0 -b 115200

# Test komanda
echo "ANGLE:90" > /dev/ttyACM0
```

### Database greške
```bash
# Proveri PostgreSQL status
sudo systemctl status postgresql

# Restartuj bazu
sudo systemctl restart postgresql
```

### Docker problemi
```bash
# Čisti Docker
docker-compose down -v
docker system prune -f
docker-compose up -d --build
```

## Development Tips

### Hot Reload
- FastAPI automatski detektuje promene
- Pico kod zahteva ponovni flash

### Testing
```bash
# Run testovi
pytest tests/ -v

# Test API sa httpx
python -c "import httpx; print(httpx.get('http://localhost:8000/health').json())"
```

### Code Quality
```bash
# Format kod
black rpi_api/ scripts/

# Sort imports
isort rpi_api/ scripts/

# Lint
flake8 rpi_api/ scripts/

# Type check
mypy rpi_api/
```

## Production Deployment

### 1. Environment Setup
```bash
# Kreiraj .env fajl
cp .env.example .env
# Edit .env sa production vrednostima
```

### 2. Security
```bash
# Promeni default lozinke
# Koristi HTTPS sa SSL certifikatom
# Limitiraj API pristup
```

### 3. Monitoring
```bash
# Setup monitoring (Prometheus/Grafana)
# Log aggregation (ELK stack)
# Alerting za sistemske greške
```

## API Reference

### ServoControl
| Method | Endpoint | Description |
|--------|----------|-------------|
| POST | `/api/servo/{angle}` | Set servo angle (0-180°) |
| GET | `/api/servo/status` | Get connection status |
| GET | `/api/servo/history` | Get movement history |
| GET | `/api/servo/history/{limit}` | Get limited history |

### Response Formats
```json
// Servo movement response
{
  "id": 1,
  "angle": 90,
  "timestamp": "2024-01-01T12:00:00Z",
  "success": true,
  "error_message": null,
  "response_time_ms": 150
}

// Status response
{
  "connected": true,
  "last_command": "2024-01-01T12:00:00Z",
  "total_movements": 42,
  "error_rate": 2.5
}
```

## License

MIT License - vidi LICENSE fajl za detalje.

## Autor

AI Assistant - RPi Pico Servo Control System

## Support

Za pitanja i podršku:
- Kreirajte GitHub issue
- Proverite troubleshooting sekciju
- Kontaktirajte autora projekta
