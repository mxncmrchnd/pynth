# libraries
import mido
import numpy as np
import soundfile as sf
import os
import argparse
from . import defaults, effects, envelope, waveform

# checks if MIDI input path is correct
def check_midi_input_path(path):
    if not os.path.isfile(path):
        raise argparse.ArgumentTypeError(f"File not found : {path}")
    if not path.lower().endswith(".mid"):
        raise argparse.ArgumentTypeError("Input must be a MIDI file")
    return path

# checks if the output is valid
def check_flac_output(path):
    if not path.lower().endswith(".flac"):
        raise argparse.ArgumentTypeError("Output must be a FLAC file")
    return path

# reads MIDI file to numpy audio array
def midi_to_audio(midi_in, wf = "sine", adsr = None, fx = None) : 
    if adsr is None:
        adsr = defaults.DEFAULT_ADSR
    ## read the file
    mid = mido.MidiFile(midi_in)
    ## getting timing info
    tpb = mid.ticks_per_beat
    tempo = defaults.DEFAULT_TEMPO
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
    audio = np.zeros(int(duration * defaults.SAMPLE_RATE), dtype=np.float32)
    # rendering the notes
    for start, end, note, velocity in rendered_notes:
        start_i = int(start * defaults.SAMPLE_RATE)
        end_i = int(end * defaults.SAMPLE_RATE)
        n_samples = end_i - start_i
        t = np.linspace(0, end - start, end_i - start_i, endpoint = False)
        freq = 440.0 * 2 ** ((note-69)/12)
        wave = waveform.generate_waveform(freq, t, wf)
        envlp = envelope.generate_adsr(n_samples, adsr['attack'], adsr['decay'], adsr['sustain'], adsr['release'])
        wave *= envlp
        wave *= velocity / 127.0
        ## add it to the audio
        audio[start_i:end_i] += wave
    # normalize the audio
    peak = np.max(np.abs(audio))
    if peak > 0 : 
        audio /= peak
    
    # effects
    if fx :
        if 'chorus' in fx :
            params = fx['chorus']
            audio = effects.apply_chorus(audio, **params)
        if 'delay' in fx :
            params = fx['delay']
            audio = effects.apply_delay(audio, **params)
        if 'reverb' in fx:
            params = fx['reverb']
            audio = effects.apply_reverb(audio, **params)
    
    return audio, rendered_notes

## write to file
def audio_to_flac(audio, file_out):
    if audio is None:
        print("No audio to write")
        return
    sf.write(file_out, audio, defaults.SAMPLE_RATE, format="FLAC")
    print(f"Rendered MIDI to {file_out}, containing {len(audio)} samples")

## high level function
def midi_to_flac(midi_in, file_out, wf="sine", adsr = None, fx = None) : 
    audio, rendered_notes = midi_to_audio(midi_in, wf = wf, adsr = adsr, fx = fx)
    if audio is None : 
        return
    audio_to_flac(audio, file_out)
    print(f"File rendered to {file_out} with {len(rendered_notes)} notes")