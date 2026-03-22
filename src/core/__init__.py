"""
核心功能模块
"""

from .screenshot import ScreenshotCapture, ScreenshotMode, ScreenshotResult
from .annotation import (
    AnnotationManager, AnnotationType,
    RectangleAnnotation, ArrowAnnotation, TextAnnotation, MosaicAnnotation,
    apply_annotations_to_pixmap
)

__all__ = [
    "ScreenshotCapture", "ScreenshotMode", "ScreenshotResult",
    "AnnotationManager", "AnnotationType",
    "RectangleAnnotation", "ArrowAnnotation", "TextAnnotation", "MosaicAnnotation",
    "apply_annotations_to_pixmap"
]
