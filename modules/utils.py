"""
Utility functions for the OCR PDF to DOCX converter.

This module contains various helper functions used throughout the application.
"""

import os
import hashlib
import json
import pickle
from pathlib import Path
from typing import List, Tuple, Optional, Any, Union
import numpy as np
from PIL import Image
import cv2
from loguru import logger

from config import Config


def setup_logging(verbose: int = 0) -> None:
    """
    Setup logging configuration.

    Args:
        verbose: Verbosity level (0=INFO, 1=DEBUG, 2+=TRACE)
    """
    logger.remove()  # Remove default handler

    # Determine log level based on verbosity
    if verbose == 0:
        log_level = Config.LOG_LEVEL
    elif verbose == 1:
        log_level = "DEBUG"
    else:
        log_level = "TRACE"

    # Console logging
    logger.add(
        sink=lambda msg: print(msg, end=''),
        format=Config.LOG_FORMAT,
        level=log_level,
        colorize=True,
    )

    # File logging
    if Config.LOG_TO_FILE:
        log_file = Config.LOGS_DIR / "ocr_converter.log"
        logger.add(
            sink=log_file,
            format=Config.LOG_FORMAT,
            level=log_level,
            rotation=Config.LOG_ROTATION,
            retention=Config.LOG_RETENTION,
        )


def parse_page_range(page_range: str, total_pages: int) -> List[int]:
    """
    Parse page range string into list of page numbers.

    Args:
        page_range: Page range string (e.g., "1-5,7,10-12" or "all")
        total_pages: Total number of pages in the document

    Returns:
        List of page numbers (0-indexed)

    Examples:
        >>> parse_page_range("1-3,5", 10)
        [0, 1, 2, 4]
        >>> parse_page_range("all", 5)
        [0, 1, 2, 3, 4]
    """
    if page_range.lower() == 'all':
        return list(range(total_pages))

    pages = set()

    for part in page_range.split(','):
        part = part.strip()

        if '-' in part:
            # Range of pages
            start, end = part.split('-')
            start = int(start.strip()) - 1  # Convert to 0-indexed
            end = int(end.strip()) - 1
            pages.update(range(start, end + 1))
        else:
            # Single page
            pages.add(int(part.strip()) - 1)

    # Filter out invalid pages
    valid_pages = [p for p in sorted(pages) if 0 <= p < total_pages]

    if not valid_pages:
        logger.warning(f"No valid pages found in range '{page_range}'")

    return valid_pages


def calculate_file_hash(file_path: Path) -> str:
    """
    Calculate SHA256 hash of a file.

    Args:
        file_path: Path to the file

    Returns:
        Hex string of the hash
    """
    sha256_hash = hashlib.sha256()

    with open(file_path, "rb") as f:
        # Read in chunks to handle large files
        for byte_block in iter(lambda: f.read(4096), b""):
            sha256_hash.update(byte_block)

    return sha256_hash.hexdigest()


def get_cache_path(cache_key: str, cache_type: str = 'ocr') -> Path:
    """
    Get cache file path for a given key.

    Args:
        cache_key: Unique identifier for the cached item
        cache_type: Type of cache (ocr, image, etc.)

    Returns:
        Path to cache file
    """
    cache_dir = Config.CACHE_DIR / cache_type
    cache_dir.mkdir(parents=True, exist_ok=True)
    return cache_dir / f"{cache_key}.pkl"


def save_to_cache(data: Any, cache_key: str, cache_type: str = 'ocr') -> bool:
    """
    Save data to cache.

    Args:
        data: Data to cache
        cache_key: Unique identifier
        cache_type: Type of cache

    Returns:
        True if successful
    """
    if not Config.CACHE_ENABLED:
        return False

    try:
        cache_path = get_cache_path(cache_key, cache_type)
        with open(cache_path, 'wb') as f:
            pickle.dump(data, f)
        logger.debug(f"Saved to cache: {cache_path}")
        return True
    except Exception as e:
        logger.error(f"Failed to save to cache: {e}")
        return False


def load_from_cache(cache_key: str, cache_type: str = 'ocr') -> Optional[Any]:
    """
    Load data from cache.

    Args:
        cache_key: Unique identifier
        cache_type: Type of cache

    Returns:
        Cached data or None if not found
    """
    if not Config.CACHE_ENABLED:
        return None

    try:
        cache_path = get_cache_path(cache_key, cache_type)
        if cache_path.exists():
            with open(cache_path, 'rb') as f:
                data = pickle.load(f)
            logger.debug(f"Loaded from cache: {cache_path}")
            return data
    except Exception as e:
        logger.error(f"Failed to load from cache: {e}")

    return None


