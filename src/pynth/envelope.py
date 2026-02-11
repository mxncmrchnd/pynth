import numpy as np
from. import defaults

# creates the envelope
def generate_adsr(num_samples, attack, decay, sustain, release):
    if num_samples == 0:
        return np.array([]) 
    ## short notes : simple fade-in/out
    if num_samples < 10:
        envelope = np.linspace(0, 1, num_samples // 2 + 1)
        envelope = np.concatenate([envelope, np.linspace(1, 0, num_samples - len(envelope))])
        return envelope[:num_samples]
    
    note_duration = num_samples / defaults.SAMPLE_RATE
    attack_samples = int(attack * defaults.SAMPLE_RATE)
    decay_samples = int(decay * defaults.SAMPLE_RATE)
    release_samples = int(release * defaults.SAMPLE_RATE)   
    ## calculates total adsr time
    total_adsr_samples = attack_samples + decay_samples + release_samples
    total_adsr_time = total_adsr_samples / defaults.SAMPLE_RATE
    
    ## decision threshold: if note is longer than 1.5x the ADSR time, use fixed mode
    if note_duration > total_adsr_time * 1.5:
        ### FIXED MODE: use exact A/D/R times, sustain fills the rest
        sustain_samples = num_samples - total_adsr_samples
    else:
        ### PROPORTIONAL MODE: scale everything to fit the note
        if total_adsr_samples > num_samples:
            scale_factor = num_samples / total_adsr_samples
            attack_samples = max(1, int(attack_samples * scale_factor))
            decay_samples = max(1, int(decay_samples * scale_factor))
            release_samples = max(1, int(release_samples * scale_factor))
            sustain_samples = 0
        else:
            sustain_samples = num_samples - attack_samples - decay_samples - release_samples
    
    # builds the envelope
    envelope = np.zeros(num_samples)
    idx = 0   
    if attack_samples > 0:
        envelope[idx:idx + attack_samples] = np.linspace(0, 1, attack_samples)
        idx += attack_samples
    if decay_samples > 0:
        envelope[idx:idx + decay_samples] = np.linspace(1, sustain, decay_samples)
        idx += decay_samples
    if sustain_samples > 0:
        envelope[idx:idx + sustain_samples] = sustain
        idx += sustain_samples
    if release_samples > 0:
        if idx > 0:
            start_level = envelope[idx - 1]
        else:
            start_level = 0
        envelope[idx:idx + release_samples] = np.linspace(start_level, 0, release_samples)
    
    return envelope