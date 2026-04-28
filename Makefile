.PHONY: install dev build clean

install:
	@echo "Installing frontend dependencies..."
	cd audio-editor-frontend && npm install
	@echo "Frontend dependencies installed."

dev:
	@echo "Starting backend..."
	cd audio_editor && source venv/bin/activate && python -m flask --app api run --port 5001 &
	@echo "Starting frontend..."
	cd audio-editor-frontend && npm run dev
	@echo "Both services are starting..."
	@echo "Frontend: http://localhost:5173"
	@echo "Backend:  http://localhost:5001"

build:
	@echo "Building frontend..."
	cd audio-editor-frontend && npm run build
	@echo "Build complete."

clean:
	@echo "Cleaning build artifacts..."
	cd audio-editor-frontend && rm -rf dist
	@echo "Clean complete."