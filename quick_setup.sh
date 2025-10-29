#!/bin/bash
# Quick setup script for testing OptimOCR2

echo "=== OptimOCR2 Quick Setup ==="

# Detect OS
if [[ "$OSTYPE" == "linux-gnu"* ]]; then
    echo "Detected: Linux"

    # Install Tesseract and Poppler
    sudo apt-get update
    sudo apt-get install -y tesseract-ocr tesseract-ocr-fra poppler-utils

elif [[ "$OSTYPE" == "darwin"* ]]; then
    echo "Detected: macOS"

    # Install with Homebrew
    brew install tesseract tesseract-lang poppler

else
    echo "Windows detected. Please install manually:"
    echo "1. Tesseract: https://github.com/UB-Mannheim/tesseract/wiki"
    echo "2. Poppler: http://blog.alivate.com.au/poppler-windows/"
    exit 1
fi

# Install Python dependencies
echo "Installing Python dependencies..."
pip install -r requirements.txt

echo ""
echo "=== Setup Complete! ==="
echo ""
echo "Test with:"
echo "  python main.py your_document.pdf --quality balanced -vv"
echo ""
echo "Or try ultra quality:"
echo "  python main.py your_document.pdf --quality ultra -vv"
