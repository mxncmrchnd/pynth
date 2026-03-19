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

## generates a waveform with frequency modulation
def generate_waveform_fm(freq, t, modulator_signal, fm_depth, waveform="sine"):
    dt = t[1] - t[0] if len(t) > 1 else 1.0 / 44100
    phase_deviation = fm_depth * np.cumsum(modulator_signal) * dt
    phase = 2 * np.pi * freq * t + 2 * np.pi * phase_deviation
    if waveform == "sine" :
        return np.sin(phase)
    elif waveform == "saw" :
        return signal.sawtooth(phase)
    elif waveform == "square" :
        return signal.square(phase)
    elif waveform == "triangle" :
        return signal.sawtooth(phase, width = 0.5)
    else :
        raise ValueError(f"Unknown wave type : {waveform}")