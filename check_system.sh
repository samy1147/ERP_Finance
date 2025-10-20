#!/bin/bash

echo "========================================"
echo "Finance ERP - System Check"
echo "========================================"
echo ""

# Detect OS
if [ -f /etc/oracle-release ]; then
    OS_TYPE="Oracle Linux"
    echo "Detected: Oracle Linux"
elif [ -f /etc/redhat-release ]; then
    OS_TYPE="Red Hat/CentOS"
    echo "Detected: Red Hat/CentOS"
elif [ -f /etc/debian_version ]; then
    OS_TYPE="Debian/Ubuntu"
    echo "Detected: Debian/Ubuntu"
else
    OS_TYPE="Unknown"
    echo "Detected: Unknown Linux distribution"
fi
echo ""

echo "Checking prerequisites..."
echo ""

# Color codes for better readability
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
NC='\033[0m' # No Color

# Get the directory where the script is located
SCRIPT_DIR="$( cd "$( dirname "${BASH_SOURCE[0]}" )" && pwd )"
cd "$SCRIPT_DIR"

# Check Python
echo "[1/4] Checking Python..."
if command -v python3 &> /dev/null; then
    PYTHON_VERSION=$(python3 --version 2>&1)
    echo "$PYTHON_VERSION"
    echo -e "${GREEN}[OK]${NC} Python is installed"
    if [[ "$OS_TYPE" == "Oracle Linux" ]]; then
        echo -e "${BLUE}[INFO]${NC} On Oracle Linux, install with: sudo yum install python3"
    fi
    echo ""
elif command -v python &> /dev/null; then
    PYTHON_VERSION=$(python --version 2>&1)
    echo "$PYTHON_VERSION"
    echo -e "${GREEN}[OK]${NC} Python is installed"
    echo ""
else
    echo -e "${RED}[ERROR]${NC} Python is not installed or not in PATH"
    if [[ "$OS_TYPE" == "Oracle Linux" ]]; then
        echo "On Oracle Linux, install with: sudo yum install python3 python3-pip"
    else
        echo "Please install Python 3.8+ from your package manager"
    fi
    echo ""
fi

# Check pip
echo "[2/4] Checking pip..."
if command -v pip3 &> /dev/null; then
    pip3 --version
    echo -e "${GREEN}[OK]${NC} pip is installed"
    echo ""
elif command -v pip &> /dev/null; then
    pip --version
    echo -e "${GREEN}[OK]${NC} pip is installed"
    echo ""
else
    echo -e "${RED}[ERROR]${NC} pip is not installed"
    echo ""
fi

# Check Node.js
echo "[3/4] Checking Node.js..."
if command -v node &> /dev/null; then
    NODE_VERSION=$(node --version 2>&1)
    echo "$NODE_VERSION"
    echo -e "${GREEN}[OK]${NC} Node.js is installed"
    if [[ "$OS_TYPE" == "Oracle Linux" ]]; then
        echo -e "${BLUE}[INFO]${NC} On Oracle Linux, install with: sudo yum install nodejs npm"
    fi
    echo ""
else
    echo -e "${RED}[ERROR]${NC} Node.js is not installed or not in PATH"
    if [[ "$OS_TYPE" == "Oracle Linux" ]]; then
        echo "On Oracle Linux, install with:"
        echo "  sudo yum install nodejs npm"
        echo "Or for newer versions, enable Node.js module:"
        echo "  sudo yum module install nodejs:18"
    else
        echo "Please install Node.js 18+ from https://nodejs.org/"
    fi
    echo ""
fi

# Check npm
echo "[4/4] Checking npm..."
if command -v npm &> /dev/null; then
    npm --version
    echo -e "${GREEN}[OK]${NC} npm is installed"
    echo ""
else
    echo -e "${RED}[ERROR]${NC} npm is not installed"
    echo ""
fi

echo "========================================"
echo "Checking project structure..."
echo "========================================"
echo ""

