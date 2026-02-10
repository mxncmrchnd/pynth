# libraries
import argparse
import os
from .synth import midi_to_flac

# main function
def main():
    ## parse the arguments
    parser = argparse.ArgumentParser()
    parser.add_argument("input_midi")
    parser.add_argument("output_flac")
    args = parser.parse_args()
    ## build the paths
    midi_path = os.path.abspath(args.input_midi)
    output_path = os.path.abspath(args.output_flac)

    # call the synth function
    midi_to_flac(midi_path, output_path)