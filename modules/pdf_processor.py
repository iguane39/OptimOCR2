"""
PDF processor module for converting PDF pages to images.

This module handles the conversion of PDF documents to high-resolution images
suitable for OCR processing.
"""

from pathlib import Path
from typing import List, Optional, Tuple
import numpy as np
from PIL import Image
import cv2
from loguru import logger

try:
    from pdf2image import convert_from_path
    PDF2IMAGE_AVAILABLE = True
except ImportError:
    PDF2IMAGE_AVAILABLE = False
    logger.warning("pdf2image not installed. PDF processing will not be available.")

from config import Config
from modules.utils import (
    deskew_image,
    enhance_image,
    pil_to_cv2,
    cv2_to_pil,
    ensure_directory,
    calculate_file_hash,
    save_to_cache,
    load_from_cache,
)


class PDFProcessor:
    """
    Handles PDF to image conversion and preprocessing.
    """

    def __init__(
        self,
        dpi: int = Config.DPI_DEFAULT,
        preprocess: bool = True,
        deskew: bool = Config.DESKEW_ENABLED,
    ):
        """
        Initialize PDF processor.

        Args:
            dpi: Resolution for image conversion
            preprocess: Whether to preprocess images
            deskew: Whether to deskew images
        """
        if not PDF2IMAGE_AVAILABLE:
            raise ImportError(
                "pdf2image is required for PDF processing. "
                "Install it with: pip install pdf2image"
            )

        self.dpi = dpi
        self.preprocess = preprocess
        self.deskew = deskew

        logger.info(f"Initialized PDF processor with DPI={dpi}, preprocess={preprocess}")

    def get_page_count(self, pdf_path: Path) -> int:
        """
        Get the number of pages in a PDF.

        Args:
            pdf_path: Path to PDF file

        Returns:
            Number of pages
        """
        try:
            from pdf2image import pdfinfo_from_path
            info = pdfinfo_from_path(pdf_path)
            return info.get('Pages', 0)
        except Exception as e:
            logger.error(f"Failed to get page count: {e}")
            # Fallback: try to convert first page and count
            try:
                images = convert_from_path(pdf_path, dpi=72, first_page=1, last_page=1)
                if images:
                    # If we can convert, try a larger sample
                    images = convert_from_path(pdf_path, dpi=72)
                    return len(images)
            except:
                pass
            return 0

    def pdf_to_images(
        self,
        pdf_path: Path,
        pages: Optional[List[int]] = None,
        use_cache: bool = True,
    ) -> List[Tuple[int, Image.Image]]:
        """
        Convert PDF pages to PIL Images.

        Args:
            pdf_path: Path to PDF file
            pages: List of page numbers to convert (0-indexed), None for all
            use_cache: Whether to use cached images if available

        Returns:
            List of (page_number, PIL Image) tuples
        """
        logger.info(f"Converting PDF to images: {pdf_path}")

        # Check cache
        if use_cache and Config.CACHE_ENABLED:
            cache_key = self._get_cache_key(pdf_path, pages)
            cached = load_from_cache(cache_key, 'pdf_images')
            if cached is not None:
                logger.info("Loaded PDF images from cache")
                return cached

        # Convert to 1-indexed for pdf2image
        if pages is not None:
            first_page = min(pages) + 1
            last_page = max(pages) + 1
        else:
            first_page = None
            last_page = None

        try:
            # Convert PDF to images
            pil_images = convert_from_path(
                pdf_path,
                dpi=self.dpi,
                first_page=first_page,
                last_page=last_page,
                fmt='png',
                thread_count=4,
            )

            # Create result list with page numbers
            if pages is not None:
                # Filter to requested pages
                result = []
                page_set = set(pages)
                offset = min(pages)
                for i, img in enumerate(pil_images):
                    page_num = offset + i
                    if page_num in page_set:
                        result.append((page_num, img))
            else:
                result = list(enumerate(pil_images))

            logger.info(f"Converted {len(result)} pages to images")

            # Cache the result
            if use_cache and Config.CACHE_ENABLED:
                save_to_cache(result, cache_key, 'pdf_images')

            return result

        except Exception as e:
            logger.error(f"Failed to convert PDF to images: {e}")
            raise

    def preprocess_image(
        self,
        image: Image.Image,
        deskew: Optional[bool] = None,
    ) -> Image.Image:
        """
        Preprocess image for better OCR results.

        Args:
            image: PIL Image to preprocess
            deskew: Whether to deskew, None to use instance setting

        Returns:
            Preprocessed PIL Image
        """
        if not self.preprocess:
            return image

        if deskew is None:
            deskew = self.deskew

        # Convert to OpenCV format
        cv_image = pil_to_cv2(image)

        # Deskew if enabled
        if deskew:
            cv_image = deskew_image(cv_image)

        # Enhance image
        cv_image = enhance_image(cv_image)

        # Convert back to PIL
        result = cv2_to_pil(cv_image)

        return result

    def process_pdf(
        self,
        pdf_path: Path,
        pages: Optional[List[int]] = None,
        save_images: bool = False,
        output_dir: Optional[Path] = None,
    ) -> List[Tuple[int, Image.Image]]:
        """
        Complete PDF processing pipeline.

        Args:
            pdf_path: Path to PDF file
            pages: List of page numbers to process (0-indexed), None for all
            save_images: Whether to save processed images to disk
            output_dir: Directory to save images (if save_images=True)

        Returns:
            List of (page_number, processed PIL Image) tuples
        """
        # Convert PDF to images
        images = self.pdf_to_images(pdf_path, pages)

        # Preprocess each image
        processed = []
        for page_num, img in images:
            logger.debug(f"Processing page {page_num + 1}")

            if self.preprocess:
                img = self.preprocess_image(img)

            processed.append((page_num, img))

            # Save if requested
            if save_images:
                self._save_image(img, page_num, output_dir or Config.TEMP_DIR)

        logger.info(f"Processed {len(processed)} pages")

        return processed

    def _save_image(self, image: Image.Image, page_num: int, output_dir: Path) -> None:
        """
        Save image to disk.

        Args:
            image: PIL Image to save
            page_num: Page number
            output_dir: Output directory
        """
        ensure_directory(output_dir)
        output_path = output_dir / f"page_{page_num + 1:04d}.png"
        image.save(output_path, 'PNG')
        logger.debug(f"Saved image: {output_path}")

    def _get_cache_key(self, pdf_path: Path, pages: Optional[List[int]]) -> str:
        """
        Generate cache key for PDF conversion.

        Args:
            pdf_path: Path to PDF file
            pages: Page list

        Returns:
            Cache key string
        """
        # Include file hash, DPI, and pages in cache key
        file_hash = calculate_file_hash(pdf_path)
        pages_str = ','.join(map(str, pages)) if pages else 'all'
        return f"{file_hash}_{self.dpi}_{pages_str}"

    def extract_page_dimensions(
        self,
        pdf_path: Path,
        page_num: int = 0
    ) -> Tuple[int, int]:
        """
        Extract dimensions of a PDF page.

        Args:
            pdf_path: Path to PDF file
            page_num: Page number (0-indexed)

        Returns:
            (width, height) in pixels at current DPI
        """
        try:
            # Convert just the first page to get dimensions
            images = convert_from_path(
                pdf_path,
                dpi=self.dpi,
                first_page=page_num + 1,
                last_page=page_num + 1,
            )

            if images:
                img = images[0]
                return img.size  # (width, height)

        except Exception as e:
            logger.error(f"Failed to extract page dimensions: {e}")

        return (0, 0)

    def get_pdf_metadata(self, pdf_path: Path) -> dict:
        """
        Extract metadata from PDF.

        Args:
            pdf_path: Path to PDF file

        Returns:
            Dictionary of metadata
        """
        metadata = {
            'file_path': str(pdf_path),
            'file_name': pdf_path.name,
            'file_size': pdf_path.stat().st_size,
            'page_count': 0,
            'dpi': self.dpi,
        }

        try:
            metadata['page_count'] = self.get_page_count(pdf_path)
        except Exception as e:
            logger.error(f"Failed to extract PDF metadata: {e}")

        return metadata

    def validate_pdf(self, pdf_path: Path) -> bool:
        """
        Validate that PDF can be processed.

        Args:
            pdf_path: Path to PDF file

        Returns:
            True if valid, False otherwise
        """
        try:
            # Try to get page count
            page_count = self.get_page_count(pdf_path)
            if page_count == 0:
                logger.error(f"PDF has no pages: {pdf_path}")
                return False

            logger.info(f"PDF is valid with {page_count} pages")
            return True

        except Exception as e:
            logger.error(f"PDF validation failed: {e}")
            return False


def create_pdf_processor(
    dpi: Optional[int] = None,
    quality_mode: Optional[str] = None,
) -> PDFProcessor:
    """
    Factory function to create a PDFProcessor with appropriate settings.

    Args:
        dpi: DPI for conversion (None to use config default)
        quality_mode: Quality mode ('fast', 'balanced', 'quality')

    Returns:
        Configured PDFProcessor instance
    """
    if quality_mode:
        preset = Config.QUALITY_PRESETS.get(quality_mode, Config.QUALITY_PRESETS['balanced'])
        dpi = dpi or preset['dpi']
        preprocess = preset['preprocessing']
    else:
        dpi = dpi or Config.DPI_DEFAULT
        preprocess = True

    return PDFProcessor(dpi=dpi, preprocess=preprocess)
