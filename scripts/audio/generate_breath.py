import wave
import struct
import math
import random
import os

def generate_breath(filename):
    sample_rate = 44100
    duration = 4.0 # 4 seconds per breath cycle
    num_samples = int(sample_rate * duration)
    
    os.makedirs(os.path.dirname(filename), exist_ok=True)
    
    with wave.open(filename, 'w') as wav_file:
        wav_file.setnchannels(1)
        wav_file.setsampwidth(2)
        wav_file.setframerate(sample_rate)
        
        # Simple lowpass filter state
        last_val = 0
        
        for i in range(num_samples):
            t = i / sample_rate
            
            # Envelope for breathing: sin wave mapped to 0-1 range
            # inhale (0-2s), exhale (2-4s)
            envelope = (math.sin(t * math.pi * 2 / duration - math.pi/2) + 1.0) / 2.0
            # sharpen the envelope a bit
            envelope = math.pow(envelope, 2)
            
            # Generate white noise
            noise = random.uniform(-1.0, 1.0)
            
            # Lowpass filter the noise to make it sound more like breath/air
            alpha = 0.1 # Cutoff control
            filtered_noise = last_val + alpha * (noise - last_val)
            last_val = filtered_noise
            
            # Apply envelope and scale
            sample = filtered_noise * envelope * 16000
            
            # Clip
            sample = max(-32768, min(32767, int(sample)))
            
            wav_file.writeframes(struct.pack('h', sample))

if __name__ == '__main__':
    generate_breath('/Users/kosta/SlotMachine/slot_engine/static/assets/audio/breath.wav')
