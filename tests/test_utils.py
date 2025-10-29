"""
Unit tests for utility functions.
"""

import pytest
import numpy as np
from pathlib import Path
from PIL import Image

from modules.utils import (
    parse_page_range,
    pixels_to_points,
    points_to_pixels,
    format_time,
    chunk_list,
)


class TestPageRangeParsing:
    """Tests for page range parsing."""

    def test_parse_all_pages(self):
        """Test parsing 'all' keyword."""
        result = parse_page_range('all', 10)
        assert result == list(range(10))

    def test_parse_single_page(self):
        """Test parsing single page."""
        result = parse_page_range('5', 10)
        assert result == [4]  # 0-indexed

    def test_parse_page_range(self):
        """Test parsing page range."""
        result = parse_page_range('1-5', 10)
        assert result == [0, 1, 2, 3, 4]

    def test_parse_multiple_ranges(self):
        """Test parsing multiple ranges."""
        result = parse_page_range('1-3,5,7-9', 10)
        assert result == [0, 1, 2, 4, 6, 7, 8]

    def test_parse_out_of_range(self):
        """Test handling out of range pages."""
        result = parse_page_range('8-15', 10)
        assert result == [7, 8, 9]  # Only valid pages


class TestUnitConversion:
    """Tests for unit conversion functions."""

    def test_pixels_to_points_72dpi(self):
        """Test pixel to point conversion at 72 DPI."""
        result = pixels_to_points(72, 72)
        assert result == 72.0

    def test_pixels_to_points_300dpi(self):
        """Test pixel to point conversion at 300 DPI."""
        result = pixels_to_points(300, 300)
        assert result == 72.0

    def test_points_to_pixels_72dpi(self):
        """Test point to pixel conversion at 72 DPI."""
        result = points_to_pixels(72, 72)
        assert result == 72.0

    def test_points_to_pixels_300dpi(self):
        """Test point to pixel conversion at 300 DPI."""
        result = points_to_pixels(72, 300)
        assert abs(result - 300.0) < 0.01


class TestTimeFormatting:
    """Tests for time formatting."""

    def test_format_seconds(self):
        """Test formatting seconds."""
        result = format_time(45.5)
        assert 's' in result

    def test_format_minutes(self):
        """Test formatting minutes."""
        result = format_time(125.0)
        assert 'm' in result

    def test_format_hours(self):
        """Test formatting hours."""
        result = format_time(7325.0)
        assert 'h' in result


class TestListOperations:
    """Tests for list operations."""

    def test_chunk_list(self):
        """Test chunking a list."""
        items = list(range(10))
        chunks = chunk_list(items, 3)
        assert len(chunks) == 4
        assert chunks[0] == [0, 1, 2]
        assert chunks[-1] == [9]

    def test_chunk_list_exact(self):
        """Test chunking with exact division."""
        items = list(range(9))
        chunks = chunk_list(items, 3)
        assert len(chunks) == 3
        assert all(len(chunk) == 3 for chunk in chunks)


if __name__ == '__main__':
    pytest.main([__file__, '-v'])
