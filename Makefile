.PHONY: help install run seed test clean

help:
	@echo "Available commands:"
	@echo "  make install  - Install dependencies"
	@echo "  make run      - Run the FastAPI server"
	@echo "  make seed     - Seed the database with sample data"
	@echo "  make test     - Run tests"
	@echo "  make clean    - Clean up generated files"

install:
	pip install -r requirements.txt

run:
	cd backend && uvicorn app.main:app --reload --host 0.0.0.0 --port 8000

seed:
	cd backend && python scripts/seed.py

test:
	cd backend && pytest tests/ -v

clean:
	find . -type d -name __pycache__ -exec rm -r {} + 2>/dev/null || true
	find . -type f -name "*.pyc" -delete
	find . -type f -name "*.pyo" -delete
	find . -type f -name "*.db" -delete
	find . -type f -name "*.sqlite" -delete