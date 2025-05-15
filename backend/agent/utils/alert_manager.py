import json
import os
import time
import uuid
from datetime import datetime
from pathlib import Path
import sys

# Add parent directory to path to import from shared
sys.path.append(str(Path(__file__).parent.parent.parent.parent))
from shared.config import BASE_DIR

# Alert database path
ALERTS_DB_PATH = BASE_DIR / "backend" / "agent" / "data" / "alerts.json"

class Alert:
    def __init__(self, alert_type, description, video_path=None, audio_path=None):
        """
        Initialize Alert object
        
        Args:
            alert_type: Type of alert ('inappropriate_contact', 'object_theft', 'offensive_language')
            description: Description of the alert
            video_path: Path to the video file
            audio_path: Path to the audio file
        """
        self.id = str(uuid.uuid4())[:8]  # Generate short unique ID
        self.timestamp = datetime.now().isoformat()
        self.alert_type = alert_type
        self.description = description
        self.video_path = video_path
        self.audio_path = audio_path
        self.is_false_positive = False
        self.feedback = ""
    
    def to_dict(self):
        """Convert alert to dictionary"""
        return {
            "id": self.id,
            "timestamp": self.timestamp,
            "alert_type": self.alert_type,
            "description": self.description,
            "video_path": self.video_path,
            "audio_path": self.audio_path,
            "is_false_positive": self.is_false_positive,
            "feedback": self.feedback
        }

class AlertManager:
    def __init__(self):
        """Initialize the AlertManager"""
        self.alerts = []
        self.load_alerts()
        
    def load_alerts(self):
        """Load alerts from the JSON file"""
        if os.path.exists(ALERTS_DB_PATH):
            try:
                with open(ALERTS_DB_PATH, 'r') as f:
                    data = json.load(f)
                    self.alerts = data
            except Exception as e:
                print(f"Error loading alerts: {e}")
                self.alerts = []
        else:
            # Create empty alerts file
            os.makedirs(os.path.dirname(ALERTS_DB_PATH), exist_ok=True)
            self.save_alerts()
            
    def save_alerts(self):
        """Save alerts to the JSON file"""
        with open(ALERTS_DB_PATH, 'w') as f:
            json.dump(self.alerts, f, indent=2)
            
    def add_alert(self, alert):
        """Add a new alert"""
        if isinstance(alert, Alert):
            alert_dict = alert.to_dict()
            self.alerts.append(alert_dict)
            self.save_alerts()
            return alert.id
        else:
            raise ValueError("Expected Alert object")
            
    def get_all_alerts(self):
        """Get all alerts"""
        return sorted(self.alerts, key=lambda x: x["timestamp"], reverse=True)
        
    def get_alert_by_id(self, alert_id):
        """Get an alert by ID"""
        for alert in self.alerts:
            if alert["id"] == alert_id:
                return alert
        return None
        
    def mark_as_false_positive(self, alert_id, feedback=""):
        """Mark an alert as a false positive"""
        alert = self.get_alert_by_id(alert_id)
        if alert:
            alert["is_false_positive"] = True
            alert["feedback"] = feedback
            self.save_alerts()
            return True
        return False
        
    def delete_alert(self, alert_id):
        """Delete an alert"""
        for i, alert in enumerate(self.alerts):
            if alert["id"] == alert_id:
                # Delete associated media files if they exist
                for path_key in ["video_path", "audio_path"]:
                    if alert[path_key] and os.path.exists(alert[path_key]):
                        try:
                            os.remove(alert[path_key])
                        except Exception as e:
                            print(f"Error deleting file {alert[path_key]}: {e}")
                
                # Remove from list
                self.alerts.pop(i)
                self.save_alerts()
                return True
        return False 