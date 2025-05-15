import sys
import time
import threading
import cv2
import os
from pathlib import Path

# Add parent directory to path to import from shared
sys.path.append(str(Path(__file__).parent.parent.parent))
from shared.config import VIDEO_SOURCES

# Import utility modules - using relative imports instead of absolute
from .utils.video_processing import VideoProcessor
from .utils.audio_processing import AudioProcessor
from .utils.alert_manager import Alert, AlertManager

# Import models
from .models.yolov7_pose.model import YOLOv7PoseDetector
from .models.yolov8.model import YOLOv8ObjectDetector

class Agent:
    def __init__(self, video_sources=None, show_visualization=True, safe_mode=False):
        """
        Initialize the monitoring agent
        
        Args:
            video_sources: List of video sources (camera indices or file paths)
            show_visualization: Whether to show visualization window
            safe_mode: Run in safe mode without loading ML models
        """
        self.video_sources = video_sources or VIDEO_SOURCES
        self.show_visualization = show_visualization
        self.safe_mode = safe_mode
        
        # Initialize video processors (one for each source)
        self.video_processors = []
        for source in self.video_sources:
            self.video_processors.append(VideoProcessor(source=source))
            
        # Initialize audio processor
        self.audio_processor = AudioProcessor()
        
        # Initialize models (unless in safe mode)
        if not safe_mode:
            try:
                self.pose_detector = YOLOv7PoseDetector()
                self.object_detector = YOLOv8ObjectDetector()
            except Exception as e:
                print(f"Error loading ML models: {e}")
                print("Switching to safe mode.")
                self.safe_mode = True
        
        # Initialize alert manager
        self.alert_manager = AlertManager()
        
        # Visualization windows
        self.windows = []
        
        # Flags
        self.running = False
        self.threads = []
        
    def start(self):
        """Start the monitoring agent"""
        if self.running:
            print("Agent is already running")
            return
            
        self.running = True
        
        # Print mode information
        if self.safe_mode:
            print("Running in SAFE MODE - ML models are disabled.")
        
        # Start video processors
        for i, processor in enumerate(self.video_processors):
            try:
                processor.start()
                if self.show_visualization:
                    window_name = f"Camera {i}"
                    self.windows.append(window_name)
                    cv2.namedWindow(window_name, cv2.WINDOW_NORMAL)
            except ValueError as e:
                print(f"Error starting video processor {i}: {e}")
                print("This can happen if the application doesn't have permission to access the camera.")
                print("Please check your camera permissions and try again.")
                self.stop()
                return
                
        # Start audio processor only if not in safe mode
        if not self.safe_mode:
            try:
                self.audio_processor.start_recording()
            except Exception as e:
                print(f"Error starting audio processor: {e}")
                print("Audio monitoring will be disabled.")
        
        # Start monitoring threads only if not in safe mode
        if not self.safe_mode:
            pose_thread = threading.Thread(target=self._pose_detection_thread)
            pose_thread.daemon = True
            pose_thread.start()
            self.threads.append(pose_thread)
            
            object_thread = threading.Thread(target=self._object_detection_thread)
            object_thread.daemon = True
            object_thread.start()
            self.threads.append(object_thread)
        
        print("Agent started monitoring")
        
        # Main loop for visualization
        if self.show_visualization:
            try:
                while self.running:
                    for i, processor in enumerate(self.video_processors):
                        frame = processor.read_frame()
                        if frame is not None and i < len(self.windows):
                            cv2.imshow(self.windows[i], frame)
                            
                    # Exit if 'q' is pressed
                    if cv2.waitKey(1) & 0xFF == ord('q'):
                        self.stop()
                        break
            except KeyboardInterrupt:
                self.stop()
        else:
            # Without visualization, just keep the main thread running
            try:
                while self.running:
                    time.sleep(1)
            except KeyboardInterrupt:
                self.stop()
                
    def _pose_detection_thread(self):
        """Thread for pose detection (inappropriate contact)"""
        print("Started pose detection thread")
        camera_index = 2  # Use first camera for pose detection
        
        while self.running:
            try:
                # Get frame from video processor
                frame = self.video_processors[camera_index].read_frame()
                if frame is None:
                    continue
                    
                # Detect poses
                poses = self.pose_detector.detect_poses(frame)
                
                # Check for inappropriate contact
                detected, description = self.pose_detector.check_inappropriate_contact(poses)
                
                # Create alert if detected
                if detected:
                    print(f"⚠️ {description}")
                    
                    # Save video clip
                    video_path = self.video_processors[camera_index].save_alert_video(f"pose_{int(time.time())}")
                    
                    # Save audio clip
                    audio_path = self.audio_processor.save_alert_audio(f"pose_{int(time.time())}")
                    
                    # Create and add alert
                    alert = Alert(
                        alert_type="inappropriate_contact",
                        description=description,
                        video_path=video_path,
                        audio_path=audio_path
                    )
                    self.alert_manager.add_alert(alert)
                    
                # Draw poses for visualization if enabled
                if self.show_visualization:
                    vis_frame = self.pose_detector.draw_poses(frame, poses)
                    self.video_processors[camera_index].frame_buffer[-1] = vis_frame
                
                # Sleep briefly to avoid consuming too much CPU
                time.sleep(0.05)
                
            except Exception as e:
                print(f"Error in pose detection thread: {e}")
                time.sleep(1)
                
    def _object_detection_thread(self):
        """Thread for object detection (theft)"""
        print("Started object detection thread")
        camera_index = 0  # Use first camera for object detection
        
        while self.running:
            try:
                # Get frame from video processor
                frame = self.video_processors[camera_index].read_frame()
                if frame is None:
                    continue
                    
                # Update object tracking and check for theft
                detected, description = self.object_detector.update_object_tracking(frame)
                
                # Create alert if detected
                if detected:
                    print(f"⚠️ {description}")
                    
                    # Save video clip
                    video_path = self.video_processors[camera_index].save_alert_video(f"object_{int(time.time())}")
                    
                    # Save audio clip (in case someone is talking about it)
                    audio_path = self.audio_processor.save_alert_audio(f"object_{int(time.time())}")
                    
                    # Create and add alert
                    alert = Alert(
                        alert_type="object_theft",
                        description=description,
                        video_path=video_path,
                        audio_path=audio_path
                    )
                    self.alert_manager.add_alert(alert)
                    
                # Draw detections for visualization if enabled
                if self.show_visualization:
                    detections = self.object_detector.detect_objects(frame)
                    vis_frame = self.object_detector.draw_detections(frame, detections)
                    self.video_processors[camera_index].frame_buffer[-1] = vis_frame
                
                # Sleep briefly to avoid consuming too much CPU
                time.sleep(0.1)
                
            except Exception as e:
                print(f"Error in object detection thread: {e}")
                time.sleep(1)
    
    def stop(self):
        """Stop the monitoring agent"""
        print("Stopping agent...")
        self.running = False
        
        # Wait for threads to finish
        for thread in self.threads:
            if thread.is_alive():
                thread.join(timeout=2)
                
        # Stop video processors
        for processor in self.video_processors:
            processor.release()
            
        # Stop audio processor
        self.audio_processor.stop_recording()
        
        # Close visualization windows
        if self.show_visualization:
            for window in self.windows:
                cv2.destroyWindow(window)
                
        print("Agent stopped")

if __name__ == "__main__":
    # Create and start agent
    agent = Agent(show_visualization=True)
    agent.start() 