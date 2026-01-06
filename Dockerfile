# Dockerfile for GeminiTL - Optimized for Raspberry Pi 5 (ARM64)
# This creates a containerized environment for the novel translation tool

# Use Python 3.11 slim image for ARM64
FROM python:3.11-slim-bookworm

# Set metadata
LABEL maintainer="GeminiTL"
LABEL description="AI-Powered Novel Translation Tool for Raspberry Pi 5"
LABEL version="1.0.0"

# Set environment variables
ENV PYTHONUNBUFFERED=1 \
    PYTHONDONTWRITEBYTECODE=1 \
    PIP_NO_CACHE_DIR=1 \
    PIP_DISABLE_PIP_VERSION_CHECK=1 \
    DEBIAN_FRONTEND=noninteractive

# Set working directory
WORKDIR /app

# Install system dependencies
# Note: wxPython requires GUI libraries, but we'll focus on CLI mode for Docker
RUN apt-get update && apt-get install -y --no-install-recommends \
    # Build essentials
    build-essential \
    gcc \
    g++ \
    # Image processing libraries
    libopencv-dev \
    python3-opencv \
    # OCR dependencies
    tesseract-ocr \
    tesseract-ocr-jpn \
    tesseract-ocr-kor \
    tesseract-ocr-chi-sim \
    tesseract-ocr-chi-tra \
    # Image libraries
    libjpeg-dev \
    libpng-dev \
    libtiff-dev \
    # XML processing
    libxml2-dev \
    libxslt1-dev \
    # Other utilities
    git \
    curl \
    wget \
    && rm -rf /var/lib/apt/lists/*

# Copy requirements file
COPY requirements.txt .

# Create a requirements file without wxPython for headless operation
RUN grep -v "wxPython" requirements.txt > requirements-headless.txt || true

# Install Python dependencies
# Install in stages to handle ARM64 compatibility
RUN pip install --upgrade pip setuptools wheel && \
    # Install core dependencies first
    pip install --no-cache-dir \
    vertexai>=1.38.0 \
    google-cloud-aiplatform>=1.34.0 \
    google-cloud-vision>=3.4.0 \
    google-auth>=2.17.0 \
    google-auth-oauthlib>=1.0.0 && \
    # Install AI providers
    pip install --no-cache-dir \
    openai>=1.0.0 \
    anthropic>=0.25.0 && \
    # Install web and file processing
    pip install --no-cache-dir \
    beautifulsoup4>=4.12.0 \
    lxml>=4.9.0 \
    requests>=2.31.0 \
    ebooklib>=0.18 && \
    # Install image processing (ARM64 compatible versions)
    pip install --no-cache-dir \
    Pillow>=10.0.0 \
    pytesseract>=0.3.10 \
    numpy>=1.24.0

# Install EasyOCR separately (can be heavy on ARM)
RUN pip install --no-cache-dir easyocr>=1.7.0 || \
    echo "EasyOCR installation failed, continuing without it"

# Copy application files
COPY . .

# Create necessary directories
RUN mkdir -p /app/input \
    /app/output \
    /app/compiled_epubs \
    /app/src/config

# Set permissions
RUN chmod +x main.py cli.py

# Create a non-root user for security
RUN useradd -m -u 1000 geminitl && \
    chown -R geminitl:geminitl /app

# Switch to non-root user
USER geminitl

# Expose port for potential web interface (future enhancement)
EXPOSE 8080

# Health check
HEALTHCHECK --interval=30s --timeout=10s --start-period=5s --retries=3 \
    CMD python -c "import sys; sys.exit(0)" || exit 1

# Default command - show help
CMD ["python", "main.py", "--help"]

# Usage examples:
# Build: docker build -t geminitl:latest .
# Run CLI: docker run -v $(pwd)/input:/app/input -v $(pwd)/output:/app/output geminitl:latest python main.py translate
# Interactive: docker run -it -v $(pwd)/input:/app/input -v $(pwd)/output:/app/output geminitl:latest /bin/bash

