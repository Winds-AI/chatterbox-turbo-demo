#!/bin/bash

echo "Starting Chatterbox Turbo - Streamlit + FastAPI"
echo ""

echo "[1/2] Starting FastAPI backend..."
cd backend
python main.py &
BACKEND_PID=$!
cd ..

sleep 3

echo "[2/2] Starting Streamlit frontend..."
streamlit run frontend/app.py

# Cleanup on exit
kill $BACKEND_PID 2>/dev/null
