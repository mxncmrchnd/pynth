# defaults
DEFAULT_ADSR = {
    'attack': 0.01,
    'decay': 0.3,
    'sustain': 0.0,
    'release': 0.3
}
DEFAULT_EFFECTS = {
    'chorus' : {
        'rate' : 1.5,
        'depth' : 0.002,
        'mix' : 0.4
    }
    #'delay' : {
    #   'delay_time' : 0.375,
    #   'feedback' : 0.4,
    #   'mix' : 0.3
    #},
    #'reverb':{
    #   'room_size' : 0.8,
    #    'damping' : 0.3,
    #   'mix' : 0.5
    #}
}
DEFAULT_TEMPO = 500000 # 120bpm, in microseconds per beat
SAMPLE_RATE = 44100