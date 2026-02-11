# pynth
## by Maxence Marchand, 2026
`pynth` is a small MIDI player made in python.

## Features
- reads a MIDI file input
- able to play saw, sine, square or triangle waves
- ADSR envelope (for now only being in code, can't be changed through arguments)
- effects (chorus, delay, reverb)
- exports it as FLAC

## Future features
- GUI
- realtime reading of MIDI input

## How to run it
Open a terminal in the `pynth` folder and type : 

``` pip install -e .```

Then simply run : 

``` pynth input.mid output.flac ```

It generates a sinewave by default. For other waveforms, simply run :

``` pynth input.mid output.flac --waveform saw ```

## Dependencies
- `mido`
- `numpy` 
- `scipy`
- `soundfile`

