"""
Data models for text formatting information.

This module contains dataclasses representing various formatting properties
extracted from OCR'd text.
"""

from dataclasses import dataclass, field
from typing import Optional, Tuple, List, Dict, Any
from enum import Enum


class Alignment(Enum):
    """Text alignment types."""
    LEFT = "left"
    CENTER = "center"
    RIGHT = "right"
    JUSTIFIED = "justified"


class FontFamily(Enum):
    """Common font families."""
    SERIF = "serif"
    SANS_SERIF = "sans-serif"
    MONOSPACE = "monospace"
    CURSIVE = "cursive"
    FANTASY = "fantasy"


@dataclass
class BoundingBox:
    """Represents a bounding box with coordinates."""
    x: int
    y: int
    width: int
    height: int

    @property
    def x2(self) -> int:
        """Right edge x-coordinate."""
        return self.x + self.width

    @property
    def y2(self) -> int:
        """Bottom edge y-coordinate."""
        return self.y + self.height

    @property
    def center_x(self) -> float:
        """Center x-coordinate."""
        return self.x + self.width / 2

    @property
    def center_y(self) -> float:
        """Center y-coordinate."""
        return self.y + self.height / 2

    @property
    def area(self) -> int:
        """Area of the bounding box."""
        return self.width * self.height

    def overlaps(self, other: 'BoundingBox') -> bool:
        """Check if this box overlaps with another."""
        return not (self.x2 < other.x or other.x2 < self.x or
                   self.y2 < other.y or other.y2 < self.y)

    def contains_point(self, x: int, y: int) -> bool:
        """Check if a point is inside this box."""
        return self.x <= x <= self.x2 and self.y <= y <= self.y2


@dataclass
class Color:
    """RGB color representation."""
    r: int
    g: int
    b: int

    def __post_init__(self):
        """Validate color values."""
        for value in (self.r, self.g, self.b):
            if not 0 <= value <= 255:
                raise ValueError(f"Color values must be between 0 and 255, got {value}")

    def to_tuple(self) -> Tuple[int, int, int]:
        """Convert to RGB tuple."""
        return (self.r, self.g, self.b)

    def to_hex(self) -> str:
        """Convert to hex string."""
        return f"#{self.r:02x}{self.g:02x}{self.b:02x}"

    @classmethod
    def from_tuple(cls, rgb: Tuple[int, int, int]) -> 'Color':
        """Create Color from RGB tuple."""
        return cls(r=rgb[0], g=rgb[1], b=rgb[2])

    @classmethod
    def from_hex(cls, hex_color: str) -> 'Color':
        """Create Color from hex string."""
        hex_color = hex_color.lstrip('#')
        return cls(
            r=int(hex_color[0:2], 16),
            g=int(hex_color[2:4], 16),
            b=int(hex_color[4:6], 16)
        )

    def is_black(self, threshold: int = 50) -> bool:
        """Check if color is approximately black."""
        return max(self.r, self.g, self.b) < threshold

    def is_white(self, threshold: int = 200) -> bool:
        """Check if color is approximately white."""
        return min(self.r, self.g, self.b) > threshold


@dataclass
class CharacterFormatting:
    """Character-level formatting properties."""
    font_family: Optional[str] = None
    font_size: Optional[float] = None  # in points
    is_bold: bool = False
    is_italic: bool = False
    is_underlined: bool = False
    is_strikethrough: bool = False
    is_small_caps: bool = False
    is_superscript: bool = False
    is_subscript: bool = False
    text_color: Optional[Color] = None
    background_color: Optional[Color] = None

    def to_dict(self) -> Dict[str, Any]:
        """Convert to dictionary."""
        return {
            'font_family': self.font_family,
            'font_size': self.font_size,
            'is_bold': self.is_bold,
            'is_italic': self.is_italic,
            'is_underlined': self.is_underlined,
            'is_strikethrough': self.is_strikethrough,
            'is_small_caps': self.is_small_caps,
            'is_superscript': self.is_superscript,
            'is_subscript': self.is_subscript,
            'text_color': self.text_color.to_tuple() if self.text_color else None,
            'background_color': self.background_color.to_tuple() if self.background_color else None,
        }

    def is_similar(self, other: 'CharacterFormatting', threshold: float = 0.95) -> bool:
        """
        Check if this formatting is similar to another.

        Args:
            other: Another CharacterFormatting instance
            threshold: Similarity threshold (0.0 to 1.0)

        Returns:
            True if similar enough
        """
        score = 0
        total = 0

        # Font family
        total += 1
        if self.font_family == other.font_family:
            score += 1

        # Font size (allow 0.5 point tolerance)
        total += 1
        if self.font_size and other.font_size:
            if abs(self.font_size - other.font_size) <= 0.5:
                score += 1
        elif self.font_size == other.font_size:
            score += 1

        # Boolean properties
        for attr in ['is_bold', 'is_italic', 'is_underlined', 'is_strikethrough',
                     'is_small_caps', 'is_superscript', 'is_subscript']:
            total += 1
            if getattr(self, attr) == getattr(other, attr):
                score += 1

        return (score / total) >= threshold


