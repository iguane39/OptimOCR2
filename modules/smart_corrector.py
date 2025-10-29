"""
Smart text correction module with advanced NLP techniques.

This module provides:
- Contextual correction using language models
- N-gram based correction
- Adaptive dictionary learning
- Domain-specific vocabulary
"""

from typing import Dict, List, Optional, Set, Tuple
from collections import defaultdict, Counter
from pathlib import Path
import json
import pickle
from loguru import logger

from config import Config
from models.formatting_models import OCRPage, OCRWord, OCRDocument


class AdaptiveDictionary:
    """
    Adaptive dictionary that learns from processed documents.
    """

    def __init__(self, dictionary_path: Optional[Path] = None):
        """
        Initialize adaptive dictionary.

        Args:
            dictionary_path: Path to save/load dictionary
        """
        self.dictionary_path = dictionary_path or (Config.CACHE_DIR / 'adaptive_dict.pkl')
        self.word_frequencies: Dict[str, int] = defaultdict(int)
        self.domain_vocabulary: Set[str] = set()
        self.correction_history: Dict[str, str] = {}  # error -> correction

        # Load existing dictionary if available
        self.load()

        logger.info(f"Initialized AdaptiveDictionary with {len(self.domain_vocabulary)} words")

    def learn_from_document(self, ocr_document: OCRDocument):
        """
        Learn vocabulary from a high-confidence document.

        Args:
            ocr_document: OCRDocument to learn from
        """
        learned_count = 0

        for page in ocr_document.pages:
            for word in page.get_all_words():
                # Only learn from high-confidence words
                if word.confidence > 90:
                    word_lower = word.text.lower()
                    self.word_frequencies[word_lower] += 1

                    # Add to domain vocabulary if frequent
                    if self.word_frequencies[word_lower] >= 3:
                        if word_lower not in self.domain_vocabulary:
                            self.domain_vocabulary.add(word_lower)
                            learned_count += 1

        logger.info(f"Learned {learned_count} new words from document")

    def suggest_correction(self, word: str) -> Optional[str]:
        """
        Suggest a correction for a word based on learned vocabulary.

        Args:
            word: Word to correct

        Returns:
            Suggested correction or None
        """
        word_lower = word.lower()

        # Check correction history first
        if word_lower in self.correction_history:
            return self.correction_history[word_lower]

        # Find similar words in domain vocabulary
        from difflib import get_close_matches

        matches = get_close_matches(
            word_lower,
            self.domain_vocabulary,
            n=1,
            cutoff=0.85
        )

        if matches:
            return matches[0]

        # Check in frequency dictionary
        matches = get_close_matches(
            word_lower,
            self.word_frequencies.keys(),
            n=1,
            cutoff=0.85
        )

        if matches and self.word_frequencies[matches[0]] >= 2:
            return matches[0]

        return None

    def add_correction(self, error: str, correction: str):
        """
        Record a correction for future reference.

        Args:
            error: Original (incorrect) word
            correction: Corrected word
        """
        self.correction_history[error.lower()] = correction.lower()

    def save(self):
        """Save dictionary to disk."""
        try:
            self.dictionary_path.parent.mkdir(parents=True, exist_ok=True)

            data = {
                'word_frequencies': dict(self.word_frequencies),
                'domain_vocabulary': list(self.domain_vocabulary),
                'correction_history': self.correction_history,
            }

            with open(self.dictionary_path, 'wb') as f:
                pickle.dump(data, f)

            logger.debug(f"Saved adaptive dictionary to {self.dictionary_path}")

        except Exception as e:
            logger.error(f"Failed to save dictionary: {e}")

    def load(self):
        """Load dictionary from disk."""
        try:
            if self.dictionary_path.exists():
                with open(self.dictionary_path, 'rb') as f:
                    data = pickle.load(f)

                self.word_frequencies = defaultdict(int, data.get('word_frequencies', {}))
                self.domain_vocabulary = set(data.get('domain_vocabulary', []))
                self.correction_history = data.get('correction_history', {})

                logger.debug(f"Loaded adaptive dictionary from {self.dictionary_path}")

        except Exception as e:
            logger.warning(f"Failed to load dictionary: {e}")


