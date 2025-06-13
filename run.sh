#!/bin/bash

# Open Video Watermark - Startup Script
# This script helps set up and run the video watermarking application

set -e  # Exit on any error

echo "🎬 Open Video Watermark - Setup & Run Script"
echo "============================================="

# Color codes for output
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
NC='\033[0m' # No Color

# Function to print colored output
print_status() {
    echo -e "${BLUE}[INFO]${NC} $1"
}

print_success() {
    echo -e "${GREEN}[SUCCESS]${NC} $1"
}

print_warning() {
    echo -e "${YELLOW}[WARNING]${NC} $1"
}

print_error() {
    echo -e "${RED}[ERROR]${NC} $1"
}

# Check if Python 3 is installed
check_python() {
    if command -v python3 &> /dev/null; then
        PYTHON_VERSION=$(python3 --version 2>&1 | cut -d' ' -f2)
        print_success "Python 3 found: $PYTHON_VERSION"
        return 0
    else
        print_error "Python 3 is not installed or not in PATH"
        print_error "Please install Python 3.8 or later"
        return 1
    fi
}

# Check if virtual environment exists
check_venv() {
    if [ -d "venv" ]; then
        print_success "Virtual environment found"
        return 0
    else
        print_warning "Virtual environment not found"
        return 1
    fi
}

# Create virtual environment
create_venv() {
    print_status "Creating virtual environment..."
    python3 -m venv venv
    if [ $? -eq 0 ]; then
        print_success "Virtual environment created successfully"
        return 0
    else
        print_error "Failed to create virtual environment"
        return 1
    fi
}

# Activate virtual environment
activate_venv() {
    print_status "Activating virtual environment..."
    source venv/bin/activate
    if [ $? -eq 0 ]; then
        print_success "Virtual environment activated"
        return 0
    else
        print_error "Failed to activate virtual environment"
        return 1
    fi
}

# Install dependencies
install_dependencies() {
    print_status "Installing Python dependencies..."
    pip install --upgrade pip
    pip install -r requirements.txt
    if [ $? -eq 0 ]; then
        print_success "Dependencies installed successfully"
        return 0
    else
        print_error "Failed to install dependencies"
        return 1
    fi
}

# Run tests
run_tests() {
    print_status "Running tests to verify installation..."
    python test_watermark.py
    if [ $? -eq 0 ]; then
        print_success "All tests passed!"
        return 0
    else
        print_warning "Some tests failed, but the application might still work"
        return 1
    fi
}

# Start the application
start_app() {
    print_status "Starting the Open Video Watermark application..."
    print_status "The application will be available at: http://localhost:5000"
    print_status "Press Ctrl+C to stop the application"
    echo ""
    python app.py
}

# Main execution
main() {
    # Change to script directory
    cd "$(dirname "$0")"
    
    # Check Python installation
    if ! check_python; then
        exit 1
    fi
    
    # Handle virtual environment
    if ! check_venv; then
        if ! create_venv; then
            exit 1
        fi
    fi
    
    # Activate virtual environment
    if ! activate_venv; then
        exit 1
    fi
    
    # Install dependencies
    if ! install_dependencies; then
        exit 1
    fi
    
    # Run tests (optional, continue even if they fail)
    echo ""
    read -p "Do you want to run tests before starting the application? (y/N): " -n 1 -r
    echo ""
    if [[ $REPLY =~ ^[Yy]$ ]]; then
        run_tests
        echo ""
    fi
    
    # Start the application
    start_app
}

# Help function
show_help() {
    echo "Open Video Watermark - Startup Script"
    echo ""
    echo "Usage: $0 [OPTION]"
    echo ""
    echo "Options:"
    echo "  --help, -h     Show this help message"
    echo "  --test         Run tests only"
    echo "  --setup        Setup only (don't start the app)"
    echo ""
    echo "With no options, the script will setup and start the application."
}

# Parse command line arguments
case "${1:-}" in
    --help|-h)
        show_help
        exit 0
        ;;
    --test)
        cd "$(dirname "$0")"
        check_python || exit 1
        check_venv || create_venv || exit 1
        activate_venv || exit 1
        install_dependencies || exit 1
        run_tests
        exit $?
        ;;
    --setup)
        cd "$(dirname "$0")"
        check_python || exit 1
        check_venv || create_venv || exit 1
        activate_venv || exit 1
        install_dependencies || exit 1
        print_success "Setup completed! Run './run.sh' to start the application."
        exit 0
        ;;
    "")
        main
        ;;
    *)
        echo "Unknown option: $1"
        show_help
        exit 1
        ;;
esac
