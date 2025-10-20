#!/bin/bash

echo "========================================"
echo "Finance ERP - Complete System Startup"
echo "========================================"
echo ""
echo "Starting both Backend and Frontend..."
echo ""
echo "Backend will run on: http://localhost:8007"
echo "Frontend will run on: http://localhost:3000"
echo ""
echo "Press Ctrl+C to stop both servers"
echo "========================================"
echo ""

# Get the directory where the script is located
SCRIPT_DIR="$( cd "$( dirname "${BASH_SOURCE[0]}" )" && pwd )"

# Check if virtual environment exists
if [ ! -d "$SCRIPT_DIR/venv" ]; then
    echo "ERROR: Virtual environment not found!"
    echo "Please create it with: python3 -m venv venv"
    echo "Then activate and install: source venv/bin/activate && pip install -r requirements.txt"
    exit 1
fi

# Check if npm is installed
if ! command -v npm &> /dev/null; then
    echo "ERROR: npm is not installed!"
    echo "On Oracle Linux, install with: sudo yum install nodejs npm"
    exit 1
fi

# Function to cleanup background processes on exit
cleanup() {
    echo ""
    echo "Shutting down servers..."
    kill $BACKEND_PID $FRONTEND_PID 2>/dev/null
    wait $BACKEND_PID $FRONTEND_PID 2>/dev/null
    echo "Servers stopped."
    exit 0
}

# Trap Ctrl+C and call cleanup
trap cleanup INT TERM

# Start Django backend in background
echo "Starting Django backend..."
cd "$SCRIPT_DIR"

# Use python3 or python, whichever is available
if [ -f "./venv/bin/python3" ]; then
    PYTHON="./venv/bin/python3"
elif [ -f "./venv/bin/python" ]; then
    PYTHON="./venv/bin/python"
else
    echo "ERROR: Python not found in virtual environment!"
    exit 1
fi

$PYTHON manage.py runserver 8007 > backend.log 2>&1 &
BACKEND_PID=$!
echo "Django backend started (PID: $BACKEND_PID)"

# Wait a moment for backend to start
sleep 3

# Start Next.js frontend in background
echo "Starting Next.js frontend..."
cd "$SCRIPT_DIR/frontend"
npm run dev > ../frontend.log 2>&1 &
FRONTEND_PID=$!
echo "Next.js frontend started (PID: $FRONTEND_PID)"

# Wait a moment for frontend to start
sleep 5

echo ""
echo "Both servers are running!"
echo ""
echo "Django Backend: http://localhost:8007"
echo "Next.js Frontend: http://localhost:3000"
echo ""
echo "Logs are being written to:"
echo "  - backend.log"
echo "  - frontend.log"
echo ""
echo "Press Ctrl+C to stop both servers"
echo ""

# Try to open browser (works on most Linux desktop environments)
if command -v xdg-open > /dev/null; then
    xdg-open http://localhost:3000 2>/dev/null &
elif command -v gnome-open > /dev/null; then
    gnome-open http://localhost:3000 2>/dev/null &
fi

# Wait for background processes
wait $BACKEND_PID $FRONTEND_PID
