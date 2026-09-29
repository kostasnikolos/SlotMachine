import wave
import struct
import math
import random
import os

def generate_spank(filename):
    sample_rate = 44100
    duration = 0.5
    num_samples = int(sample_rate * duration)
    
    os.makedirs(os.path.dirname(filename), exist_ok=True)
    
    with wave.open(filename, 'w') as wav_file:
        wav_file.setnchannels(1)
        wav_file.setsampwidth(2)
        wav_file.setframerate(sample_rate)
        
        phase = 0
        
        for i in range(num_samples):
            t = i / sample_rate
            
            # Envelope for the overall sound (very fast decay)
            env = math.exp(-t * 10)
            
            # Pitch drop
            # Start at 200 Hz, drop rapidly to 50 Hz
            freq = 50 + 150 * math.exp(-t * 30)
            
            # Accumulate phase
            phase += 2 * math.pi * freq / sample_rate
            
            # Body (sine wave)
            body = math.sin(phase)
            
            # Slap transient (noise burst)
            slap_env = math.exp(-t * 50)
            slap = random.uniform(-1, 1) * slap_env
            
            # Mix
            sample = (body * env * 0.6 + slap * 0.4) * 24000
            
            sample = max(-32768, min(32767, int(sample)))
            wav_file.writeframes(struct.pack('h', sample))

if __name__ == '__main__':
    generate_spank('/Users/kosta/SlotMachine/slot_engine/static/assets/audio/spank.wav')
