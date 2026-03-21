import numpy as np
from scipy.signal import butter, filtfilt
from . import defaults

def apply_lowpass(audio, cutoff = 5000.0, order = 4) :
    nyq = defaults.SAMPLE_RATE / 2
    cutoff = np.clip(cutoff, 20.0, nyq - 1.0)
    b, a = butter(order, cutoff / nyq, btype = 'low')
    return filtfilt(b, a, audio).astype(np.float32)

def apply_highpass(audio, cutoff = 200.0, order = 4):
    nyq = defaults.SAMPLE_RATE / 2
    cutoff = np.clip(cutoff, 20.0, nyq - 1.0)
    b, a = butter(order, cutoff / nyq, btype = 'high')
    return filtfilt(b, a, audio).astype(np.float32)