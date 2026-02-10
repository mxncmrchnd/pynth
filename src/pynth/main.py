# libraries
import argparse
import os
from .synth import check_midi_input_path, check_flac_output, midi_to_flac

# main function
def main():
    ## parse the arguments
    parser = argparse.ArgumentParser(description = "Reads a MIDI file and converts it to FLAC")
    parser.add_argument("input_midi", type = check_midi_input_path, help = "The MIDI file to be read")
    parser.add_argument("output_flac", type = check_flac_output, help = "The output FLAC")
    parser.add_argument("--waveform", choices = ["saw", "sine", "square", "triangle"], default = "sine", help = "The waveform type")
    args = parser.parse_args()
    ## build the paths
    midi_path = os.path.abspath(args.input_midi)
    output_path = os.path.abspath(args.output_flac)

    # call the synth function
    midi_to_flac(midi_path, output_path, waveform = args.waveform)