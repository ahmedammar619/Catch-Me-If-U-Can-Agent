import sys
import os
import cv2
import time
import numpy as np
from pathlib import Path
from ultralytics import YOLO

# Add parent directory to path to import from shared
sys.path.append(str(Path(__file__).parent.parent.parent.parent.parent))
from shared.config import OBJECT_DETECTION_CONF

class YOLOv8ObjectDetector:
    def __init__(self, model_name="yolov8n.pt", conf_threshold=OBJECT_DETECTION_CONF):
        """
        Initialize YOLOv8 object detector
        
        Args:
            model_name: YOLOv8 model name or path
            conf_threshold: Confidence threshold for object detection
        """
        self.model_name = model_name
        self.conf_threshold = conf_threshold
        self.model = None
        self.tracked_objects = {}
        self.missing_objects = []
        self.watched_classes = ["chair", "laptop", "cell phone", "keyboard", "mouse", "cup", "bottle"]
        
    def load_model(self):
        """Load YOLOv8 model"""
        print(f"Loading YOLOv8 model: {self.model_name}")
        self.model = YOLO(self.model_name)
        print("YOLOv8 model loaded successfully")
        return self
        
    def detect_objects(self, frame):
        """
        Detect objects in a frame
        
        Args:
            frame: Input frame (numpy array)
            
        Returns:
            Detections object from YOLO
        """
        if self.model is None:
            self.load_model()
            
        # Run inference
        results = self.model.predict(frame, conf=self.conf_threshold, verbose=False)
        return results[0]
        
    def update_object_tracking(self, frame):
        """
        Update object tracking and detect missing objects
        
        Args:
            frame: Input frame
            
        Returns:
            (bool, str): Tuple containing detection result and description
        """
        self.missing_objects = []
        results = self.detect_objects(frame)
        
        # Get current detections
        current_objects = {}
        
        for detection in results.boxes.data.cpu().numpy():
            x1, y1, x2, y2, conf, cls_id = detection
            cls_id = int(cls_id)
            class_name = results.names[cls_id]
            
            # Only track watched classes
            if class_name in self.watched_classes:
                box_center = ((x1 + x2) / 2, (y1 + y2) / 2)
                obj_size = (x2 - x1) * (y2 - y1)  # area
                
                # Create a unique identifier for this object
                # Using position and size to distinguish between similar objects
                obj_id = f"{class_name}_{int(box_center[0]/20)}_{int(box_center[1]/20)}_{int(obj_size/500)}"
                
                current_objects[obj_id] = {
                    "class": class_name,
                    "position": box_center,
                    "size": obj_size,
                    "last_seen": time.time(),
                    "box": (x1, y1, x2, y2)
                }
        
        # If it's the first frame, initialize tracking
        if not self.tracked_objects:
            self.tracked_objects = current_objects
            return False, ""
            
        # Check for missing objects (theft detection)
        for obj_id, obj_data in self.tracked_objects.items():
            # If an object was present but is now missing
            if obj_id not in current_objects:
                # Check if it's been missing for at least 3 seconds
                time_missing = time.time() - obj_data["last_seen"]
                
                if time_missing > 3:
                    self.missing_objects.append(obj_data)
        
        # Update tracked objects
        self.tracked_objects = current_objects
        
        # Return detection result
        if self.missing_objects:
            missing_names = [obj["class"] for obj in self.missing_objects]
            unique_names = set(missing_names)
            description = f"Potential theft detected: {', '.join(unique_names)} missing"
            return True, description
            
        return False, ""
    
    def draw_detections(self, frame, detections):
        """Draw object detections on frame for visualization"""
        frame_copy = frame.copy()
        
        # Colors for different classes (BGR format)
        colors = {
            "chair": (0, 255, 0),
            "laptop": (255, 0, 0),
            "cell phone": (0, 0, 255),
            "keyboard": (255, 255, 0),
            "mouse": (0, 255, 255),
            "cup": (255, 0, 255),
            "bottle": (0, 165, 255),
        }
        
        # Draw bounding boxes for current detections
        for box in detections.boxes.data.cpu().numpy():
            x1, y1, x2, y2, conf, cls_id = box
            cls_id = int(cls_id)
            class_name = detections.names[cls_id]
            
            if class_name in self.watched_classes:
                color = colors.get(class_name, (255, 255, 255))
                
                # Draw bounding box
                cv2.rectangle(frame_copy, (int(x1), int(y1)), (int(x2), int(y2)), color, 2)
                
                # Draw label
                label = f"{class_name}: {conf:.2f}"
                (text_width, text_height), _ = cv2.getTextSize(label, cv2.FONT_HERSHEY_SIMPLEX, 0.5, 1)
                cv2.rectangle(frame_copy, (int(x1), int(y1) - text_height - 4), (int(x1) + text_width, int(y1)), color, -1)
                cv2.putText(frame_copy, label, (int(x1), int(y1) - 2), cv2.FONT_HERSHEY_SIMPLEX, 0.5, (0, 0, 0), 1)
                
        # Highlight missing objects with a text warning
        if self.missing_objects:
            missing_text = "Missing: " + ", ".join([obj["class"] for obj in self.missing_objects])
            cv2.putText(frame_copy, missing_text, (10, 30), cv2.FONT_HERSHEY_SIMPLEX, 0.8, (0, 0, 255), 2)
            
        return frame_copy 