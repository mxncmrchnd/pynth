# libraries
import math
import customtkinter as ctk
from tkinter import filedialog, messagebox
import threading
from pathlib import Path
import sounddevice as sd

# import default values
from pynth.defaults import DEFAULT_ADSR, DEFAULT_EFFECTS, DEFAULT_AM_LFO, DEFAULT_FM_LFO, DEFAULT_OSCILLATORS, DEFAULT_FILTERS

# theme setup
ctk.set_appearance_mode("system")
ctk.set_default_color_theme("green")

# GUI class
class PynthGUI(ctk.CTk):
    def __init__(self):
        super().__init__()
        # window configuration
        self.title("Pynth - MIDI to Audio synthesizer")
        sw = self.winfo_screenwidth()
        sh = self.winfo_screenheight()
        self.geometry(f"{int(sw*0.7)}x{int(sh*0.7)}")
        self.resizable(False, False)
        # variables
        ## I/O paths
        self.midi_path = ctk.StringVar()
        self.output_path = ctk.StringVar()
        ## oscillators
        self.osc_enabled = [ctk.BooleanVar(value=o["enabled"]) for o in DEFAULT_OSCILLATORS]
        self.osc_waveform = [ctk.StringVar(value=o["waveform"]) for o in DEFAULT_OSCILLATORS]
        self.osc_volume = [ctk.DoubleVar(value=o["volume"]) for o in DEFAULT_OSCILLATORS]
        self.osc_pitch = [ctk.IntVar(value=o["pitch"]) for o in DEFAULT_OSCILLATORS]
        ## ADSR envelope
        self.attack = ctk.DoubleVar(value=DEFAULT_ADSR["attack"])
        self.decay = ctk.DoubleVar(value=DEFAULT_ADSR["decay"])
        self.sustain = ctk.DoubleVar(value=DEFAULT_ADSR["sustain"])
        self.release = ctk.DoubleVar(value=DEFAULT_ADSR["release"])
        ## AM LFO values
        self.am_lfo_enabled = ctk.BooleanVar(value=DEFAULT_AM_LFO['enabled'])
        self.am_lfo_rate = ctk.DoubleVar(value=DEFAULT_AM_LFO['rate'])
        self.am_lfo_amplitude = ctk.DoubleVar(value=DEFAULT_AM_LFO['amplitude'])
        self.am_lfo_waveform = ctk.StringVar(value=DEFAULT_AM_LFO['waveform'])
        ## FM LFO values
        self.fm_lfo_enabled = ctk.BooleanVar(value=DEFAULT_FM_LFO['enabled'])
        self.fm_lfo_rate = ctk.DoubleVar(value=DEFAULT_FM_LFO['rate'])
        self.fm_lfo_depth = ctk.DoubleVar(value=DEFAULT_FM_LFO['depth'])
        self.fm_lfo_waveform = ctk.StringVar(value=DEFAULT_FM_LFO['waveform'])
        ## effects
        ### status
        self.delay_enabled = ctk.BooleanVar(value=False)
        self.reverb_enabled = ctk.BooleanVar(value=False)
        self.chorus_enabled = ctk.BooleanVar(value=False)
        ### delay
        self.delay_time = ctk.DoubleVar(value=DEFAULT_EFFECTS["delay"]["delay_time"])
        self.delay_feedback = ctk.DoubleVar(value=DEFAULT_EFFECTS["delay"]["feedback"])
        self.delay_mix = ctk.DoubleVar(value=DEFAULT_EFFECTS["delay"]["mix"])
        ### reverb
        self.reverb_room = ctk.DoubleVar(value=DEFAULT_EFFECTS["reverb"]["room_size"])
        self.reverb_damp = ctk.DoubleVar(value=DEFAULT_EFFECTS["reverb"]["damping"])
        self.reverb_mix = ctk.DoubleVar(value=DEFAULT_EFFECTS["reverb"]["mix"])
        ### chorus
        self.chorus_rate = ctk.DoubleVar(value=DEFAULT_EFFECTS["chorus"]["rate"])
        self.chorus_depth = ctk.DoubleVar(value=DEFAULT_EFFECTS["chorus"]["depth"])
        self.chorus_mix = ctk.DoubleVar(value=DEFAULT_EFFECTS["chorus"]["mix"])
        ## filters
        self.lp_enabled = ctk.BooleanVar(value=DEFAULT_FILTERS['lowpass']['enabled'])
        self.lp_cutoff  = ctk.DoubleVar(value=DEFAULT_FILTERS['lowpass']['cutoff'])
        self.lp_order   = ctk.IntVar(value=DEFAULT_FILTERS['lowpass']['order'])
        self.hp_enabled = ctk.BooleanVar(value=DEFAULT_FILTERS['highpass']['enabled'])
        self.hp_cutoff  = ctk.DoubleVar(value=DEFAULT_FILTERS['highpass']['cutoff'])
        self.hp_order   = ctk.IntVar(value=DEFAULT_FILTERS['highpass']['order'])
        ## status and preview audio
        self.status = ctk.StringVar(value="Ready")
        self.preview_audio = None
        # call to build the UI
        self.build_ui()

    # building the UI
    def build_ui(self):
        # grid configuration
        self.grid_rowconfigure(0, weight=1)
        self.grid_rowconfigure(1, weight=0)
        self.grid_columnconfigure(0, weight=1)
        # top frame : oscillators, envelope, effects and filters
        top = ctk.CTkFrame(self)
        top.grid(row=0, column=0, sticky="nsew", padx=10, pady=10)
        tabs = ctk.CTkTabview(top)
        tabs.pack(fill="both", expand=True)
        osc_env_tab = tabs.add("Oscillators & Envelope")
        fx_tab = tabs.add("Effects")
        filter_tab = tabs.add("Filters")
        self.build_osc_env(osc_env_tab)
        self.build_effects(fx_tab)
        self.build_filters(filter_tab)
        # bottom frame : file selection and preview/export
        bottom = ctk.CTkFrame(self)
        bottom.grid(row=1, column=0, sticky="ew", padx=10, pady=(0, 10))
        bottom.grid_columnconfigure(0, weight=1)
        bottom.grid_columnconfigure(1, weight=1)
        self.build_files(bottom)
        self.build_actions(bottom)

    # build the osc/env tab
    def build_osc_env(self, parent):
        parent.grid_columnconfigure(0, weight=1)
        parent.grid_columnconfigure(1, weight=1)
        # left side : oscillators
        osc_frame = ctk.CTkFrame(parent)
        osc_frame.grid(row=0, column=0, sticky="nsew", padx=10, pady=10)
        osc_tabs = ctk.CTkTabview(osc_frame)
        osc_tabs.pack(fill="both", expand=True)
        self.osc_control_frames = []
        for i in range(3):
            tab = osc_tabs.add(f"Oscillator {i+1}")
            frame = self.build_single_oscillator(tab, i)
            self.osc_control_frames.append(frame)
            if i > 0:
                self.osc_enabled[i].trace_add("write", lambda *_, idx=i: self.update_osc_state(idx))
        # right side : envelope
        right_frame = ctk.CTkFrame(parent)
        right_frame.grid(row=0, column=1, sticky="nsew", padx=10, pady=10)
        right_tabs = ctk.CTkTabview(right_frame)
        right_tabs.pack(fill="both", expand=True)
        env_tab = right_tabs.add("Envelope")
        am_tab = right_tabs.add("AM")
        fm_tab = right_tabs.add("FM")
        self.build_envelope(env_tab)
        self.build_am(am_tab)
        self.build_fm(fm_tab)
        for i in range(1, 3):
            self.update_osc_state(i)

    # build oscillator window
    def build_single_oscillator(self, parent, i):
        container = ctk.CTkFrame(parent)
        container.pack(expand=True)
        ## for oscillators 2 and 3
        if i > 0:
            ctk.CTkCheckBox(container, text="Enabled", variable=self.osc_enabled[i]).pack(pady=10)
        controls = ctk.CTkFrame(container)
        controls.pack()
        wf = ctk.CTkFrame(controls)
        wf.pack(pady=10)
        buttons = []
        for text, val in [
            ("Sine", "sine"),
            ("Saw", "saw"),
            ("Square", "square"),
            ("Triangle", "triangle"),
        ]:
            b = ctk.CTkRadioButton(wf, text=text, variable=self.osc_waveform[i], value=val)
            b.pack(side="left", padx=10)
            buttons.append(b)
        vol = self.labeled_slider(controls, "Volume", self.osc_volume[i], 0, 1, "%", percent=True)
        pitch = self.labeled_slider(controls, "Pitch", self.osc_pitch[i], -24, 24, "st", signed=True)
        return {
            "frame": controls,
            "widgets": buttons + vol + pitch
        }

    # update oscillators states
    def update_osc_state(self, i):
        enabled = self.osc_enabled[i].get()
        state = "normal" if enabled else "disabled"
        data = self.osc_control_frames[i]
        for w in data["widgets"]:
            w.configure(state=state)
        data["frame"].configure(fg_color=("gray85", "gray25") if enabled else ("gray75", "gray15"))

    # build envelope tab
    def build_envelope(self, parent):
        frame = ctk.CTkFrame(parent)
        frame.pack(expand=True, padx=10, pady=10)
        ctk.CTkLabel(frame, text="ADSR Envelope", font=ctk.CTkFont(size=16, weight="bold")).pack(pady=(10, 20))
        sliders = ctk.CTkFrame(frame)
        sliders.pack()
        self.vertical_slider(sliders, "Attack", self.attack, 0.001, 2, "s")
        self.vertical_slider(sliders, "Decay", self.decay, 0.001, 2, "s")
        self.vertical_slider(sliders, "Sustain", self.sustain, 0, 1, "")
        self.vertical_slider(sliders, "Release", self.release, 0.001, 3, "s")

    # build AM tab
    def build_am(self, parent):
        frame = ctk.CTkFrame(parent)
        frame.pack(expand=True, padx=10, pady=10)
        ctk.CTkLabel(frame, text="Amplitude Modulation", font=ctk.CTkFont(size=16, weight="bold")).pack(pady=(10, 5))
        ctk.CTkCheckBox(frame, text="Enabled", variable=self.am_lfo_enabled).pack(pady=(0, 10))
        content = ctk.CTkFrame(frame)
        content.pack()
        ## LFO waveform selection
        wf_frame = ctk.CTkFrame(content)
        wf_frame.pack(side="left", padx=(10, 20), pady=10)
        ctk.CTkLabel(wf_frame, text="Waveform").pack(pady=(5, 6))
        self.am_lfo_wf_buttons = []
        for text, val in [("Sine", "sine"), ("Saw", "saw"), ("Square", "square"), ("Triangle", "triangle")]:
            b = ctk.CTkRadioButton(wf_frame, text=text, variable=self.am_lfo_waveform, value=val)
            b.pack(anchor="w", pady=4)
            self.am_lfo_wf_buttons.append(b)
        sliders = ctk.CTkFrame(content)
        sliders.pack(side="left", pady=10)
        ## rate slider (beat-synced)
        BEAT_VALUES = [1/64, 1/32, 1/16, 1/8, 1/4, 1/2, 1.0]
        BEAT_LABELS = ["1/64", "1/32", "1/16", "1/8", "1/4", "1/2", "1"]
        self.am_lfo_rate_idx = ctk.IntVar(value=BEAT_VALUES.index(min(BEAT_VALUES, key=lambda x: abs(x - self.am_lfo_rate.get()))))
        rate_frame = ctk.CTkFrame(sliders)
        rate_frame.pack(pady=10)
        ctk.CTkLabel(rate_frame, text="Rate").pack()
        rate_slider = ctk.CTkSlider(rate_frame, from_=0, to=6, number_of_steps=6, variable=self.am_lfo_rate_idx, width=250)
        rate_slider.pack()
        rate_label = ctk.CTkLabel(rate_frame, text="")
        rate_label.pack()
        def update_rate(*_):
            idx = int(round(self.am_lfo_rate_idx.get()))
            self.am_lfo_rate.set(BEAT_VALUES[idx])
            rate_label.configure(text=f"{BEAT_LABELS[idx]} beat")
        self.am_lfo_rate_idx.trace_add("write", update_rate)
        update_rate()
        ## depth slider
        depth_slider = self.labeled_slider(sliders, "Depth", self.am_lfo_amplitude, 0.1, 1.0, "%", percent=True)[0]
        ## disabling sliders when AM disabled
        self.am_lfo_widgets = [rate_slider, depth_slider] + self.am_lfo_wf_buttons
        def update_lfo_state(*_):
            state = "normal" if self.am_lfo_enabled.get() else "disabled"
            for w in self.am_lfo_widgets:
                w.configure(state=state)
        self.am_lfo_enabled.trace_add("write", update_lfo_state)
        update_lfo_state()

    # build FM tab
    def build_fm(self, parent):
        frame = ctk.CTkFrame(parent)
        frame.pack(expand=True, padx=10, pady=10)
        ctk.CTkLabel(frame, text="Frequency Modulation", font=ctk.CTkFont(size=16, weight="bold")).pack(pady=(10, 5))
        ctk.CTkCheckBox(frame, text="Enabled", variable=self.fm_lfo_enabled).pack(pady=(0, 10))
        content = ctk.CTkFrame(frame)
        content.pack()
        ## LFO waveform selection
        wf_frame = ctk.CTkFrame(content)
        wf_frame.pack(side="left", padx=(10, 20), pady=10)
        ctk.CTkLabel(wf_frame, text="Waveform").pack(pady=(5, 6))
        self.fm_lfo_wf_buttons = []
        for text, val in [("Sine", "sine"), ("Saw", "saw"), ("Square", "square"), ("Triangle", "triangle")]:
            b = ctk.CTkRadioButton(wf_frame, text=text, variable=self.fm_lfo_waveform, value=val)
            b.pack(anchor="w", pady=4)
            self.fm_lfo_wf_buttons.append(b)
        sliders = ctk.CTkFrame(content)
        sliders.pack(side="left", pady=10)
        ## rate slider (beat-synced, same as AM)
        BEAT_VALUES = [1/64, 1/32, 1/16, 1/8, 1/4, 1/2, 1.0]
        BEAT_LABELS = ["1/64", "1/32", "1/16", "1/8", "1/4", "1/2", "1"]
        self.fm_lfo_rate_idx = ctk.IntVar(value=BEAT_VALUES.index(min(BEAT_VALUES, key=lambda x: abs(x - self.fm_lfo_rate.get()))))
        rate_frame = ctk.CTkFrame(sliders)
        rate_frame.pack(pady=10)
        ctk.CTkLabel(rate_frame, text="Rate").pack()
        rate_slider = ctk.CTkSlider(rate_frame, from_=0, to=6, number_of_steps=6, variable=self.fm_lfo_rate_idx, width=250)
        rate_slider.pack()
        rate_label = ctk.CTkLabel(rate_frame, text="")
        rate_label.pack()
        def update_fm_rate(*_):
            idx = int(round(self.fm_lfo_rate_idx.get()))
            self.fm_lfo_rate.set(BEAT_VALUES[idx])
            rate_label.configure(text=f"{BEAT_LABELS[idx]} beat")
        self.fm_lfo_rate_idx.trace_add("write", update_fm_rate)
        update_fm_rate()
        ## depth slider (0 to 200 Hz)
        depth_slider = self.labeled_slider(sliders, "Depth", self.fm_lfo_depth, 0.1, 200.0, "Hz")[0]
        ## disabling sliders when FM disabled
        self.fm_lfo_widgets = [rate_slider, depth_slider] + self.fm_lfo_wf_buttons
        def update_fm_state(*_):
            state = "normal" if self.fm_lfo_enabled.get() else "disabled"
            for w in self.fm_lfo_widgets:
                w.configure(state=state)
        self.fm_lfo_enabled.trace_add("write", update_fm_state)
        update_fm_state()

    # build the effects tab
    def build_effects(self, parent):
        parent.grid_columnconfigure((0, 1, 2), weight=1)
        self.effect_block(parent, "Delay",
            self.delay_enabled,
            [
                ("Time", self.delay_time, 0.01, 2, "s"),
                ("Feedback", self.delay_feedback, 0, 0.95, "%", True),
                ("Mix", self.delay_mix, 0, 1, "%", True),
            ],
            0
        )
        self.effect_block(parent, "Reverb",
            self.reverb_enabled,
            [
                ("Room", self.reverb_room, 0, 1, "%", True),
                ("Damp", self.reverb_damp, 0, 1, "%", True),
                ("Mix", self.reverb_mix, 0, 1, "%", True),
            ],
            1
        )
        self.effect_block(parent, "Chorus",
            self.chorus_enabled,
            [
                ("Rate", self.chorus_rate, 0.1, 5, "Hz"),
                ("Depth", self.chorus_depth, 0.0001, 0.01, ""),
                ("Mix", self.chorus_mix, 0, 1, "%", True),
            ],
            2
        )

    # build a single effect block
    def effect_block(self, parent, name, enabled_var, sliders, column):
        frame = ctk.CTkFrame(parent)
        frame.grid(row=0, column=column, padx=20, pady=20)
        ctk.CTkCheckBox(frame, text=name, variable=enabled_var).pack(pady=10)
        cont = ctk.CTkFrame(frame)
        cont.pack()
        for data in sliders:
            if len(data) == 5:
                label, var, mn, mx, unit = data
                percent = False
            else:
                label, var, mn, mx, unit, percent = data
            self.vertical_slider(cont, label, var, mn, mx, unit, percent)

    # log-scale helpers for filter frequency sliders
    @staticmethod
    def _freq_to_pos(freq, f_min=20.0, f_max=20000.0):
        return math.log(freq / f_min) / math.log(f_max / f_min)

    @staticmethod
    def _pos_to_freq(pos, f_min=20.0, f_max=20000.0):
        return f_min * (f_max / f_min) ** pos

    # build the filters tab
    def build_filters(self, parent):
        parent.grid_columnconfigure(0, weight=1)
        parent.grid_columnconfigure(1, weight=1)
        lp_info = self._filter_block(
            parent, "Low-pass",  self.lp_enabled, self.lp_cutoff, self.lp_order,
            from_freq=DEFAULT_FILTERS['highpass']['cutoff'], to_freq=20000, column=0
        )
        hp_info = self._filter_block(
            parent, "High-pass", self.hp_enabled, self.hp_cutoff, self.hp_order,
            from_freq=20, to_freq=DEFAULT_FILTERS['lowpass']['cutoff'], column=1
        )
        self._lp_slider = lp_info['slider']
        self._hp_slider = hp_info['slider']
        # cross-constrain in log-position space
        def on_hp_change(*_):
            self._lp_slider.configure(from_=self._freq_to_pos(self.hp_cutoff.get()))
        def on_lp_change(*_):
            self._hp_slider.configure(to=self._freq_to_pos(self.lp_cutoff.get()))
        self.hp_cutoff.trace_add("write", on_hp_change)
        self.lp_cutoff.trace_add("write", on_lp_change)

    # build a single filter block
    def _filter_block(self, parent, name, enabled_var, cutoff_var, order_var, from_freq, to_freq, column):
        frame = ctk.CTkFrame(parent)
        frame.grid(row=0, column=column, padx=30, pady=20, sticky="n")
        ctk.CTkCheckBox(frame, text=name, variable=enabled_var).pack(pady=(10, 6))
        # frequency slider (log scale: internal position 0.0–1.0)
        pos_var = ctk.DoubleVar(value=self._freq_to_pos(cutoff_var.get()))
        ctk.CTkLabel(frame, text="Frequency").pack()
        freq_slider = ctk.CTkSlider(
            frame,
            from_=self._freq_to_pos(from_freq),
            to=self._freq_to_pos(to_freq),
            variable=pos_var,
            width=220
        )
        freq_slider.pack(pady=(2, 0))
        freq_val = ctk.CTkLabel(frame, text="")
        freq_val.pack()
        def on_pos_change(*_):
            freq = self._pos_to_freq(pos_var.get())
            cutoff_var.set(freq)
            freq_val.configure(text=f"{freq/1000:.1f} kHz" if freq >= 1000 else f"{freq:.0f} Hz")
        pos_var.trace_add("write", on_pos_change)
        on_pos_change()
        # order / slope slider
        ctk.CTkLabel(frame, text="Slope").pack(pady=(12, 0))
        order_slider = ctk.CTkSlider(frame, from_=1, to=8, number_of_steps=7, variable=order_var, width=220)
        order_slider.pack(pady=(2, 0))
        slope_val = ctk.CTkLabel(frame, text="")
        slope_val.pack()
        def update_slope(*_):
            o = order_var.get()
            slope_val.configure(text=f"{o * 12} dB/oct  (order {o})")
        order_var.trace_add("write", update_slope)
        update_slope()
        # disable both sliders when filter is off
        def update_state(*_):
            state = "normal" if enabled_var.get() else "disabled"
            freq_slider.configure(state=state)
            order_slider.configure(state=state)
        enabled_var.trace_add("write", update_state)
        update_state()
        return {'slider': freq_slider, 'pos_var': pos_var}

    # build the file selection frame
    def build_files(self, parent):
        frame = ctk.CTkFrame(parent)
        frame.grid(row=0, column=0, sticky="ew", padx=10, pady=10)
        ctk.CTkLabel(frame, text="MIDI Input").grid(row=0, column=0, sticky="w")
        ctk.CTkEntry(frame, textvariable=self.midi_path, width=300).grid(row=0, column=1, padx=5)
        ctk.CTkButton(frame, text="Browse", command=self.browse_midi).grid(row=0, column=2)
        ctk.CTkLabel(frame, text="Output").grid(row=1, column=0, sticky="w")
        ctk.CTkEntry(frame, textvariable=self.output_path, width=300).grid(row=1, column=1, padx=5)
        ctk.CTkButton(frame, text="Browse", command=self.browse_output).grid(row=1, column=2)

    # build the actions frame
    def build_actions(self, parent):
        frame = ctk.CTkFrame(parent)
        frame.grid(row=0, column=1, sticky="ew", padx=10, pady=10)
        btn_frame = ctk.CTkFrame(frame, fg_color="transparent")
        btn_frame.pack(pady=(5, 2))
        ctk.CTkButton(btn_frame, text="Preview", command=self.preview_audio_action).pack(side="left", padx=5)
        ctk.CTkButton(btn_frame, text="Stop", command=self.stop_audio).pack(side="left", padx=5)
        ctk.CTkButton(btn_frame, text="Render & Export", command=self.render_audio).pack(side="left", padx=5)
        ctk.CTkLabel(frame, textvariable=self.status).pack(pady=(4, 6))

    # build sliders
    ## labeled slider
    def labeled_slider(self, parent, text, var, minv, maxv, unit="", signed=False, percent=False):
        frame = ctk.CTkFrame(parent)
        frame.pack(pady=10)
        ctk.CTkLabel(frame, text=text).pack()
        slider = ctk.CTkSlider(frame, from_=minv, to=maxv, variable=var, width=250)
        slider.pack()
        value_label = ctk.CTkLabel(frame, text="")
        value_label.pack()
        def update(*_):
            v = var.get()
            if percent:
                txt = f"{v*100:.0f} %"
            elif signed:
                txt = f"{v:+.0f} {unit}"
            else:
                txt = f"{v:.2f} {unit}"
            value_label.configure(text=txt)
        var.trace_add("write", update)
        update()
        return [slider]

    ## vertical slider
    def vertical_slider(self, parent, text, var, minv, maxv, unit="", percent=False):
        frame = ctk.CTkFrame(parent)
        frame.pack(side="left", padx=20, pady=10)
        ctk.CTkLabel(frame, text=text).pack()
        slider = ctk.CTkSlider(frame, orientation="vertical", from_=minv, to=maxv, variable=var, height=180)
        slider.pack()
        value_label = ctk.CTkLabel(frame, text="")
        value_label.pack()
        def update(*_):
            v = var.get()
            if percent:
                txt = f"{v*100:.0f} %"
            else:
                txt = f"{v:.2f} {unit}"
            value_label.configure(text=txt)
        var.trace_add("write", update)
        update()
        return slider

    # build file dialogs
    ## input
    def browse_midi(self):
        f = filedialog.askopenfilename(filetypes=[("MIDI", "*.mid")])
        if f:
            self.midi_path.set(f)
            if not self.output_path.get():
                self.output_path.set(str(Path(f).with_suffix(".flac")))

    ## output
    def browse_output(self):
        f = filedialog.asksaveasfilename(defaultextension=".flac")
        if f:
            self.output_path.set(f)

    # parameters getter
    def get_parameters(self):
        ## ADSR envelope
        adsr = dict(attack=self.attack.get(), decay=self.decay.get(), sustain=self.sustain.get(), release=self.release.get())
        ## effects
        effects = {}
        if self.delay_enabled.get():
            effects["delay"] = dict(delay_time=self.delay_time.get(), feedback=self.delay_feedback.get(), mix=self.delay_mix.get())
        if self.reverb_enabled.get():
            effects["reverb"] = dict(room_size=self.reverb_room.get(), damping=self.reverb_damp.get(), mix=self.reverb_mix.get())
        if self.chorus_enabled.get():
            effects["chorus"] = dict(rate=self.chorus_rate.get(), depth=self.chorus_depth.get(), mix=self.chorus_mix.get())
        ## oscillators
        oscillators = []
        for i in range(3):
            oscillators.append(dict(enabled=self.osc_enabled[i].get(), waveform=self.osc_waveform[i].get(), volume=self.osc_volume[i].get(), pitch=self.osc_pitch[i].get()))
        ## AM LFO
        am_lfo = dict(enabled=self.am_lfo_enabled.get(), rate=self.am_lfo_rate.get(), amplitude=self.am_lfo_amplitude.get(), waveform=self.am_lfo_waveform.get())
        ## FM LFO
        fm_lfo = dict(enabled=self.fm_lfo_enabled.get(), rate=self.fm_lfo_rate.get(), depth=self.fm_lfo_depth.get(), waveform=self.fm_lfo_waveform.get())
        ## filters
        filters = {
            'lowpass':  dict(enabled=self.lp_enabled.get(), cutoff=self.lp_cutoff.get(), order=self.lp_order.get()),
            'highpass': dict(enabled=self.hp_enabled.get(), cutoff=self.hp_cutoff.get(), order=self.hp_order.get()),
        }
        return adsr, effects, oscillators, am_lfo, fm_lfo, filters

    # preview audio
    def preview_audio_action(self):
        if not self.midi_path.get():
            messagebox.showerror("Error", "Select MIDI file")
            return
        def worker():
            try:
                from pynth.midi import midi_to_audio
                self.status.set("Generating preview...")
                adsr, fx, osc, am_lfo, fm_lfo, filters = self.get_parameters()
                audio, _ = midi_to_audio(self.midi_path.get(), adsr=adsr, fx=fx if fx else None, osc=osc, am_lfo=am_lfo, fm_lfo=fm_lfo, filters=filters)
                self.preview_audio = audio
                self.status.set("Playing...")
                sd.play(audio, 44100)
                sd.wait()
                self.status.set("Done")
            except Exception as e:
                messagebox.showerror("Error", str(e))
                self.status.set("Error")
        threading.Thread(target=worker, daemon=True).start()

    # stop the preview
    def stop_audio(self):
        sd.stop()
        self.status.set("Stopped")

    # render audio
    def render_audio(self):
        if not self.midi_path.get() or not self.output_path.get():
            messagebox.showerror("Error", "Missing paths")
            return
        def worker():
            try:
                from pynth.midi import midi_to_flac
                self.status.set("Rendering...")
                adsr, fx, osc, am_lfo, fm_lfo, filters = self.get_parameters()
                midi_to_flac(self.midi_path.get(), self.output_path.get(), adsr=adsr, fx=fx if fx else None, osc=osc, am_lfo=am_lfo, fm_lfo=fm_lfo, filters=filters)
                self.status.set("Done")
            except Exception as e:
                messagebox.showerror("Error", str(e))
                self.status.set("Error")
        threading.Thread(target=worker, daemon=True).start()


# main function
def main():
    app = PynthGUI()
    app.mainloop()

if __name__ == "__main__":
    main()