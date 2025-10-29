"""
Advanced image enhancement module for improved OCR accuracy.

This module provides sophisticated image preprocessing techniques including:
- Advanced binarization (Sauvola, Niblack, Multi-method)
- Perspective correction
- Advanced denoising
- Shadow removal
- Background normalization
"""

from typing import Optional, Tuple, List
import numpy as np
from PIL import Image
import cv2
from loguru import logger

from config import Config
from modules.utils import pil_to_cv2, cv2_to_pil


class ImageEnhancer:
    """
    Advanced image enhancement for OCR preprocessing.
    """

    def __init__(self, method: str = 'auto'):
        """
        Initialize image enhancer.

        Args:
            method: Enhancement method ('auto', 'aggressive', 'gentle')
        """
        self.method = method
        logger.info(f"Initialized ImageEnhancer with method={method}")

    def enhance(self, image: Image.Image) -> Image.Image:
        """
        Apply full enhancement pipeline.

        Args:
            image: PIL Image to enhance

        Returns:
            Enhanced PIL Image
        """
        cv_image = pil_to_cv2(image)

        # Step 1: Perspective correction
        cv_image = self.correct_perspective(cv_image)

        # Step 2: Advanced denoising
        cv_image = self.advanced_denoise(cv_image)

        # Step 3: Shadow removal
        cv_image = self.remove_shadows(cv_image)

        # Step 4: Background normalization
        cv_image = self.normalize_background(cv_image)

        # Step 5: Advanced binarization
        cv_image = self.advanced_binarization(cv_image)

        return cv2_to_pil(cv_image)

    def advanced_binarization(self, image: np.ndarray) -> np.ndarray:
        """
        Advanced binarization with multiple methods.

        Args:
            image: OpenCV image (grayscale or color)

        Returns:
            Binarized image
        """
        # Convert to grayscale if needed
        if len(image.shape) == 3:
            gray = cv2.cvtColor(image, cv2.COLOR_BGR2GRAY)
        else:
            gray = image.copy()

        # Try multiple binarization methods
        methods = {}

        # Method 1: Otsu
        try:
            _, otsu = cv2.threshold(gray, 0, 255, cv2.THRESH_BINARY + cv2.THRESH_OTSU)
            methods['otsu'] = otsu
        except Exception as e:
            logger.debug(f"Otsu failed: {e}")

        # Method 2: Adaptive Gaussian
        try:
            adaptive = cv2.adaptiveThreshold(
                gray, 255, cv2.ADAPTIVE_THRESH_GAUSSIAN_C,
                cv2.THRESH_BINARY, 11, 2
            )
            methods['adaptive'] = adaptive
        except Exception as e:
            logger.debug(f"Adaptive failed: {e}")

        # Method 3: Sauvola (better for ancient documents)
        try:
            sauvola = self.sauvola_threshold(gray, window_size=25, k=0.2)
            methods['sauvola'] = sauvola
        except Exception as e:
            logger.debug(f"Sauvola failed: {e}")

        # Method 4: Niblack
        try:
            niblack = self.niblack_threshold(gray, window_size=25, k=0.2)
            methods['niblack'] = niblack
        except Exception as e:
            logger.debug(f"Niblack failed: {e}")

        # Select best method based on image characteristics
        best_method = self.select_best_binarization(gray, methods)

        logger.debug(f"Selected binarization method: {best_method}")
        return methods.get(best_method, methods.get('otsu', gray))

    def sauvola_threshold(
        self,
        image: np.ndarray,
        window_size: int = 25,
        k: float = 0.2,
        r: float = 128
    ) -> np.ndarray:
        """
        Sauvola local thresholding method.

        Args:
            image: Grayscale image
            window_size: Window size for local calculation
            k: Parameter controlling threshold
            r: Dynamic range of standard deviation

        Returns:
            Binarized image
        """
        # Calculate local mean
        mean = cv2.boxFilter(image, -1, (window_size, window_size))

        # Calculate local standard deviation
        sqr_mean = cv2.boxFilter(image ** 2, -1, (window_size, window_size))
        variance = sqr_mean - mean ** 2
        stddev = np.sqrt(np.maximum(variance, 0))

        # Sauvola threshold
        threshold = mean * (1 + k * ((stddev / r) - 1))

        # Apply threshold
        binary = np.where(image > threshold, 255, 0).astype(np.uint8)

        return binary

    def niblack_threshold(
        self,
        image: np.ndarray,
        window_size: int = 25,
        k: float = -0.2
    ) -> np.ndarray:
        """
        Niblack local thresholding method.

        Args:
            image: Grayscale image
            window_size: Window size
            k: Parameter controlling threshold

        Returns:
            Binarized image
        """
        # Calculate local mean
        mean = cv2.boxFilter(image, -1, (window_size, window_size))

        # Calculate local standard deviation
        sqr_mean = cv2.boxFilter(image ** 2, -1, (window_size, window_size))
        variance = sqr_mean - mean ** 2
        stddev = np.sqrt(np.maximum(variance, 0))

        # Niblack threshold
        threshold = mean + k * stddev

        # Apply threshold
        binary = np.where(image > threshold, 255, 0).astype(np.uint8)

        return binary

    def select_best_binarization(
        self,
        original: np.ndarray,
        methods: dict
    ) -> str:
        """
        Select the best binarization method based on image quality metrics.

        Args:
            original: Original grayscale image
            methods: Dictionary of method_name -> binarized_image

        Returns:
            Name of best method
        """
        if not methods:
            return 'otsu'

        scores = {}

        for name, binary in methods.items():
            # Calculate quality metrics

            # 1. Edge preservation (more edges = better for OCR)
            edges_original = cv2.Canny(original, 50, 150)
            edges_binary = cv2.Canny(binary, 50, 150)
            edge_score = np.sum(edges_binary) / max(np.sum(edges_original), 1)

            # 2. Contrast (higher is better)
            contrast = np.std(binary)

            # 3. Not too much noise (check for salt-and-pepper)
            # Count isolated pixels
            kernel = np.ones((3, 3), np.uint8)
            dilated = cv2.dilate(binary, kernel, iterations=1)
            eroded = cv2.erode(binary, kernel, iterations=1)
            noise_pixels = np.sum(dilated != eroded)
            noise_ratio = noise_pixels / binary.size
            noise_score = 1.0 - min(noise_ratio, 1.0)

            # Combined score
            total_score = edge_score * 0.4 + (contrast / 255) * 0.3 + noise_score * 0.3
            scores[name] = total_score

            logger.debug(
                f"Binarization {name}: edge={edge_score:.3f}, "
                f"contrast={contrast:.1f}, noise={noise_score:.3f}, "
                f"total={total_score:.3f}"
            )

        # Return method with highest score
        best = max(scores, key=scores.get)
        return best

    def correct_perspective(self, image: np.ndarray) -> np.ndarray:
        """
        Automatically detect and correct perspective distortion.

        Args:
            image: OpenCV image

        Returns:
            Perspective-corrected image
        """
        try:
            # Convert to grayscale
            if len(image.shape) == 3:
                gray = cv2.cvtColor(image, cv2.COLOR_BGR2GRAY)
            else:
                gray = image.copy()

            # Edge detection
            edges = cv2.Canny(gray, 50, 150, apertureSize=3)

            # Dilate edges to connect nearby edges
            kernel = np.ones((5, 5), np.uint8)
            dilated = cv2.dilate(edges, kernel, iterations=1)

            # Find contours
            contours, _ = cv2.findContours(
                dilated, cv2.RETR_EXTERNAL, cv2.CHAIN_APPROX_SIMPLE
            )

            if not contours:
                return image

            # Find the largest contour (likely the document)
            largest_contour = max(contours, key=cv2.contourArea)

            # Approximate contour to a polygon
            perimeter = cv2.arcLength(largest_contour, True)
            approx = cv2.approxPolyDP(largest_contour, 0.02 * perimeter, True)

            # If we found a quadrilateral
            if len(approx) == 4:
                logger.debug("Detected quadrilateral, correcting perspective")

                # Order points: top-left, top-right, bottom-right, bottom-left
                pts = self.order_points(approx.reshape(4, 2))

                # Calculate the dimensions of the new image
                width = int(max(
                    np.linalg.norm(pts[0] - pts[1]),
                    np.linalg.norm(pts[2] - pts[3])
                ))
                height = int(max(
                    np.linalg.norm(pts[0] - pts[3]),
                    np.linalg.norm(pts[1] - pts[2])
                ))

                # Define destination points
                dst = np.array([
                    [0, 0],
                    [width - 1, 0],
                    [width - 1, height - 1],
                    [0, height - 1]
                ], dtype=np.float32)

                # Calculate perspective transform matrix
                M = cv2.getPerspectiveTransform(pts.astype(np.float32), dst)

                # Apply perspective transformation
                warped = cv2.warpPerspective(image, M, (width, height))

                return warped

        except Exception as e:
            logger.debug(f"Perspective correction failed: {e}")

        return image

    def order_points(self, pts: np.ndarray) -> np.ndarray:
        """
        Order points in clockwise order: top-left, top-right, bottom-right, bottom-left.

        Args:
            pts: Array of 4 points

        Returns:
            Ordered points
        """
        # Sort by y-coordinate
        sorted_pts = pts[np.argsort(pts[:, 1]), :]

        # Get top two points (smallest y)
        top = sorted_pts[:2, :]
        # Sort top points by x-coordinate
        top = top[np.argsort(top[:, 0]), :]
        top_left, top_right = top[0], top[1]

        # Get bottom two points
        bottom = sorted_pts[2:, :]
        # Sort bottom points by x-coordinate
        bottom = bottom[np.argsort(bottom[:, 0]), :]
        bottom_left, bottom_right = bottom[0], bottom[1]

        return np.array([top_left, top_right, bottom_right, bottom_left])

    def advanced_denoise(self, image: np.ndarray) -> np.ndarray:
        """
        Advanced multi-stage denoising.

        Args:
            image: OpenCV image

        Returns:
            Denoised image
        """
        # Convert to grayscale if needed
        if len(image.shape) == 3:
            gray = cv2.cvtColor(image, cv2.COLOR_BGR2GRAY)
        else:
            gray = image.copy()

        # Stage 1: Morphological denoising (salt-and-pepper noise)
        kernel = cv2.getStructuringElement(cv2.MORPH_RECT, (3, 3))
        opened = cv2.morphologyEx(gray, cv2.MORPH_OPEN, kernel, iterations=1)
        closed = cv2.morphologyEx(opened, cv2.MORPH_CLOSE, kernel, iterations=1)

        # Stage 2: Bilateral filter (preserves edges)
        bilateral = cv2.bilateralFilter(closed, 9, 75, 75)

        # Stage 3: Non-local means (gaussian noise)
        denoised = cv2.fastNlMeansDenoising(bilateral, None, h=10, templateWindowSize=7, searchWindowSize=21)

        logger.debug("Applied advanced denoising")
        return denoised

    def remove_shadows(self, image: np.ndarray) -> np.ndarray:
        """
        Remove shadows and uneven illumination.

        Args:
            image: OpenCV image

        Returns:
            Shadow-removed image
        """
        try:
            # Convert to grayscale if needed
            if len(image.shape) == 3:
                gray = cv2.cvtColor(image, cv2.COLOR_BGR2GRAY)
            else:
                gray = image.copy()

            # Dilate to estimate background
            dilated = cv2.dilate(gray, np.ones((7, 7), np.uint8))
            background = cv2.medianBlur(dilated, 21)

            # Subtract background
            diff = 255 - cv2.absdiff(gray, background)

            # Normalize
            normalized = cv2.normalize(diff, None, 0, 255, cv2.NORM_MINMAX)

            logger.debug("Removed shadows")
            return normalized

        except Exception as e:
            logger.debug(f"Shadow removal failed: {e}")
            return image

    def normalize_background(self, image: np.ndarray) -> np.ndarray:
        """
        Normalize background to white and text to black.

        Args:
            image: OpenCV grayscale image

        Returns:
            Normalized image
        """
        try:
            # Ensure grayscale
            if len(image.shape) == 3:
                gray = cv2.cvtColor(image, cv2.COLOR_BGR2GRAY)
            else:
                gray = image.copy()

            # Estimate background color (most common bright color)
            hist = cv2.calcHist([gray], [0], None, [256], [0, 256])
            # Find peak in upper half (bright pixels)
            upper_hist = hist[128:]
            background_value = 128 + np.argmax(upper_hist)

            # If background is dark, invert
            if background_value < 128:
                gray = 255 - gray

            # Normalize to full range
            normalized = cv2.normalize(gray, None, 0, 255, cv2.NORM_MINMAX)

            logger.debug("Normalized background")
            return normalized

        except Exception as e:
            logger.debug(f"Background normalization failed: {e}")
            return image


def enhance_for_ocr(image: Image.Image, method: str = 'auto') -> Image.Image:
    """
    Convenience function to enhance image for OCR.

    Args:
        image: PIL Image
        method: Enhancement method

    Returns:
        Enhanced PIL Image
    """
    enhancer = ImageEnhancer(method=method)
    return enhancer.enhance(image)
