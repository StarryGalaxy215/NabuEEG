import math
import struct
import random
import time
from typing import Optional
from PyQt5.QtCore import QIODevice, QTimer, Qt, pyqtSignal, QObject
from PyQt5.QtMultimedia import QAudioFormat, QAudioOutput, QAudio

class ToneGenerator(QIODevice):
    """
    Real-time audio generator that creates binaural beats and modulated tones.
    """
    
    def __init__(self, format: QAudioFormat, parent: Optional[QObject] = None):
        if parent:
            super().__init__(parent)
        else:
            super().__init__()
        self.format = format
        self.sample_rate = format.sampleRate()
        self.amplitude = 0.5  # Base volume
        self.base_freq = 200.0  # Hz (Carrier frequency)
        self.beat_freq = 10.0   # Hz (Target brainwave frequency, e.g., Alpha=10Hz)
        self.phase_l = 0.0
        self.phase_r = 0.0
        
        # State variables for modulation
        self.stress_level = 0.5  # 0.0 (Relaxed) to 1.0 (Stressed)
        self.noise_level = 0.1   # Amount of white noise
        self.modulation_speed = 1.0 # Speed of volume LFO
        
        self.buffer_size = 4096
        
    def start(self):
        self.open(QIODevice.ReadOnly)
        
    def set_parameters(self, base_freq, beat_freq, stress_level):
        """Update audio parameters based on EEG data"""
        self.base_freq = base_freq
        self.beat_freq = beat_freq
        self.stress_level = max(0.0, min(1.0, stress_level))
        
        # Stress increases noise and modulation speed
        self.noise_level = 0.05 + (self.stress_level * 0.2)
        self.modulation_speed = 0.5 + (self.stress_level * 4.0)
        
    def readData(self, maxlen):
        """Generate raw audio data"""
        data = bytearray()
        sample_count = maxlen // 2  # 16-bit samples
        
        # Frequencies for left and right ears
        freq_l = self.base_freq - (self.beat_freq / 2)
        freq_r = self.base_freq + (self.beat_freq / 2)
        
        step_l = freq_l * 2 * math.pi / self.sample_rate
        step_r = freq_r * 2 * math.pi / self.sample_rate
        
        # Generate samples
        # For simplicity, generate stereo interleaved 16-bit signed integer (little endian)
        # L R L R ...
        
        # Using a simpler approach: calculate chunks
        # Since struct.pack is slow in loops, we can use pre-calculated lists or bytearrays
        # But for real-time flexibility, let's try a direct approach
        
        values = []
        
        # Generate samples
        # Note: This loop might be slow in pure Python for high sample rates (44100).
        # Optimization: Generate a chunk using math operations.
        # Even better: Use QByteArray directly if possible.
        
        # Let's generate roughly `maxlen` bytes.
        # Since it's stereo 16-bit, each sample frame is 4 bytes.
        frames_to_generate = maxlen // 4
        
        for _ in range(frames_to_generate):
            # Left Ear
            val_l = math.sin(self.phase_l)
            self.phase_l += step_l
            if self.phase_l > 2 * math.pi: self.phase_l -= 2 * math.pi
            
            # Right Ear
            val_r = math.sin(self.phase_r)
            self.phase_r += step_r
            if self.phase_r > 2 * math.pi: self.phase_r -= 2 * math.pi
            
            # Add Noise (Simulating rain/wind)
            noise = (random.random() * 2 - 1) * self.noise_level
            
            # Combine
            sample_l = int((val_l * 0.8 + noise) * self.amplitude * 32767)
            sample_r = int((val_r * 0.8 + noise) * self.amplitude * 32767)
            
            # Clamp
            sample_l = max(-32768, min(32767, sample_l))
            sample_r = max(-32768, min(32767, sample_r))
            
            # Pack
            # Little-endian 16-bit signed
            values.extend([sample_l & 0xFF, (sample_l >> 8) & 0xFF, 
                           sample_r & 0xFF, (sample_r >> 8) & 0xFF])
            
        return bytes(values)

    def bytesAvailable(self):
        return self.buffer_size + super().bytesAvailable()

class BioMusicEngine:
    def __init__(self):
        self.output: Optional[QAudioOutput] = None
        self.generator: Optional[ToneGenerator] = None
        self.format = QAudioFormat()
        self.format.setSampleRate(44100)
        self.format.setChannelCount(2)
        self.format.setSampleSize(16)
        self.format.setCodec("audio/pcm")
        self.format.setByteOrder(QAudioFormat.LittleEndian)
        self.format.setSampleType(QAudioFormat.SignedInt)
        
        from PyQt5.QtMultimedia import QAudioDeviceInfo
        info = QAudioDeviceInfo.defaultOutputDevice()
        if not info.isFormatSupported(self.format):
            print("Audio format not valid, using nearest format")
            self.format = info.nearestFormat(self.format)
            
        self.output = QAudioOutput(self.format)
        self.output.setVolume(0.5)
        
        self.generator = ToneGenerator(self.format)
        
    def start(self):
        if self.generator and self.output:
            self.generator.start()
            self.output.start(self.generator)
        
    def stop(self):
        if self.output:
            self.output.stop()
        if self.generator:
            self.generator.close()
        
    def set_volume(self, volume):
        """0.0 to 1.0"""
        if self.output:
            self.output.setVolume(volume)
        
    def update_eeg_state(self, alpha_power, beta_power):
        """
        Map EEG power to audio parameters.
        Alpha (Relaxed) -> Lower pitch, Slower beats (Theta/Alpha range)
        Beta (Stressed/Focused) -> Higher pitch, Faster beats (Beta range)
        """
        # Normalize roughly (assuming power is 0-100 relative)
        total = alpha_power + beta_power + 0.001
        alpha_ratio = alpha_power / total
        beta_ratio = beta_power / total
        
        # Calculate Stress Level (0 = Relaxed, 1 = Stressed)
        # High Beta = High Stress
        stress = beta_ratio
        
        # Base Frequency: 100Hz (Deep) to 400Hz (Tense)
        base_freq = 100 + (stress * 300)
        
        # Beat Frequency: 
        # Relaxed -> Alpha/Theta (4-12 Hz)
        # Stressed -> Beta/Gamma (13-40 Hz)
        beat_freq = 8 + (stress * 20) 
        
        if self.generator:
            self.generator.set_parameters(base_freq, beat_freq, stress)
        
        return stress # Return for UI visualization
