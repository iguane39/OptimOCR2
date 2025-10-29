"""
Format analyzer module for detecting text formatting from visual features.

This module analyzes images to detect font properties, styles, alignment,
and spacing.
"""

from typing import List, Tuple, Optional
import numpy as np
from PIL import Image
import cv2
from loguru import logger
from sklearn.cluster import KMeans

from config import Config
from models.formatting_models import (
    OCRPage,
    OCRParagraph,
    OCRLine,
    OCRWord,
    CharacterFormatting,
    ParagraphFormatting,
    Alignment,
    Color,
    BoundingBox,
)
from modules.utils import pixels_to_points, pil_to_cv2


class FormatAnalyzer:
    """
    Analyzes visual formatting of text in images.
    """

    def __init__(self, dpi: int = Config.DPI_DEFAULT):
        """
        Initialize format analyzer.

        Args:
            dpi: DPI of the images being analyzed
        """
        self.dpi = dpi
        logger.info(f"Initialized format analyzer with DPI={dpi}")

    def analyze_page(self, ocr_page: OCRPage, image: Image.Image) -> OCRPage:
        """
        Analyze formatting for an entire page.

        Args:
            ocr_page: OCRPage with text data
            image: Original PIL Image

        Returns:
            OCRPage with formatting information added
        """
        logger.debug(f"Analyzing formatting for page {ocr_page.page_number}")

        # Convert image to OpenCV format
        cv_image = pil_to_cv2(image)

        # Analyze each paragraph
        for paragraph in ocr_page.paragraphs:
            self._analyze_paragraph(paragraph, cv_image, ocr_page.width)

        logger.info(f"Format analysis complete for page {ocr_page.page_number}")

        return ocr_page

    def _analyze_paragraph(
        self,
        paragraph: OCRParagraph,
        image: np.ndarray,
        page_width: int,
    ) -> None:
        """
        Analyze formatting for a paragraph.

        Args:
            paragraph: OCRParagraph to analyze
            image: OpenCV image
            page_width: Width of the page
        """
        if not paragraph.lines:
            return

        # Detect paragraph alignment
        paragraph.para_formatting.alignment = self._detect_alignment(
            paragraph.lines,
            page_width
        )

        # Calculate spacing
        self._calculate_paragraph_spacing(paragraph)

        # Analyze each line
        for line in paragraph.lines:
            self._analyze_line(line, image)

    def _analyze_line(self, line: OCRLine, image: np.ndarray) -> None:
        """
        Analyze formatting for a line.

        Args:
            line: OCRLine to analyze
            image: OpenCV image
        """
        if not line.words:
            return

        # Analyze each word
        for word in line.words:
            self._analyze_word(word, image)

    def _analyze_word(self, word: OCRWord, image: np.ndarray) -> None:
        """
        Analyze formatting for a single word.

        Args:
            word: OCRWord to analyze
            image: OpenCV image
        """
        bbox = word.bbox

        # Extract word region from image
        word_img = image[bbox.y:bbox.y2, bbox.x:bbox.x2]

        if word_img.size == 0:
            return

        # Detect font size
        font_size = self._estimate_font_size(word_img, bbox.height)
        word.char_formatting.font_size = font_size

        # Detect bold
        is_bold = self._detect_bold(word_img)
        word.char_formatting.is_bold = is_bold

        # Detect italic
        is_italic = self._detect_italic(word_img)
        word.char_formatting.is_italic = is_italic

        # Detect font family
        font_family = self._detect_font_family(word_img, is_bold, is_italic)
        word.char_formatting.font_family = font_family

        # Detect colors
        text_color, bg_color = self._detect_colors(word_img)
        word.char_formatting.text_color = text_color
        word.char_formatting.background_color = bg_color

        # Detect small caps (simplified)
        if word.text.isupper() and len(word.text) >= Config.SMALL_CAPS_MIN_CHARS:
            word.char_formatting.is_small_caps = self._detect_small_caps(word_img)

    def _estimate_font_size(self, word_img: np.ndarray, height: int) -> float:
        """
        Estimate font size from word image.

        Args:
            word_img: Word image region
            height: Bounding box height in pixels

        Returns:
            Font size in points
        """
        # Simple estimation: convert height to points
        # A more sophisticated approach would analyze character heights
        font_size_px = height
        font_size_pt = pixels_to_points(font_size_px, self.dpi)

        # Clamp to reasonable range
        font_size_pt = max(Config.FONT_SIZE_MIN, min(Config.FONT_SIZE_MAX, font_size_pt))

        return round(font_size_pt, 1)

    def _detect_bold(self, word_img: np.ndarray) -> bool:
        """
        Detect if text is bold by analyzing stroke width.

        Args:
            word_img: Word image region

        Returns:
            True if bold
        """
        if word_img.size == 0:
            return False

        # Convert to grayscale if needed
        if len(word_img.shape) == 3:
            gray = cv2.cvtColor(word_img, cv2.COLOR_BGR2GRAY)
        else:
            gray = word_img

        # Threshold
        _, binary = cv2.threshold(gray, 0, 255, cv2.THRESH_BINARY_INV + cv2.THRESH_OTSU)

        # Calculate ratio of black pixels to total pixels
        total_pixels = binary.size
        black_pixels = np.sum(binary == 255)

        if total_pixels == 0:
            return False

        ratio = black_pixels / total_pixels

        # Bold text has more black pixels
        is_bold = ratio > Config.BOLD_THRESHOLD

        return is_bold

    def _detect_italic(self, word_img: np.ndarray) -> bool:
        """
        Detect if text is italic by analyzing slant angle.

        Args:
            word_img: Word image region

        Returns:
            True if italic
        """
        if word_img.size == 0 or word_img.shape[0] < 10 or word_img.shape[1] < 10:
            return False

        try:
            # Convert to grayscale
            if len(word_img.shape) == 3:
                gray = cv2.cvtColor(word_img, cv2.COLOR_BGR2GRAY)
            else:
                gray = word_img

            # Edge detection
            edges = cv2.Canny(gray, 50, 150)

            # Detect lines using probabilistic Hough transform
            lines = cv2.HoughLinesP(
                edges,
                rho=1,
                theta=np.pi / 180,
                threshold=10,
                minLineLength=int(gray.shape[0] * 0.3),
                maxLineGap=5
            )

            if lines is None or len(lines) == 0:
                return False

            # Calculate angles of vertical-ish lines
            angles = []
            for line in lines:
                x1, y1, x2, y2 = line[0]

                # Skip near-horizontal lines
                if abs(y2 - y1) < abs(x2 - x1):
                    continue

                # Calculate angle from vertical
                if y2 != y1:
                    angle = np.degrees(np.arctan2(x2 - x1, y2 - y1))
                    angles.append(angle)

            if not angles:
                return False

            # Median angle
            median_angle = np.median(angles)

            # Italic text typically has 5-20 degrees slant
            is_italic = (Config.ITALIC_ANGLE_RANGE[0] <= abs(median_angle) <= Config.ITALIC_ANGLE_RANGE[1])

            return is_italic

        except Exception as e:
            logger.debug(f"Italic detection failed: {e}")
            return False

    def _detect_font_family(
        self,
        word_img: np.ndarray,
        is_bold: bool,
        is_italic: bool,
    ) -> str:
        """
        Detect font family (serif vs sans-serif).

        Args:
            word_img: Word image region
            is_bold: Whether text is bold
            is_italic: Whether text is italic

        Returns:
            Font family name
        """
        # This is a simplified implementation
        # A real implementation would analyze character features

        # For now, use a simple heuristic based on stroke characteristics
        has_serifs = self._detect_serifs(word_img)

        if has_serifs:
            base_font = Config.FONT_MAPPING['serif']
        else:
            base_font = Config.FONT_MAPPING['sans-serif']

        return base_font

    def _detect_serifs(self, word_img: np.ndarray) -> bool:
        """
        Detect if text has serifs.

        Args:
            word_img: Word image region

        Returns:
            True if serifs detected
        """
        # Simplified: assume sans-serif for now
        # A real implementation would analyze edge patterns
        return False

    def _detect_colors(
        self,
        word_img: np.ndarray,
    ) -> Tuple[Optional[Color], Optional[Color]]:
        """
        Detect text and background colors.

        Args:
            word_img: Word image region

        Returns:
            (text_color, background_color) tuple
        """
        if word_img.size == 0:
            return None, None

        try:
            # Convert to RGB if needed
            if len(word_img.shape) == 3:
                rgb_img = cv2.cvtColor(word_img, cv2.COLOR_BGR2RGB)
            else:
                rgb_img = cv2.cvtColor(word_img, cv2.COLOR_GRAY2RGB)

            # Flatten to list of pixels
            pixels = rgb_img.reshape(-1, 3)

            # Use KMeans to find 2 dominant colors (text and background)
            if len(pixels) < 2:
                return None, None

            kmeans = KMeans(n_clusters=2, random_state=42, n_init=10)
            kmeans.fit(pixels)

            # Get the two cluster centers
            colors = kmeans.cluster_centers_.astype(int)

            # Assume darker color is text, lighter is background
            color1 = Color.from_tuple(tuple(colors[0]))
            color2 = Color.from_tuple(tuple(colors[1]))

            # Determine which is text and which is background
            brightness1 = sum(colors[0]) / 3
            brightness2 = sum(colors[1]) / 3

            if brightness1 < brightness2:
                text_color = color1
                bg_color = color2
            else:
                text_color = color2
                bg_color = color1

            return text_color, bg_color

        except Exception as e:
            logger.debug(f"Color detection failed: {e}")
            return None, None

    def _detect_small_caps(self, word_img: np.ndarray) -> bool:
        """
        Detect if text uses small caps.

        Args:
            word_img: Word image region

        Returns:
            True if small caps
        """
        # Simplified implementation
        # Would need to compare letter heights within the word
        return False

    def _detect_alignment(
        self,
        lines: List[OCRLine],
        page_width: int,
    ) -> Alignment:
        """
        Detect text alignment.

        Args:
            lines: List of OCRLine objects
            page_width: Width of the page

        Returns:
            Alignment enum value
        """
        if not lines:
            return Alignment.LEFT

        # Get left and right edges of lines
        left_edges = []
        right_edges = []

        for line in lines:
            if not line.bbox:
                continue
            left_edges.append(line.bbox.x)
            right_edges.append(line.bbox.x2)

        if not left_edges:
            return Alignment.LEFT

        # Calculate statistics
        left_variance = np.var(left_edges)
        right_variance = np.var(right_edges)

        # Check for centered text
        centers = [(l + r) / 2 for l, r in zip(left_edges, right_edges)]
        page_center = page_width / 2
        center_distances = [abs(c - page_center) for c in centers]
        avg_center_distance = np.mean(center_distances)

        tolerance = page_width * Config.CENTER_TOLERANCE

        if avg_center_distance < tolerance:
            return Alignment.CENTER

        # Check for right alignment
        if right_variance < left_variance:
            # Right edges are more consistent
            avg_right = np.mean(right_edges)
            if avg_right > page_width * 0.7:  # Close to right edge
                return Alignment.RIGHT

        # Check for justified
        if len(lines) >= Config.JUSTIFIED_MIN_LINES:
            if left_variance < 50 and right_variance < 50:
                return Alignment.JUSTIFIED

        # Default to left
        return Alignment.LEFT

    def _calculate_paragraph_spacing(self, paragraph: OCRParagraph) -> None:
        """
        Calculate spacing for a paragraph.

        Args:
            paragraph: OCRParagraph to update
        """
        if not paragraph.lines or len(paragraph.lines) < 2:
            return

        # Calculate line spacing
        line_heights = []
        line_gaps = []

        for i, line in enumerate(paragraph.lines):
            if not line.bbox:
                continue

            line_heights.append(line.bbox.height)

            # Calculate gap to next line
            if i < len(paragraph.lines) - 1:
                next_line = paragraph.lines[i + 1]
                if next_line.bbox:
                    gap = next_line.bbox.y - line.bbox.y2
                    line_gaps.append(gap)

        if line_heights:
            avg_line_height = np.mean(line_heights)
            avg_line_height_pt = pixels_to_points(avg_line_height, self.dpi)

            if line_gaps:
                avg_gap = np.mean(line_gaps)
                avg_gap_pt = pixels_to_points(avg_gap, self.dpi)

                # Line spacing as multiplier
                if avg_line_height > 0:
                    line_spacing = (avg_line_height + avg_gap) / avg_line_height
                    paragraph.para_formatting.line_spacing = round(line_spacing, 2)

                # Spacing before/after (simplified)
                paragraph.para_formatting.spacing_after = round(avg_gap_pt, 1)

        # Detect indentation
        if paragraph.lines:
            first_line = paragraph.lines[0]
            other_lines = paragraph.lines[1:]

            if first_line.bbox and other_lines:
                other_left_edges = [line.bbox.x for line in other_lines if line.bbox]
                if other_left_edges:
                    avg_other_left = np.mean(other_left_edges)
                    indent_px = first_line.bbox.x - avg_other_left
                    if abs(indent_px) > 10:  # Significant indent
                        indent_pt = pixels_to_points(abs(indent_px), self.dpi)
                        if indent_px > 0:
                            paragraph.para_formatting.indent_first_line = round(indent_pt, 1)
                        else:
                            paragraph.para_formatting.indent_left = round(indent_pt, 1)


def create_format_analyzer(dpi: int = Config.DPI_DEFAULT) -> FormatAnalyzer:
    """
    Factory function to create a FormatAnalyzer.

    Args:
        dpi: DPI of images

    Returns:
        FormatAnalyzer instance
    """
    return FormatAnalyzer(dpi=dpi)
