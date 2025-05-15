"""
Computer vision and audio processing models used for monitoring.
"""

from .yolov7_pose.model import YOLOv7PoseDetector
from .yolov8.model import YOLOv8ObjectDetector

__all__ = ["YOLOv7PoseDetector", "YOLOv8ObjectDetector"] 