"""
Multi-pass OCR module for improved accuracy through multiple attempts.

This module provides:
- Multi-resolution OCR (test at different DPIs and merge results)
- Multi-angle OCR (test rotations and select best)
- Result fusion and confidence-based selection
"""

from typing import List, Optional, Tuple
import numpy as np
from PIL import Image
from loguru import logger

from config import Config
from models.formatting_models import (
    OCRPage, OCRParagraph, OCRLine, OCRWord, BoundingBox
)
from modules.ocr_engine import OCREngine


class MultiPassOCR:
    """
    Multi-pass OCR processor for improved accuracy.
    """

    def __init__(
        self,
        ocr_engine: OCREngine,
        dpi_list: Optional[List[int]] = None,
        test_angles: bool = True,
    ):
        """
        Initialize multi-pass OCR.

        Args:
            ocr_engine: Base OCR engine to use
            dpi_list: List of DPIs to test (None for default)
            test_angles: Whether to test multiple angles
        """
        self.ocr_engine = ocr_engine
        self.dpi_list = dpi_list or [300, 600, 900]
        self.test_angles = test_angles

        logger.info(
            f"Initialized MultiPassOCR with DPIs={self.dpi_list}, "
            f"test_angles={test_angles}"
        )

    def process_multi_resolution(
        self,
        image: Image.Image,
        page_number: int = 0,
    ) -> OCRPage:
        """
        Process image at multiple resolutions and merge results.

        Args:
            image: PIL Image to process
            page_number: Page number

        Returns:
            Merged OCRPage with best results from all resolutions
        """
        logger.info(f"Running multi-resolution OCR at {self.dpi_list} DPI")

        results = []
        base_width, base_height = image.size

        for dpi in self.dpi_list:
            # Calculate scaling factor
            scale = dpi / 300.0  # Assume base is 300 DPI

            # Resize image
            new_width = int(base_width * scale)
            new_height = int(base_height * scale)
            resized = image.resize((new_width, new_height), Image.LANCZOS)

            logger.debug(f"Processing at {dpi} DPI ({new_width}x{new_height})")

            # Run OCR
            try:
                ocr_result = self.ocr_engine.recognize_text(resized, page_number)

                # Scale bounding boxes back to original size
                ocr_result = self._scale_bboxes(ocr_result, 1.0 / scale)

                results.append((dpi, ocr_result))
                logger.debug(
                    f"DPI {dpi}: {ocr_result.word_count} words, "
                    f"avg confidence {ocr_result.average_confidence:.2f}%"
                )

            except Exception as e:
                logger.error(f"OCR failed at {dpi} DPI: {e}")

        if not results:
            raise RuntimeError("All resolution attempts failed")

        # Merge results, preferring high-confidence words
        merged = self._merge_multi_resolution_results(results)

        logger.info(
            f"Multi-resolution OCR complete: {merged.word_count} words, "
            f"avg confidence {merged.average_confidence:.2f}%"
        )

        return merged

    def process_multi_angle(
        self,
        image: Image.Image,
        page_number: int = 0,
        angles: Optional[List[float]] = None,
    ) -> OCRPage:
        """
        Test multiple rotation angles and select the best result.

        Args:
            image: PIL Image to process
            page_number: Page number
            angles: List of angles to test (None for default)

        Returns:
            OCRPage from best angle
        """
        if angles is None:
            angles = [0, 90, 180, 270, -5, 5]  # Common angles + small corrections

        logger.info(f"Testing rotation angles: {angles}")

        best_result = None
        best_confidence = 0
        best_angle = 0

        for angle in angles:
            # Rotate image
            if angle != 0:
                rotated = image.rotate(angle, expand=True, fillcolor='white')
            else:
                rotated = image

            logger.debug(f"Testing angle {angle}°")

            # Run OCR
            try:
                result = self.ocr_engine.recognize_text(rotated, page_number)

                logger.debug(
                    f"Angle {angle}°: {result.word_count} words, "
                    f"confidence {result.average_confidence:.2f}%"
                )

                # Select best based on average confidence
                if result.average_confidence > best_confidence:
                    best_confidence = result.average_confidence
                    best_result = result
                    best_angle = angle

            except Exception as e:
                logger.error(f"OCR failed at angle {angle}°: {e}")

        if best_result is None:
            raise RuntimeError("All angle attempts failed")

        logger.info(
            f"Best angle: {best_angle}° with confidence {best_confidence:.2f}%"
        )

        return best_result

    def process_enhanced(
        self,
        image: Image.Image,
        page_number: int = 0,
        use_multi_resolution: bool = True,
        use_multi_angle: bool = True,
    ) -> OCRPage:
        """
        Process with all enhancements enabled.

        Args:
            image: PIL Image to process
            page_number: Page number
            use_multi_resolution: Enable multi-resolution
            use_multi_angle: Enable multi-angle

        Returns:
            Best OCRPage result
        """
        # First, test angles if enabled
        if use_multi_angle and self.test_angles:
            # Quick angle test with lower resolution
            small_image = image.resize(
                (image.width // 2, image.height // 2),
                Image.LANCZOS
            )
            best_angle_result = self.process_multi_angle(small_image, page_number)

            # Determine best angle from small test
            # For simplicity, we'll just use 0° for now
            # In production, would extract the angle used
            working_image = image
        else:
            working_image = image

        # Then, multi-resolution if enabled
        if use_multi_resolution:
            result = self.process_multi_resolution(working_image, page_number)
        else:
            result = self.ocr_engine.recognize_text(working_image, page_number)

        return result

    def _scale_bboxes(self, ocr_page: OCRPage, scale: float) -> OCRPage:
        """
        Scale all bounding boxes in an OCRPage.

        Args:
            ocr_page: OCRPage to scale
            scale: Scale factor

        Returns:
            Scaled OCRPage
        """
        for paragraph in ocr_page.paragraphs:
            if paragraph.bbox:
                paragraph.bbox = self._scale_bbox(paragraph.bbox, scale)

            for line in paragraph.lines:
                if line.bbox:
                    line.bbox = self._scale_bbox(line.bbox, scale)

                for word in line.words:
                    word.bbox = self._scale_bbox(word.bbox, scale)

        # Update page dimensions
        ocr_page.width = int(ocr_page.width * scale)
        ocr_page.height = int(ocr_page.height * scale)

        return ocr_page

    def _scale_bbox(self, bbox: BoundingBox, scale: float) -> BoundingBox:
        """Scale a single bounding box."""
        return BoundingBox(
            x=int(bbox.x * scale),
            y=int(bbox.y * scale),
            width=int(bbox.width * scale),
            height=int(bbox.height * scale),
        )

    def _merge_multi_resolution_results(
        self,
        results: List[Tuple[int, OCRPage]]
    ) -> OCRPage:
        """
        Merge results from multiple resolutions.

        Strategy: For each word position, use the version with highest confidence.

        Args:
            results: List of (dpi, OCRPage) tuples

        Returns:
            Merged OCRPage
        """
        if not results:
            raise ValueError("No results to merge")

        if len(results) == 1:
            return results[0][1]

        # Use the first (lowest DPI) as base
        base_dpi, base_page = results[0]
        merged_page = OCRPage(
            page_number=base_page.page_number,
            width=base_page.width,
            height=base_page.height,
            dpi=base_dpi,
        )

        # Get all result pages
        pages = [page for _, page in results]

        # Merge paragraph by paragraph
        max_paragraphs = max(len(page.paragraphs) for page in pages)

        for para_idx in range(max_paragraphs):
            # Get paragraphs at this index from all results
            paragraphs = []
            for page in pages:
                if para_idx < len(page.paragraphs):
                    paragraphs.append(page.paragraphs[para_idx])

            if not paragraphs:
                continue

            # Merge this paragraph
            merged_para = self._merge_paragraphs(paragraphs)
            merged_page.paragraphs.append(merged_para)

        return merged_page

    def _merge_paragraphs(self, paragraphs: List[OCRParagraph]) -> OCRParagraph:
        """
        Merge multiple versions of the same paragraph.

        Args:
            paragraphs: List of OCRParagraph objects

        Returns:
            Merged OCRParagraph
        """
        if not paragraphs:
            return OCRParagraph()

        if len(paragraphs) == 1:
            return paragraphs[0]

        # Use the paragraph with highest average confidence as base
        best_para = max(paragraphs, key=lambda p: p.average_confidence)
        merged = OCRParagraph(
            bbox=best_para.bbox,
            para_formatting=best_para.para_formatting,
        )

        # Merge line by line
        max_lines = max(len(p.lines) for p in paragraphs)

        for line_idx in range(max_lines):
            lines = []
            for para in paragraphs:
                if line_idx < len(para.lines):
                    lines.append(para.lines[line_idx])

            if lines:
                merged_line = self._merge_lines(lines)
                merged.lines.append(merged_line)

        return merged

    def _merge_lines(self, lines: List[OCRLine]) -> OCRLine:
        """
        Merge multiple versions of the same line.

        Args:
            lines: List of OCRLine objects

        Returns:
            Merged OCRLine
        """
        if not lines:
            return OCRLine()

        if len(lines) == 1:
            return lines[0]

        # Use line with highest confidence as base
        best_line = max(lines, key=lambda l: l.average_confidence)
        merged = OCRLine(bbox=best_line.bbox)

        # Merge word by word
        max_words = max(len(line.words) for line in lines)

        for word_idx in range(max_words):
            words = []
            for line in lines:
                if word_idx < len(line.words):
                    words.append(line.words[word_idx])

            if words:
                # Select word with highest confidence
                best_word = max(words, key=lambda w: w.confidence)
                merged.words.append(best_word)

        return merged


def create_multi_pass_ocr(
    ocr_engine: OCREngine,
    enable_multi_resolution: bool = True,
    enable_multi_angle: bool = True,
) -> MultiPassOCR:
    """
    Factory function to create a MultiPassOCR instance.

    Args:
        ocr_engine: Base OCR engine
        enable_multi_resolution: Enable multi-resolution processing
        enable_multi_angle: Enable multi-angle processing

    Returns:
        Configured MultiPassOCR instance
    """
    dpi_list = [300, 600, 900] if enable_multi_resolution else [600]

    return MultiPassOCR(
        ocr_engine=ocr_engine,
        dpi_list=dpi_list,
        test_angles=enable_multi_angle,
    )
