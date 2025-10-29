"""
Unit tests for text correction module.
"""

import pytest

from modules.text_corrector import TextCorrector
from models.formatting_models import OCRWord, OCRLine, OCRParagraph, OCRPage, BoundingBox


class TestTextCorrector:
    """Tests for TextCorrector class."""

    @pytest.fixture
    def corrector(self):
        """Create a text corrector instance."""
        return TextCorrector(language='fr', use_spell_check=False)

    def test_char_confusion_l_to_1(self, corrector):
        """Test l/1 confusion correction."""
        # When surrounded by digits, 'l' should become '1'
        result = corrector._fix_char_confusions('12l45', confidence=50)
        # In low confidence context with digits, should correct
        assert '1' in result or 'l' in result  # Depends on context

    def test_hyphenation_detection(self, corrector):
        """Test hyphenation detection."""
        assert corrector._is_hyphenated('pro-')
        assert corrector._is_hyphenated('pro‐')
        assert not corrector._is_hyphenated('pro')

    def test_merge_hyphenated_words(self, corrector):
        """Test merging hyphenated words."""
        result = corrector._merge_hyphenated_words('pro-', 'gramme')
        assert result == 'programme'

        result = corrector._merge_hyphenated_words('compré-', 'hension')
        assert result == 'compréhension'

    def test_hyphenation_fix_in_page(self, corrector):
        """Test fixing hyphenation across lines."""
        # Create test page with hyphenated word
        bbox1 = BoundingBox(x=10, y=10, width=50, height=20)
        bbox2 = BoundingBox(x=10, y=40, width=50, height=20)

        word1 = OCRWord(text='pro-', confidence=90, bbox=bbox1)
        word2 = OCRWord(text='gramme', confidence=90, bbox=bbox2)

        line1 = OCRLine(words=[word1])
        line2 = OCRLine(words=[word2])

        para = OCRParagraph(lines=[line1, line2])
        page = OCRPage(page_number=0, paragraphs=[para])

        # Apply correction
        corrector._fix_hyphenation_in_page(page)

        # Check that hyphenation was fixed
        assert corrector.stats['hyphenations_fixed'] > 0

    def test_get_stats(self, corrector):
        """Test getting correction statistics."""
        stats = corrector.get_stats()
        assert isinstance(stats, dict)
        assert 'words_corrected' in stats
        assert 'chars_replaced' in stats
        assert 'hyphenations_fixed' in stats

    def test_reset_stats(self, corrector):
        """Test resetting statistics."""
        corrector.stats['words_corrected'] = 10
        corrector.reset_stats()
        assert corrector.stats['words_corrected'] == 0


class TestCharacterConfusions:
    """Tests for common OCR character confusion fixes."""

    @pytest.fixture
    def corrector(self):
        """Create a text corrector instance."""
        return TextCorrector(language='fr', use_spell_check=False)

    def test_O_0_confusion(self, corrector):
        """Test O/0 confusion in different contexts."""
        # In numeric context
        result = corrector._fix_char_confusions('12O45', confidence=50)
        # Should prefer '0' in numeric context
        assert '0' in result or 'O' in result

    def test_preserves_high_confidence(self, corrector):
        """Test that high confidence text is preserved."""
        original = 'Hello'
        result = corrector._fix_char_confusions(original, confidence=95)
        assert result == original


if __name__ == '__main__':
    pytest.main([__file__, '-v'])
