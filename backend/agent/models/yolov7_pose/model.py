import sys
import os
import cv2
import torch
import numpy as np
from pathlib import Path
import math

# Add parent directory to path to import from shared
sys.path.append(str(Path(__file__).parent.parent.parent.parent.parent))
from shared.config import YOLOV7_POSE_MODEL_PATH, POSE_DETECTION_CONF

class YOLOv7PoseDetector:
    def __init__(self, model_path=None, conf_threshold=POSE_DETECTION_CONF):
        """
        Initialize YOLOv7 pose detector
        
        Args:
            model_path: Path to YOLOv7 pose model
            conf_threshold: Confidence threshold for pose detection
        """
        self.model_path = model_path or YOLOV7_POSE_MODEL_PATH
        self.conf_threshold = conf_threshold
        self.model = None
        
    def load_model(self):
        """Load YOLOv7 pose model"""
        if not os.path.exists(self.model_path):
            raise FileNotFoundError(f"Model file not found: {self.model_path}")
            
        print(f"Loading YOLOv7 pose model from {self.model_path}")
        self.model = torch.hub.load('WongKinYiu/yolov7', 'custom', 
                                    path=self.model_path, 
                                    force_reload=True,
                                    trust_repo=True)
                                    
        # Set model parameters
        self.model.conf = self.conf_threshold
        self.model.iou = 0.45  # IoU threshold for NMS
        
        # Use GPU if available
        if torch.cuda.is_available():
            self.model.cuda()
            
        print("YOLOv7 pose model loaded successfully")
        return self
        
    def detect_poses(self, frame):
        """
        Detect human poses in a frame
        
        Args:
            frame: Input frame (numpy array)
            
        Returns:
            List of detected poses (keypoints)
        """
        if self.model is None:
            self.load_model()
            
        # Run inference
        results = self.model(frame)
        poses = []
        
        # Extract keypoints from detections
        keypoints = results.keypoints.cpu().numpy()
        if len(keypoints) > 0:
            for person_keypoints in keypoints:
                poses.append(person_keypoints)
                
        return poses
        
    def check_inappropriate_contact(self, poses):
        """
        Check if there is inappropriate contact between people
        
        Args:
            poses: List of detected poses
            
        Returns:
            (bool, str): Tuple containing detection result and description
        """
        if len(poses) < 2:
            return False, ""
            
        for i in range(len(poses)):
            for j in range(i+1, len(poses)):
                person1 = poses[i]
                person2 = poses[j]
                
                # Calculate distance between key body parts
                # Key indices: 5-6 (shoulders), 11-12 (hips), 13-14 (knees)
                distance = self._calculate_minimum_distance(person1, person2)
                
                # If people are very close and in a suspicious pose
                if distance < 30:  # Threshold in pixels
                    # Check if they're facing each other
                    facing = self._are_facing_each_other(person1, person2)
                    
                    if facing:
                        # Detect if hands are on other person
                        hand_contact = self._detect_hand_contact(person1, person2)
                        
                        if hand_contact:
                            return True, "Detected inappropriate physical contact between people"
                            
        return False, ""
        
    def _calculate_minimum_distance(self, person1, person2):
        """Calculate minimum distance between key body parts of two people"""
        # Skip if any of the keypoints confidence is low
        min_distance = float('inf')
        
        # Key body points to check (shoulders, torso, hips)
        key_points = [5, 6, 11, 12]  # shoulder and hip indices
        
        for p1_idx in key_points:
            p1 = person1[p1_idx]
            if p1[2] < 0.5:  # Skip low confidence
                continue
                
            for p2_idx in key_points:
                p2 = person2[p2_idx]
                if p2[2] < 0.5:  # Skip low confidence
                    continue
                    
                dist = math.sqrt((p1[0] - p2[0])**2 + (p1[1] - p2[1])**2)
                min_distance = min(min_distance, dist)
                
        return min_distance
        
    def _are_facing_each_other(self, person1, person2):
        """Check if two people are facing each other"""
        # Get shoulder midpoints
        p1_shoulders_mid = [(person1[5][0] + person1[6][0])/2, (person1[5][1] + person1[6][1])/2]
        p2_shoulders_mid = [(person2[5][0] + person2[6][0])/2, (person2[5][1] + person2[6][1])/2]
        
        # Get hip midpoints
        p1_hips_mid = [(person1[11][0] + person1[12][0])/2, (person1[11][1] + person1[12][1])/2]
        p2_hips_mid = [(person2[11][0] + person2[12][0])/2, (person2[11][1] + person2[12][1])/2]
        
        # Calculate direction vectors
        p1_direction = [p1_shoulders_mid[0] - p1_hips_mid[0], p1_shoulders_mid[1] - p1_hips_mid[1]]
        p2_direction = [p2_shoulders_mid[0] - p2_hips_mid[0], p2_shoulders_mid[1] - p2_hips_mid[1]]
        
        # Normalize vectors
        p1_norm = math.sqrt(p1_direction[0]**2 + p1_direction[1]**2)
        p2_norm = math.sqrt(p2_direction[0]**2 + p2_direction[1]**2)
        
        if p1_norm > 0 and p2_norm > 0:
            p1_direction = [p1_direction[0]/p1_norm, p1_direction[1]/p1_norm]
            p2_direction = [p2_direction[0]/p2_norm, p2_direction[1]/p2_norm]
            
            # Dot product to check angle
            dot_product = p1_direction[0]*p2_direction[0] + p1_direction[1]*p2_direction[1]
            
            # If dot product is negative, they are facing each other
            return dot_product < 0
            
        return False
        
    def _detect_hand_contact(self, person1, person2):
        """Check if hands of one person are touching the other person"""
        # Hand keypoints indices
        hand_indices = [9, 10]  # Wrists
        body_indices = [5, 6, 11, 12]  # Shoulders and hips
        
        # Check hands of person1 touching person2
        for hand_idx in hand_indices:
            hand = person1[hand_idx]
            if hand[2] < 0.5:  # Skip low confidence
                continue
                
            for body_idx in body_indices:
                body = person2[body_idx]
                if body[2] < 0.5:  # Skip low confidence
                    continue
                    
                dist = math.sqrt((hand[0] - body[0])**2 + (hand[1] - body[1])**2)
                if dist < 20:  # Threshold in pixels
                    return True
                    
        # Check hands of person2 touching person1
        for hand_idx in hand_indices:
            hand = person2[hand_idx]
            if hand[2] < 0.5:  # Skip low confidence
                continue
                
            for body_idx in body_indices:
                body = person1[body_idx]
                if body[2] < 0.5:  # Skip low confidence
                    continue
                    
                dist = math.sqrt((hand[0] - body[0])**2 + (hand[1] - body[1])**2)
                if dist < 20:  # Threshold in pixels
                    return True
                    
        return False
        
    def draw_poses(self, frame, poses):
        """Draw detected poses on frame for visualization"""
        frame_copy = frame.copy()
        
        if len(poses) == 0:
            return frame_copy
            
        # Define the keypoint connections (pairs of points to connect)
        keypoint_pairs = [
            (0, 1), (0, 2), (1, 3), (2, 4),  # Face
            (5, 6), (5, 7), (7, 9), (6, 8), (8, 10),  # Arms
            (5, 11), (6, 12), (11, 12),  # Torso
            (11, 13), (13, 15), (12, 14), (14, 16)  # Legs
        ]
        
        # Colors for different people
        colors = [(0, 255, 0), (255, 0, 0), (0, 0, 255), (255, 255, 0), (0, 255, 255)]
        
        # Draw each person
        for i, person in enumerate(poses):
            color = colors[i % len(colors)]
            
            # Draw keypoints
            for j, (x, y, conf) in enumerate(person):
                if conf > 0.5:  # Only draw high confidence keypoints
                    cv2.circle(frame_copy, (int(x), int(y)), 5, color, -1)
                    
            # Draw connections
            for pair in keypoint_pairs:
                p1, p2 = person[pair[0]], person[pair[1]]
                
                if p1[2] > 0.5 and p2[2] > 0.5:  # Both points have high confidence
                    cv2.line(frame_copy, 
                            (int(p1[0]), int(p1[1])), 
                            (int(p2[0]), int(p2[1])), 
                            color, 2)
                            
        return frame_copy 