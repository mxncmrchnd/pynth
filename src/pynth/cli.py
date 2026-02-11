# libraries
import argparse
import os
from . import defaults, midi

# main function
def main():
    ## parse the arguments
    parser = argparse.ArgumentParser(description = "Reads a MIDI file and converts it to FLAC")
    parser.add_argument("input_midi", type = midi.check_midi_input_path, help = "The MIDI file to be read")
    parser.add_argument("output_flac", type = midi.check_flac_output, help = "The output FLAC")
    parser.add_argument("--waveform", choices = ["saw", "sine", "square", "triangle"], default = "sine", help = "The waveform type")
    parser.add_argument("--effect", choices = ["chorus", "delay", "reverb"], default = None, help = "The type of effect to be applied")
    args = parser.parse_args()
    ## build the paths
    midi_path = os.path.abspath(args.input_midi)
    output_path = os.path.abspath(args.output_flac)
    # call the synth function
    midi.midi_to_flac(midi_path, output_path, wf = args.waveform, fx = args.effect)