"""
OCR engine module for text recognition.

This module handles OCR using Tesseract and optionally other OCR engines.
"""

from pathlib import Path
from typing import List, Optional, Dict, Any
import numpy as np
from PIL import Image
from loguru import logger

try:
    import pytesseract
    from pytesseract import Output
    PYTESSERACT_AVAILABLE = True
except ImportError:
    PYTESSERACT_AVAILABLE = False
    logger.warning("pytesseract not installed. OCR will not be available.")

from config import Config
from models.formatting_models import (
    OCRWord,
    OCRLine,
    OCRParagraph,
    OCRPage,
    BoundingBox,
    CharacterFormatting,
)
from modules.utils import save_to_cache, load_from_cache, calculate_file_hash


class OCREngine:
    """
    OCR engine using Tesseract.
    """

    def __init__(
        self,
        language: str = Config.DEFAULT_LANGUAGE,
        config: Optional[str] = None,
    ):
        """
        Initialize OCR engine.

        Args:
            language: OCR language (ISO 639-2 code)
            config: Custom Tesseract configuration string
        """
        if not PYTESSERACT_AVAILABLE:
            raise ImportError(
                "pytesseract is required. Install it with: pip install pytesseract"
            )

        self.language = language
        self.config = config or Config.TESSERACT_CONFIG

        # Set Tesseract path if configured
        tesseract_path = Config.get_tesseract_path()
        if tesseract_path:
            pytesseract.pytesseract.tesseract_cmd = tesseract_path

        logger.info(f"Initialized OCR engine with language={language}")

        # Verify Tesseract is available
        try:
            version = pytesseract.get_tesseract_version()
            logger.info(f"Tesseract version: {version}")
        except Exception as e:
            logger.error(f"Tesseract not found or not working: {e}")
            raise

    def recognize_text(
        self,
        image: Image.Image,
        page_number: int = 0,
        use_cache: bool = True,
    ) -> OCRPage:
        """
        Perform OCR on an image.

        Args:
            image: PIL Image to OCR
            page_number: Page number (for tracking)
            use_cache: Whether to use cached results

        Returns:
            OCRPage with recognized text and formatting
        """
        # Check cache
        if use_cache and Config.CACHE_ENABLED and Config.CACHE_OCR_RESULTS:
            cache_key = self._get_cache_key(image, page_number)
            cached = load_from_cache(cache_key, 'ocr')
            if cached is not None:
                logger.debug(f"Loaded OCR results from cache for page {page_number}")
                return cached

        logger.debug(f"Running OCR on page {page_number}")

        # Get detailed OCR data
        ocr_data = pytesseract.image_to_data(
            image,
            lang=self.language,
            config=self.config,
            output_type=Output.DICT
        )

        # Parse OCR data into structured format
        ocr_page = self._parse_ocr_data(ocr_data, page_number, image.size)

        # Cache the result
        if use_cache and Config.CACHE_ENABLED and Config.CACHE_OCR_RESULTS:
            save_to_cache(ocr_page, cache_key, 'ocr')

        logger.info(
            f"OCR complete for page {page_number}: "
            f"{ocr_page.word_count} words, "
            f"{ocr_page.average_confidence:.2f}% confidence"
        )

        return ocr_page

    def _parse_ocr_data(
        self,
        ocr_data: Dict[str, List],
        page_number: int,
        image_size: tuple,
    ) -> OCRPage:
        """
        Parse Tesseract OCR data into structured format.

        Args:
            ocr_data: Raw OCR data from Tesseract
            page_number: Page number
            image_size: (width, height) of image

        Returns:
            Structured OCRPage
        """
        ocr_page = OCRPage(
            page_number=page_number,
            width=image_size[0],
            height=image_size[1],
        )

        # Group words by block, paragraph, and line
        current_block = None
        current_para = None
        current_line = None

        n_boxes = len(ocr_data['text'])

        for i in range(n_boxes):
            level = ocr_data['level'][i]
            text = ocr_data['text'][i].strip()
            conf = ocr_data['conf'][i]

            # Skip empty text or low-level elements
            if not text or conf < 0:
                continue

            # Filter by minimum confidence
            if conf < Config.MIN_CONFIDENCE:
                logger.debug(f"Skipping low confidence word: '{text}' (conf={conf})")
                continue

            # Get bounding box
            x = ocr_data['left'][i]
            y = ocr_data['top'][i]
            w = ocr_data['width'][i]
            h = ocr_data['height'][i]
            bbox = BoundingBox(x=x, y=y, width=w, height=h)

            # Level 1: Page (skip)
            # Level 2: Block (new section)
            # Level 3: Paragraph
            # Level 4: Line
            # Level 5: Word

            block_num = ocr_data['block_num'][i]
            para_num = ocr_data['par_num'][i]
            line_num = ocr_data['line_num'][i]

            # Start new paragraph if needed
            if current_para is None or para_num != getattr(current_para, '_para_num', None):
                if current_para and current_para.lines:
                    ocr_page.paragraphs.append(current_para)

                current_para = OCRParagraph()
                current_para._para_num = para_num  # Track for grouping
                current_line = None

            # Start new line if needed
            if current_line is None or line_num != getattr(current_line, '_line_num', None):
                if current_line and current_line.words:
                    current_para.lines.append(current_line)

                current_line = OCRLine()
                current_line._line_num = line_num  # Track for grouping

            # Add word to current line
            word = OCRWord(
                text=text,
                confidence=float(conf),
                bbox=bbox,
                char_formatting=CharacterFormatting(),  # Will be filled by format analyzer
            )
            current_line.words.append(word)

        # Add last line and paragraph
        if current_line and current_line.words:
            current_para.lines.append(current_line)
        if current_para and current_para.lines:
            ocr_page.paragraphs.append(current_para)

        # Calculate bounding boxes for lines and paragraphs
        self._calculate_bounding_boxes(ocr_page)

        return ocr_page

    def _calculate_bounding_boxes(self, ocr_page: OCRPage) -> None:
        """
        Calculate bounding boxes for lines and paragraphs.

        Args:
            ocr_page: OCRPage to update
        """
        for paragraph in ocr_page.paragraphs:
            para_boxes = []

            for line in paragraph.lines:
                if not line.words:
                    continue

                # Calculate line bounding box
                word_boxes = [word.bbox for word in line.words]
                line.bbox = self._merge_bounding_boxes(word_boxes)
                para_boxes.append(line.bbox)

            # Calculate paragraph bounding box
            if para_boxes:
                paragraph.bbox = self._merge_bounding_boxes(para_boxes)

    def _merge_bounding_boxes(self, boxes: List[BoundingBox]) -> BoundingBox:
        """
        Merge multiple bounding boxes into one.

        Args:
            boxes: List of BoundingBox objects

        Returns:
            Merged BoundingBox
        """
        if not boxes:
            return BoundingBox(x=0, y=0, width=0, height=0)

        x_min = min(box.x for box in boxes)
        y_min = min(box.y for box in boxes)
        x_max = max(box.x2 for box in boxes)
        y_max = max(box.y2 for box in boxes)

        return BoundingBox(
            x=x_min,
            y=y_min,
            width=x_max - x_min,
            height=y_max - y_min,
        )

    def _get_cache_key(self, image: Image.Image, page_number: int) -> str:
        """
        Generate cache key for OCR results.

        Args:
            image: PIL Image
            page_number: Page number

        Returns:
            Cache key string
        """
        # Create a simple hash from image data and parameters
        import hashlib
        img_bytes = image.tobytes()
        img_hash = hashlib.md5(img_bytes[:10000]).hexdigest()  # Sample for speed
        return f"{img_hash}_{page_number}_{self.language}"

    def get_text_only(self, image: Image.Image) -> str:
        """
        Get just the text from an image (fast, no structure).

        Args:
            image: PIL Image to OCR

        Returns:
            Plain text string
        """
        try:
            text = pytesseract.image_to_string(
                image,
                lang=self.language,
                config=self.config,
            )
            return text.strip()
        except Exception as e:
            logger.error(f"OCR failed: {e}")
            return ""

    def validate_ocr_languages(self) -> List[str]:
        """
        Get list of available Tesseract languages.

        Returns:
            List of language codes
        """
        try:
            langs = pytesseract.get_languages()
            return langs
        except Exception as e:
            logger.error(f"Failed to get OCR languages: {e}")
            return []

    def is_language_available(self, language: str) -> bool:
        """
        Check if a language is available.

        Args:
            language: Language code to check

        Returns:
            True if available
        """
        available = self.validate_ocr_languages()
        return language in available


