# Makefile za RPi Pico Servo Control
# Autor: AI Assistant

.PHONY: help install setup flash deploy test lint format clean docker-up docker-down logs

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
	@echo "  clean       - Čisti cache i temp fajlove"

# Install dependencies
install:
	pip install -r requirements.txt
	pip install -r rpi_api/requirements.txt

# Setup RPi environment
setup:
	chmod +x scripts/setup.sh
	sudo ./scripts/setup.sh

# Flash Pico
flash:
	python3 scripts/flash_pico.py

# Development server
dev:
	python -m uvicorn rpi_api.main:app --host 0.0.0.0 --port 8000 --reload

# Run tests
test:
	python -m pytest tests/ -v --tb=short

# Lint code
lint:
	python -m flake8 rpi_api/ scripts/
	python -m mypy rpi_api/

# Format code
format:
	python -m black rpi_api/ scripts/
	python -m isort rpi_api/ scripts/

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
