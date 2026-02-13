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
    },
    'delay' : {
       'delay_time' : 0.375,
       'feedback' : 0.4,
       'mix' : 0.7
    },
    'reverb':{
       'room_size' : 0.8,
        'damping' : 0.3,
       'mix' : 0.5
    }
}
DEFAULT_OSCILLATORS = [
    {
        'enabled' : True,
        'waveform' : 'sine',
        'volume' : 1.0,
        'pitch' : 0
    },
    {
        'enabled' : False,
        'waveform' : 'sine',
        'volume' : 0.75,
        'pitch' : -12
    },
    {
        'enabled' : False,
        'waveform' : 'sine',
        'volume' : 0.5,
        'pitch' : -24
    }
]
DEFAULT_TEMPO = 500000 # 120bpm, in microseconds per beat
SAMPLE_RATE = 44100