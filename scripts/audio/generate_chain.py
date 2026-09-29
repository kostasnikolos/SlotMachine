import wave
import struct
import math
import random
import os

def generate_chain(filename):
    sample_rate = 44100
    duration = 2.0
    num_samples = int(sample_rate * duration)
    
    os.makedirs(os.path.dirname(filename), exist_ok=True)
    
    with wave.open(filename, 'w') as wav_file:
        wav_file.setnchannels(1)
        wav_file.setsampwidth(2)
        wav_file.setframerate(sample_rate)
        
        # Frequencies for metallic sound
        freqs = [800, 800 * 1.414, 800 * 1.732, 800 * 2.14, 800 * 3.1]
        
        for i in range(num_samples):
            t = i / sample_rate
            
            # General decaying envelope
            global_env = math.exp(-t * 2)
            
            # Clank triggers
            clank_env = 0
            # Simulating multiple dragging clanks
            clank_times = [0.1, 0.4, 0.9, 1.3, 1.8]
            for ct in clank_times:
                if t >= ct:
                    clank_env += math.exp(-(t - ct) * 15)
            
            env = global_env * 0.3 + clank_env * 0.7
            
            sample_val = 0
            for f in freqs:
                # Add FM modulation to each frequency
                mod = math.sin(2 * math.pi * f * 0.5 * t) * 100
                sample_val += math.sin(2 * math.pi * (f + mod) * t)
                
            sample_val /= len(freqs)
            
            # Add some noise for the drag
            drag_noise = random.uniform(-1, 1) * math.exp(-t * 1.5) * 0.2
            
            sample = (sample_val * env + drag_noise) * 20000
            
            sample = max(-32768, min(32767, int(sample)))
            wav_file.writeframes(struct.pack('h', sample))

if __name__ == '__main__':
    generate_chain('/Users/kosta/SlotMachine/slot_engine/static/assets/audio/chain.wav')
