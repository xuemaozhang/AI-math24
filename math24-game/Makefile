.PHONY: help install test test-ui test-coverage dev dev-all stop-backend build preview lint clean

# Default target
help:
	@echo "Available commands:"
	@echo "  make install        - Install dependencies"
	@echo "  make test           - Run all tests"
	@echo "  make test-ui        - Run tests with UI"
	@echo "  make test-coverage  - Run tests with coverage"
	@echo "  make dev            - Start development server"
	@echo "  make dev-all        - Start backend and frontend together"
	@echo "  make stop-backend   - Stop backend started by dev-all"
	@echo "  make build          - Build for production"
	@echo "  make preview        - Preview production build"
	@echo "  make lint           - Run linter"
	@echo "  make clean          - Remove build and cache files"

# Install dependencies
install:
	npm install

# Run tests
test:
	npm test -- --run

# Run tests with UI
test-ui:
	npm run test:ui

# Run tests with coverage
test-coverage:
	npm run test:coverage

# Start development server
dev:
	npm run dev

# Start both backend (uvicorn) and frontend (vite) together
dev-all:
	@echo "Starting backend (uvicorn) in background..."
	@cd ../backend && uv run uvicorn main:app --reload --host 0.0.0.0 --port 8000 & echo $$! > ../math24-game/.backend.pid
	@echo "Backend PID: `cat .backend.pid`"
	@echo "Starting frontend (vite)..."
	@npm run dev
	@echo "Shutting down backend..."
	@-if test -f .backend.pid; then kill `cat .backend.pid` || true; rm .backend.pid; fi

# Stop backend if still running (after dev-all)
stop-backend:
	@-if test -f .backend.pid; then echo "Stopping backend `cat .backend.pid`"; kill `cat .backend.pid` || true; rm .backend.pid; else echo "No backend PID file found."; fi

# Build for production
build:
	npm run build

# Preview production build
preview:
	npm run preview

# Run linter
lint:
	npm run lint

# Clean build and cache files
clean:
	rm -rf dist node_modules/.vite
	find . -type d -name ".vite" -exec rm -rf {} + 2>/dev/null || true