@dataclass
class ParagraphFormatting:
    """Paragraph-level formatting properties."""
    alignment: Alignment = Alignment.LEFT
    indent_first_line: float = 0.0  # in points
    indent_left: float = 0.0
    indent_right: float = 0.0
    spacing_before: float = 0.0  # in points
    spacing_after: float = 0.0
    line_spacing: float = 1.0  # multiplier
    keep_with_next: bool = False
    keep_together: bool = False
    page_break_before: bool = False
    widow_control: bool = True

    def to_dict(self) -> Dict[str, Any]:
        """Convert to dictionary."""
        return {
            'alignment': self.alignment.value,
            'indent_first_line': self.indent_first_line,
            'indent_left': self.indent_left,
            'indent_right': self.indent_right,
            'spacing_before': self.spacing_before,
            'spacing_after': self.spacing_after,
            'line_spacing': self.line_spacing,
            'keep_with_next': self.keep_with_next,
            'keep_together': self.keep_together,
            'page_break_before': self.page_break_before,
            'widow_control': self.widow_control,
        }


@dataclass
class OCRWord:
    """Represents a single word from OCR with its properties."""
    text: str
    confidence: float  # 0-100
    bbox: BoundingBox
    char_formatting: CharacterFormatting = field(default_factory=CharacterFormatting)

    @property
    def is_low_confidence(self) -> bool:
        """Check if word has low confidence."""
        from config import Config
        return self.confidence < Config.LOW_CONFIDENCE_THRESHOLD

    def to_dict(self) -> Dict[str, Any]:
        """Convert to dictionary."""
        return {
            'text': self.text,
            'confidence': self.confidence,
            'bbox': {
                'x': self.bbox.x,
                'y': self.bbox.y,
                'width': self.bbox.width,
                'height': self.bbox.height,
            },
            'char_formatting': self.char_formatting.to_dict(),
        }


@dataclass
class OCRLine:
    """Represents a line of text from OCR."""
    words: List[OCRWord] = field(default_factory=list)
    bbox: Optional[BoundingBox] = None

    @property
    def text(self) -> str:
        """Get full text of the line."""
        return ' '.join(word.text for word in self.words)

    @property
    def average_confidence(self) -> float:
        """Calculate average confidence for the line."""
        if not self.words:
            return 0.0
        return sum(word.confidence for word in self.words) / len(self.words)

    @property
    def height(self) -> int:
        """Get line height."""
        if self.bbox:
            return self.bbox.height
        if self.words:
            return max(word.bbox.height for word in self.words)
        return 0

    def get_dominant_formatting(self) -> CharacterFormatting:
        """Get the most common formatting in the line."""
        if not self.words:
            return CharacterFormatting()

        # For simplicity, return the first word's formatting
        # In a real implementation, you'd analyze all words and pick the most common
        return self.words[0].char_formatting


