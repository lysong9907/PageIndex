#!/usr/bin/env bash
set -e

# Build frontend
cd web
npm install
npm run build
cd ..

# Start backend (Render sets PORT env var)
PORT=${PORT:-8001}
uvicorn server.main:app --host 0.0.0.0 --port $PORT