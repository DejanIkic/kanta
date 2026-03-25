#!/bin/bash
# Setup skripta za Raspberry Pi 5
# Autor: AI Assistant

set -e

echo "=== RPi Pico Servo Control Setup ==="

# Proveri da li smo na Raspberry Pi
if ! grep -q "Raspberry Pi" /proc/cpuinfo; then
    echo "Upozorenje: Ova skripta je namenjena za Raspberry Pi"
    read -p "Nastaviti? (y/N): " -n 1 -r
    echo
    if [[ ! $REPLY =~ ^[Yy]$ ]]; then
        exit 1
    fi
fi

# Update sistema
echo "Update sistema..."
sudo apt update && sudo apt upgrade -y

# Instaliraj potrebne pakete
echo "Instalacija paketa..."
sudo apt install -y \
    python3.11 \
    python3.11-venv \
    python3.11-dev \
    python3-pip \
    git \
    curl \
    docker.io \
    docker-compose \
    postgresql-client \
    build-essential \
    libpq-dev \
    portaudio19-dev \
    python3-serial \
    minicom

# Instaliraj rshell i mpremote via pip (nisu dostupni kao apt paketi)
echo "Instalacija rshell i mpremote..."
pip3 install --break-system-packages rshell mpremote

# Dodaj korisnika u docker grupu
echo "Dodavanje korisnika u docker grupu..."
sudo usermod -aG docker $USER

# Omogući serijski port
echo "Konfiguracija serijskog porta..."
if ! grep -q "enable_uart=1" /boot/config.txt; then
    echo "enable_uart=1" | sudo tee -a /boot/config.txt
fi

# Konfiguriši USB za Pico
echo "Konfiguracija USB-a..."
if ! grep -q "max_usb_current=1" /boot/config.txt; then
    echo "max_usb_current=1" | sudo tee -a /boot/config.txt
fi

# Kreiraj direktorijume
echo "Kreiranje direktorijuma..."
mkdir -p /home/$USER/servo_logs
mkdir -p /home/$USER/servo_data

# Postaviti prava za serijski port
echo "Postavljanje prava za serijske portove..."
sudo usermod -a -G dialout $USER

# Kreiraj systemd servis za automatsko pokretanje
echo "Kreiranje systemd servisa..."
sudo tee /etc/systemd/system/servo-api.service > /dev/null <<EOF
[Unit]
Description=RPi Pico Servo Control API
After=docker.service
Requires=docker.service

[Service]
Type=oneshot
RemainAfterExit=yes
WorkingDirectory=/home/$USER/rpi-pico-servo-python
ExecStart=/usr/bin/docker-compose up -d
ExecStop=/usr/bin/docker-compose down
TimeoutStartSec=0

[Install]
WantedBy=multi-user.target
EOF

# Enable servis
sudo systemctl enable servo-api.service

# Install Python dependencies za development
echo "Instalacija Python development alata..."
python3.11 -m pip install --user \
    black \
    isort \
    flake8 \
    mypy \
    pytest \
    pytest-asyncio \
    httpx

# Konfiguriši git (ako nije)
if ! git config user.name; then
    echo "Konfiguracija Git-a..."
    read -p "Unesite Vaše ime: " git_name
    read -p "Unesite Vaš email: " git_email
    git config --global user.name "$git_name"
    git config --global user.email "$git_email"
fi

# Kreiraj .env fajl
if [ ! -f .env ]; then
    echo "Kreiranje .env fajla..."
    cat > .env <<EOF
# Database konfiguracija
DATABASE_URL=postgresql://postgres:password@localhost:5432/servo_db

# Serial port konfiguracija
SERIAL_PORT=/dev/ttyACM0
SERIAL_BAUDRATE=115200
SERIAL_TIMEOUT=1.0

# API konfiguracija
API_TITLE="RPi Pico Servo Control API"
API_VERSION="1.0.0"

# Logging
LOG_LEVEL=INFO
LOG_FORMAT=json

# Servo postavke
SERVO_MIN_ANGLE=0
SERVO_MAX_ANGLE=180
SERVO_MOVE_TIMEOUT=2.0
EOF
fi

# Vrati prava za ttyACM0
echo "Konfiguracija udev pravila..."
sudo tee /etc/udev/rules.d/99-pico.rules > /dev/null <<EOF
# Raspberry Pi Pico USB Serial
KERNEL=="ttyACM*", MODE="0666", GROUP="dialout"
EOF
sudo udevadm control --reload-rules
sudo udevadm trigger

echo ""
echo "=== Setup završen! ==="
echo ""
echo "Sledeći koraci:"
echo "1. Restartujte sistem: sudo reboot"
echo "2. Nakon restarta, clone-ujte repozitorijum"
echo "3. Povežite Pico i pokrenite: python3 scripts/flash_pico.py"
echo "4. Startujte servise: docker compose up -d"
echo "5. Proverite status: docker compose ps"
echo ""
echo "API će biti dostupan na: http://localhost:8000"
echo "Dokumentacija: http://localhost:8000/docs"
echo ""
echo "Napomena: Morate se logout/login da bi docker grupa imala efekat!"
