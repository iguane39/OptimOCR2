#!/usr/bin/env python3
"""
Quick test script for OptimOCR2.

Usage:
    python test_document.py your_document.pdf
"""

import sys
import time
from pathlib import Path

# Add current directory to path
sys.path.insert(0, str(Path(__file__).parent))

from config import Config
from modules.utils import setup_logging, validate_pdf_path, get_output_path
from modules.pdf_processor import create_pdf_processor
from modules.ocr_engine import create_ocr_engine
from modules.format_analyzer import create_format_analyzer
from modules.docx_builder import create_docx_builder
from models.formatting_models import OCRDocument

# Optional enhancements (will gracefully skip if not available)
try:
    from modules.image_enhancer import ImageEnhancer
    ENHANCEMENTS_AVAILABLE = True
except ImportError:
    ENHANCEMENTS_AVAILABLE = False
    print("⚠️  Enhancement modules not fully available (this is OK for basic testing)")


def test_document(pdf_path: str, use_enhancements: bool = True):
    """
    Test OCR on a document with simple pipeline.

    Args:
        pdf_path: Path to PDF file
        use_enhancements: Whether to use advanced enhancements
    """
    setup_logging(verbose=2)

    print("=" * 70)
    print("OptimOCR2 - Quick Test")
    print("=" * 70)

    # Validate input
    input_path = validate_pdf_path(pdf_path)
    output_path = get_output_path(input_path)

    print(f"📄 Input: {input_path}")
    print(f"📝 Output: {output_path}")
    print()

    start_time = time.time()

    # Initialize components
    print("🔧 Initializing components...")
    pdf_processor = create_pdf_processor(dpi=600)
    ocr_engine = create_ocr_engine(language='fra')
    format_analyzer = create_format_analyzer(dpi=600)
    docx_builder = create_docx_builder()

    if use_enhancements and ENHANCEMENTS_AVAILABLE:
        print("✨ Using advanced enhancements")
        image_enhancer = ImageEnhancer(method='auto')
    else:
        image_enhancer = None
        print("📊 Using basic OCR (no enhancements)")

    # Get page count
    total_pages = pdf_processor.get_page_count(input_path)
    print(f"📄 Total pages: {total_pages}")

    # Process first page only for quick test
    print(f"\n🔍 Processing page 1 (quick test)...")

    # Convert PDF to image
    print("  → Converting PDF to image...")
    images = pdf_processor.process_pdf(input_path, pages=[0])

    if not images:
        print("❌ Error: Could not convert PDF to image")
        return

    page_num, image = images[0]

    # Enhance image if available
    if image_enhancer:
        print("  → Enhancing image (advanced preprocessing)...")
        image = image_enhancer.enhance(image)

    # Run OCR
    print("  → Running OCR...")
    ocr_page = ocr_engine.recognize_text(image, page_num)

    print(f"  ✓ Found {ocr_page.word_count} words")
    print(f"  ✓ Average confidence: {ocr_page.average_confidence:.1f}%")

    # Analyze formatting
    print("  → Analyzing formatting...")
    ocr_page = format_analyzer.analyze_page(ocr_page, image)

    # Create document
    print("\n📝 Creating Word document...")
    ocr_document = OCRDocument(
        pages=[ocr_page],
        metadata={'source': str(input_path)}
    )

    docx_builder.create_document(ocr_document, output_path)

    # Show results
    elapsed = time.time() - start_time

    print("\n" + "=" * 70)
    print("✅ Test Complete!")
    print("=" * 70)
    print(f"⏱️  Processing time: {elapsed:.2f}s")
    print(f"📊 Words extracted: {ocr_page.word_count}")
    print(f"📈 Average confidence: {ocr_page.average_confidence:.1f}%")
    print(f"📄 Output saved to: {output_path}")
    print()

    # Show sample text
    print("📝 Sample text (first 500 characters):")
    print("-" * 70)
    sample = ocr_page.text[:500]
    print(sample)
    if len(ocr_page.text) > 500:
        print("...")
    print("-" * 70)

    # Recommendations
    print("\n💡 Recommendations:")
    if ocr_page.average_confidence < 90:
        print("  • Confidence is below 90% - try using --quality quality mode")
        print("  • Consider enabling advanced enhancements")
    else:
        print("  • Good confidence! Results should be accurate.")

    if use_enhancements:
        print("  • To process all pages: python main.py", input_path)

    print()


def main():
    """Main entry point."""
    if len(sys.argv) < 2:
        print("Usage: python test_document.py <pdf_file>")
        print()
        print("Example:")
        print("  python test_document.py my_document.pdf")
        sys.exit(1)

    pdf_path = sys.argv[1]

    # Check if enhancements flag is provided
    use_enhancements = '--no-enhancements' not in sys.argv

    try:
        test_document(pdf_path, use_enhancements=use_enhancements)
    except KeyboardInterrupt:
        print("\n⚠️  Test interrupted by user")
        sys.exit(130)
    except Exception as e:
        print(f"\n❌ Error: {e}")
        import traceback
        traceback.print_exc()
        sys.exit(1)


if __name__ == '__main__':
    main()
