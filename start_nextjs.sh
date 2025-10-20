#!/bin/bash

echo "Starting Next.js Frontend Server..."
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

echo "Starting on http://localhost:3000"
echo ""

npm run dev

read -p "Press Enter to continue..."
