"""
Text corrector module for fixing OCR errors and improving accuracy.

This module handles spell checking, context-based correction, and
fixing common OCR errors.
"""

import re
from typing import List, Dict, Optional, Set
from pathlib import Path
from loguru import logger

from config import Config
from models.formatting_models import OCRPage, OCRWord, ProcessingStats


class TextCorrector:
    """
    Corrects OCR errors and improves text accuracy.
    """

    def __init__(
        self,
        language: str = 'fr',
        use_spell_check: bool = Config.SPELL_CHECK_ENABLED,
        fix_hyphenation: bool = Config.FIX_HYPHENATION,
    ):
        """
        Initialize text corrector.

        Args:
            language: Language for correction
            use_spell_check: Enable spell checking
            fix_hyphenation: Fix hyphenated words at line breaks
        """
        self.language = language
        self.use_spell_check = use_spell_check
        self.fix_hyphenation = fix_hyphenation

        # Initialize optional components
        self.spacy_nlp = None
        self.spell_checker = None

        if use_spell_check:
            self._initialize_spell_checker()

        # Load common OCR error patterns
        self.char_replacements = Config.OCR_CHAR_REPLACEMENTS

        # Statistics
        self.stats = {
            'words_corrected': 0,
            'chars_replaced': 0,
            'hyphenations_fixed': 0,
        }

        logger.info(
            f"Initialized text corrector (language={language}, "
            f"spell_check={use_spell_check})"
        )

    def _initialize_spell_checker(self) -> None:
        """Initialize spell checking libraries."""
        # Try to import spell checking libraries
        # This is optional - the corrector will work without them

        # Attempt to load spaCy
        try:
            import spacy
            try:
                self.spacy_nlp = spacy.load(f'{self.language}_core_news_sm')
                logger.info(f"Loaded spaCy model for {self.language}")
            except OSError:
                logger.warning(
                    f"spaCy model for {self.language} not found. "
                    f"Install with: python -m spacy download {self.language}_core_news_sm"
                )
        except ImportError:
            logger.debug("spaCy not available")

        # Attempt to load LanguageTool
        try:
            import language_tool_python
            self.spell_checker = language_tool_python.LanguageTool(self.language)
            logger.info(f"Loaded LanguageTool for {self.language}")
        except ImportError:
            logger.debug("LanguageTool not available")
        except Exception as e:
            logger.warning(f"Failed to load LanguageTool: {e}")

    def correct_page(self, ocr_page: OCRPage) -> OCRPage:
        """
        Correct all text in a page.

        Args:
            ocr_page: OCRPage to correct

        Returns:
            Corrected OCRPage
        """
        logger.debug(f"Correcting text on page {ocr_page.page_number}")

        # Fix hyphenation across line breaks
        if self.fix_hyphenation:
            self._fix_hyphenation_in_page(ocr_page)

        # Correct each word
        for paragraph in ocr_page.paragraphs:
            for line in paragraph.lines:
                for word in line.words:
                    self._correct_word(word)

        logger.info(
            f"Text correction complete for page {ocr_page.page_number}: "
            f"{self.stats['words_corrected']} words corrected"
        )

        return ocr_page

    def _correct_word(self, word: OCRWord) -> None:
        """
        Correct a single word.

        Args:
            word: OCRWord to correct (modified in place)
        """
        original_text = word.text

        # Skip very short words
        if len(original_text) < Config.MIN_WORD_LENGTH_CORRECTION:
            return

        # Fix common OCR character confusions
        corrected = self._fix_char_confusions(original_text, word.confidence)

        # Apply spell checking for low-confidence words
        if self.use_spell_check and word.is_low_confidence:
            corrected = self._spell_check_word(corrected)

        # Update if changed
        if corrected != original_text:
            word.text = corrected
            self.stats['words_corrected'] += 1
            logger.debug(f"Corrected: '{original_text}' -> '{corrected}'")

    def _fix_char_confusions(self, text: str, confidence: float) -> str:
        """
        Fix common OCR character confusion errors.

        Args:
            text: Text to fix
            confidence: OCR confidence score

        Returns:
            Corrected text
        """
        # Only apply aggressive fixes for low-confidence text
        if confidence >= Config.LOW_CONFIDENCE_THRESHOLD:
            return text

        corrected = text

        # Common patterns based on context
        # These are heuristic replacements

        # Fix l/1/I confusion based on context
        # If surrounded by letters, likely 'l' or 'I'
        # If surrounded by numbers, likely '1'
        for i, char in enumerate(text):
            if char in ['l', '1', 'I', '|']:
                # Check neighbors
                prev_is_digit = (i > 0 and text[i-1].isdigit())
                next_is_digit = (i < len(text) - 1 and text[i+1].isdigit())
                prev_is_alpha = (i > 0 and text[i-1].isalpha())
                next_is_alpha = (i < len(text) - 1 and text[i+1].isalpha())

                # In numeric context
                if prev_is_digit or next_is_digit:
                    corrected = corrected[:i] + '1' + corrected[i+1:]
                # In alphabetic context
                elif prev_is_alpha or next_is_alpha:
                    # Uppercase I if at start or after space
                    if i == 0 or (i > 0 and text[i-1].isspace()):
                        corrected = corrected[:i] + 'I' + corrected[i+1:]
                    else:
                        corrected = corrected[:i] + 'l' + corrected[i+1:]

        # Fix O/0 confusion
        for i, char in enumerate(text):
            if char in ['O', '0']:
                prev_is_digit = (i > 0 and text[i-1].isdigit())
                next_is_digit = (i < len(text) - 1 and text[i+1].isdigit())

                if prev_is_digit or next_is_digit:
                    corrected = corrected[:i] + '0' + corrected[i+1:]
                else:
                    corrected = corrected[:i] + 'O' + corrected[i+1:]

        if corrected != text:
            self.stats['chars_replaced'] += 1

        return corrected

    def _spell_check_word(self, word: str) -> str:
        """
        Check and correct spelling of a word.

        Args:
            word: Word to check

        Returns:
            Corrected word
        """
        if not self.spell_checker:
            return word

        try:
            # Get corrections
            matches = self.spell_checker.check(word)

            if matches:
                # Use first suggestion
                corrected = language_tool_python.utils.correct(word, matches)
                return corrected

        except Exception as e:
            logger.debug(f"Spell check failed for '{word}': {e}")

        return word

    def _fix_hyphenation_in_page(self, ocr_page: OCRPage) -> None:
        """
        Fix hyphenated words across line breaks.

        Args:
            ocr_page: OCRPage to fix
        """
        for paragraph in ocr_page.paragraphs:
            if len(paragraph.lines) < 2:
                continue

            for i in range(len(paragraph.lines) - 1):
                current_line = paragraph.lines[i]
                next_line = paragraph.lines[i + 1]

                if not current_line.words or not next_line.words:
                    continue

                # Check if last word of current line ends with hyphen
                last_word = current_line.words[-1]
                first_word_next = next_line.words[0]

                if self._is_hyphenated(last_word.text):
                    # Remove hyphen and merge with next word
                    merged_text = self._merge_hyphenated_words(
                        last_word.text,
                        first_word_next.text
                    )

                    # Update the last word with merged text
                    last_word.text = merged_text

                    # Remove first word from next line
                    next_line.words.pop(0)

                    self.stats['hyphenations_fixed'] += 1
                    logger.debug(
                        f"Fixed hyphenation: '{last_word.text}' + "
                        f"'{first_word_next.text}' -> '{merged_text}'"
                    )

    def _is_hyphenated(self, text: str) -> bool:
        """
        Check if a word is hyphenated.

        Args:
            text: Text to check

        Returns:
            True if hyphenated
        """
        if not text:
            return False

        # Check if ends with hyphen character
        return text[-1] in Config.HYPHEN_CHARS

    def _merge_hyphenated_words(self, first: str, second: str) -> str:
        """
        Merge hyphenated words.

        Args:
            first: First part (with hyphen)
            second: Second part

        Returns:
            Merged word
        """
        # Remove hyphen from first part
        first_clean = first.rstrip(''.join(Config.HYPHEN_CHARS))

        # Merge
        merged = first_clean + second

        return merged

    def correct_text(self, text: str) -> str:
        """
        Correct plain text (without structure).

        Args:
            text: Text to correct

        Returns:
            Corrected text
        """
        if not self.spell_checker:
            return text

        try:
            matches = self.spell_checker.check(text)
            corrected = language_tool_python.utils.correct(text, matches)
            return corrected
        except Exception as e:
            logger.error(f"Text correction failed: {e}")
            return text

    def get_stats(self) -> Dict[str, int]:
        """
        Get correction statistics.

        Returns:
            Dictionary of statistics
        """
        return self.stats.copy()

    def reset_stats(self) -> None:
        """Reset statistics."""
        self.stats = {
            'words_corrected': 0,
            'chars_replaced': 0,
            'hyphenations_fixed': 0,
        }