class MultiEngineOCR:
    """
    OCR engine that can use multiple OCR backends and merge results.
    """

    def __init__(
        self,
        engines: List[str] = ['tesseract'],
        language: str = Config.DEFAULT_LANGUAGE,
    ):
        """
        Initialize multi-engine OCR.

        Args:
            engines: List of engine names ('tesseract', 'easyocr', etc.)
            language: OCR language
        """
        self.engines = []
        self.language = language

        # Initialize requested engines
        for engine_name in engines:
            if engine_name == 'tesseract':
                try:
                    self.engines.append(OCREngine(language=language))
                    logger.info("Added Tesseract OCR engine")
                except Exception as e:
                    logger.warning(f"Failed to initialize Tesseract: {e}")

            elif engine_name == 'easyocr':
                # EasyOCR integration would go here
                logger.warning("EasyOCR not yet implemented")

        if not self.engines:
            raise ValueError("No OCR engines could be initialized")

    def recognize_text(
        self,
        image: Image.Image,
        page_number: int = 0,
    ) -> OCRPage:
        """
        Recognize text using all engines and merge results.

        Args:
            image: PIL Image
            page_number: Page number

        Returns:
            Merged OCRPage
        """
        if len(self.engines) == 1:
            # Single engine, no merging needed
            return self.engines[0].recognize_text(image, page_number)

        # Run all engines
        results = []
        for engine in self.engines:
            try:
                result = engine.recognize_text(image, page_number)
                results.append(result)
            except Exception as e:
                logger.error(f"Engine failed: {e}")

        if not results:
            raise RuntimeError("All OCR engines failed")

        if len(results) == 1:
            return results[0]

        # Merge results (simple implementation: use first result)
        # A more sophisticated implementation would compare and merge words
        logger.info(f"Merging results from {len(results)} OCR engines")
        return results[0]


def create_ocr_engine(
    engine: str = 'tesseract',
    language: str = Config.DEFAULT_LANGUAGE,
) -> OCREngine:
    """
    Factory function to create an OCR engine.

    Args:
        engine: Engine type ('tesseract', 'easyocr', 'both')
        language: OCR language

    Returns:
        OCR engine instance
    """
    if engine == 'tesseract':
        return OCREngine(language=language)
    elif engine == 'both':
        return MultiEngineOCR(engines=['tesseract'], language=language)
    else:
        raise ValueError(f"Unknown OCR engine: {engine}")