def clear_cache(cache_type: Optional[str] = None) -> None:
    """
    Clear cache files.

    Args:
        cache_type: Type of cache to clear, or None for all
    """
    if cache_type:
        cache_dir = Config.CACHE_DIR / cache_type
        if cache_dir.exists():
            for file in cache_dir.glob('*.pkl'):
                file.unlink()
            logger.info(f"Cleared {cache_type} cache")
    else:
        # Clear all caches
        for cache_dir in Config.CACHE_DIR.glob('*'):
            if cache_dir.is_dir():
                for file in cache_dir.glob('*.pkl'):
                    file.unlink()
        logger.info("Cleared all caches")


def pil_to_cv2(pil_image: Image.Image) -> np.ndarray:
    """
    Convert PIL Image to OpenCV format.

    Args:
        pil_image: PIL Image

    Returns:
        OpenCV image (BGR)
    """
    # Convert PIL Image to numpy array
    numpy_image = np.array(pil_image)

    # Convert RGB to BGR if needed
    if len(numpy_image.shape) == 3 and numpy_image.shape[2] == 3:
        opencv_image = cv2.cvtColor(numpy_image, cv2.COLOR_RGB2BGR)
    else:
        opencv_image = numpy_image

    return opencv_image


def cv2_to_pil(cv2_image: np.ndarray) -> Image.Image:
    """
    Convert OpenCV image to PIL Image.

    Args:
        cv2_image: OpenCV image (BGR)

    Returns:
        PIL Image
    """
    # Convert BGR to RGB if needed
    if len(cv2_image.shape) == 3 and cv2_image.shape[2] == 3:
        rgb_image = cv2.cvtColor(cv2_image, cv2.COLOR_BGR2RGB)
    else:
        rgb_image = cv2_image

    return Image.fromarray(rgb_image)


def detect_skew_angle(image: np.ndarray) -> float:
    """
    Detect skew angle of text in image using Hough transform.

    Args:
        image: OpenCV image (grayscale or BGR)

    Returns:
        Skew angle in degrees
    """
    # Convert to grayscale if needed
    if len(image.shape) == 3:
        gray = cv2.cvtColor(image, cv2.COLOR_BGR2GRAY)
    else:
        gray = image.copy()

    # Apply edge detection
    edges = cv2.Canny(gray, 50, 150, apertureSize=3)

    # Detect lines using Hough transform
    lines = cv2.HoughLinesP(
        edges,
        rho=1,
        theta=np.pi / 180,
        threshold=100,
        minLineLength=100,
        maxLineGap=10
    )

    if lines is None:
        return 0.0

    # Calculate angles of all lines
    angles = []
    for line in lines:
        x1, y1, x2, y2 = line[0]
        angle = np.degrees(np.arctan2(y2 - y1, x2 - x1))
        angles.append(angle)

    # Filter angles to those close to horizontal
    horizontal_angles = [a for a in angles if -45 <= a <= 45]

    if not horizontal_angles:
        return 0.0

    # Calculate median angle
    median_angle = np.median(horizontal_angles)

    return median_angle


