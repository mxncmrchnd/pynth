# pynth
## by Maxence Marchand, 2026
`pynth` is a small MIDI player made in python.

## Features
- reads a MIDI file input
- plays it as a sinwave
- exports it as FLAC

## Future features
- selection of the wave type
- basic ADSR envelope
- effects (reverb, delay)
- realtime reading of MIDI input

## How to run it
Open a terminal in the `pynth` folder and type : 
``` pip install -e .```
Then simply run : 
``` pynth input.mid output.flac ```

## Dependencies
- `mido`
- `soundfile`
- `numpy` 
