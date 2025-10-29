"""
EasyOCR engine integration module.

This module provides an alternative OCR engine using EasyOCR,
which can be used standalone or in ensemble with Tesseract.
"""

from typing import List, Optional
import numpy as np
from PIL import Image
from loguru import logger

try:
    import easyocr
    EASYOCR_AVAILABLE = True
except ImportError:
    EASYOCR_AVAILABLE = False
    logger.warning("EasyOCR not installed. Install with: pip install easyocr")

from config import Config
from models.formatting_models import (
    OCRWord,
    OCRLine,
    OCRParagraph,
    OCRPage,
    BoundingBox,
    CharacterFormatting,
)


class EasyOCREngine:
    """
    OCR engine using EasyOCR.
    """

    def __init__(
        self,
        languages: List[str] = None,
        gpu: bool = False,
    ):
        """
        Initialize EasyOCR engine.

        Args:
            languages: List of language codes (e.g., ['fr', 'en'])
            gpu: Whether to use GPU acceleration
        """
        if not EASYOCR_AVAILABLE:
            raise ImportError(
                "EasyOCR is required. Install it with: pip install easyocr"
            )

        # Convert language codes (fra -> fr, eng -> en)
        if languages is None:
            languages = ['fr', 'en']
        else:
            languages = [self._convert_lang_code(lang) for lang in languages]

        self.languages = languages
        self.gpu = gpu

        logger.info(f"Initializing EasyOCR with languages={languages}, gpu={gpu}")

        try:
            self.reader = easyocr.Reader(
                languages,
                gpu=gpu,
                verbose=False,
            )
            logger.info("EasyOCR initialized successfully")
        except Exception as e:
            logger.error(f"Failed to initialize EasyOCR: {e}")
            raise

    def recognize_text(
        self,
        image: Image.Image,
        page_number: int = 0,
    ) -> OCRPage:
        """
        Perform OCR on an image using EasyOCR.

        Args:
            image: PIL Image to OCR
            page_number: Page number (for tracking)

        Returns:
            OCRPage with recognized text
        """
        logger.debug(f"Running EasyOCR on page {page_number}")

        # Convert PIL to numpy array
        image_np = np.array(image)

        # Run EasyOCR
        try:
            results = self.reader.readtext(
                image_np,
                detail=1,  # Get bounding boxes and confidence
                paragraph=False,  # We'll group ourselves
            )
        except Exception as e:
            logger.error(f"EasyOCR recognition failed: {e}")
            raise

        # Parse results into OCRPage structure
        ocr_page = self._parse_easyocr_results(
            results,
            page_number,
            image.size
        )

        logger.info(
            f"EasyOCR complete for page {page_number}: "
            f"{ocr_page.word_count} words, "
            f"{ocr_page.average_confidence:.2f}% confidence"
        )

        return ocr_page

    def _parse_easyocr_results(
        self,
        results: List,
        page_number: int,
        image_size: tuple,
    ) -> OCRPage:
        """
        Parse EasyOCR results into OCRPage structure.

        Args:
            results: EasyOCR results
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

        if not results:
            return ocr_page

        # Group results into lines based on y-coordinate
        lines_dict = {}

        for bbox_points, text, confidence in results:
            # bbox_points is [[x1,y1], [x2,y2], [x3,y3], [x4,y4]]
            # Convert to our BoundingBox format
            points = np.array(bbox_points)
            x = int(np.min(points[:, 0]))
            y = int(np.min(points[:, 1]))
            w = int(np.max(points[:, 0]) - x)
            h = int(np.max(points[:, 1]) - y)

            bbox = BoundingBox(x=x, y=y, width=w, height=h)

            # Create OCRWord
            word = OCRWord(
                text=text,
                confidence=float(confidence * 100),  # Convert to 0-100 range
                bbox=bbox,
                char_formatting=CharacterFormatting(),
            )

            # Group by line (approximate y-coordinate)
            line_key = round(y / 10) * 10  # Group words within 10 pixels
            if line_key not in lines_dict:
                lines_dict[line_key] = []
            lines_dict[line_key].append(word)

        # Sort lines by y-coordinate
        sorted_line_keys = sorted(lines_dict.keys())

        # Create OCRLines
        current_paragraph = OCRParagraph()

        for line_key in sorted_line_keys:
            words = lines_dict[line_key]

            # Sort words by x-coordinate (left to right)
            words.sort(key=lambda w: w.bbox.x)

            # Create line
            line = OCRLine(words=words)

            # Calculate line bounding box
            if words:
                line.bbox = self._calculate_line_bbox(words)

            current_paragraph.lines.append(line)

        # Add paragraph to page
        if current_paragraph.lines:
            # Calculate paragraph bounding box
            if current_paragraph.lines:
                line_boxes = [line.bbox for line in current_paragraph.lines if line.bbox]
                if line_boxes:
                    current_paragraph.bbox = self._merge_bboxes(line_boxes)

            ocr_page.paragraphs.append(current_paragraph)

        return ocr_page

    def _calculate_line_bbox(self, words: List[OCRWord]) -> BoundingBox:
        """Calculate bounding box for a line of words."""
        if not words:
            return BoundingBox(x=0, y=0, width=0, height=0)

        boxes = [word.bbox for word in words]
        return self._merge_bboxes(boxes)

    def _merge_bboxes(self, boxes: List[BoundingBox]) -> BoundingBox:
        """Merge multiple bounding boxes."""
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

    def _convert_lang_code(self, lang: str) -> str:
        """
        Convert Tesseract language codes to EasyOCR codes.

        Args:
            lang: Tesseract language code (e.g., 'fra', 'eng')

        Returns:
            EasyOCR language code (e.g., 'fr', 'en')
        """
        mapping = {
            'fra': 'fr',
            'eng': 'en',
            'deu': 'de',
            'spa': 'es',
            'ita': 'it',
            'por': 'pt',
            'chi_sim': 'ch_sim',
            'chi_tra': 'ch_tra',
            'jpn': 'ja',
            'kor': 'ko',
        }

        return mapping.get(lang, lang[:2])  # Default to first 2 chars


class EnsembleOCREngine:
    """
    Ensemble OCR engine that combines multiple OCR engines.
    """

    def __init__(
        self,
        engines: List[str] = None,
        language: str = 'fra',
        gpu: bool = False,
    ):
        """
        Initialize ensemble OCR.

        Args:
            engines: List of engine names ('tesseract', 'easyocr')
            language: Language code
            gpu: Use GPU for EasyOCR
        """
        if engines is None:
            engines = ['tesseract', 'easyocr']

        self.engine_instances = []
        self.engine_names = []

        # Initialize Tesseract
        if 'tesseract' in engines:
            try:
                from modules.ocr_engine import OCREngine
                tesseract = OCREngine(language=language)
                self.engine_instances.append(tesseract)
                self.engine_names.append('tesseract')
                logger.info("Added Tesseract to ensemble")
            except Exception as e:
                logger.warning(f"Failed to initialize Tesseract: {e}")

        # Initialize EasyOCR
        if 'easyocr' in engines:
            try:
                easyocr_engine = EasyOCREngine(languages=[language], gpu=gpu)
                self.engine_instances.append(easyocr_engine)
                self.engine_names.append('easyocr')
                logger.info("Added EasyOCR to ensemble")
            except Exception as e:
                logger.warning(f"Failed to initialize EasyOCR: {e}")

        if not self.engine_instances:
            raise ValueError("No OCR engines could be initialized")

        logger.info(f"Ensemble OCR initialized with engines: {self.engine_names}")

    def recognize_text(
        self,
        image: Image.Image,
        page_number: int = 0,
        strategy: str = 'voting',
    ) -> OCRPage:
        """
        Recognize text using all engines and merge results.

        Args:
            image: PIL Image to OCR
            page_number: Page number
            strategy: Merging strategy ('voting', 'confidence', 'best')

        Returns:
            Merged OCRPage
        """
        logger.info(f"Running ensemble OCR with {len(self.engine_instances)} engines")

        results = []

        for engine_name, engine in zip(self.engine_names, self.engine_instances):
            try:
                logger.debug(f"Running {engine_name}...")
                result = engine.recognize_text(image, page_number)
                results.append((engine_name, result))
                logger.debug(
                    f"{engine_name}: {result.word_count} words, "
                    f"{result.average_confidence:.2f}% confidence"
                )
            except Exception as e:
                logger.error(f"{engine_name} failed: {e}")

        if not results:
            raise RuntimeError("All OCR engines failed")

        # Merge results based on strategy
        if strategy == 'voting':
            merged = self._merge_by_voting(results)
        elif strategy == 'confidence':
            merged = self._merge_by_confidence(results)
        else:  # 'best'
            merged = self._select_best(results)

        logger.info(
            f"Ensemble OCR complete: {merged.word_count} words, "
            f"{merged.average_confidence:.2f}% confidence"
        )

        return merged

    def _merge_by_voting(self, results: List[tuple]) -> OCRPage:
        """
        Merge by majority voting on each word.

        Args:
            results: List of (engine_name, OCRPage) tuples

        Returns:
            Merged OCRPage
        """
        # For simplicity, use the result with highest average confidence
        # A full voting implementation would compare word-by-word
        return self._select_best(results)

    def _merge_by_confidence(self, results: List[tuple]) -> OCRPage:
        """
        Merge by selecting highest confidence for each word.

        Args:
            results: List of (engine_name, OCRPage) tuples

        Returns:
            Merged OCRPage
        """
        # Use the first result as base, but replace words with higher confidence
        # versions from other results
        if not results:
            raise ValueError("No results to merge")

        base_name, base_page = results[0]

        # For now, simple implementation: just use best overall
        # Full implementation would merge word-by-word
        return self._select_best(results)

    def _select_best(self, results: List[tuple]) -> OCRPage:
        """
        Select the result with highest overall confidence.

        Args:
            results: List of (engine_name, OCRPage) tuples

        Returns:
            Best OCRPage
        """
        if not results:
            raise ValueError("No results to select from")

        best_name, best_page = max(
            results,
            key=lambda x: x[1].average_confidence
        )

        logger.info(f"Selected {best_name} as best result")
        return best_page


def create_easyocr_engine(
    languages: List[str] = None,
    gpu: bool = False,
) -> EasyOCREngine:
    """
    Factory function to create an EasyOCR engine.

    Args:
        languages: List of language codes
        gpu: Use GPU acceleration

    Returns:
        EasyOCREngine instance
    """
    return EasyOCREngine(languages=languages, gpu=gpu)


def create_ensemble_engine(
    engines: List[str] = None,
    language: str = 'fra',
    gpu: bool = False,
) -> EnsembleOCREngine:
    """
    Factory function to create an ensemble OCR engine.

    Args:
        engines: List of engine names
        language: Language code
        gpu: Use GPU for EasyOCR

    Returns:
        EnsembleOCREngine instance
    """
    return EnsembleOCREngine(engines=engines, language=language, gpu=gpu)
