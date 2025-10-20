#!/bin/bash

echo "========================================"
echo "Finance ERP - Frontend Startup"
echo "========================================"
echo ""

# Get the directory where the script is located
SCRIPT_DIR="$( cd "$( dirname "${BASH_SOURCE[0]}" )" && pwd )"

# Check if npm is installed
if ! command -v npm &> /dev/null; then
    echo "ERROR: npm is not installed!"
    echo "On Oracle Linux, install with: sudo yum install nodejs npm"
    read -p "Press Enter to continue..."
    exit 1
fi

cd "$SCRIPT_DIR/frontend"

# Check if frontend directory exists
if [ ! -f "package.json" ]; then
    echo "ERROR: Frontend directory not found or package.json missing!"
    read -p "Press Enter to continue..."
    exit 1
fi

echo "Checking if node_modules exists..."
if [ ! -d "node_modules" ]; then
    echo "Installing dependencies..."
    npm install
    if [ $? -ne 0 ]; then
        echo "ERROR: Failed to install dependencies!"
        read -p "Press Enter to continue..."
        exit 1
    fi
    echo ""
else
    echo "Dependencies already installed."
    echo ""
fi

echo "Starting Next.js development server..."
echo "Frontend will be available at: http://localhost:3000"
echo ""
echo "Press Ctrl+C to stop the server"
echo ""

npm run dev
