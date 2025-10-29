#!/usr/bin/env python3
"""
Main entry point for OCR PDF to DOCX converter.

This script provides a command-line interface for converting scanned PDFs
to Word documents with formatting preservation.
"""

import sys
import time
from pathlib import Path
from typing import Optional

import click
from tqdm import tqdm
from loguru import logger

from config import Config
from models.formatting_models import OCRDocument, ProcessingStats
from modules.utils import (
    setup_logging,
    parse_page_range,
    validate_pdf_path,
    get_output_path,
    format_time,
)
from modules.pdf_processor import create_pdf_processor
from modules.ocr_engine import create_ocr_engine
from modules.format_analyzer import create_format_analyzer
from modules.text_corrector import create_text_corrector
from modules.docx_builder import create_docx_builder


@click.command()
@click.argument('input_pdf', type=click.Path(exists=True))
@click.option(
    '--output', '-o',
    type=click.Path(),
    default=None,
    help='Output DOCX file path (default: input_name.docx in output/ directory)'
)
@click.option(
    '--pages', '-p',
    default='all',
    help='Pages to process (e.g., "1-10", "5,7,9", or "all")'
)
@click.option(
    '--dpi',
    type=int,
    default=Config.DPI_DEFAULT,
    help=f'DPI resolution for PDF conversion (default: {Config.DPI_DEFAULT})'
)
@click.option(
    '--language', '-l',
    default=Config.DEFAULT_LANGUAGE,
    help=f'OCR language code (default: {Config.DEFAULT_LANGUAGE})'
)
@click.option(
    '--ocr-engine',
    type=click.Choice(['tesseract', 'easyocr', 'both']),
    default='tesseract',
    help='OCR engine to use (default: tesseract)'
)
@click.option(
    '--correct-text/--no-correct-text',
    default=True,
    help='Enable/disable text correction (default: enabled)'
)
@click.option(
    '--preserve-images/--no-preserve-images',
    default=False,
    help='Keep intermediate images (default: disabled)'
)
@click.option(
    '--parallel/--no-parallel',
    default=True,
    help='Enable/disable parallel processing (default: enabled)'
)
@click.option(
    '--quality',
    type=click.Choice(['fast', 'balanced', 'quality']),
    default='balanced',
    help='Quality preset (default: balanced)'
)
@click.option(
    '--verbose', '-v',
    count=True,
    help='Verbosity level (use -v, -vv, or -vvv)'
)
def convert_pdf_to_docx(
    input_pdf: str,
    output: Optional[str],
    pages: str,
    dpi: int,
    language: str,
    ocr_engine: str,
    correct_text: bool,
    preserve_images: bool,
    parallel: bool,
    quality: str,
    verbose: int,
):
    """
    Convert a scanned PDF to a Word document with formatting preservation.

    \b
    Examples:
        # Basic conversion
        python main.py document.pdf

        \b
        # Advanced conversion
        python main.py document.pdf -o output.docx --pages 1-50 --dpi 600 -vv

        \b
        # High quality conversion
        python main.py document.pdf --quality quality --correct-text
    """
    # Setup logging
    setup_logging(verbose)

    logger.info("=" * 70)
    logger.info("OCR PDF to DOCX Converter")
    logger.info("=" * 70)

    try:
        # Validate input
        input_path = validate_pdf_path(input_pdf)
        output_path = get_output_path(input_path, Path(output) if output else None)

        logger.info(f"Input PDF: {input_path}")
        logger.info(f"Output DOCX: {output_path}")

        # Apply quality preset
        Config.apply_quality_preset(quality)
        if dpi != Config.DPI_DEFAULT:
            Config.DPI_DEFAULT = dpi  # Override with command-line DPI

        # Start processing
        start_time = time.time()

        # Initialize components
        pdf_processor = create_pdf_processor(dpi=dpi, quality_mode=quality)
        ocr_engine = create_ocr_engine(engine=ocr_engine, language=language)
        format_analyzer = create_format_analyzer(dpi=dpi)
        text_corrector = create_text_corrector(language=language, enabled=correct_text)
        docx_builder = create_docx_builder()

        # Get total pages
        total_pages = pdf_processor.get_page_count(input_path)
        logger.info(f"Total pages in PDF: {total_pages}")

        # Parse page range
        page_list = parse_page_range(pages, total_pages)
        logger.info(f"Processing {len(page_list)} pages: {page_list[:10]}{'...' if len(page_list) > 10 else ''}")

        # Process PDF
        logger.info("Step 1/5: Converting PDF to images...")
        images = pdf_processor.process_pdf(
            input_path,
            pages=page_list,
            save_images=preserve_images,
        )

        # Create OCR document
        ocr_document = OCRDocument(
            metadata={
                'source_file': str(input_path),
                'dpi': dpi,
                'language': language,
                'quality': quality,
            }
        )

        # Process each page with progress bar
        logger.info("Step 2/5: Running OCR...")
        with tqdm(total=len(images), desc="OCR Progress", unit="page") as pbar:
            for page_num, image in images:
                # OCR
                ocr_page = ocr_engine.recognize_text(image, page_num)

                # Format analysis
                logger.debug(f"Step 3/5: Analyzing formatting for page {page_num + 1}...")
                ocr_page = format_analyzer.analyze_page(ocr_page, image)

                # Text correction
                if text_corrector:
                    logger.debug(f"Step 4/5: Correcting text for page {page_num + 1}...")
                    ocr_page = text_corrector.correct_page(ocr_page)

                # Add to document
                ocr_document.pages.append(ocr_page)

                pbar.update(1)

        # Build DOCX
        logger.info("Step 5/5: Creating Word document...")
        docx_builder.create_document(ocr_document, output_path)

        # Calculate statistics
        end_time = time.time()
        processing_time = end_time - start_time

        stats = ProcessingStats(
            total_pages=total_pages,
            processed_pages=len(page_list),
            total_words=ocr_document.word_count,
            processing_time=processing_time,
            average_confidence=ocr_document.average_confidence,
        )

        # Display results
        logger.info("=" * 70)
        logger.info("Processing Complete!")
        logger.info("=" * 70)
        logger.info(f"Pages processed: {stats.processed_pages}/{stats.total_pages}")
        logger.info(f"Total words: {stats.total_words}")
        logger.info(f"Average confidence: {stats.average_confidence:.2f}%")
        logger.info(f"Processing time: {format_time(stats.processing_time)}")
        logger.info(f"Speed: {stats.total_words / stats.processing_time:.1f} words/second")
        logger.info(f"Output saved to: {output_path}")
        logger.info("=" * 70)

        if text_corrector:
            correction_stats = text_corrector.get_stats()
            if correction_stats['words_corrected'] > 0:
                logger.info(f"Text corrections: {correction_stats['words_corrected']} words")

        # Success
        click.echo(f"\n✓ Document created successfully: {output_path}")
        return 0

    except KeyboardInterrupt:
        logger.warning("\nProcessing interrupted by user")
        return 130

    except Exception as e:
        logger.error(f"Error: {e}")
        if verbose >= 2:
            logger.exception("Full traceback:")
        return 1