def deskew_image(image: np.ndarray, angle: Optional[float] = None) -> np.ndarray:
    """
    Deskew (rotate) an image to correct tilt.

    Args:
        image: OpenCV image
        angle: Rotation angle (if None, auto-detect)

    Returns:
        Deskewed image
    """
    if angle is None:
        angle = detect_skew_angle(image)

    if abs(angle) < 0.5:  # Skip if angle is too small
        return image

    # Get image center
    (h, w) = image.shape[:2]
    center = (w // 2, h // 2)

    # Get rotation matrix
    M = cv2.getRotationMatrix2D(center, angle, 1.0)

    # Perform rotation
    rotated = cv2.warpAffine(
        image,
        M,
        (w, h),
        flags=cv2.INTER_CUBIC,
        borderMode=cv2.BORDER_REPLICATE
    )

    logger.debug(f"Deskewed image by {angle:.2f} degrees")

    return rotated


def enhance_image(image: np.ndarray) -> np.ndarray:
    """
    Enhance image for better OCR results.

    Args:
        image: OpenCV image

    Returns:
        Enhanced image
    """
    # Convert to grayscale if needed
    if len(image.shape) == 3:
        gray = cv2.cvtColor(image, cv2.COLOR_BGR2GRAY)
    else:
        gray = image.copy()

    enhanced = gray

    # Denoise
    if Config.DENOISE_ENABLED:
        enhanced = cv2.fastNlMeansDenoising(enhanced, None, 10, 7, 21)
        logger.debug("Applied denoising")

    # Contrast enhancement with CLAHE
    if Config.CONTRAST_ENHANCEMENT:
        clahe = cv2.createCLAHE(
            clipLimit=Config.CLAHE_CLIP_LIMIT,
            tileGridSize=Config.CLAHE_TILE_GRID_SIZE
        )
        enhanced = clahe.apply(enhanced)
        logger.debug("Applied CLAHE contrast enhancement")

    # Binarization
    if Config.BINARIZATION_ENABLED:
        enhanced = cv2.adaptiveThreshold(
            enhanced,
            255,
            cv2.ADAPTIVE_THRESH_GAUSSIAN_C,
            cv2.THRESH_BINARY,
            Config.ADAPTIVE_THRESH_BLOCK_SIZE,
            Config.ADAPTIVE_THRESH_C
        )
        logger.debug("Applied adaptive thresholding")

    return enhanced


def calculate_line_height(line_boxes: List[Tuple[int, int, int, int]]) -> float:
    """
    Calculate average line height from a list of line bounding boxes.

    Args:
        line_boxes: List of (x, y, width, height) tuples

    Returns:
        Average line height
    """
    if not line_boxes:
        return 0.0

    heights = [box[3] for box in line_boxes]
    return np.mean(heights)


def pixels_to_points(pixels: float, dpi: int = 72) -> float:
    """
    Convert pixels to typographic points.

    Args:
        pixels: Number of pixels
        dpi: DPI of the image

    Returns:
        Size in points
    """
    return (pixels * 72) / dpi


def points_to_pixels(points: float, dpi: int = 72) -> float:
    """
    Convert typographic points to pixels.

    Args:
        points: Size in points
        dpi: DPI of the image

    Returns:
        Number of pixels
    """
    return (points * dpi) / 72


def ensure_directory(path: Union[str, Path]) -> Path:
    """
    Ensure a directory exists, create if it doesn't.

    Args:
        path: Directory path

    Returns:
        Path object
    """
    path = Path(path)
    path.mkdir(parents=True, exist_ok=True)
    return path


def get_output_path(input_path: Path, output_path: Optional[Path] = None) -> Path:
    """
    Determine output file path.

    Args:
        input_path: Input PDF path
        output_path: Optional output path

    Returns:
        Output path for DOCX file
    """
    if output_path:
        return Path(output_path)

    # Generate output path from input path
    output_name = input_path.stem + '.docx'
    return Config.OUTPUT_DIR / output_name


def format_time(seconds: float) -> str:
    """
    Format time duration in human-readable format.

    Args:
        seconds: Duration in seconds

    Returns:
        Formatted time string
    """
    if seconds < 60:
        return f"{seconds:.2f}s"
    elif seconds < 3600:
        minutes = int(seconds // 60)
        secs = seconds % 60
        return f"{minutes}m {secs:.1f}s"
    else:
        hours = int(seconds // 3600)
        minutes = int((seconds % 3600) // 60)
        secs = seconds % 60
        return f"{hours}h {minutes}m {secs:.0f}s"


def validate_pdf_path(pdf_path: Union[str, Path]) -> Path:
    """
    Validate that a PDF file exists and is readable.

    Args:
        pdf_path: Path to PDF file

    Returns:
        Validated Path object

    Raises:
        FileNotFoundError: If file doesn't exist
        ValueError: If file is not a PDF
    """
    path = Path(pdf_path)

    if not path.exists():
        raise FileNotFoundError(f"PDF file not found: {path}")

    if not path.is_file():
        raise ValueError(f"Path is not a file: {path}")

    if path.suffix.lower() != '.pdf':
        raise ValueError(f"File is not a PDF: {path}")

    return path


def get_available_workers() -> int:
    """
    Get the number of workers to use for parallel processing.

    Returns:
        Number of workers
    """
    if not Config.PARALLEL_PROCESSING:
        return 1

    if Config.MAX_WORKERS:
        return Config.MAX_WORKERS

    # Auto-detect
    import multiprocessing
    return max(1, multiprocessing.cpu_count() - 1)


def chunk_list(items: List[Any], chunk_size: int) -> List[List[Any]]:
    """
    Split a list into chunks.

    Args:
        items: List to chunk
        chunk_size: Size of each chunk

    Returns:
        List of chunks
    """
    return [items[i:i + chunk_size] for i in range(0, len(items), chunk_size)]
