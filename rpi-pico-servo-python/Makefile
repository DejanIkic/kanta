# Makefile za RPi Pico Servo Control
# Autor: AI Assistant

# Virtual environment
VENV   = venv
PYTHON = venv/bin/python3
PIP    = venv/bin/pip

.PHONY: help install setup flash update-firmware deploy test lint format clean docker-up docker-down logs venv

# Default target
help:
	@echo "RPi Pico Servo Control - Makefile komande"
	@echo ""
	@echo "Setup:"
	@echo "  install     - Install Python dependencies"
	@echo "  setup       - Pokreni setup skriptu za RPi"
	@echo ""
	@echo "Pico:"
	@echo "  flash       - Flash MicroPython na Pico"
	@echo "  update-firmware - Upload firmware fajlove i restartuj Pico"
	@echo ""
	@echo "Development:"
	@echo "  dev         - Pokreni development server"
	@echo "  test        - Run testove"
	@echo "  lint        - Lint kod"
	@echo "  format      - Format kod"
	@echo ""
	@echo "Docker:"
	@echo "  docker-up   - Pokreni Docker servise"
	@echo "  docker-down - Zaustavi Docker servise"
	@echo "  logs        - Prikazi Docker logove"
	@echo "  build       - Build Docker images"
	@echo ""
	@echo "Deployment:"
	@echo "  deploy      - Deploy aplikaciju"
	@echo "  clean       - Cisti cache i temp fajlove"

# Create virtual environment
venv:
	@if [ ! -d "$(VENV)" ]; then \
		echo "Creating virtual environment..."; \
		python3 -m venv $(VENV); \
	fi

# Install dependencies
install: venv
	$(PIP) install -r requirements.txt
	$(PIP) install -r rpi_api/requirements.txt
	@echo "Dependencies installed successfully."

# Setup RPi environment
setup:
	chmod +x scripts/setup.sh
	sudo ./scripts/setup.sh

# Flash Pico
flash:
	$(PYTHON) scripts/flash_pico.py

# Update firmware (upload files and restart)
update-firmware:
	$(PYTHON) scripts/update_firmware.py

# Development server (with debugpy)
dev:
	$(PYTHON) -m uvicorn rpi_api.main:app --host 0.0.0.0 --port 8000 --reload

# Debug server (without debugpy)
debug:
	$(PYTHON) -m debugpy --listen 0.0.0.0:5679 --wait-for-client -m uvicorn rpi_api.main:app --host 0.0.0.0 --port 8000 --reload

# Run tests
test:
	$(PYTHON) -m pytest tests/ -v --tb=short

# Lint code
lint:
	$(PYTHON) -m flake8 rpi_api/ scripts/
	$(PYTHON) -m mypy rpi_api/

# Format code
format:
	$(PYTHON) -m black rpi_api/ scripts/
	$(PYTHON) -m isort rpi_api/ scripts/

# Docker commands
docker-up:
	docker-compose up -d

docker-down:
	docker-compose down

logs:
	docker-compose logs -f

build:
	docker-compose build --no-cache

# Deployment
deploy:
	chmod +x scripts/deploy.sh
	./scripts/deploy.sh

# Database migrations
migrate:
	alembic upgrade head

migration:
	alembic revision --autogenerate -m "$(MSG)"

# Clean
clean:
	find . -type d -name "__pycache__" -delete
	find . -type f -name "*.pyc" -delete
	find . -type f -name "*.pyo" -delete
	find . -type d -name "*.egg-info" -exec rm -rf {} +
	rm -rf build/
	rm -rf dist/
	rm -rf venv/
	docker system prune -f

# Full setup for new environment
full-setup: install setup flash docker-up
	@echo "Full setup completed!"
	@echo "API dostupan na: http://localhost:8000"
	@echo "Dokumentacija: http://localhost:8000/docs"

# Quick development start
quick-dev: docker-up
	@echo "Development server started!"
	@echo "API: http://localhost:8000"
	@echo "Logs: make logs"
