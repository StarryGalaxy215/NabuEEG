import random
import struct
from typing import Optional
from PyQt5.QtCore import QIODevice, QObject
from PyQt5.QtMultimedia import QAudioFormat, QAudioOutput

class NoiseGenerator(QIODevice):
    """
    Real-time noise generator: White, Pink, Brown.
    """
    def __init__(self, format: QAudioFormat, parent: Optional[QObject] = None):
        if parent:
            super().__init__(parent)
        else:
            super().__init__()
        self.format = format
        self.sample_rate = format.sampleRate()
        self.noise_type = "white"  # white, pink, brown
        self.amplitude = 0.5
        self.buffer_size = 4096 * 2
        
        # Pink noise state (Paul Kellet's refined method)
        self.pink_b = [0.0] * 7
        
        # Brown noise state
        self.brown_last = 0.0
        
    def start(self):
        self.open(QIODevice.ReadOnly)
        
    def set_noise_type(self, type_name):
        self.noise_type = type_name
        # Reset states to avoid pops
        self.pink_b = [0.0] * 7
        self.brown_last = 0.0
        
    def set_volume(self, vol):
        self.amplitude = max(0.0, min(1.0, vol))
        
    def readData(self, maxlen):
        """Generate raw audio data"""
        # Calculate how many frames we need
        # Stereo 16-bit = 4 bytes per frame
        frames = maxlen // 4
        if frames <= 0:
            return b""
            
        values = []
        
        # Optimization: Local variable lookup is faster
        noise_type = self.noise_type
        amp = self.amplitude * 32767
        
        # Generate samples
        # To avoid Python loop overhead causing stuttering at 44.1kHz,
        # we try to keep operations minimal.
        
        # Pre-allocate buffer is hard with variable logic, so we just loop.
        # If this is too slow, we might need to lower sample rate or use numpy if available.
        # For now, let's try standard python.
        
        # Using a slightly larger chunk or optimizing the inner loop?
        # Actually, for white noise, we can generate a block.
        
        if noise_type == "white":
            for _ in range(frames):
                val = random.random() * 2 - 1
                sample = int(val * amp)
                # Stereo
                values.extend([sample & 0xFF, (sample >> 8) & 0xFF,
                               sample & 0xFF, (sample >> 8) & 0xFF])
                               
        elif noise_type == "pink":
            # Paul Kellet's method
            for _ in range(frames):
                white = random.random() * 2 - 1
                self.pink_b[0] = 0.99886 * self.pink_b[0] + white * 0.0555179
                self.pink_b[1] = 0.99332 * self.pink_b[1] + white * 0.0750759
                self.pink_b[2] = 0.96900 * self.pink_b[2] + white * 0.1538520
                self.pink_b[3] = 0.86650 * self.pink_b[3] + white * 0.3104856
                self.pink_b[4] = 0.55000 * self.pink_b[4] + white * 0.5329522
                self.pink_b[5] = -0.7616 * self.pink_b[5] - white * 0.0168980
                self.pink_b[6] = white * 0.115926
                val = sum(self.pink_b) * 0.11 # Approximate normalization
                
                # Clamp
                if val > 1.0: val = 1.0
                elif val < -1.0: val = -1.0
                
                sample = int(val * amp)
                values.extend([sample & 0xFF, (sample >> 8) & 0xFF,
                               sample & 0xFF, (sample >> 8) & 0xFF])
                               
        elif noise_type == "brown":
            for _ in range(frames):
                white = random.random() * 2 - 1
                self.brown_last = (self.brown_last + (0.02 * white)) / 1.02
                val = self.brown_last * 3.5
                
                if val > 1.0: val = 1.0
                elif val < -1.0: val = -1.0
                
                sample = int(val * amp)
                values.extend([sample & 0xFF, (sample >> 8) & 0xFF,
                               sample & 0xFF, (sample >> 8) & 0xFF])
                               
        return bytes(values)

    def bytesAvailable(self):
        return self.buffer_size + super().bytesAvailable()


class NoiseEngine:
    def __init__(self):
        self.output = None
        self.generator = None
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
            self.format = info.nearestFormat(self.format)
            
        self.output = QAudioOutput(self.format)
        self.output.setVolume(1.0) # Controlled by generator amplitude
        
        self.generator = NoiseGenerator(self.format)
        
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
        if self.generator:
            self.generator.set_volume(volume)
            
    def set_noise_type(self, noise_type):
        if self.generator:
            self.generator.set_noise_type(noise_type)
