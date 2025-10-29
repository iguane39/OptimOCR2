# Quick Start Guide

## Installation

1. **Install System Dependencies**

   ```bash
   # Ubuntu/Debian
   sudo apt-get update
   sudo apt-get install tesseract-ocr tesseract-ocr-fra poppler-utils

   # macOS
   brew install tesseract tesseract-lang poppler
   ```

2. **Install Python Dependencies**

   ```bash
   pip install -r requirements.txt
   ```

3. **Verify Installation**

   ```bash
   python main.py --help
   ```

## Basic Usage

### Convert a PDF (Default Settings)

```bash
python main.py document.pdf
```

Output: `output/document.docx`

### Specify Output File

```bash
python main.py input.pdf -o custom_output.docx
```

### Process Specific Pages

```bash
# Pages 1-10
python main.py book.pdf --pages 1-10

# Specific pages
python main.py document.pdf --pages "1,5,10,15-20"
```

### Quality Modes

```bash
# Fast (300 DPI, no corrections)
python main.py scan.pdf --quality fast

# Balanced (600 DPI, with corrections) - DEFAULT
python main.py scan.pdf --quality balanced

# High Quality (1200 DPI, full processing)
python main.pdf scan.pdf --quality quality
```

### Verbose Output

```bash
# Show progress
python main.py document.pdf -v

# Show detailed debug info
python main.py document.pdf -vv
```

## Common Tasks

### Get PDF Information

```bash
python main.py info document.pdf
```

### List Available Languages

```bash
python main.py languages
```

### Process English Document

```bash
python main.py english.pdf --language eng
```

### Batch Process Multiple Files

```bash
for file in *.pdf; do
    python main.py "$file"
done
```

## Tips for Best Results

1. **Use high DPI for complex documents**:
   ```bash
   python main.py complex.pdf --dpi 1200
   ```

2. **Enable text correction for scanned documents**:
   ```bash
   python main.py scan.pdf --correct-text
   ```

3. **Process pages in chunks for large documents**:
   ```bash
   python main.py large.pdf --pages 1-50 -o part1.docx
   python main.py large.pdf --pages 51-100 -o part2.docx
   ```

## Troubleshooting

### Tesseract Not Found

If you get a Tesseract error, install it:

```bash
# Ubuntu/Debian
sudo apt-get install tesseract-ocr

# macOS
brew install tesseract
```

### Low OCR Accuracy

Try these options:
- Increase DPI: `--dpi 1200`
- Use quality mode: `--quality quality`
- Enable corrections: `--correct-text`

### Slow Processing

Try these options:
- Lower DPI: `--dpi 300`
- Use fast mode: `--quality fast`
- Disable corrections: `--no-correct-text`

## Next Steps

- Read the full [README.md](README.md) for detailed documentation
- Check the [Configuration Guide](config.py) for customization options
- Run tests: `pytest tests/`

## Support

For issues or questions:
- GitHub Issues: https://github.com/iguane39/OptimOCR2/issues
