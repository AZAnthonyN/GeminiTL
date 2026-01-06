#!/bin/bash
# GeminiTL Docker Quick Start Script for Raspberry Pi 5
# This script provides common Docker commands for easy reference

set -e

# Colors for output
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
NC='\033[0m' # No Color

# Function to print colored output
print_info() {
    echo -e "${GREEN}[INFO]${NC} $1"
}

print_warn() {
    echo -e "${YELLOW}[WARN]${NC} $1"
}

print_error() {
    echo -e "${RED}[ERROR]${NC} $1"
}

# Check if Docker is installed
check_docker() {
    if ! command -v docker &> /dev/null; then
        print_error "Docker is not installed. Please install Docker first."
        exit 1
    fi
    print_info "Docker is installed: $(docker --version)"
}

# Check if Docker Compose is installed
check_compose() {
    if ! docker compose version &> /dev/null; then
        print_error "Docker Compose is not installed."
        exit 1
    fi
    print_info "Docker Compose is installed: $(docker compose version)"
}

# Build the Docker image
build_image() {
    print_info "Building GeminiTL Docker image for Raspberry Pi 5..."
    print_warn "This may take 15-30 minutes on first build..."
    docker build -t geminitl:latest .
    print_info "Build complete!"
}

# Run help command
show_help() {
    print_info "Showing GeminiTL help..."
    docker-compose run --rm geminitl python main.py --help
}

# Separate EPUB
separate_epub() {
    if [ -z "$1" ]; then
        print_error "Usage: $0 separate-epub <epub-file>"
        exit 1
    fi
    
    epub_file="$1"
    print_info "Separating EPUB: $epub_file"
    docker-compose run --rm geminitl \
        python main.py epub-separate "/app/input/$epub_file" /app/input
}

# Run translation
run_translate() {
    lang="${1:-Japanese}"
    provider="${2:-gemini}"
    
    print_info "Running translation (Language: $lang, Provider: $provider)..."
    docker-compose run --rm geminitl \
        python main.py translate --source-lang "$lang" --provider "$provider"
}

# Run proofing
run_proof() {
    print_info "Running proofing..."
    docker-compose run --rm geminitl python main.py proof
}

# Combine to EPUB
combine_epub() {
    output_name="${1:-translated.epub}"
    
    print_info "Combining to EPUB: $output_name"
    docker-compose run --rm geminitl \
        python main.py epub-combine /app/output "/app/compiled_epubs/$output_name"
}

# Interactive shell
interactive_shell() {
    print_info "Starting interactive shell..."
    docker-compose run --rm geminitl /bin/bash
}

# Show logs
show_logs() {
    print_info "Showing container logs..."
    docker-compose logs -f geminitl
}

# Clean up
cleanup() {
    print_warn "Cleaning up Docker resources..."
    docker-compose down
    docker system prune -f
    print_info "Cleanup complete!"
}

# Main menu
show_menu() {
    echo ""
    echo "======================================"
    echo "  GeminiTL Docker Quick Start"
    echo "  Raspberry Pi 5 Edition"
    echo "======================================"
    echo ""
    echo "1)  Build Docker image"
    echo "2)  Show help"
    echo "3)  Separate EPUB"
    echo "4)  Run translation"
    echo "5)  Run proofing"
    echo "6)  Combine to EPUB"
    echo "7)  Interactive shell"
    echo "8)  Show logs"
    echo "9)  Clean up"
    echo "10) Exit"
    echo ""
}

# Main script
main() {
    check_docker
    check_compose
    
    if [ $# -eq 0 ]; then
        # Interactive mode
        while true; do
            show_menu
            read -p "Select option: " choice
            
            case $choice in
                1) build_image ;;
                2) show_help ;;
                3) read -p "Enter EPUB filename: " epub; separate_epub "$epub" ;;
                4) read -p "Source language (Japanese/Korean/Chinese): " lang;
                   read -p "Provider (gemini/openai/anthropic): " prov;
                   run_translate "$lang" "$prov" ;;
                5) run_proof ;;
                6) read -p "Output EPUB name: " name; combine_epub "$name" ;;
                7) interactive_shell ;;
                8) show_logs ;;
                9) cleanup ;;
                10) print_info "Goodbye!"; exit 0 ;;
                *) print_error "Invalid option" ;;
            esac
        done
    else
        # Command-line mode
        case "$1" in
            build) build_image ;;
            help) show_help ;;
            separate) separate_epub "$2" ;;
            translate) run_translate "$2" "$3" ;;
            proof) run_proof ;;
            combine) combine_epub "$2" ;;
            shell) interactive_shell ;;
            logs) show_logs ;;
            clean) cleanup ;;
            *) print_error "Unknown command: $1"
               echo "Usage: $0 {build|help|separate|translate|proof|combine|shell|logs|clean}"
               exit 1 ;;
        esac
    fi
}

# Run main function
main "$@"

