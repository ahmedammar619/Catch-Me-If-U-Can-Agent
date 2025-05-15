import cv2
import torch
import numpy as np
import time
from pathlib import Path
import sys
import os

# Add parent directory to path to import from shared
sys.path.append(str(Path(__file__).parent.parent.parent.parent))
from shared.config import VIDEO_DIR, ALERT_VIDEO_DURATION

class VideoProcessor:
    def __init__(self, source=0, output_size=(640, 480), fps=30):
        """
        Initialize VideoProcessor
        
        Args:
            source: Camera index or video file path
            output_size: (width, height) tuple for output frame size
            fps: Frames per second 
        """
        self.source = source
        self.output_size = output_size
        self.fps = fps
        self.cap = None
        self.writer = None
        self.frame_buffer = []
        self.max_buffer_size = ALERT_VIDEO_DURATION * fps
        
    def start(self):
        """Start video capture"""
        self.cap = cv2.VideoCapture(self.source)
        if not self.cap.isOpened():
            raise ValueError(f"Failed to open video source {self.source}")
        return self
    
    def read_frame(self):
        """Read a frame from the video source"""
        if self.cap is None:
            self.start()
        
        ret, frame = self.cap.read()
        if not ret:
            return None
        
        # Resize frame if needed
        if frame.shape[1] != self.output_size[0] or frame.shape[0] != self.output_size[1]:
            frame = cv2.resize(frame, self.output_size)
            
        # Add frame to buffer and remove oldest if buffer is full
        self.frame_buffer.append(frame.copy())
        if len(self.frame_buffer) > self.max_buffer_size:
            self.frame_buffer.pop(0)
            
        return frame
    
    def save_alert_video(self, alert_id):
        """Save buffered frames as video clip for an alert"""
        if not self.frame_buffer:
            return None
            
        # Create filename with timestamp
        timestamp = time.strftime("%Y%m%d_%H%M%S")
        video_path = os.path.join(VIDEO_DIR, f"alert_{alert_id}_{timestamp}.mp4")
        
        # Create video writer
        fourcc = cv2.VideoWriter_fourcc(*'mp4v')
        height, width = self.frame_buffer[0].shape[:2]
        writer = cv2.VideoWriter(video_path, fourcc, self.fps, (width, height))
        
        # Write frames to video
        for frame in self.frame_buffer:
            writer.write(frame)
            
        writer.release()
        return video_path
    
    def release(self):
        """Release video capture resources"""
        if self.cap is not None:
            self.cap.release()
            self.cap = None
        if self.writer is not None:
            self.writer.release()
            self.writer = None
    
    def __del__(self):
        self.release() 