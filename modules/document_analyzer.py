"""
Document analyzer module for detecting document types and structures.

This module provides:
- Document type detection (book, article, form, table, etc.)
- Table structure extraction
- Layout analysis
- Adaptive OCR configuration based on document type
"""

from typing import Dict, List, Optional, Tuple
from enum import Enum
import numpy as np
from PIL import Image
import cv2
from loguru import logger

from config import Config
from models.formatting_models import OCRPage, BoundingBox
from modules.utils import pil_to_cv2


class DocumentType(Enum):
    """Document type classification."""
    GENERAL = "general"
    BOOK = "book"
    ARTICLE = "article"
    SCIENTIFIC = "scientific"
    FORM = "form"
    TABLE = "table"
    INVOICE = "invoice"
    RECEIPT = "receipt"
    MULTI_COLUMN = "multi_column"


class DocumentAnalyzer:
    """
    Analyzes document structure and type.
    """

    def __init__(self):
        """Initialize document analyzer."""
        logger.info("Initialized DocumentAnalyzer")

    def detect_document_type(
        self,
        image: Image.Image,
        ocr_page: Optional[OCRPage] = None
    ) -> DocumentType:
        """
        Detect the type of document.

        Args:
            image: PIL Image of the page
            ocr_page: Optional OCR results for text-based analysis

        Returns:
            DocumentType enum
        """
        features = self._extract_features(image, ocr_page)

        # Decision tree based on features
        if features['has_table_structure']:
            if features['form_like']:
                return DocumentType.FORM
            else:
                return DocumentType.TABLE

        if features['has_mathematical_symbols']:
            return DocumentType.SCIENTIFIC

        if features['multi_column']:
            return DocumentType.MULTI_COLUMN

        if features['dense_text'] and features['consistent_margins']:
            return DocumentType.BOOK

        if features['short_lines'] and features['sparse_layout']:
            if features['has_amounts']:
                return DocumentType.RECEIPT
            elif features['has_invoice_keywords']:
                return DocumentType.INVOICE

        return DocumentType.GENERAL

    def _extract_features(
        self,
        image: Image.Image,
        ocr_page: Optional[OCRPage]
    ) -> Dict[str, bool]:
        """
        Extract features from document for classification.

        Args:
            image: PIL Image
            ocr_page: Optional OCR results

        Returns:
            Dictionary of boolean features
        """
        cv_image = pil_to_cv2(image)

        features = {
            'has_table_structure': self._detect_table_structure(cv_image),
            'form_like': self._detect_form_structure(cv_image),
            'multi_column': self._detect_columns(cv_image, ocr_page),
            'dense_text': self._analyze_text_density(ocr_page) if ocr_page else False,
            'consistent_margins': self._check_margins(ocr_page) if ocr_page else False,
            'short_lines': self._check_line_lengths(ocr_page) if ocr_page else False,
            'sparse_layout': self._check_layout_sparsity(ocr_page) if ocr_page else False,
            'has_mathematical_symbols': self._detect_math_symbols(ocr_page) if ocr_page else False,
            'has_amounts': self._detect_amounts(ocr_page) if ocr_page else False,
            'has_invoice_keywords': self._detect_invoice_keywords(ocr_page) if ocr_page else False,
        }

        logger.debug(f"Extracted features: {features}")
        return features

    def _detect_table_structure(self, image: np.ndarray) -> bool:
        """
        Detect if image contains table structure.

        Args:
            image: OpenCV image

        Returns:
            True if table detected
        """
        try:
            # Convert to grayscale
            if len(image.shape) == 3:
                gray = cv2.cvtColor(image, cv2.COLOR_BGR2GRAY)
            else:
                gray = image.copy()

            # Detect horizontal and vertical lines
            horizontal = self._detect_lines(gray, horizontal=True)
            vertical = self._detect_lines(gray, horizontal=False)

            # Check for grid pattern
            h_count = np.sum(horizontal > 0) / horizontal.shape[0]
            v_count = np.sum(vertical > 0) / vertical.shape[1]

            # If we have significant horizontal and vertical lines, likely a table
            has_table = h_count > 0.1 and v_count > 0.05

            logger.debug(f"Table detection: h_lines={h_count:.3f}, v_lines={v_count:.3f}, has_table={has_table}")
            return has_table

        except Exception as e:
            logger.debug(f"Table detection failed: {e}")
            return False

    def _detect_lines(self, gray: np.ndarray, horizontal: bool = True) -> np.ndarray:
        """
        Detect horizontal or vertical lines in image.

        Args:
            gray: Grayscale image
            horizontal: True for horizontal lines, False for vertical

        Returns:
            Binary image with detected lines
        """
        # Binary threshold
        _, binary = cv2.threshold(gray, 0, 255, cv2.THRESH_BINARY_INV + cv2.THRESH_OTSU)

        # Create kernel for line detection
        if horizontal:
            kernel_length = gray.shape[1] // 30
            kernel = cv2.getStructuringElement(cv2.MORPH_RECT, (kernel_length, 1))
        else:
            kernel_length = gray.shape[0] // 30
            kernel = cv2.getStructuringElement(cv2.MORPH_RECT, (1, kernel_length))

        # Detect lines
        lines = cv2.morphologyEx(binary, cv2.MORPH_OPEN, kernel, iterations=2)

        return lines

    def _detect_form_structure(self, image: np.ndarray) -> bool:
        """
        Detect if image is a form (has fields/boxes).

        Args:
            image: OpenCV image

        Returns:
            True if form detected
        """
        try:
            # Convert to grayscale
            if len(image.shape) == 3:
                gray = cv2.cvtColor(image, cv2.COLOR_BGR2GRAY)
            else:
                gray = image.copy()

            # Detect rectangles (form fields)
            edges = cv2.Canny(gray, 50, 150)
            contours, _ = cv2.findContours(edges, cv2.RETR_TREE, cv2.CHAIN_APPROX_SIMPLE)

            # Count rectangular contours
            rect_count = 0
            for contour in contours:
                approx = cv2.approxPolyDP(contour, 0.02 * cv2.arcLength(contour, True), True)
                if len(approx) == 4:  # Rectangle
                    area = cv2.contourArea(contour)
                    if 100 < area < 10000:  # Reasonable field size
                        rect_count += 1

            # Forms typically have many small rectangles
            is_form = rect_count > 10

            logger.debug(f"Form detection: {rect_count} rectangles, is_form={is_form}")
            return is_form

        except Exception as e:
            logger.debug(f"Form detection failed: {e}")
            return False

    def _detect_columns(
        self,
        image: np.ndarray,
        ocr_page: Optional[OCRPage]
    ) -> bool:
        """
        Detect multi-column layout.

        Args:
            image: OpenCV image
            ocr_page: Optional OCR results

        Returns:
            True if multiple columns detected
        """
        if not ocr_page or not ocr_page.paragraphs:
            return False

        # Analyze x-coordinates of paragraphs/lines
        x_positions = []

        for para in ocr_page.paragraphs:
            for line in para.lines:
                if line.bbox:
                    x_positions.append(line.bbox.x)

        if not x_positions:
            return False

        # Cluster x-positions to find column boundaries
        x_positions = np.array(x_positions)
        hist, bins = np.histogram(x_positions, bins=20)

        # Find peaks (column starts)
        from scipy.signal import find_peaks
        peaks, _ = find_peaks(hist, height=len(x_positions) * 0.05)

        has_columns = len(peaks) >= 2

        logger.debug(f"Column detection: {len(peaks)} peaks, has_columns={has_columns}")
        return has_columns

    def _analyze_text_density(self, ocr_page: OCRPage) -> bool:
        """Check if text is dense (like a book)."""
        if not ocr_page.paragraphs:
            return False

        total_words = ocr_page.word_count
        total_lines = sum(len(para.lines) for para in ocr_page.paragraphs)

        if total_lines == 0:
            return False

        words_per_line = total_words / total_lines
        return words_per_line > 8  # Books typically have 8+ words per line

    def _check_margins(self, ocr_page: OCRPage) -> bool:
        """Check if document has consistent margins."""
        if not ocr_page.paragraphs:
            return False

        left_margins = []
        for para in ocr_page.paragraphs:
            for line in para.lines:
                if line.bbox:
                    left_margins.append(line.bbox.x)

        if not left_margins:
            return False

        # Check variance of left margins
        variance = np.var(left_margins)
        return variance < 100  # Low variance = consistent margins

    def _check_line_lengths(self, ocr_page: OCRPage) -> bool:
        """Check if lines are short (like receipts)."""
        if not ocr_page.paragraphs:
            return False

        line_lengths = []
        for para in ocr_page.paragraphs:
            for line in para.lines:
                line_lengths.append(len(line.words))

        if not line_lengths:
            return False

        avg_length = np.mean(line_lengths)
        return avg_length < 5  # Short lines

    def _check_layout_sparsity(self, ocr_page: OCRPage) -> bool:
        """Check if layout is sparse."""
        if not ocr_page.paragraphs:
            return False

        return len(ocr_page.paragraphs) < 20  # Few paragraphs = sparse

    def _detect_math_symbols(self, ocr_page: OCRPage) -> bool:
        """Detect mathematical symbols."""
        math_symbols = set('∫∑∏√±≤≥≠≈∞∂∇')
        text = ocr_page.text.lower()

        return any(symbol in text for symbol in math_symbols)

    def _detect_amounts(self, ocr_page: OCRPage) -> bool:
        """Detect monetary amounts."""
        import re
        text = ocr_page.text

        # Look for currency patterns
        patterns = [
            r'\$\d+\.?\d*',  # $123.45
            r'\d+\.?\d*\s*€',  # 123.45 €
            r'\d+\.?\d*\s*EUR',  # 123.45 EUR
            r'\d+,\d{2}\s*€',  # 123,45 €
        ]

        for pattern in patterns:
            if re.search(pattern, text):
                return True

        return False

    def _detect_invoice_keywords(self, ocr_page: OCRPage) -> bool:
        """Detect invoice-related keywords."""
        keywords = ['facture', 'invoice', 'total', 'montant', 'amount', 'due', 'payé']
        text = ocr_page.text.lower()

        return sum(1 for kw in keywords if kw in text) >= 2

    def get_optimized_config(self, doc_type: DocumentType) -> Dict:
        """
        Get optimized OCR configuration for document type.

        Args:
            doc_type: Detected document type

        Returns:
            Configuration dictionary
        """
        configs = {
            DocumentType.GENERAL: {
                'psm': 3,  # Auto
                'preserve_layout': False,
            },
            DocumentType.BOOK: {
                'psm': 1,  # Auto with OSD
                'preserve_layout': False,
                'fix_hyphenation': True,
            },
            DocumentType.SCIENTIFIC: {
                'psm': 6,  # Single block
                'preserve_layout': True,
                'preserve_formulas': True,
            },
            DocumentType.TABLE: {
                'psm': 6,  # Single block
                'preserve_layout': True,
                'table_detection': True,
            },
            DocumentType.FORM: {
                'psm': 6,  # Single block
                'preserve_layout': True,
            },
            DocumentType.MULTI_COLUMN: {
                'psm': 1,  # Auto with OSD
                'preserve_layout': True,
                'column_detection': True,
            },
            DocumentType.INVOICE: {
                'psm': 6,  # Single block
                'preserve_layout': True,
            },
            DocumentType.RECEIPT: {
                'psm': 6,  # Single block
                'preserve_layout': True,
            },
        }

        return configs.get(doc_type, configs[DocumentType.GENERAL])


