import numpy as np
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

