"""
Configuration module for OCR PDF to DOCX converter.

This module contains all configuration settings and constants used throughout
the application.
"""

import os
from pathlib import Path
from typing import Dict, List, Optional


class Config:
    """Main configuration class containing all application settings."""

    # ========================================================================
    # PROJECT PATHS
    # ========================================================================
    PROJECT_ROOT = Path(__file__).parent.absolute()
    CACHE_DIR = PROJECT_ROOT / '.cache'
    OUTPUT_DIR = PROJECT_ROOT / 'output'
    TEMP_DIR = PROJECT_ROOT / 'temp'
    LOGS_DIR = PROJECT_ROOT / 'logs'

    # ========================================================================
    # OCR SETTINGS
    # ========================================================================

    # Tesseract configuration
    TESSERACT_CMD: Optional[str] = None  # Auto-detect if None
    TESSERACT_CONFIG = '--psm 1 --oem 3'  # Page segmentation mode 1, OCR Engine Mode 3

    # OCR Languages (ISO 639-2 codes)
    OCR_LANGUAGES = ['fra', 'eng']  # French and English by default
    DEFAULT_LANGUAGE = 'fra'

    # Confidence thresholds
    MIN_CONFIDENCE = 60  # Minimum confidence score (0-100)
    LOW_CONFIDENCE_THRESHOLD = 75  # Words below this will be flagged for correction

    # OCR Engine selection
    AVAILABLE_ENGINES = ['tesseract', 'easyocr', 'both']
    DEFAULT_OCR_ENGINE = 'tesseract'

    # Page Segmentation Modes (PSM)
    PSM_MODES = {
        'auto': 1,          # Automatic page segmentation with OSD
        'single_column': 4,  # Single column of text
        'single_block': 6,   # Single uniform block of text
        'single_line': 7,    # Single text line
        'single_word': 8,    # Single word
        'sparse': 11,        # Sparse text without specific order
    }

    # ========================================================================
    # IMAGE PROCESSING SETTINGS
    # ========================================================================

    # DPI settings
    DPI_DEFAULT = 600
    DPI_MIN = 150
    DPI_MAX = 1200
    DPI_OPTIONS = [300, 600, 900, 1200]

    # Image preprocessing
    DESKEW_ENABLED = True
    DENOISE_ENABLED = True
    CONTRAST_ENHANCEMENT = True
    BINARIZATION_ENABLED = True

    # Image enhancement parameters
    GAUSSIAN_BLUR_KERNEL = (3, 3)
    BILATERAL_FILTER_D = 9
    BILATERAL_FILTER_SIGMA_COLOR = 75
    BILATERAL_FILTER_SIGMA_SPACE = 75

    # Contrast settings
    CLAHE_CLIP_LIMIT = 2.0
    CLAHE_TILE_GRID_SIZE = (8, 8)

    # Binarization
    ADAPTIVE_THRESH_BLOCK_SIZE = 11
    ADAPTIVE_THRESH_C = 2

    # ========================================================================
    # FONT DETECTION SETTINGS
    # ========================================================================

    FONT_DETECTION_ENABLED = True

    # Font family mapping (fallback mapping for detected features)
    FONT_MAPPING = {
        'serif': 'Times New Roman',
        'sans-serif': 'Arial',
        'monospace': 'Courier New',
        'cursive': 'Comic Sans MS',
        'fantasy': 'Impact',
    }

    # Common font families by characteristics
    SERIF_FONTS = [
        'Times New Roman', 'Georgia', 'Garamond',
        'Palatino', 'Book Antiqua', 'Cambria'
    ]

    SANS_SERIF_FONTS = [
        'Arial', 'Helvetica', 'Calibri', 'Verdana',
        'Tahoma', 'Trebuchet MS', 'Geneva'
    ]

    MONOSPACE_FONTS = [
        'Courier New', 'Consolas', 'Monaco',
        'Lucida Console', 'DejaVu Sans Mono'
    ]

    # Font size range (in points)
    FONT_SIZE_MIN = 6
    FONT_SIZE_MAX = 72
    FONT_SIZE_DEFAULT = 12

    # ========================================================================
    # FORMATTING DETECTION THRESHOLDS
    # ========================================================================

    # Bold detection
    BOLD_THRESHOLD = 0.25  # Ratio of black pixels to total pixels
    BOLD_STROKE_WIDTH_RATIO = 1.3  # Bold is typically 1.3x normal stroke width

    # Italic detection
    ITALIC_ANGLE_THRESHOLD = 5  # Minimum angle in degrees to be considered italic
    ITALIC_ANGLE_RANGE = (8, 20)  # Typical italic angle range

    # Underline detection
    UNDERLINE_LINE_THICKNESS_RATIO = 0.05  # Relative to character height
    UNDERLINE_POSITION_RATIO = 0.9  # Position below baseline

    # Small caps detection
    SMALL_CAPS_HEIGHT_RATIO = 0.75  # Small caps are typically 75% of capital height
    SMALL_CAPS_MIN_CHARS = 3  # Minimum characters to be considered small caps

    # ========================================================================
    # ALIGNMENT DETECTION
    # ========================================================================

    # Tolerance for alignment detection (as fraction of page width)
    LEFT_ALIGN_TOLERANCE = 0.05
    RIGHT_ALIGN_TOLERANCE = 0.05
    CENTER_TOLERANCE = 0.15

    # Justified text detection
    JUSTIFIED_MIN_VARIANCE = 0.02  # Maximum variance in line endings for justified text
    JUSTIFIED_MIN_LINES = 3  # Minimum lines needed to detect justified text

    # ========================================================================
    # SPACING SETTINGS
    # ========================================================================

    # Line spacing multipliers
    SINGLE_SPACING = 1.0
    SPACING_1_5 = 1.5
    DOUBLE_SPACING = 2.0

    # Spacing detection tolerance
    LINE_SPACING_TOLERANCE = 0.2  # 20% tolerance for spacing detection

    # Paragraph spacing (in points)
    PARAGRAPH_SPACING_MIN = 0
    PARAGRAPH_SPACING_MAX = 72
    PARAGRAPH_SPACING_DEFAULT = 6

    # Indentation (in points)
    INDENT_DEFAULT = 36  # 0.5 inch
    INDENT_MIN = 0
    INDENT_MAX = 144  # 2 inches

    # ========================================================================
    # TEXT CORRECTION SETTINGS
    # ========================================================================

    SPELL_CHECK_ENABLED = True
    CONTEXT_CORRECTION_ENABLED = True
    MIN_WORD_LENGTH_CORRECTION = 3

    # Common OCR character confusions
    OCR_CHAR_REPLACEMENTS = {
        'l': ['1', 'I', '|'],
        '1': ['l', 'I', '|'],
        'I': ['l', '1', '|'],
        'O': ['0', 'Q'],
        '0': ['O', 'Q'],
        'S': ['5'],
        '5': ['S'],
        'B': ['8'],
        '8': ['B'],
    }

    # Dictionary settings
    USE_CUSTOM_DICTIONARY = True
    CUSTOM_DICTIONARY_PATH = PROJECT_ROOT / 'data' / 'custom_dictionary.txt'

    # Hyphenation handling
    FIX_HYPHENATION = True
    HYPHEN_CHARS = ['-', '‐', '‑', '‒', '–', '—']  # Various hyphen characters

    # ========================================================================
    # PERFORMANCE SETTINGS
    # ========================================================================

    # Parallel processing
    PARALLEL_PROCESSING = True
    MAX_WORKERS: Optional[int] = None  # None = auto-detect (cpu_count)
    CHUNK_SIZE = 1  # Pages per worker

    # Caching
    CACHE_ENABLED = True
    CACHE_OCR_RESULTS = True
    CACHE_PREPROCESSED_IMAGES = True
    CACHE_MAX_SIZE_MB = 1000  # Maximum cache size in MB

    # Memory management
    MAX_IMAGE_SIZE_MB = 100  # Maximum size for a single image
    CLEANUP_TEMP_FILES = True

    # ========================================================================
    # DOCX OUTPUT SETTINGS
    # ========================================================================

    # Document optimization
    DOCX_OPTIMIZATION = True
    CREATE_STYLES = True
    MERGE_SIMILAR_STYLES = True
    STYLE_SIMILARITY_THRESHOLD = 0.95

    # Page formatting
    PRESERVE_PAGE_BREAKS = False  # If True, each PDF page becomes a Word page
    ADD_PAGE_NUMBERS = False

    # Margins (in inches)
    MARGIN_TOP = 1.0
    MARGIN_BOTTOM = 1.0
    MARGIN_LEFT = 1.0
    MARGIN_RIGHT = 1.0

    # Paper size
    PAPER_SIZE = 'A4'  # Options: 'A4', 'Letter', 'Legal'
    PAPER_SIZES = {
        'A4': (210, 297),  # mm
        'Letter': (215.9, 279.4),  # mm
        'Legal': (215.9, 355.6),  # mm
    }

    # ========================================================================
    # LOGGING SETTINGS
    # ========================================================================

    LOG_LEVEL = 'INFO'  # Options: DEBUG, INFO, WARNING, ERROR, CRITICAL
    LOG_FORMAT = '<green>{time:YYYY-MM-DD HH:mm:ss}</green> | <level>{level: <8}</level> | <cyan>{name}</cyan>:<cyan>{function}</cyan>:<cyan>{line}</cyan> - <level>{message}</level>'
    LOG_TO_FILE = True
    LOG_ROTATION = '10 MB'
    LOG_RETENTION = '1 week'

    # ========================================================================
    # ADVANCED ENHANCEMENT SETTINGS
    # ========================================================================

    # Image Enhancement
    USE_ADVANCED_BINARIZATION = True  # Use Sauvola/Niblack instead of simple Otsu
    USE_PERSPECTIVE_CORRECTION = True  # Auto-detect and correct perspective
    USE_SHADOW_REMOVAL = True  # Remove shadows and uneven illumination
    BINARIZATION_METHOD = 'auto'  # Options: 'auto', 'sauvola', 'niblack', 'otsu'

    # Multi-pass OCR
    USE_MULTI_RESOLUTION = False  # Test multiple DPIs (slower but more accurate)
    MULTI_RESOLUTION_DPIS = [300, 600, 900]  # DPIs to test
    USE_MULTI_ANGLE = False  # Test multiple rotations (slower but handles rotated docs)
    TEST_ANGLES = [0, 90, 180, 270, -5, 5]  # Angles to test in degrees

    # Ensemble OCR
    USE_ENSEMBLE_OCR = False  # Use multiple OCR engines (requires EasyOCR)
    ENSEMBLE_ENGINES = ['tesseract', 'easyocr']  # Engines to combine
    ENSEMBLE_STRATEGY = 'confidence'  # Options: 'voting', 'confidence', 'best'

    # Smart Correction
    USE_SMART_CORRECTION = True  # Use advanced text correction
    USE_ADAPTIVE_DICTIONARY = True  # Learn vocabulary from documents
    USE_NGRAM_CORRECTION = True  # Use n-gram based correction
    USE_CONTEXTUAL_CORRECTION = False  # Use transformer models (requires transformers)
    NGRAM_SIZE = 3  # Size of n-grams (3 = trigrams)

    # Document Analysis
    AUTO_DETECT_DOCUMENT_TYPE = True  # Detect and optimize for document type
    USE_TABLE_EXTRACTION = False  # Extract table structures (experimental)
    OPTIMIZE_FOR_DOCUMENT_TYPE = True  # Apply type-specific optimizations

    # ========================================================================
    # FEATURE FLAGS
    # ========================================================================

    # Advanced features
    DETECT_TABLES = False  # Table detection (experimental)
    DETECT_IMAGES = False  # Image extraction (experimental)
    DETECT_HEADERS_FOOTERS = False  # Header/footer detection (experimental)
    MULTI_COLUMN_SUPPORT = False  # Multi-column layout (experimental)

    # Quality vs Speed trade-offs
    QUALITY_MODE = 'balanced'  # Options: 'fast', 'balanced', 'quality'

    QUALITY_PRESETS = {
        'fast': {
            'dpi': 300,
            'ocr_engine': 'tesseract',
            'preprocessing': False,
            'text_correction': False,
            'font_detection': False,
            'advanced_binarization': False,
            'multi_resolution': False,
            'multi_angle': False,
            'ensemble_ocr': False,
            'smart_correction': False,
        },
        'balanced': {
            'dpi': 600,
            'ocr_engine': 'tesseract',
            'preprocessing': True,
            'text_correction': True,
            'font_detection': True,
            'advanced_binarization': True,
            'multi_resolution': False,
            'multi_angle': False,
            'ensemble_ocr': False,
            'smart_correction': True,
        },
        'quality': {
            'dpi': 1200,
            'ocr_engine': 'both',
            'preprocessing': True,
            'text_correction': True,
            'font_detection': True,
            'advanced_binarization': True,
            'multi_resolution': True,
            'multi_angle': False,
            'ensemble_ocr': True,
            'smart_correction': True,
        },
        'ultra': {
            'dpi': 1200,
            'ocr_engine': 'both',
            'preprocessing': True,
            'text_correction': True,
            'font_detection': True,
            'advanced_binarization': True,
            'multi_resolution': True,
            'multi_angle': True,
            'ensemble_ocr': True,
            'smart_correction': True,
        },
    }

    @classmethod
    def create_directories(cls) -> None:
        """Create necessary directories if they don't exist."""
        for directory in [cls.CACHE_DIR, cls.OUTPUT_DIR, cls.TEMP_DIR, cls.LOGS_DIR]:
            directory.mkdir(parents=True, exist_ok=True)

    @classmethod
    def get_tesseract_path(cls) -> Optional[str]:
        """Get Tesseract executable path based on platform."""
        if cls.TESSERACT_CMD:
            return cls.TESSERACT_CMD

        # Try to find Tesseract in common locations
        import platform
        system = platform.system()

        if system == 'Windows':
            common_paths = [
                r'C:\Program Files\Tesseract-OCR\tesseract.exe',
                r'C:\Program Files (x86)\Tesseract-OCR\tesseract.exe',
            ]
        elif system == 'Darwin':  # macOS
            common_paths = [
                '/usr/local/bin/tesseract',
                '/opt/homebrew/bin/tesseract',
            ]
        else:  # Linux and others
            common_paths = [
                '/usr/bin/tesseract',
                '/usr/local/bin/tesseract',
            ]

        for path in common_paths:
            if Path(path).exists():
                return path

        return None  # Will use system PATH

    @classmethod
    def apply_quality_preset(cls, preset: str) -> None:
        """Apply a quality preset configuration."""
        if preset not in cls.QUALITY_PRESETS:
            raise ValueError(f"Invalid preset: {preset}. Choose from {list(cls.QUALITY_PRESETS.keys())}")

        settings = cls.QUALITY_PRESETS[preset]
        cls.DPI_DEFAULT = settings['dpi']
        cls.DEFAULT_OCR_ENGINE = settings['ocr_engine']
        cls.DESKEW_ENABLED = settings['preprocessing']
        cls.DENOISE_ENABLED = settings['preprocessing']
        cls.CONTRAST_ENHANCEMENT = settings['preprocessing']
        cls.SPELL_CHECK_ENABLED = settings['text_correction']
        cls.FONT_DETECTION_ENABLED = settings['font_detection']


# Initialize directories on module import
Config.create_directories()
