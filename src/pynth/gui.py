# libraries
import customtkinter as ctk
from tkinter import filedialog, messagebox
import threading
from pathlib import Path
import sounddevice as sd

# import default values
from pynth.defaults import DEFAULT_ADSR, DEFAULT_EFFECTS, DEFAULT_OSCILLATORS

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
        self.geometry(f"{int(sw*0.7)}x{int(sh*0.6)}")
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
        # top frame : oscillators, envelope and effects
        top = ctk.CTkFrame(self)
        top.grid(row=0, column=0, sticky="nsew", padx=10, pady=10)
        tabs = ctk.CTkTabview(top)
        tabs.pack(fill="both", expand=True)
        osc_env_tab = tabs.add("Oscillators & Envelope")
        fx_tab = tabs.add("Effects")
        self.build_osc_env(osc_env_tab)
        self.build_effects(fx_tab)
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
                self.osc_enabled[i].trace_add("write", lambda *_, idx = i: self.update_osc_state(idx))
        # right side : envelope
        env_frame = ctk.CTkFrame(parent)
        env_frame.grid(row=0, column=1, sticky="nsew", padx=10, pady=10)
        self.build_envelope(env_frame)
        for i in range(1, 3):
            self.update_osc_state(i)
    # build oscillator window
    def build_single_oscillator(self, parent, i):
        container = ctk.CTkFrame(parent)
        container.pack(expand=True)
        ## for oscillators 2 and 3
        if i > 0:
            ctk.CTkCheckBox(container, text = "Enabled", variable = self.osc_enabled[i],).pack(pady=10)
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
            b = ctk.CTkRadioButton(wf, text = text, variable = self.osc_waveform[i], value = val)
            b.pack(side="left", padx=10)
            buttons.append(b)
        vol = self.labeled_slider(controls, "Volume", self.osc_volume[i], 0, 1, "%", percent = True)
        pitch = self.labeled_slider(controls, "Pitch", self.osc_pitch[i], -24, 24, "st", signed = True)
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
        ctk.CTkLabel(frame, text = "ADSR Envelope", font = ctk.CTkFont(size = 16, weight = "bold")).pack(pady = (10, 20))
        sliders = ctk.CTkFrame(frame)
        sliders.pack()
        self.vertical_slider(sliders, "Attack", self.attack, 0.001, 2, "s")
        self.vertical_slider(sliders, "Decay", self.decay, 0.001, 2, "s")
        self.vertical_slider(sliders, "Sustain", self.sustain, 0, 1, "")
        self.vertical_slider(sliders, "Release", self.release, 0.001, 3, "s")
    # build the effects tabs
    def build_effects(self, parent):
        parent.grid_columnconfigure((0, 1, 2), weight=1)
        # delay tab
        self.effect_block(parent, "Delay",
            self.delay_enabled,
            [
                ("Time", self.delay_time, 0.01, 2, "s"),
                ("Feedback", self.delay_feedback, 0, 0.95, "%", True),
                ("Mix", self.delay_mix, 0, 1, "%", True),
            ],
            0
        )
        # reverb tab
        self.effect_block(
            parent,
            "Reverb",
            self.reverb_enabled,
            [
                ("Room", self.reverb_room, 0, 1, "%", True),
                ("Damp", self.reverb_damp, 0, 1, "%", True),
                ("Mix", self.reverb_mix, 0, 1, "%", True),
            ],
            1
        )
        # chorus tab
        self.effect_block(
            parent,
            "Chorus",
            self.chorus_enabled,
            [
                ("Rate", self.chorus_rate, 0.1, 5, "Hz"),
                ("Depth", self.chorus_depth, 0.0001, 0.01, ""),
                ("Mix", self.chorus_mix, 0, 1, "%", True),
            ],
            2
        )
    # build the single effect tab
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
        ## buttons
        ctk.CTkButton(btn_frame, text = "Preview", command = self.preview_audio_action).pack(side = "left", padx = 5)
        ctk.CTkButton(btn_frame, text="Stop", command = self.stop_audio).pack(side = "left", padx = 5)
        ctk.CTkButton(btn_frame, text = "Render & Export", command = self.render_audio).pack(side = "left", padx = 5)
        ## status label
        ctk.CTkLabel(frame, textvariable = self.status).pack(pady = (4, 6))
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
        slider = ctk.CTkSlider(frame, orientation = "vertical",from_ = minv, to = maxv, variable = var, height = 180)
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
        adsr = dict(attack = self.attack.get(), decay = self.decay.get(), sustain = self.sustain.get(), release = self.release.get())
        ## effects
        effects = {}
        ### delay
        if self.delay_enabled.get():
            effects["delay"] = dict(delay_time = self.delay_time.get(), feedback = self.delay_feedback.get(), mix = self.delay_mix.get())
        ### reverb
        if self.reverb_enabled.get():
            effects["reverb"] = dict(room_size = self.reverb_room.get(), damping = self.reverb_damp.get(), mix = self.reverb_mix.get())
        ### chorus
        if self.chorus_enabled.get():
            effects["chorus"] = dict(rate = self.chorus_rate.get(), depth = self.chorus_depth.get(), mix = self.chorus_mix.get())
        ## oscillators
        oscillators = []
        for i in range(3):
            oscillators.append(dict(enabled = self.osc_enabled[i].get(), waveform = self.osc_waveform[i].get(), volume = self.osc_volume[i].get(),pitch = self.osc_pitch[i].get()))
        return adsr, effects, oscillators
    # preview audio
    def preview_audio_action(self):
        ## if no MIDI has been provided
        if not self.midi_path.get():
            messagebox.showerror("Error", "Select MIDI file")
            return
        ## play the audio
        def worker():
            try:
                from pynth.midi import midi_to_audio
                self.status.set("Generating preview...")
                adsr, fx, osc = self.get_parameters()
                audio, _ = midi_to_audio(self.midi_path.get(), adsr = adsr, fx = fx if fx else None, osc = osc)
                self.preview_audio = audio
                ### change status
                self.status.set("Playing...")
                sd.play(audio, 44100)
                sd.wait()
                self.status.set("Done")
            ## if an error occured
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
        ## if no MIDI input or FLAC output has been provided
        if not self.midi_path.get() or not self.output_path.get():
            messagebox.showerror("Error", "Missing paths")
            return
        ## render the audio
        def worker():
            try:
                from pynth.midi import midi_to_flac
                ### update status
                self.status.set("Rendering...")
                ### export
                adsr, fx, osc = self.get_parameters()
                midi_to_flac(self.midi_path.get(), self.output_path.get(), adsr = adsr, fx = fx if fx else None, osc = osc)
                ### update status to done
                self.status.set("Done")
            ## if an error occured
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