class DictionaryManager:
    """
    Manages custom dictionaries for domain-specific terms.
    """

    def __init__(self, dictionary_path: Optional[Path] = None):
        """
        Initialize dictionary manager.

        Args:
            dictionary_path: Path to custom dictionary file
        """
        self.dictionary_path = dictionary_path or Config.CUSTOM_DICTIONARY_PATH
        self.custom_words: Set[str] = set()

        if self.dictionary_path and self.dictionary_path.exists():
            self.load_dictionary()

    def load_dictionary(self) -> None:
        """Load custom dictionary from file."""
        try:
            with open(self.dictionary_path, 'r', encoding='utf-8') as f:
                self.custom_words = {line.strip().lower() for line in f if line.strip()}
            logger.info(f"Loaded {len(self.custom_words)} custom words")
        except Exception as e:
            logger.error(f"Failed to load dictionary: {e}")

    def save_dictionary(self) -> None:
        """Save custom dictionary to file."""
        try:
            self.dictionary_path.parent.mkdir(parents=True, exist_ok=True)
            with open(self.dictionary_path, 'w', encoding='utf-8') as f:
                for word in sorted(self.custom_words):
                    f.write(f"{word}\n")
            logger.info(f"Saved {len(self.custom_words)} custom words")
        except Exception as e:
            logger.error(f"Failed to save dictionary: {e}")

    def add_word(self, word: str) -> None:
        """
        Add a word to the dictionary.

        Args:
            word: Word to add
        """
        self.custom_words.add(word.strip().lower())

    def is_in_dictionary(self, word: str) -> bool:
        """
        Check if a word is in the dictionary.

        Args:
            word: Word to check

        Returns:
            True if in dictionary
        """
        return word.lower() in self.custom_words


def create_text_corrector(
    language: str = 'fr',
    enabled: bool = Config.SPELL_CHECK_ENABLED,
) -> Optional[TextCorrector]:
    """
    Factory function to create a TextCorrector.

    Args:
        language: Language code
        enabled: Whether correction is enabled

    Returns:
        TextCorrector instance or None if disabled
    """
    if not enabled:
        return None

    return TextCorrector(language=language)
