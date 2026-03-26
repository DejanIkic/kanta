#!/bin/bash
# Deployment skripta za RPi Pico Servo Control
# Autor: AI Assistant

set -e

echo "=== RPi Pico Servo Control Deployment ==="

# Proveri da li smo u pravom direktorijumu
if [ ! -f "docker-compose.yml" ]; then
    echo "Greška: docker-compose.yml nije pronađen!"
    echo "Pokrenite skriptu iz projektnog direktorijuma."
    exit 1
fi

# Proveri Docker
if ! command -v docker &> /dev/null; then
    echo "Greška: Docker nije instaliran!"
    echo "Pokrenite: sudo ./scripts/setup.sh"
    exit 1
fi

# Proveri docker-compose
if ! command -v docker-compose &> /dev/null; then
    echo "Greška: docker-compose nije instaliran!"
    echo "Pokrenite: sudo ./scripts/setup.sh"
    exit 1
fi

# Proveri Pico konekciju
echo "Provera Pico konekcije..."
if [ ! -e "/dev/ttyAMA10" ]; then
    echo "Upozorenje: Pico (/dev/ttyAMA10) nije povezan!"
    read -p "Nastaviti bez Pico-a? (y/N): " -n 1 -r
    echo
    if [[ ! $REPLY =~ ^[Yy]$ ]]; then
        exit 1
    fi
else
    echo "Pico je povezan na /dev/ttyAMA10"
fi

# Pull najnovije changes
echo "Update koda..."
if [ -d ".git" ]; then
    git pull origin main || echo "Nije moguće uraditi git pull"
fi

# Build Docker images
echo "Build Docker images..."
docker-compose build --no-cache

# Zaustavi postojeće servise
echo "Zaustavljanje postojećih servisa..."
docker-compose down

# Pokreni servise
echo "Pokretanje servisa..."
docker-compose up -d

# Čekaj da servisi pokrenu
echo "Čekam da servisi pokrenu..."
sleep 10

# Proveri status servisa
echo "Status servisa:"
docker-compose ps

# Proveri health check
echo "Provera health check-a..."
for i in {1..30}; do
    if curl -f http://localhost:8000/health &> /dev/null; then
        echo "✓ API je zdrav!"
        break
    else
        echo "Čekam API da postane zdrav... ($i/30)"
        sleep 2
    fi
    
    if [ $i -eq 30 ]; then
        echo "⚠ API nije postao zdrav nakon 60 sekundi"
        echo "Proverite logove: docker-compose logs api"
    fi
done

# Proveri bazu
echo "Provera baze podataka..."
if docker-compose exec -T postgres pg_isready -U postgres; then
    echo "✓ Baza podataka je zdrava!"
else
    echo "⚠ Baza podataka nije spremna"
fi

# Prikaži logove
echo ""
echo "=== Poslednji API logovi ==="
docker-compose logs --tail=20 api

echo ""
echo "=== Deployment završen! ==="
echo ""
echo "Servisi:"
echo "- API: http://localhost:8000"
echo "- Dokumentacija: http://localhost:8000/docs"
echo "- PostgreSQL: localhost:5432"
echo ""
echo "Korisne komande:"
echo "- Proveri status: docker-compose ps"
echo "- Prikazi logove: docker-compose logs -f api"
echo "- Zaustavi servise: docker-compose down"
echo "- Restartuj API: docker-compose restart api"
echo ""
echo "Test komande:"
echo "- curl http://localhost:8000/api/servo/90"
echo "- curl http://localhost:8000/api/servo/status"
echo "- curl http://localhost:8000/api/servo/history"
