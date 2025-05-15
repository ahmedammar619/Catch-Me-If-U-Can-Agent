import os
import sys
import time
import numpy as np
import sounddevice as sd
import soundfile as sf
import torch
from pathlib import Path
from transformers import Wav2Vec2ForCTC, Wav2Vec2Processor
from queue import Queue
from threading import Thread

# Add parent directory to path to import from shared
sys.path.append(str(Path(__file__).parent.parent.parent.parent))
from shared.config import AUDIO_DIR, ALERT_AUDIO_DURATION, CURSE_WORDS

class AudioProcessor:
    def __init__(self, sample_rate=16000, channels=1, device=None):
        """
        Initialize AudioProcessor
        
        Args:
            sample_rate: Audio sample rate
            channels: Number of audio channels
            device: Audio device index or None for default
        """
        self.sample_rate = sample_rate
        self.channels = channels
        self.device = device
        self.audio_buffer = []
        self.max_buffer_size = ALERT_AUDIO_DURATION * sample_rate * channels
        self.recording = False
        self.stream = None
        self.processor = None
        self.model = None
        self.queue = Queue()
        self.processor_thread = None
        
    def load_model(self):
        """Load the Wav2Vec2 model for Egyptian Arabic speech recognition"""
        # Use a smaller model from Hugging Face hub trained on Egyptian Arabic
        model_name = "Zaid/wav2vec2-large-xlsr-53-arabic-egyptian"
        
        print("Loading speech recognition model...")
        self.processor = Wav2Vec2Processor.from_pretrained(model_name)
        self.model = Wav2Vec2ForCTC.from_pretrained(model_name)
        print("Model loaded.")
        
    def start_recording(self):
        """Start recording audio from microphone"""
        if self.recording:
            return
            
        def audio_callback(indata, frames, time, status):
            """Callback function for audio stream processing"""
            data = indata.copy()
            self.queue.put(data)
            
            # Add audio data to buffer
            self.audio_buffer.extend(data.flatten())
            
            # Limit buffer size
            if len(self.audio_buffer) > self.max_buffer_size:
                self.audio_buffer = self.audio_buffer[-self.max_buffer_size:]
        
        self.recording = True
        self.stream = sd.InputStream(
            samplerate=self.sample_rate,
            channels=self.channels,
            device=self.device,
            callback=audio_callback
        )
        self.stream.start()
        
        # Start processing thread
        if self.processor_thread is None:
            self.processor_thread = Thread(target=self._process_audio)
            self.processor_thread.daemon = True
            self.processor_thread.start()
            
        return self
    
    def _process_audio(self):
        """Process audio in a separate thread"""
        if self.model is None:
            self.load_model()
            
        # Process audio chunks
        chunk_size = int(self.sample_rate * 5)  # Process 5 seconds at a time
        buffer = []
        
        while self.recording:
            # Get new audio data
            try:
                data = self.queue.get(timeout=1)
                buffer.extend(data.flatten())
                
                # Process when buffer is large enough
                if len(buffer) >= chunk_size:
                    audio_chunk = np.array(buffer[:chunk_size], dtype=np.float32)
                    buffer = buffer[chunk_size//2:]  # Overlap chunks for better detection
                    
                    # Process audio with the model
                    self._transcribe_and_check(audio_chunk)
                    
            except Exception as e:
                pass  # Handle queue timeout
    
    def _transcribe_and_check(self, audio_data):
        """Transcribe audio chunk and check for curse words"""
        try:
            # Normalize audio
            audio_data = audio_data / np.max(np.abs(audio_data))
            
            # Process through model
            input_values = self.processor(
                audio_data, 
                sampling_rate=self.sample_rate, 
                return_tensors="pt"
            ).input_values
            
            with torch.no_grad():
                logits = self.model(input_values).logits
                
            # Decode the model output
            predicted_ids = torch.argmax(logits, dim=-1)
            transcription = self.processor.decode(predicted_ids[0])
            
            # Check for curse words
            return self._check_for_curse_words(transcription.lower())
            
        except Exception as e:
            print(f"Error in transcription: {e}")
            return False
    
    def _check_for_curse_words(self, text):
        """Check if transcribed text contains any curse words"""
        for word in CURSE_WORDS:
            if word in text:
                print(f"❌ Detected curse word: {word}")
                return True
        return False
    
    def save_alert_audio(self, alert_id):
        """Save buffered audio as a WAV file for an alert"""
        if not self.audio_buffer:
            return None
            
        # Create filename with timestamp
        timestamp = time.strftime("%Y%m%d_%H%M%S")
        audio_path = os.path.join(AUDIO_DIR, f"alert_{alert_id}_{timestamp}.wav")
        
        # Normalize audio data
        audio_data = np.array(self.audio_buffer)
        if len(audio_data) > 0:
            audio_data = audio_data / np.max(np.abs(audio_data))
            
            # Save audio file
            sf.write(audio_path, audio_data, self.sample_rate)
            return audio_path
        
        return None
    
    def stop_recording(self):
        """Stop recording audio"""
        self.recording = False
        if self.stream is not None:
            self.stream.stop()
            self.stream.close()
            self.stream = None
    
    def __del__(self):
        self.stop_recording() 