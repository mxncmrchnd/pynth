# libraries
import mido
import numpy as np
import soundfile as sf

# constants
SAMPLE_RATE = 44100
DEFAULT_TEMPO = 500000 # 120bpm, in microseconds per beat

# functions
def midi_to_flac(midi_in, file_out) : 
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
    audio = np.zeros(int(duration * SAMPLE_RATE))
    # rendering the notes
    for start, end, note, velocity in rendered_notes:
        start_i = int(start * SAMPLE_RATE)
        end_i = int(end * SAMPLE_RATE)
        t = np.linspace(0, end - start, end_i - start_i, endpoint = False)
        freq = 440.0 * 2 ** ((note-69)/12)
        wave = np.sin(2 * np.pi * freq * t)
        wave*= velocity / 127.0
        ## add a fade-in/out, to reduce clicking (10ms)
        fade_len = int(0.01 * SAMPLE_RATE)
        wave[:fade_len] *= np.linspace(0, 1, fade_len)
        wave[-fade_len:] *= np.linspace(1, 0, fade_len)
        ## add it to the audio
        audio[start_i:end_i] += wave
    # normalize the audio
    peak = np.max(np.abs(audio))
    if peak > 0 : 
        audio /= peak

    # write to file
    sf.write(file_out, audio, SAMPLE_RATE, format="FLAC")
    print(f"Rendered MIDI to {file_out}, containing {len(rendered_notes)} notes")