class TableExtractor:
    """
    Extracts table structure from images.
    """

    def __init__(self):
        """Initialize table extractor."""
        logger.info("Initialized TableExtractor")

    def extract_table(
        self,
        image: Image.Image,
    ) -> Optional[List[List[BoundingBox]]]:
        """
        Extract table structure (cell positions).

        Args:
            image: PIL Image containing a table

        Returns:
            2D list of cell bounding boxes (rows x columns) or None
        """
        try:
            cv_image = pil_to_cv2(image)

            # Convert to grayscale
            if len(cv_image.shape) == 3:
                gray = cv2.cvtColor(cv_image, cv2.COLOR_BGR2GRAY)
            else:
                gray = cv_image.copy()

            # Detect lines
            horizontal_lines = self._detect_table_lines(gray, horizontal=True)
            vertical_lines = self._detect_table_lines(gray, horizontal=False)

            # Find intersections
            cells = self._find_cells(horizontal_lines, vertical_lines)

            if cells:
                logger.info(f"Extracted {len(cells)} rows from table")
                return cells

        except Exception as e:
            logger.error(f"Table extraction failed: {e}")

        return None

    def _detect_table_lines(self, gray: np.ndarray, horizontal: bool) -> List[int]:
        """
        Detect table lines.

        Args:
            gray: Grayscale image
            horizontal: True for horizontal, False for vertical

        Returns:
            List of line positions
        """
        # Binarize
        _, binary = cv2.threshold(gray, 0, 255, cv2.THRESH_BINARY_INV + cv2.THRESH_OTSU)

        # Create kernel
        if horizontal:
            kernel = cv2.getStructuringElement(cv2.MORPH_RECT, (gray.shape[1] // 20, 1))
        else:
            kernel = cv2.getStructuringElement(cv2.MORPH_RECT, (1, gray.shape[0] // 20))

        # Detect lines
        lines = cv2.morphologyEx(binary, cv2.MORPH_OPEN, kernel, iterations=2)

        # Find line positions
        if horizontal:
            projection = np.sum(lines, axis=1)
        else:
            projection = np.sum(lines, axis=0)

        # Find peaks
        threshold = np.max(projection) * 0.5
        line_positions = np.where(projection > threshold)[0]

        # Group nearby positions
        grouped = []
        if len(line_positions) > 0:
            current_group = [line_positions[0]]
            for pos in line_positions[1:]:
                if pos - current_group[-1] < 5:  # Within 5 pixels
                    current_group.append(pos)
                else:
                    grouped.append(int(np.mean(current_group)))
                    current_group = [pos]
            grouped.append(int(np.mean(current_group)))

        return grouped

    def _find_cells(
        self,
        h_lines: List[int],
        v_lines: List[int]
    ) -> List[List[BoundingBox]]:
        """
        Find cell bounding boxes from line positions.

        Args:
            h_lines: Horizontal line positions (y-coordinates)
            v_lines: Vertical line positions (x-coordinates)

        Returns:
            2D list of cell bounding boxes
        """
        if len(h_lines) < 2 or len(v_lines) < 2:
            return []

        cells = []

        # Create cells between lines
        for i in range(len(h_lines) - 1):
            row = []
            for j in range(len(v_lines) - 1):
                cell = BoundingBox(
                    x=v_lines[j],
                    y=h_lines[i],
                    width=v_lines[j + 1] - v_lines[j],
                    height=h_lines[i + 1] - h_lines[i],
                )
                row.append(cell)
            cells.append(row)

        return cells


def create_document_analyzer() -> DocumentAnalyzer:
    """
    Factory function to create a DocumentAnalyzer.

    Returns:
        DocumentAnalyzer instance
    """
    return DocumentAnalyzer()


def create_table_extractor() -> TableExtractor:
    """
    Factory function to create a TableExtractor.

    Returns:
        TableExtractor instance
    """
    return TableExtractor()