@dataclass
class OCRParagraph:
    """Represents a paragraph of text from OCR."""
    lines: List[OCRLine] = field(default_factory=list)
    bbox: Optional[BoundingBox] = None
    para_formatting: ParagraphFormatting = field(default_factory=ParagraphFormatting)

    @property
    def text(self) -> str:
        """Get full text of the paragraph."""
        return '\n'.join(line.text for line in self.lines)

    @property
    def average_confidence(self) -> float:
        """Calculate average confidence for the paragraph."""
        if not self.lines:
            return 0.0
        return sum(line.average_confidence for line in self.lines) / len(self.lines)

    @property
    def word_count(self) -> int:
        """Get total word count in paragraph."""
        return sum(len(line.words) for line in self.lines)

    def get_all_words(self) -> List[OCRWord]:
        """Get all words from all lines."""
        words = []
        for line in self.lines:
            words.extend(line.words)
        return words


@dataclass
class OCRPage:
    """Represents a complete page from OCR."""
    page_number: int
    paragraphs: List[OCRParagraph] = field(default_factory=list)
    width: int = 0
    height: int = 0
    dpi: int = 300

    @property
    def text(self) -> str:
        """Get full text of the page."""
        return '\n\n'.join(para.text for para in self.paragraphs)

    @property
    def average_confidence(self) -> float:
        """Calculate average confidence for the page."""
        if not self.paragraphs:
            return 0.0
        return sum(para.average_confidence for para in self.paragraphs) / len(self.paragraphs)

    @property
    def word_count(self) -> int:
        """Get total word count in page."""
        return sum(para.word_count for para in self.paragraphs)

    def get_all_words(self) -> List[OCRWord]:
        """Get all words from all paragraphs."""
        words = []
        for para in self.paragraphs:
            words.extend(para.get_all_words())
        return words

    def to_dict(self) -> Dict[str, Any]:
        """Convert to dictionary."""
        return {
            'page_number': self.page_number,
            'width': self.width,
            'height': self.height,
            'dpi': self.dpi,
            'word_count': self.word_count,
            'average_confidence': self.average_confidence,
            'text': self.text,
        }


@dataclass
class OCRDocument:
    """Represents a complete OCR'd document."""
    pages: List[OCRPage] = field(default_factory=list)
    metadata: Dict[str, Any] = field(default_factory=dict)

    @property
    def page_count(self) -> int:
        """Get total number of pages."""
        return len(self.pages)

    @property
    def text(self) -> str:
        """Get full text of the document."""
        return '\n\n--- PAGE BREAK ---\n\n'.join(page.text for page in self.pages)

    @property
    def average_confidence(self) -> float:
        """Calculate average confidence for the entire document."""
        if not self.pages:
            return 0.0
        return sum(page.average_confidence for page in self.pages) / len(self.pages)

    @property
    def word_count(self) -> int:
        """Get total word count in document."""
        return sum(page.word_count for page in self.pages)

    def to_dict(self) -> Dict[str, Any]:
        """Convert to dictionary."""
        return {
            'page_count': self.page_count,
            'word_count': self.word_count,
            'average_confidence': self.average_confidence,
            'metadata': self.metadata,
            'pages': [page.to_dict() for page in self.pages],
        }


@dataclass
class ProcessingStats:
    """Statistics about the processing."""
    total_pages: int = 0
    processed_pages: int = 0
    total_words: int = 0
    low_confidence_words: int = 0
    corrected_words: int = 0
    processing_time: float = 0.0  # in seconds
    average_confidence: float = 0.0

    def to_dict(self) -> Dict[str, Any]:
        """Convert to dictionary."""
        return {
            'total_pages': self.total_pages,
            'processed_pages': self.processed_pages,
            'total_words': self.total_words,
            'low_confidence_words': self.low_confidence_words,
            'corrected_words': self.corrected_words,
            'processing_time': self.processing_time,
            'average_confidence': self.average_confidence,
            'words_per_second': self.total_words / self.processing_time if self.processing_time > 0 else 0,
        }

    def __str__(self) -> str:
        """String representation of stats."""
        return (
            f"Processing Statistics:\n"
            f"  Pages: {self.processed_pages}/{self.total_pages}\n"
            f"  Words: {self.total_words}\n"
            f"  Low confidence words: {self.low_confidence_words}\n"
            f"  Corrected words: {self.corrected_words}\n"
            f"  Average confidence: {self.average_confidence:.2f}%\n"
            f"  Processing time: {self.processing_time:.2f}s\n"
        )