class NGramCorrector:
    """
    N-gram based text correction.
    """

    def __init__(self, n: int = 3, language: str = 'fr'):
        """
        Initialize n-gram corrector.

        Args:
            n: N-gram size (3 for trigrams)
            language: Language code
        """
        self.n = n
        self.language = language
        self.ngrams: Dict[Tuple[str, ...], int] = defaultdict(int)

        # Load common n-grams for the language if available
        self._load_common_ngrams()

        logger.info(f"Initialized NGramCorrector with n={n}, {len(self.ngrams)} n-grams")

    def _load_common_ngrams(self):
        """Load common n-grams from file if available."""
        ngram_file = Config.CACHE_DIR / f'ngrams_{self.language}_{self.n}.pkl'

        try:
            if ngram_file.exists():
                with open(ngram_file, 'rb') as f:
                    self.ngrams = pickle.load(f)
                logger.debug(f"Loaded {len(self.ngrams)} n-grams from cache")
        except Exception as e:
            logger.debug(f"Could not load n-grams: {e}")

    def learn_from_text(self, text: str):
        """
        Learn n-grams from text.

        Args:
            text: Text to learn from
        """
        words = text.lower().split()

        for i in range(len(words) - self.n + 1):
            ngram = tuple(words[i:i + self.n])
            self.ngrams[ngram] += 1

    def correct_text(self, text: str, min_confidence: float = 0.5) -> str:
        """
        Correct text using n-gram probabilities.

        Args:
            text: Text to correct
            min_confidence: Minimum confidence to apply correction

        Returns:
            Corrected text
        """
        words = text.split()
        corrected = []

        for i, word in enumerate(words):
            # Get context
            if i >= self.n - 1:
                # Check if current n-gram exists
                ngram = tuple(w.lower() for w in words[i - self.n + 1:i + 1])

                if ngram in self.ngrams:
                    # N-gram is known, keep the word
                    corrected.append(word)
                else:
                    # Try to find similar n-gram
                    similar = self._find_similar_ngram(ngram)
                    if similar and self._calculate_similarity(ngram, similar) > min_confidence:
                        # Use the last word from similar n-gram
                        corrected.append(similar[-1])
                    else:
                        corrected.append(word)
            else:
                corrected.append(word)

        return ' '.join(corrected)

    def _find_similar_ngram(self, ngram: Tuple[str, ...]) -> Optional[Tuple[str, ...]]:
        """
        Find the most similar n-gram.

        Args:
            ngram: N-gram to match

        Returns:
            Most similar n-gram or None
        """
        # Compare first n-1 words exactly, vary last word
        prefix = ngram[:-1]

        candidates = [
            ng for ng in self.ngrams.keys()
            if ng[:-1] == prefix
        ]

        if candidates:
            # Return most frequent candidate
            return max(candidates, key=lambda ng: self.ngrams[ng])

        return None

    def _calculate_similarity(self, ngram1: Tuple[str, ...], ngram2: Tuple[str, ...]) -> float:
        """Calculate similarity between two n-grams."""
        if not ngram1 or not ngram2 or len(ngram1) != len(ngram2):
            return 0.0

        matches = sum(1 for w1, w2 in zip(ngram1, ngram2) if w1 == w2)
        return matches / len(ngram1)

    def save(self):
        """Save n-grams to disk."""
        try:
            ngram_file = Config.CACHE_DIR / f'ngrams_{self.language}_{self.n}.pkl'
            ngram_file.parent.mkdir(parents=True, exist_ok=True)

            with open(ngram_file, 'wb') as f:
                pickle.dump(dict(self.ngrams), f)

            logger.debug(f"Saved {len(self.ngrams)} n-grams")

        except Exception as e:
            logger.error(f"Failed to save n-grams: {e}")


class ContextualCorrector:
    """
    Contextual correction using transformers (optional, requires additional libraries).
    """

    def __init__(self, language: str = 'fr', model_name: Optional[str] = None):
        """
        Initialize contextual corrector.

        Args:
            language: Language code
            model_name: Transformer model name (None for default)
        """
        self.language = language
        self.model_name = model_name
        self.pipeline = None

        # Try to initialize transformer pipeline
        try:
            from transformers import pipeline
            import torch

            if model_name is None:
                # Use default models per language
                models = {
                    'fr': 'camembert-base',
                    'en': 'bert-base-uncased',
                }
                model_name = models.get(language, 'bert-base-multilingual-cased')

            self.pipeline = pipeline(
                'fill-mask',
                model=model_name,
                device=0 if torch.cuda.is_available() else -1
            )

            logger.info(f"Initialized ContextualCorrector with {model_name}")

        except ImportError:
            logger.warning(
                "transformers library not available. "
                "Install with: pip install transformers torch"
            )
        except Exception as e:
            logger.warning(f"Could not initialize contextual corrector: {e}")

    def correct_word(
        self,
        word: str,
        context_before: str,
        context_after: str,
        threshold: float = 0.7
    ) -> Optional[str]:
        """
        Correct a word using context.

        Args:
            word: Word to potentially correct
            context_before: Text before the word
            context_after: Text after the word
            threshold: Confidence threshold

        Returns:
            Corrected word or None if no correction needed
        """
        if self.pipeline is None:
            return None

        try:
            # Create masked text
            masked_text = f"{context_before} [MASK] {context_after}"

            # Get predictions
            predictions = self.pipeline(masked_text, top_k=5)

            # Check if any prediction is different from original and has high confidence
            for pred in predictions:
                if pred['score'] > threshold and pred['token_str'].lower() != word.lower():
                    logger.debug(
                        f"Contextual correction: '{word}' -> '{pred['token_str']}' "
                        f"(confidence: {pred['score']:.2f})"
                    )
                    return pred['token_str']

        except Exception as e:
            logger.debug(f"Contextual correction failed: {e}")

        return None


