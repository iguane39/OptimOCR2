#!/usr/bin/env python3
"""
Batch processing script for multiple PDFs.

Usage:
    python process_batch.py
    python process_batch.py --quality quality
    python process_batch.py --input pdf/to_process --quality balanced
"""

import sys
import time
import argparse
from pathlib import Path
from typing import List

# Add current directory to path
sys.path.insert(0, str(Path(__file__).parent))

from config import Config
from modules.utils import setup_logging
from loguru import logger


def find_pdfs(directory: Path) -> List[Path]:
    """
    Find all PDF files in a directory.

    Args:
        directory: Directory to search

    Returns:
        List of PDF file paths
    """
    if not directory.exists():
        logger.error(f"Directory not found: {directory}")
        return []

    pdfs = sorted(directory.glob("*.pdf"))
    return pdfs


def process_batch(
    input_dir: Path = None,
    quality: str = 'balanced',
    move_processed: bool = True,
    verbose: int = 1,
):
    """
    Process all PDFs in a directory.

    Args:
        input_dir: Input directory (default: pdf/to_process)
        quality: Quality mode
        move_processed: Move PDFs to processed/ after completion
        verbose: Verbosity level
    """
    setup_logging(verbose)

    # Default directories
    if input_dir is None:
        input_dir = Path('pdf/to_process')

    processed_dir = Path('pdf/processed')
    output_dir = Path('output')

    # Create directories if needed
    input_dir.mkdir(parents=True, exist_ok=True)
    processed_dir.mkdir(parents=True, exist_ok=True)
    output_dir.mkdir(parents=True, exist_ok=True)

    # Find PDFs
    pdfs = find_pdfs(input_dir)

    if not pdfs:
        print("=" * 70)
        print("📁 No PDFs found in", input_dir)
        print("=" * 70)
        print()
        print("ℹ️  Place your PDFs in the 'pdf/to_process/' folder:")
        print("   cp your_document.pdf pdf/to_process/")
        print()
        return

    print("=" * 70)
    print("📦 OptimOCR2 - Batch Processing")
    print("=" * 70)
    print(f"📁 Input directory: {input_dir}")
    print(f"📄 Found {len(pdfs)} PDF(s)")
    print(f"🎯 Quality mode: {quality}")
    print(f"📝 Output directory: {output_dir}")
    print("=" * 70)
    print()

    # List files
    print("📋 Files to process:")
    for i, pdf in enumerate(pdfs, 1):
        print(f"  {i}. {pdf.name}")
    print()

    # Confirm
    try:
        response = input("Continue? (Y/n): ").strip().lower()
        if response and response not in ['y', 'yes', 'o', 'oui']:
            print("Cancelled.")
            return
    except KeyboardInterrupt:
        print("\nCancelled.")
        return

    print()

    # Process each PDF
    total_start = time.time()
    successful = 0
    failed = []

    for i, pdf_path in enumerate(pdfs, 1):
        print(f"📄 Processing {i}/{len(pdfs)}: {pdf_path.name}")
        print("-" * 70)

        try:
            # Build command
            import subprocess

            cmd = [
                sys.executable,
                'main.py',
                str(pdf_path),
                '--quality', quality,
            ]

            if verbose >= 2:
                cmd.append('-vv')
            elif verbose >= 1:
                cmd.append('-v')

            # Run
            start_time = time.time()
            result = subprocess.run(cmd, capture_output=False)
            elapsed = time.time() - start_time

            if result.returncode == 0:
                print(f"✅ Success in {elapsed:.1f}s")
                successful += 1

                # Move to processed
                if move_processed:
                    destination = processed_dir / pdf_path.name
                    pdf_path.rename(destination)
                    print(f"📦 Moved to: {destination}")

            else:
                print(f"❌ Failed (exit code {result.returncode})")
                failed.append(pdf_path.name)

        except KeyboardInterrupt:
            print("\n⚠️  Interrupted by user")
            break

        except Exception as e:
            print(f"❌ Error: {e}")
            failed.append(pdf_path.name)

        print()

    # Summary
    total_elapsed = time.time() - total_start

    print("=" * 70)
    print("📊 Batch Processing Complete")
    print("=" * 70)
    print(f"✅ Successful: {successful}/{len(pdfs)}")

    if failed:
        print(f"❌ Failed: {len(failed)}")
        print("   Failed files:")
        for name in failed:
            print(f"   - {name}")

    print(f"⏱️  Total time: {total_elapsed:.1f}s")
    print(f"📝 Output directory: {output_dir}")
    print("=" * 70)


def main():
    """Main entry point."""
    parser = argparse.ArgumentParser(
        description='Batch process multiple PDF files',
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
Examples:
  python process_batch.py
  python process_batch.py --quality quality
  python process_batch.py --input my_pdfs/ --no-move
        """
    )

    parser.add_argument(
        '--input', '-i',
        type=Path,
        default=Path('pdf/to_process'),
        help='Input directory (default: pdf/to_process)'
    )

    parser.add_argument(
        '--quality', '-q',
        choices=['fast', 'balanced', 'quality', 'ultra'],
        default='balanced',
        help='Quality mode (default: balanced)'
    )

    parser.add_argument(
        '--no-move',
        action='store_true',
        help='Do not move PDFs to processed/ after completion'
    )

    parser.add_argument(
        '--verbose', '-v',
        action='count',
        default=1,
        help='Increase verbosity (-v, -vv)'
    )

    args = parser.parse_args()

    try:
        process_batch(
            input_dir=args.input,
            quality=args.quality,
            move_processed=not args.no_move,
            verbose=args.verbose,
        )
    except KeyboardInterrupt:
        print("\n⚠️  Interrupted by user")
        sys.exit(130)
    except Exception as e:
        print(f"\n❌ Error: {e}")
        import traceback
        traceback.print_exc()
        sys.exit(1)


if __name__ == '__main__':
    main()
