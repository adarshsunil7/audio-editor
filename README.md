# Audio Editor

A web-based audio editor with a React frontend and Flask backend.

## Prerequisites

- **Python**: 3.10+
- **Node.js**: 18+

## Frontend

The frontend is a React application using Vite.

### Setup

```bash
cd audio-editor-frontend
npm install
```

### Development

```bash
npm run dev
```

The frontend will start at `http://localhost:5173`.

### Build

```bash
npm run build
```

## Backend

The backend is a Flask application.

### Setup

```bash
cd audio_editor
python -m venv venv
source venv/bin/activate  # macOS/Linux
# venv\Scripts\activate  # Windows
pip install -r requirements.txt
```

### Running

```bash
python -m flask --app api run --port 5001
```

The API will be available at `http://localhost:5001`.

## Development (Running Both)

### Option 1: Using Makefile

```bash
make dev
```

This runs both the backend and frontend in parallel.

### Option 2: Manual

1. Start the backend:
   ```bash
   cd audio_editor
   source venv/bin/activate
   python -m flask --app api run --port 5001
   ```

2. In another terminal, start the frontend:
   ```bash
   cd audio-editor-frontend
   npm run dev
   ```

## Available Makefile Targets

- `make install` - Install all dependencies (frontend + backend)
- `make dev` - Run both frontend and backend
- `make build` - Build the frontend for production
- `make clean` - Remove build artifacts