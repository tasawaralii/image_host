.PHONY: help install dev prod docker docker-up docker-down lint test clean

help:
	@echo "Anime Image Service - Available Commands"
	@echo "========================================"
	@echo ""
	@echo "Development:"
	@echo "  make install    - Install development dependencies"
	@echo "  make dev        - Run development server with auto-reload"
	@echo "  make lint       - Check code style (future)"
	@echo "  make test       - Run tests (future)"
	@echo ""
	@echo "Production:"
	@echo "  make prod       - Run production server with gunicorn"
	@echo "  make docker     - Build Docker image"
	@echo "  make docker-up  - Start Docker Compose stack"
	@echo "  make docker-down- Stop Docker Compose stack"
	@echo ""
	@echo "Utilities:"
	@echo "  make clean      - Clean cache and temp files"
	@echo "  make db-clean   - Delete database (careful!)"

install:
	python -m venv venv
	. venv/bin/activate && pip install -r requirements.txt

dev:
	. venv/bin/activate && uvicorn app.main:app --reload --host 0.0.0.0 --port 8000

prod:
	. venv/bin/activate && gunicorn app.main:app --workers 4 --worker-class uvicorn.workers.UvicornWorker --bind 0.0.0.0:8000

docker:
	docker build -t anime-image-service .

docker-up:
	docker-compose up -d

docker-down:
	docker-compose down

clean:
	find . -type d -name __pycache__ -exec rm -rf {} +
	find . -type f -name "*.pyc" -delete
	rm -rf .pytest_cache
	rm -rf .coverage

db-clean:
	rm -f images.db
	@echo "⚠️  Database deleted. Upload a new image to create it."
