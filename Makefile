.PHONY: help build run stop clean logs shell test dev production

# Default target
help:
	@echo "Available commands:"
	@echo "  build       - Build Docker image"
	@echo "  run         - Run application in development mode"
	@echo "  production  - Run application in production mode with Nginx"
	@echo "  stop        - Stop all containers"
	@echo "  clean       - Remove containers and images"
	@echo "  logs        - Show application logs"
	@echo "  shell       - Open shell in running container"
	@echo "  test        - Run tests"
	@echo "  dev         - Run in development mode (local Python)"

# Docker commands
build:
	docker-compose build

run:
	docker-compose up -d

production:
	docker-compose --profile production up -d

stop:
	docker-compose down

clean:
	docker-compose down -v --rmi all --remove-orphans

logs:
	docker-compose logs -f video-watermark

shell:
	docker-compose exec video-watermark /bin/bash

# Development commands
dev:
	python app.py

test:
	pytest -v --cov=watermark tests/

format:
	black . --exclude="venv|env"

lint:
	flake8 . --exclude="venv,env" --max-line-length=88

# Setup commands
setup:
	cp .env.example .env
	mkdir -p uploads processed logs
	echo "Please edit .env file with your configuration"

install:
	pip install -r requirements.txt

# Backup and restore
backup:
	tar -czf backup_$(shell date +%Y%m%d_%H%M%S).tar.gz uploads processed

# Security
security-check:
	docker run --rm -v $(PWD):/app securecodewarrior/docker-image-validator /app/Dockerfile
