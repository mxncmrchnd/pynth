import numpy as np
from scipy import signal

## generates a waveform
def generate_waveform(freq, t, waveform="sine"):
    if waveform == "saw" :
        return signal.sawtooth(2 * np.pi * freq * t)
    elif waveform == "sine" : 
        return np.sin(2 * np.pi * freq * t)
    elif waveform == "square" : 
        return signal.square(2 * np.pi * freq * t)
    elif waveform == "triangle" : 
        return signal.sawtooth(2 * np.pi * freq * t, width = 0.5)
    else : 
        raise ValueError(f"Unknown wave type : {waveform}")