# Check if key files exist
if [ -f "manage.py" ]; then
    echo -e "${GREEN}[OK]${NC} Django project found"
else
    echo -e "${RED}[ERROR]${NC} manage.py not found - are you in the project root?"
fi

if [ -f "frontend/package.json" ]; then
    echo -e "${GREEN}[OK]${NC} Frontend project found"
else
    echo -e "${RED}[ERROR]${NC} frontend/package.json not found"
fi

if [ -f "db.sqlite3" ]; then
    echo -e "${GREEN}[OK]${NC} Database file exists"
else
    echo -e "${YELLOW}[WARNING]${NC} Database not found - run: python manage.py migrate"
fi

if [ -d "frontend/node_modules" ]; then
    echo -e "${GREEN}[OK]${NC} Frontend dependencies installed"
else
    echo -e "${YELLOW}[WARNING]${NC} Frontend dependencies not installed - run: cd frontend && npm install"
fi

if [ -d "venv" ]; then
    echo -e "${GREEN}[OK]${NC} Virtual environment found"
else
    echo -e "${YELLOW}[WARNING]${NC} Virtual environment not found - run: python3 -m venv venv"
fi

echo ""
echo "========================================"
echo "Checking ports..."
echo "========================================"
echo ""

# Check if ports are available (using ss or netstat)
if command -v ss &> /dev/null; then
    # Modern Linux systems use ss
    if ss -tuln | grep -q ':8007 '; then
        echo -e "${YELLOW}[WARNING]${NC} Port 8007 is in use - Django backend may not start"
    else
        echo -e "${GREEN}[OK]${NC} Port 8007 is available"
    fi
    
    if ss -tuln | grep -q ':3000 '; then
        echo -e "${YELLOW}[WARNING]${NC} Port 3000 is in use - Next.js frontend may not start"
    else
        echo -e "${GREEN}[OK]${NC} Port 3000 is available"
    fi
elif command -v netstat &> /dev/null; then
    # Fallback to netstat
    if netstat -tuln | grep -q ':8007 '; then
        echo -e "${YELLOW}[WARNING]${NC} Port 8007 is in use - Django backend may not start"
    else
        echo -e "${GREEN}[OK]${NC} Port 8007 is available"
    fi
    
    if netstat -tuln | grep -q ':3000 '; then
        echo -e "${YELLOW}[WARNING]${NC} Port 3000 is in use - Next.js frontend may not start"
    else
        echo -e "${GREEN}[OK]${NC} Port 3000 is available"
    fi
else
    echo -e "${YELLOW}[WARNING]${NC} Cannot check ports - neither ss nor netstat available"
fi

echo ""
echo "========================================"
echo "Summary"
echo "========================================"
echo ""
echo "If all checks passed, you can start the system with:"
echo "  chmod +x start_system.sh"
echo "  ./start_system.sh"
echo ""
echo "If there were errors:"
if [[ "$OS_TYPE" == "Oracle Linux" ]]; then
    echo "  On Oracle Linux:"
    echo "  1. Install Python: sudo yum install python3 python3-pip python3-devel"
    echo "  2. Install Node.js: sudo yum install nodejs npm"
    echo "  3. Install development tools: sudo yum groupinstall 'Development Tools'"
fi
echo "  1. Install missing prerequisites (Python, Node.js)"
echo "  2. Create virtual environment: python3 -m venv venv"
echo "  3. Activate venv: source venv/bin/activate"
echo "  4. Run: pip install -r requirements.txt"
echo "  5. Run: python manage.py migrate"
echo "  6. Run: cd frontend && npm install"
echo "  7. Make scripts executable: chmod +x *.sh"
echo "  8. Try again!"
echo ""
echo "For detailed setup instructions, see: SETUP_GUIDE.md"
echo "For quick start, see: QUICK_START.md"
echo ""

read -p "Press Enter to continue..."
