"""
Unit tests for data models.
"""

import pytest

from models.formatting_models import (
    BoundingBox,
    Color,
    CharacterFormatting,
    ParagraphFormatting,
    Alignment,
    OCRWord,
    OCRLine,
    OCRParagraph,
    OCRPage,
)


class TestBoundingBox:
    """Tests for BoundingBox class."""

    def test_create_bbox(self):
        """Test creating a bounding box."""
        bbox = BoundingBox(x=10, y=20, width=100, height=50)
        assert bbox.x == 10
        assert bbox.y == 20
        assert bbox.width == 100
        assert bbox.height == 50

    def test_bbox_properties(self):
        """Test bounding box computed properties."""
        bbox = BoundingBox(x=10, y=20, width=100, height=50)
        assert bbox.x2 == 110
        assert bbox.y2 == 70
        assert bbox.center_x == 60
        assert bbox.center_y == 45
        assert bbox.area == 5000

    def test_bbox_overlaps(self):
        """Test bounding box overlap detection."""
        bbox1 = BoundingBox(x=0, y=0, width=100, height=100)
        bbox2 = BoundingBox(x=50, y=50, width=100, height=100)
        bbox3 = BoundingBox(x=200, y=200, width=100, height=100)

        assert bbox1.overlaps(bbox2)
        assert not bbox1.overlaps(bbox3)

    def test_bbox_contains_point(self):
        """Test point containment."""
        bbox = BoundingBox(x=10, y=10, width=100, height=100)
        assert bbox.contains_point(50, 50)
        assert not bbox.contains_point(200, 200)


class TestColor:
    """Tests for Color class."""

    def test_create_color(self):
        """Test creating a color."""
        color = Color(r=255, g=128, b=0)
        assert color.r == 255
        assert color.g == 128
        assert color.b == 0

    def test_color_validation(self):
        """Test color value validation."""
        with pytest.raises(ValueError):
            Color(r=256, g=0, b=0)

        with pytest.raises(ValueError):
            Color(r=-1, g=0, b=0)

    def test_color_to_tuple(self):
        """Test color to tuple conversion."""
        color = Color(r=255, g=128, b=0)
        assert color.to_tuple() == (255, 128, 0)

    def test_color_to_hex(self):
        """Test color to hex conversion."""
        color = Color(r=255, g=128, b=0)
        assert color.to_hex() == '#ff8000'

    def test_color_from_tuple(self):
        """Test creating color from tuple."""
        color = Color.from_tuple((255, 128, 0))
        assert color.r == 255
        assert color.g == 128
        assert color.b == 0

    def test_color_from_hex(self):
        """Test creating color from hex."""
        color = Color.from_hex('#ff8000')
        assert color.r == 255
        assert color.g == 128
        assert color.b == 0

    def test_is_black(self):
        """Test black color detection."""
        black = Color(r=0, g=0, b=0)
        assert black.is_black()

        not_black = Color(r=100, g=100, b=100)
        assert not not_black.is_black()

    def test_is_white(self):
        """Test white color detection."""
        white = Color(r=255, g=255, b=255)
        assert white.is_white()

        not_white = Color(r=100, g=100, b=100)
        assert not not_white.is_white()


class TestCharacterFormatting:
    """Tests for CharacterFormatting class."""

    def test_create_formatting(self):
        """Test creating character formatting."""
        fmt = CharacterFormatting(
            font_family='Arial',
            font_size=12.0,
            is_bold=True,
        )
        assert fmt.font_family == 'Arial'
        assert fmt.font_size == 12.0
        assert fmt.is_bold is True
        assert fmt.is_italic is False

    def test_formatting_to_dict(self):
        """Test converting formatting to dictionary."""
        fmt = CharacterFormatting(font_family='Arial', font_size=12.0)
        result = fmt.to_dict()
        assert isinstance(result, dict)
        assert result['font_family'] == 'Arial'
        assert result['font_size'] == 12.0

    def test_formatting_similarity(self):
        """Test formatting similarity comparison."""
        fmt1 = CharacterFormatting(
            font_family='Arial',
            font_size=12.0,
            is_bold=True,
        )
        fmt2 = CharacterFormatting(
            font_family='Arial',
            font_size=12.0,
            is_bold=True,
        )
        fmt3 = CharacterFormatting(
            font_family='Times',
            font_size=14.0,
            is_bold=False,
        )

        assert fmt1.is_similar(fmt2, threshold=0.95)
        assert not fmt1.is_similar(fmt3, threshold=0.95)


class TestOCRStructures:
    """Tests for OCR data structures."""

    def test_ocr_word(self):
        """Test OCRWord creation."""
        bbox = BoundingBox(x=10, y=10, width=50, height=20)
        word = OCRWord(text='Hello', confidence=95.5, bbox=bbox)

        assert word.text == 'Hello'
        assert word.confidence == 95.5
        assert not word.is_low_confidence

    def test_ocr_line(self):
        """Test OCRLine with multiple words."""
        bbox1 = BoundingBox(x=10, y=10, width=50, height=20)
        bbox2 = BoundingBox(x=70, y=10, width=50, height=20)

        word1 = OCRWord(text='Hello', confidence=95.0, bbox=bbox1)
        word2 = OCRWord(text='World', confidence=90.0, bbox=bbox2)

        line = OCRLine(words=[word1, word2])

        assert line.text == 'Hello World'
        assert line.average_confidence == 92.5

    def test_ocr_paragraph(self):
        """Test OCRParagraph with multiple lines."""
        bbox = BoundingBox(x=10, y=10, width=50, height=20)
        word = OCRWord(text='Test', confidence=95.0, bbox=bbox)
        line = OCRLine(words=[word])
        para = OCRParagraph(lines=[line])

        assert 'Test' in para.text
        assert para.word_count == 1

    def test_ocr_page(self):
        """Test OCRPage structure."""
        bbox = BoundingBox(x=10, y=10, width=50, height=20)
        word = OCRWord(text='Test', confidence=95.0, bbox=bbox)
        line = OCRLine(words=[word])
        para = OCRParagraph(lines=[line])
        page = OCRPage(page_number=0, paragraphs=[para])

        assert page.page_number == 0
        assert page.word_count == 1
        assert 'Test' in page.text


if __name__ == '__main__':
    pytest.main([__file__, '-v'])