@click.group()
def cli():
    """OCR PDF to DOCX Converter - Advanced Tools"""
    pass


@cli.command()
@click.argument('pdf_path', type=click.Path(exists=True))
def info(pdf_path: str):
    """Display information about a PDF file."""
    setup_logging(0)

    try:
        pdf_path = validate_pdf_path(pdf_path)
        pdf_processor = create_pdf_processor()

        metadata = pdf_processor.get_pdf_metadata(pdf_path)

        click.echo("\n" + "=" * 50)
        click.echo("PDF Information")
        click.echo("=" * 50)
        click.echo(f"File: {metadata['file_name']}")
        click.echo(f"Path: {metadata['file_path']}")
        click.echo(f"Size: {metadata['file_size'] / 1024 / 1024:.2f} MB")
        click.echo(f"Pages: {metadata['page_count']}")
        click.echo("=" * 50 + "\n")

    except Exception as e:
        click.echo(f"Error: {e}", err=True)
        return 1


@cli.command()
def languages():
    """List available OCR languages."""
    setup_logging(0)

    try:
        ocr_engine = create_ocr_engine()
        langs = ocr_engine.validate_ocr_languages()

        click.echo("\n" + "=" * 50)
        click.echo("Available OCR Languages")
        click.echo("=" * 50)

        for lang in sorted(langs):
            click.echo(f"  - {lang}")

        click.echo("=" * 50)
        click.echo(f"Total: {len(langs)} languages")
        click.echo("=" * 50 + "\n")

    except Exception as e:
        click.echo(f"Error: {e}", err=True)
        return 1


@cli.command()
@click.option('--cache-type', type=str, default=None)
def clear_cache(cache_type: Optional[str]):
    """Clear cached data."""
    from modules.utils import clear_cache as clear_cache_func

    setup_logging(0)

    try:
        clear_cache_func(cache_type)
        click.echo(f"✓ Cache cleared: {cache_type or 'all'}")
    except Exception as e:
        click.echo(f"Error: {e}", err=True)
        return 1


if __name__ == '__main__':
    # If no arguments provided, show help
    if len(sys.argv) == 1:
        convert_pdf_to_docx(['--help'])
    else:
        # Check if first arg is a command
        if sys.argv[1] in ['info', 'languages', 'clear-cache']:
            cli()
        else:
            convert_pdf_to_docx()
