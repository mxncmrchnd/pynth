# pynth

![Python Version](https://img.shields.io/badge/python-3.8%2B-blue)
![License](https://img.shields.io/github/license/mxncmrchnd/pynth)
![GitHub Release](https://img.shields.io/github/v/release/mxncmrchnd/pynth)
![Code Size](https://img.shields.io/github/languages/code-size/mxncmrchnd/pynth)

`pynth` is a small MIDI player made in python.
by Maxence Marchand, 2026

## Features

- Reading MIDI files (in single track mode)
- Choice of waveform : sine, saw, square or triangle
- ADSR envelope modification
- Multiple oscillators, with independent waveform, volume and pitch controls
- Effects : chorus, delay and reverb
- Amplitude and frequency modulation
- Highpass and lowpass filters
- Audio preview
- Export as FLAC

## How to run pynth

Open a terminal in the `pynth` folder and type :

`pip install -e .`

Then simply run :

`pynth` and play around.

![Oscillators](screenshot1.png)
![Effects](screenshot2.png)
![Filters](screenshot3.png)

## Versions changelog

- 1.0 : first release
- 1.1 : removed CLI, added multiple oscillators, GUI refinements
- 1.2 : reworked GUI : replaced previous tkinter GUI with CustomTkinter
- 1.3 : added amplitude modulation
- 1.4 : added frequency modulation

## Dependencies

- [`customtkinter`](https://customtkinter.tomschimansky.com/)
- [`mido`](https://mido.readthedocs.io/en/stable/)
- [`numpy`](https://numpy.org/)
- [`scipy`](https://scipy.org/)
- [`sounddevice`](https://python-sounddevice.readthedocs.io/en/0.5.3/)
- [`soundfile`](https://pypi.org/project/soundfile/)
