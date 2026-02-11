import numpy as np
from scipy.signal import fftconvolve, butter, filtfilt
from. import defaults

# delay
def apply_delay(audio, delay_time = 0.3, feedback = 0.5, mix = 0.3):
    delay_samples = int(delay_time * defaults.SAMPLE_RATE)
    output = np.copy(audio)
    delayed = np.zeros(len(audio) + delay_samples)
    delayed[:len(audio)] = audio
    for i in range(len(audio)):
        if i + delay_samples < len(delayed):
            delayed[i + delay_samples] += delayed[i] * feedback
    delayed = delayed[:len(audio)]
    output = audio * (1 - mix) + delayed * mix
    peak = np.max(np.abs(output))
    if peak > 1.0 :
        output /= peak
    return output

# reverb
def apply_reverb(audio, room_size=0.5, damping=0.5, mix=0.3):
    reverb_time = 0.5 + room_size * 2.0
    ir_length = int(reverb_time * defaults.SAMPLE_RATE)
    t = np.arange(ir_length) / defaults.SAMPLE_RATE
    decay = np.exp(-3 * t / reverb_time)
    noise = np.random.randn(ir_length)
    impulse = noise * decay
    if damping > 0:
        cutoff = 8000 * (1 - damping * 0.7)
        b, a = butter(2, cutoff / (defaults.SAMPLE_RATE / 2), 'low')
        impulse = filtfilt(b, a, impulse)
    impulse /= np.max(np.abs(impulse))
    wet = fftconvolve(audio, impulse, mode='full')
    wet = wet[:len(audio)]
    wet_peak = np.max(np.abs(wet))
    if wet_peak > 0:
        wet /= wet_peak
    result = audio * (1 - mix) + wet * mix
    peak = np.max(np.abs(result))
    if peak > 1.0:
        result /= peak   
    return result