class SmartCorrector:
    """
    Advanced text corrector combining multiple techniques.
    """

    def __init__(
        self,
        language: str = 'fr',
        use_adaptive_dict: bool = True,
        use_ngrams: bool = True,
        use_contextual: bool = False,  # Disabled by default (requires transformers)
    ):
        """
        Initialize smart corrector.

        Args:
            language: Language code
            use_adaptive_dict: Use adaptive dictionary
            use_ngrams: Use n-gram correction
            use_contextual: Use contextual correction (requires transformers)
        """
        self.language = language

        # Initialize components
        self.adaptive_dict = AdaptiveDictionary() if use_adaptive_dict else None
        self.ngram_corrector = NGramCorrector(n=3, language=language) if use_ngrams else None
        self.contextual_corrector = ContextualCorrector(language=language) if use_contextual else None

        self.stats = {
            'corrections': 0,
            'adaptive_dict': 0,
            'ngram': 0,
            'contextual': 0,
        }

        logger.info(
            f"Initialized SmartCorrector (language={language}, "
            f"adaptive_dict={use_adaptive_dict}, ngrams={use_ngrams}, "
            f"contextual={use_contextual})"
        )

    def correct_page(self, ocr_page: OCRPage) -> OCRPage:
        """
        Apply smart corrections to a page.

        Args:
            ocr_page: OCRPage to correct

        Returns:
            Corrected OCRPage
        """
        for paragraph in ocr_page.paragraphs:
            for line in paragraph.lines:
                for word_idx, word in enumerate(line.words):
                    if word.is_low_confidence:
                        # Try corrections in order of sophistication
                        correction = self._correct_word(word, line.words, word_idx)

                        if correction and correction != word.text:
                            original = word.text
                            word.text = correction
                            self.stats['corrections'] += 1
                            logger.debug(f"Corrected: '{original}' -> '{correction}'")

        return ocr_page

    def _correct_word(
        self,
        word: OCRWord,
        line_words: List[OCRWord],
        word_idx: int
    ) -> Optional[str]:
        """
        Try to correct a single word using available methods.

        Args:
            word: Word to correct
            line_words: All words in the line
            word_idx: Index of word in line

        Returns:
            Corrected word or original if no correction found
        """
        original = word.text

        # 1. Try adaptive dictionary
        if self.adaptive_dict:
            suggestion = self.adaptive_dict.suggest_correction(original)
            if suggestion:
                self.stats['adaptive_dict'] += 1
                return suggestion

        # 2. Try contextual correction (if enabled and available)
        if self.contextual_corrector:
            context_before = ' '.join(w.text for w in line_words[:word_idx])
            context_after = ' '.join(w.text for w in line_words[word_idx + 1:])

            correction = self.contextual_corrector.correct_word(
                original,
                context_before,
                context_after
            )

            if correction:
                self.stats['contextual'] += 1
                return correction

        return original

    def learn_from_document(self, ocr_document: OCRDocument):
        """
        Learn from a document for future corrections.

        Args:
            ocr_document: Document to learn from
        """
        if self.adaptive_dict:
            self.adaptive_dict.learn_from_document(ocr_document)

        if self.ngram_corrector:
            # Learn n-grams from document text
            text = ocr_document.text
            self.ngram_corrector.learn_from_text(text)

        logger.info("Learned from document")

    def save_models(self):
        """Save learned models to disk."""
        if self.adaptive_dict:
            self.adaptive_dict.save()

        if self.ngram_corrector:
            self.ngram_corrector.save()

        logger.info("Saved correction models")

    def get_stats(self) -> Dict[str, int]:
        """Get correction statistics."""
        return self.stats.copy()


def create_smart_corrector(
    language: str = 'fr',
    enable_all: bool = False,
) -> SmartCorrector:
    """
    Factory function to create a smart corrector.

    Args:
        language: Language code
        enable_all: Enable all features including contextual (requires transformers)

    Returns:
        SmartCorrector instance
    """
    return SmartCorrector(
        language=language,
        use_adaptive_dict=True,
        use_ngrams=True,
        use_contextual=enable_all,
    )
