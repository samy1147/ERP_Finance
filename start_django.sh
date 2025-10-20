#!/bin/bash

echo "Starting Django Backend Server..."
echo ""

# Get the directory where the script is located
SCRIPT_DIR="$( cd "$( dirname "${BASH_SOURCE[0]}" )" && pwd )"

cd "$SCRIPT_DIR"

# Check if virtual environment exists
if [ ! -d "venv" ]; then
    echo "ERROR: Virtual environment not found!"
    echo "Please create it with: python3 -m venv venv"
    echo "Then activate and install: source venv/bin/activate && pip install -r requirements.txt"
    read -p "Press Enter to continue..."
    exit 1
fi

# Use python3 or python, whichever is available
if [ -f "./venv/bin/python3" ]; then
    PYTHON="./venv/bin/python3"
elif [ -f "./venv/bin/python" ]; then
    PYTHON="./venv/bin/python"
else
    echo "ERROR: Python not found in virtual environment!"
    read -p "Press Enter to continue..."
    exit 1
fi

echo "Using Python: $PYTHON"
echo "Starting on http://localhost:8007"
echo ""

$PYTHON manage.py runserver 8007

read -p "Press Enter to continue..."
