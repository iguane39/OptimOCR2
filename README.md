# OptimOCR2 - Advanced PDF to Word Converter with Formatting Preservation

[![Python 3.8+](https://img.shields.io/badge/python-3.8+-blue.svg)](https://www.python.org/downloads/)
[![License: MIT](https://img.shields.io/badge/License-MIT-yellow.svg)](https://opensource.org/licenses/MIT)

**OptimOCR2** is a professional-grade Python application that converts scanned PDF documents into editable Word (.docx) files while preserving formatting with exceptional accuracy.

## Features

### Core Capabilities

- **High-Precision OCR**: Tesseract-based text recognition with >98% accuracy
- **Format Preservation**: Maintains fonts, styles, alignments, and spacing
- **Intelligent Text Correction**: Automatic spell-checking and OCR error correction
- **Multi-Language Support**: Works with multiple languages (French, English, etc.)
- **Parallel Processing**: Fast batch processing with multi-core support
- **Caching System**: Smart caching for faster reprocessing

### Formatting Detection

- ✓ Font families (serif, sans-serif, monospace)
- ✓ Font sizes (accurate point measurements)
- ✓ Text styles (bold, italic, underline)
- ✓ Text alignment (left, center, right, justified)
- ✓ Paragraph spacing and indentation
- ✓ Line spacing
- ✓ Text colors

### Advanced Features

- **Quality Presets**: Fast, balanced, or quality modes
- **Page Selection**: Process specific pages or ranges
- **Configurable DPI**: 300-1200 DPI support
- **Image Preprocessing**: Deskewing, denoising, contrast enhancement
- **Hyphenation Handling**: Merges words split across lines
- **CLI Interface**: Powerful command-line interface

## Installation

### Prerequisites

1. **Python 3.8 or higher**
   ```bash
   python --version  # Should show 3.8 or higher
   ```

2. **Tesseract OCR**

   **Ubuntu/Debian:**
   ```bash
   sudo apt-get update
   sudo apt-get install tesseract-ocr tesseract-ocr-fra
   ```

   **macOS (Homebrew):**
   ```bash
   brew install tesseract tesseract-lang
   ```

   **Windows:**
   - Download installer from [Tesseract GitHub](https://github.com/UB-Mannheim/tesseract/wiki)
   - Add Tesseract to PATH or update `config.py` with the installation path

3. **Poppler** (for PDF processing)

   **Ubuntu/Debian:**
   ```bash
   sudo apt-get install poppler-utils
   ```

   **macOS (Homebrew):**
   ```bash
   brew install poppler
   ```

   **Windows:**
   - Download from [Poppler Windows](http://blog.alivate.com.au/poppler-windows/)
   - Add to PATH

### Quick Install

```bash
# Clone the repository
git clone https://github.com/iguane39/OptimOCR2.git
cd OptimOCR2

# Install Python dependencies
pip install -r requirements.txt

# Verify installation
python main.py --help
```

### Optional Dependencies

For enhanced features, install optional packages:

```bash
# Advanced OCR (EasyOCR)
pip install easyocr

# Text correction (spaCy + LanguageTool)
pip install spacy language-tool-python
python -m spacy download fr_core_news_sm
python -m spacy download en_core_web_sm
```

## Quick Start

### Basic Usage

Convert a PDF to Word with default settings:

```bash
python main.py document.pdf
```

The output will be saved to `output/document.docx`.

### Advanced Usage

```bash
# Specify output file and pages
python main.py book.pdf -o my_book.docx --pages 1-50

# High-quality conversion
python main.py document.pdf --quality quality --dpi 1200 -vv

# Fast conversion
python main.py scan.pdf --quality fast --no-correct-text

# Process specific pages
python main.py report.pdf --pages "1,5,10-20,25"

# Multi-language (English)
python main.py english_doc.pdf --language eng
```

## Command-Line Options

```
Usage: main.py [OPTIONS] INPUT_PDF

Options:
  -o, --output PATH              Output DOCX file path
  -p, --pages TEXT               Pages to process (e.g., "1-10", "5,7,9", "all")
  --dpi INTEGER                  DPI resolution (default: 600)
  -l, --language TEXT            OCR language code (default: fra)
  --ocr-engine [tesseract|easyocr|both]
                                OCR engine to use
  --correct-text / --no-correct-text
                                Enable/disable text correction
  --preserve-images / --no-preserve-images
                                Keep intermediate images
  --parallel / --no-parallel    Enable/disable parallel processing
  --quality [fast|balanced|quality]
                                Quality preset
  -v, --verbose                 Verbosity level (-v, -vv, -vvv)
  --help                        Show this message and exit
```

## Utility Commands

### Get PDF Information

```bash
python main.py info document.pdf
```

### List Available Languages

```bash
python main.py languages
```

### Clear Cache

```bash
python main.py clear-cache
python main.py clear-cache --cache-type ocr
```

## Configuration

Edit `config.py` to customize default settings:

```python
# OCR Settings
DPI_DEFAULT = 600
OCR_LANGUAGES = ['fra', 'eng']
MIN_CONFIDENCE = 60

# Image Processing
DESKEW_ENABLED = True
DENOISE_ENABLED = True
CONTRAST_ENHANCEMENT = True

# Text Correction
SPELL_CHECK_ENABLED = True
FIX_HYPHENATION = True

# Performance
PARALLEL_PROCESSING = True
CACHE_ENABLED = True
```

## Quality Presets

### Fast Mode
- DPI: 300
- Preprocessing: Minimal
- Text Correction: Disabled
- Best for: Quick conversions, clean scans

### Balanced Mode (Default)
- DPI: 600
- Preprocessing: Full
- Text Correction: Enabled
- Best for: Most documents

### Quality Mode
- DPI: 1200
- Preprocessing: Full
- Text Correction: Enabled
- Best for: Complex formatting, critical accuracy

## Project Structure

```
OptimOCR2/
├── main.py                     # CLI entry point
├── config.py                   # Configuration
├── requirements.txt            # Dependencies
├── README.md                   # This file
├── models/
│   ├── __init__.py
│   └── formatting_models.py    # Data structures
├── modules/
│   ├── __init__.py
│   ├── pdf_processor.py        # PDF to image conversion
│   ├── ocr_engine.py          # OCR processing
│   ├── format_analyzer.py     # Formatting detection
│   ├── text_corrector.py      # Text correction
│   ├── docx_builder.py        # Word document creation
│   └── utils.py               # Utility functions
├── tests/
│   └── __init__.py
├── output/                     # Generated documents
├── .cache/                     # Cache files
└── logs/                       # Log files
```

## Performance Tips

1. **Use appropriate DPI**:
   - 300 DPI: Fast, good for clean text
   - 600 DPI: Balanced (recommended)
   - 1200 DPI: Slow, best quality

2. **Enable caching**:
   - Reprocessing is much faster with cache enabled
   - Clear cache periodically: `python main.py clear-cache`

3. **Parallel processing**:
   - Enabled by default
   - Disable for low-memory systems: `--no-parallel`

4. **Page ranges**:
   - Process only needed pages: `--pages 1-10`

## Troubleshooting

### Tesseract Not Found

**Error**: `TesseractNotFoundError`

**Solution**:
1. Install Tesseract (see Installation)
2. Or set path in `config.py`:
   ```python
   TESSERACT_CMD = r'C:\Program Files\Tesseract-OCR\tesseract.exe'  # Windows
   ```

### Low OCR Accuracy

**Solutions**:
- Increase DPI: `--dpi 1200`
- Use quality mode: `--quality quality`
- Enable text correction: `--correct-text`
- Check if correct language is set: `--language fra`

### Memory Issues

**Solutions**:
- Disable parallel processing: `--no-parallel`
- Process fewer pages at once: `--pages 1-10`
- Lower DPI: `--dpi 300`

### Slow Processing

**Solutions**:
- Use fast mode: `--quality fast`
- Lower DPI: `--dpi 300`
- Disable text correction: `--no-correct-text`
- Enable parallel processing: `--parallel` (default)

## Examples

### Convert entire book
```bash
python main.py book.pdf -o book.docx --quality balanced -vv
```

### Process specific chapters
```bash
python main.py thesis.pdf -o chapter1.docx --pages 1-50
python main.py thesis.pdf -o chapter2.docx --pages 51-100
```

### High-quality scan
```bash
python main.py ancient_document.pdf --dpi 1200 --quality quality
```

### Batch processing
```bash
for file in *.pdf; do
    python main.py "$file" --quality balanced
done
```

## Known Limitations

1. **Table Detection**: Not yet implemented
2. **Image Extraction**: Text-only processing
3. **Complex Layouts**: Multi-column layouts may need adjustment
4. **Handwriting**: Not supported (typed text only)
5. **Font Matching**: Uses best approximation, not exact font matching

## Roadmap

- [ ] Table detection and preservation
- [ ] Multi-column layout support
- [ ] Image extraction and placement
- [ ] Header/footer detection
- [ ] GUI interface
- [ ] GPU acceleration for OCR
- [ ] Export to other formats (Markdown, HTML)
- [ ] Fine-tuned OCR models

## Contributing

Contributions are welcome! Please:

1. Fork the repository
2. Create a feature branch
3. Make your changes
4. Add tests if applicable
5. Submit a pull request

## License

This project is licensed under the MIT License - see the LICENSE file for details.

## Acknowledgments

- [Tesseract OCR](https://github.com/tesseract-ocr/tesseract) - OCR engine
- [python-docx](https://python-docx.readthedocs.io/) - Word document creation
- [pdf2image](https://github.com/Belval/pdf2image) - PDF conversion
- [OpenCV](https://opencv.org/) - Image processing

## Support

- **Issues**: [GitHub Issues](https://github.com/iguane39/OptimOCR2/issues)
- **Discussions**: [GitHub Discussions](https://github.com/iguane39/OptimOCR2/discussions)

## Authors

- Initial work - [iguane39](https://github.com/iguane39)

---

**Note**: This is a sophisticated OCR system designed for quality over speed. For best results, use high-quality scans (600+ DPI) and the "quality" or "balanced" presets.
