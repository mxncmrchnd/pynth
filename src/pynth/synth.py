# libraries
import mido
import numpy as np
import soundfile as sf
import os
import argparse
from scipy import signal

# constants
SAMPLE_RATE = 44100
DEFAULT_TEMPO = 500000 # 120bpm, in microseconds per beat
DEFAULT_ADSR = {
    'attack': 0.01,
    'decay': 0.1,
    'sustain': 0.7,
    'release': 0.2
}

# functions
## checks if MIDI input path is correct
def check_midi_input_path(path):
    if not os.path.isfile(path):
        raise argparse.ArgumentTypeError(f"File not found : {path}")
    if not path.lower().endswith(".mid"):
        raise argparse.ArgumentTypeError("Input must be a MIDI file")
    return path

## checks if the output is valid
def check_flac_output(path):
    if not path.lower().endswith(".flac"):
        raise argparse.ArgumentTypeError("Output must be a FLAC file")
    return path

## generates an adsr envelope
def generate_adsr(n_samples, attack, decay, sustain, release, sample_rate=SAMPLE_RATE):   
    ### edge case for notes with 0 length
    if n_samples == 0:
        return np.array([])
    envelope = np.zeros(n_samples)
    attack_samples = int(attack * sample_rate)
    decay_samples = int(decay * sample_rate)
    release_samples = int(release * sample_rate)
    ### checks total ADSR time
    total_adsr_samples = attack_samples + decay_samples + release_samples 
    ### proportional scaling if note is shorter than ADSR
    if total_adsr_samples > n_samples:
        scale_factor = n_samples / total_adsr_samples
        attack_samples = int(attack_samples * scale_factor)
        decay_samples = int(decay_samples * scale_factor)
        release_samples = int(release_samples * scale_factor)
        sustain_samples = 0
    else:
        sustain_samples = n_samples - attack_samples - decay_samples - release_samples
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

## reads MIDI file to numpy audio array
def midi_to_audio(midi_in, waveform = "sine", adsr = None) : 
    if adsr is None:
        adsr = DEFAULT_ADSR
    ## read the file
    mid = mido.MidiFile(midi_in)
    ## getting timing info
    tpb = mid.ticks_per_beat
    tempo = DEFAULT_TEMPO
    ## merge tracks
    all_messages = mido.merge_tracks(mid.tracks)
    ## tracking the MIDI state
    current_time = 0.0
    active_notes = {}
    rendered_notes = []

    ## parsing MIDI messages
    for msg in all_messages :
        ### convert time from ticks to seconds
        delta_sec = mido.tick2second(msg.time, tpb, tempo)
        current_time += delta_sec
        ### set the tempo if it receives a set_tempo message (usually start of the file)
        if msg.type == "set_tempo":
            tempo = msg.tempo
        ### if message = note_on (and positive velocity), register it
        elif msg.type == "note_on" and msg.velocity > 0:
            active_notes[msg.note] = (current_time, msg.velocity)
        ### if message = note_off or null velocity on note_on
        elif msg.type == "note_off" or (msg.type == "note_on" and msg.velocity == 0):
            if msg.note in active_notes :
                start, velocity = active_notes.pop(msg.note)
                rendered_notes.append((start, current_time, msg.note, velocity))

    ## if no rendered notes have been found : exit the function
    if not rendered_notes : 
        print("No notes found")
        return
    
    ## determining total duration
    duration = max(end for _, end, _, _ in rendered_notes)
    audio = np.zeros(int(duration * SAMPLE_RATE), dtype=np.float32)
    # rendering the notes
    for start, end, note, velocity in rendered_notes:
        start_i = int(start * SAMPLE_RATE)
        end_i = int(end * SAMPLE_RATE)
        n_samples = end_i - start_i
        t = np.linspace(0, end - start, end_i - start_i, endpoint = False)
        freq = 440.0 * 2 ** ((note-69)/12)
        wave = generate_waveform(freq, t, waveform)
        envelope = generate_adsr(n_samples, adsr['attack'], adsr['decay'], adsr['sustain'], adsr['release'])
        wave *= envelope
        wave *= velocity / 127.0
        ## add it to the audio
        audio[start_i:end_i] += wave
    # normalize the audio
    peak = np.max(np.abs(audio))
    if peak > 0 : 
        audio /= peak
    
    return audio, rendered_notes

## write to file
def audio_to_flac(audio, file_out):
    if audio is None:
        print("No audio to write")
        return
    sf.write(file_out, audio, SAMPLE_RATE, format="FLAC")
    print(f"Rendered MIDI to {file_out}, containing {len(audio)} samples")

## high level function
def midi_to_flac(midi_in, file_out, waveform="sine", adsr = None) : 
    audio, rendered_notes = midi_to_audio(midi_in, waveform = waveform, adsr = adsr)
    if audio is None : 
        return
    audio_to_flac(audio, file_out)
    print(f"File rendered to {file_out} with {len(rendered_notes)} notes")