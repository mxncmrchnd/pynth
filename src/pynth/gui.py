## GUI made with the help of Claude Sonnet 4.5

import tkinter as tk
from tkinter import ttk, filedialog, messagebox
import threading
from pathlib import Path
import numpy as np
import matplotlib.pyplot as plt
from matplotlib.backends.backend_tkagg import FigureCanvasTkAgg
from matplotlib.figure import Figure
import sounddevice as sd

from pynth.defaults import DEFAULT_ADSR, DEFAULT_EFFECTS, DEFAULT_OSCILLATORS

class PynthGUI:
    def __init__(self, root):
        self.root = root
        self.root.title("Pynth - MIDI to Audio Synthesizer")
        
        # Make window fullscreen
        self.root.state('zoomed')  # Windows
        # For Linux/Mac, use: self.root.attributes('-zoomed', True)
        
        self.root.resizable(True, True)
        
        # Configure grid weights for proportional scaling
        self.root.grid_rowconfigure(0, weight=1)
        self.root.grid_columnconfigure(0, weight=1)
        
        # Variables
        self.midi_path = tk.StringVar()
        self.output_path = tk.StringVar()
        
        # Oscillator variables (3 oscillators)
        self.osc_enabled = [tk.BooleanVar(value=osc['enabled']) for osc in DEFAULT_OSCILLATORS]
        self.osc_waveform = [tk.StringVar(value=osc['waveform']) for osc in DEFAULT_OSCILLATORS]
        self.osc_volume = [tk.DoubleVar(value=osc['volume']) for osc in DEFAULT_OSCILLATORS]
        self.osc_pitch = [tk.IntVar(value=osc['pitch']) for osc in DEFAULT_OSCILLATORS]
        
        # ADSR variables - use defaults from defaults.py
        self.attack = tk.DoubleVar(value=DEFAULT_ADSR['attack'])
        self.decay = tk.DoubleVar(value=DEFAULT_ADSR['decay'])
        self.sustain = tk.DoubleVar(value=DEFAULT_ADSR['sustain'])
        self.release = tk.DoubleVar(value=DEFAULT_ADSR['release'])
        
        # Effects toggles
        self.delay_enabled = tk.BooleanVar(value=False)
        self.reverb_enabled = tk.BooleanVar(value=False)
        self.chorus_enabled = tk.BooleanVar(value=False)
        
        # Delay parameters - use defaults from defaults.py
        self.delay_time = tk.DoubleVar(value=DEFAULT_EFFECTS['delay']['delay_time'])
        self.delay_feedback = tk.DoubleVar(value=DEFAULT_EFFECTS['delay']['feedback'])
        self.delay_mix = tk.DoubleVar(value=DEFAULT_EFFECTS['delay']['mix'])
        
        # Reverb parameters - use defaults from defaults.py
        self.reverb_room_size = tk.DoubleVar(value=DEFAULT_EFFECTS['reverb']['room_size'])
        self.reverb_damping = tk.DoubleVar(value=DEFAULT_EFFECTS['reverb']['damping'])
        self.reverb_mix = tk.DoubleVar(value=DEFAULT_EFFECTS['reverb']['mix'])
        
        # Chorus parameters - use defaults from defaults.py
        self.chorus_rate = tk.DoubleVar(value=DEFAULT_EFFECTS['chorus']['rate'])
        self.chorus_depth = tk.DoubleVar(value=DEFAULT_EFFECTS['chorus']['depth'])
        self.chorus_mix = tk.DoubleVar(value=DEFAULT_EFFECTS['chorus']['mix'])
        
        # Audio storage for preview
        self.preview_audio = None
        self.is_playing = False
        
        self.setup_ui()
        self.update_adsr_plot()
    
    def setup_ui(self):
        # Main container with two columns
        main_frame = ttk.Frame(self.root, padding="10")
        main_frame.grid(row=0, column=0, sticky=(tk.W, tk.E, tk.N, tk.S))
        main_frame.grid_rowconfigure(0, weight=1)
        main_frame.grid_columnconfigure(0, weight=1, minsize=550)  # Left column minimum width
        main_frame.grid_columnconfigure(1, weight=1, minsize=450)  # Right column minimum width
        
        # Left column (controls)
        left_frame = ttk.Frame(main_frame)
        left_frame.grid(row=0, column=0, sticky=(tk.W, tk.E, tk.N, tk.S), padx=(0, 10))
        left_frame.grid_columnconfigure(0, weight=1)
        
        # Configure row weights - all content-based, no expansion
        left_frame.grid_rowconfigure(0, weight=0)  # File selection
        left_frame.grid_rowconfigure(1, weight=0)  # Oscillators
        left_frame.grid_rowconfigure(2, weight=0)  # ADSR
        left_frame.grid_rowconfigure(3, weight=0)  # Effects
        
        # Right column (ADSR visualization + controls)
        right_frame = ttk.Frame(main_frame)
        right_frame.grid(row=0, column=1, sticky=(tk.W, tk.E, tk.N, tk.S))
        right_frame.grid_rowconfigure(0, weight=1)  # Visualization - expandable
        right_frame.grid_rowconfigure(1, weight=0)  # Buttons - fixed
        right_frame.grid_rowconfigure(2, weight=0)  # Status - fixed
        right_frame.grid_columnconfigure(0, weight=1)
        
        # File Selection Section
        file_frame = ttk.LabelFrame(left_frame, text="File Selection", padding="5")
        file_frame.grid(row=0, column=0, sticky=(tk.W, tk.E), pady=5)
        
        ttk.Label(file_frame, text="MIDI Input:").grid(row=0, column=0, sticky=tk.W, pady=2)
        ttk.Entry(file_frame, textvariable=self.midi_path, width=35).grid(row=0, column=1, padx=5)
        ttk.Button(file_frame, text="Browse", command=self.browse_midi).grid(row=0, column=2)
        
        ttk.Label(file_frame, text="FLAC Output:").grid(row=1, column=0, sticky=tk.W, pady=2)
        ttk.Entry(file_frame, textvariable=self.output_path, width=35).grid(row=1, column=1, padx=5)
        ttk.Button(file_frame, text="Browse", command=self.browse_output).grid(row=1, column=2)
        
        # Oscillators Section with Tabs
        osc_frame = ttk.LabelFrame(left_frame, text="Oscillators", padding="5")
        osc_frame.grid(row=1, column=0, sticky=(tk.W, tk.E), pady=5)
        
        # Create notebook (tabbed interface)
        self.osc_notebook = ttk.Notebook(osc_frame)
        self.osc_notebook.pack(fill=tk.BOTH, expand=True)
        
        # Create tabs for each oscillator
        self.osc_widgets = []
        for i in range(3):
            tab = ttk.Frame(self.osc_notebook, padding="5")
            self.osc_notebook.add(tab, text=f"Oscillator {i+1}")
            
            widgets = self.create_oscillator_tab(tab, i)
            self.osc_widgets.append(widgets)
            
            # Oscillator 1 is always enabled, others start disabled
            if i > 0:
                self.set_widgets_state(widgets[1:], tk.DISABLED)  # Skip checkbox
        
        # ADSR Section (shared across all oscillators)
        adsr_frame = ttk.LabelFrame(left_frame, text="ADSR Envelope (Shared)", padding="5")
        adsr_frame.grid(row=2, column=0, sticky=(tk.W, tk.E), pady=5)
        
        # Create a sub-frame to center ADSR controls
        adsr_container = ttk.Frame(adsr_frame)
        adsr_container.pack(expand=True)
        
        self.create_knob(adsr_container, "Attack", self.attack, 1.0, 0.001, 0)
        self.create_knob(adsr_container, "Decay", self.decay, 2.0, 0.001, 1)
        self.create_knob(adsr_container, "Sustain", self.sustain, 1.0, 0.0, 2)
        self.create_knob(adsr_container, "Release", self.release, 2.0, 0.001, 3)
        
        # Add trace to update plot when ADSR changes
        self.attack.trace_add('write', lambda *args: self.update_adsr_plot())
        self.decay.trace_add('write', lambda *args: self.update_adsr_plot())
        self.sustain.trace_add('write', lambda *args: self.update_adsr_plot())
        self.release.trace_add('write', lambda *args: self.update_adsr_plot())
        
        # Effects Section
        effects_frame = ttk.LabelFrame(left_frame, text="Effects", padding="5")
        effects_frame.grid(row=3, column=0, sticky=(tk.W, tk.E), pady=5)
        
        # Delay
        delay_frame = ttk.Frame(effects_frame)
        delay_frame.pack(fill=tk.X, pady=2)
        
        ttk.Checkbutton(delay_frame, text="Delay", variable=self.delay_enabled,
                    command=self.toggle_delay).pack(anchor=tk.W)
        
        self.delay_controls = ttk.Frame(delay_frame)
        self.delay_controls.pack(fill=tk.X, padx=20)
        self.delay_widgets = self.create_mini_knob(self.delay_controls, "Time (s)", self.delay_time, 0.01, 2.0, 0)
        self.delay_widgets.extend(self.create_mini_knob(self.delay_controls, "Feedback", self.delay_feedback, 0.0, 0.9, 1))
        self.delay_widgets.extend(self.create_mini_knob(self.delay_controls, "Mix", self.delay_mix, 0.0, 1.0, 2))
        
        # Reverb
        reverb_frame = ttk.Frame(effects_frame)
        reverb_frame.pack(fill=tk.X, pady=2)
        
        ttk.Checkbutton(reverb_frame, text="Reverb", variable=self.reverb_enabled,
                    command=self.toggle_reverb).pack(anchor=tk.W)
        
        self.reverb_controls = ttk.Frame(reverb_frame)
        self.reverb_controls.pack(fill=tk.X, padx=20)
        self.reverb_widgets = self.create_mini_knob(self.reverb_controls, "Room Size", self.reverb_room_size, 0.0, 1.0, 0)
        self.reverb_widgets.extend(self.create_mini_knob(self.reverb_controls, "Damping", self.reverb_damping, 0.0, 1.0, 1))
        self.reverb_widgets.extend(self.create_mini_knob(self.reverb_controls, "Mix", self.reverb_mix, 0.0, 1.0, 2))
        
        # Chorus
        chorus_frame = ttk.Frame(effects_frame)
        chorus_frame.pack(fill=tk.X, pady=2)
        
        ttk.Checkbutton(chorus_frame, text="Chorus", variable=self.chorus_enabled,
                    command=self.toggle_chorus).pack(anchor=tk.W)
        
        self.chorus_controls = ttk.Frame(chorus_frame)
        self.chorus_controls.pack(fill=tk.X, padx=20)
        self.chorus_widgets = self.create_mini_knob(self.chorus_controls, "Rate (Hz)", self.chorus_rate, 0.1, 5.0, 0)
        self.chorus_widgets.extend(self.create_mini_knob(self.chorus_controls, "Depth", self.chorus_depth, 0.0001, 0.01, 1))
        self.chorus_widgets.extend(self.create_mini_knob(self.chorus_controls, "Mix", self.chorus_mix, 0.0, 1.0, 2))
        
        # Initially disable all effect controls
        self.set_widgets_state(self.delay_widgets, tk.DISABLED)
        self.set_widgets_state(self.reverb_widgets, tk.DISABLED)
        self.set_widgets_state(self.chorus_widgets, tk.DISABLED)
        
        # RIGHT COLUMN - ADSR Visualization
        viz_frame = ttk.LabelFrame(right_frame, text="ADSR Envelope Visualization", padding="10")
        viz_frame.grid(row=0, column=0, sticky=(tk.W, tk.E, tk.N, tk.S))
        viz_frame.grid_rowconfigure(0, weight=1)
        viz_frame.grid_columnconfigure(0, weight=1)
        
        # Create matplotlib figure - let it scale with window
        self.fig = Figure(dpi=100)
        self.ax = self.fig.add_subplot(111)
        self.canvas = FigureCanvasTkAgg(self.fig, master=viz_frame)
        self.canvas.get_tk_widget().grid(row=0, column=0, sticky=(tk.W, tk.E, tk.N, tk.S))
        
        # Buttons (moved to right panel)
        button_frame = ttk.Frame(right_frame)
        button_frame.grid(row=1, column=0, pady=10)
        
        self.preview_button = ttk.Button(button_frame, text="▶ Preview", command=self.preview_audio_action)
        self.preview_button.pack(side=tk.LEFT, padx=5)
        
        self.stop_button = ttk.Button(button_frame, text="⏹ Stop", command=self.stop_audio, state=tk.DISABLED)
        self.stop_button.pack(side=tk.LEFT, padx=5)
        
        ttk.Button(button_frame, text="💾 Render & Export", command=self.render_audio).pack(side=tk.LEFT, padx=5)
        
        # Status Bar (moved to right panel)
        self.status = tk.StringVar(value="Ready")
        status_bar = ttk.Label(right_frame, textvariable=self.status, relief=tk.SUNKEN, anchor=tk.W)
        status_bar.grid(row=2, column=0, sticky=(tk.W, tk.E), pady=(0, 5))
    
    def create_oscillator_tab(self, parent, osc_index):
        """Create controls for a single oscillator tab"""
        widgets = []
        
        # Enable/Disable checkbox (only for oscillators 2 and 3)
        if osc_index > 0:
            enable_check = ttk.Checkbutton(
                parent, 
                text="Enable Oscillator", 
                variable=self.osc_enabled[osc_index],
                command=lambda: self.toggle_oscillator(osc_index)
            )
            enable_check.pack(anchor=tk.W, pady=(0, 5))
            widgets.append(enable_check)
        
        # Waveform Selection
        wave_frame = ttk.Frame(parent)
        wave_frame.pack(fill=tk.X, pady=5)
        
        wave_label = ttk.Label(wave_frame, text="Waveform:")
        wave_label.pack(side=tk.LEFT, padx=(0, 10))
        widgets.append(wave_label)
        
        waveforms = [("Sine", "sine"), ("Saw", "saw"), ("Square", "square"), ("Triangle", "triangle")]
        for text, value in waveforms:
            rb = ttk.Radiobutton(
                wave_frame, 
                text=text, 
                variable=self.osc_waveform[osc_index], 
                value=value
            )
            rb.pack(side=tk.LEFT, padx=5)
            widgets.append(rb)
        
        # Volume Control
        vol_frame = ttk.Frame(parent)
        vol_frame.pack(fill=tk.X, pady=10)
        
        vol_label = ttk.Label(vol_frame, text="Volume:", width=10)
        vol_label.pack(side=tk.LEFT)
        widgets.append(vol_label)
        
        vol_scale = ttk.Scale(
            vol_frame, 
            from_=0.0, 
            to=1.0, 
            orient=tk.HORIZONTAL,
            variable=self.osc_volume[osc_index]
        )
        vol_scale.pack(side=tk.LEFT, fill=tk.X, expand=True, padx=10)
        widgets.append(vol_scale)
        
        vol_value = ttk.Label(vol_frame, text=f"{self.osc_volume[osc_index].get():.2f}", width=6)
        vol_value.pack(side=tk.LEFT)
        widgets.append(vol_value)
        
        # Update volume label
        def update_vol_label(*args):
            vol_value.config(text=f"{self.osc_volume[osc_index].get():.2f}")
        self.osc_volume[osc_index].trace_add('write', update_vol_label)
        
        # Pitch Control (in semitones)
        pitch_frame = ttk.Frame(parent)
        pitch_frame.pack(fill=tk.X, pady=10)
        
        pitch_label = ttk.Label(pitch_frame, text="Pitch:", width=10)
        pitch_label.pack(side=tk.LEFT)
        widgets.append(pitch_label)
        
        pitch_scale = ttk.Scale(
            pitch_frame, 
            from_=-24, 
            to=24, 
            orient=tk.HORIZONTAL,
            variable=self.osc_pitch[osc_index]
        )
        pitch_scale.pack(side=tk.LEFT, fill=tk.X, expand=True, padx=10)
        widgets.append(pitch_scale)
        
        pitch_value = ttk.Label(pitch_frame, text=f"{self.osc_pitch[osc_index].get():+d} st", width=8)
        pitch_value.pack(side=tk.LEFT)
        widgets.append(pitch_value)
        
        # Update pitch label
        def update_pitch_label(*args):
            val = self.osc_pitch[osc_index].get()
            pitch_value.config(text=f"{val:+d} st")
        self.osc_pitch[osc_index].trace_add('write', update_pitch_label)
        
        # Info text
        info_label = ttk.Label(
            parent, 
            text="💡 Tip: Use pitch offset to create octaves (+12, -12) or detuned sounds (+/-1 to +/-7)",
            wraplength=350,
            foreground="gray"
        )
        info_label.pack(pady=10)
        widgets.append(info_label)
        
        return widgets
    
    def toggle_oscillator(self, osc_index):
        """Enable/disable oscillator controls"""
        if self.osc_enabled[osc_index].get():
            # Enable all widgets except the checkbox
            self.set_widgets_state(self.osc_widgets[osc_index][1:], tk.NORMAL)
        else:
            # Disable all widgets except the checkbox
            self.set_widgets_state(self.osc_widgets[osc_index][1:], tk.DISABLED)
    
    def create_knob(self, parent, label, variable, max_val, min_val, column):
        """Create a labeled slider (knob) for ADSR parameters - inverted"""
        frame = ttk.Frame(parent)
        frame.grid(row=0, column=column, padx=10)
        
        ttk.Label(frame, text=label).pack()
        
        # from_=max, to=min for inverted slider
        scale = ttk.Scale(frame, from_=max_val, to=min_val, orient=tk.VERTICAL,
                         variable=variable, length=120)
        scale.pack()
        
        value_label = ttk.Label(frame, text=f"{variable.get():.3f}")
        value_label.pack()
        
        # Update label when slider changes
        def update_label(*args):
            value_label.config(text=f"{variable.get():.3f}")
        variable.trace_add('write', update_label)
    
    def create_mini_knob(self, parent, label, variable, min_val, max_val, column):
        """Create a smaller horizontal slider for effect parameters
        Returns list of widgets that can be enabled/disabled"""
        frame = ttk.Frame(parent)
        frame.grid(row=0, column=column, padx=3, pady=2)
        
        label_widget = ttk.Label(frame, text=label, width=9)
        label_widget.pack(side=tk.LEFT)
        
        scale = ttk.Scale(frame, from_=min_val, to=max_val, orient=tk.HORIZONTAL,
                         variable=variable, length=80)
        scale.pack(side=tk.LEFT, padx=3)
        
        value_label = ttk.Label(frame, text=f"{variable.get():.3f}", width=6)
        value_label.pack(side=tk.LEFT)
        
        def update_label(*args):
            value_label.config(text=f"{variable.get():.3f}")
        variable.trace_add('write', update_label)
        
        # Return widgets that should be enabled/disabled
        return [label_widget, scale, value_label]
    
    def set_widgets_state(self, widgets, state):
        """Enable or disable a list of widgets"""
        for widget in widgets:
            widget.config(state=state)
    
    def update_adsr_plot(self):
        """Update the ADSR envelope visualization"""
        self.ax.clear()
        
        attack = self.attack.get()
        decay = self.decay.get()
        sustain = self.sustain.get()
        release = self.release.get()
        
        # Calculate time points
        total_time = attack + decay + 0.5 + release  # 0.5s sustain for visualization
        
        times = []
        levels = []
        
        # Attack phase
        times.append(0)
        levels.append(0)
        times.append(attack)
        levels.append(1.0)
        
        # Decay phase
        times.append(attack + decay)
        levels.append(sustain)
        
        # Sustain phase
        times.append(attack + decay + 0.5)
        levels.append(sustain)
        
        # Release phase
        times.append(attack + decay + 0.5 + release)
        levels.append(0)
        
        # Plot
        self.ax.plot(times, levels, 'b-', linewidth=2)
        self.ax.fill_between(times, levels, alpha=0.3)
        
        # Annotations
        self.ax.axvline(attack, color='r', linestyle='--', alpha=0.5, label='Attack')
        self.ax.axvline(attack + decay, color='g', linestyle='--', alpha=0.5, label='Decay')
        self.ax.axhline(sustain, color='orange', linestyle='--', alpha=0.5, label='Sustain Level')
        
        self.ax.set_xlabel('Time (seconds)')
        self.ax.set_ylabel('Amplitude')
        self.ax.set_title('ADSR Envelope Shape')
        self.ax.grid(True, alpha=0.3)
        self.ax.set_ylim(-0.1, 1.1)
        self.ax.set_xlim(0, total_time * 1.05)
        self.ax.legend(loc='upper right', fontsize=9)
        
        self.canvas.draw()
    
    def toggle_delay(self):
        if self.delay_enabled.get():
            self.set_widgets_state(self.delay_widgets, tk.NORMAL)
        else:
            self.set_widgets_state(self.delay_widgets, tk.DISABLED)
    
    def toggle_reverb(self):
        if self.reverb_enabled.get():
            self.set_widgets_state(self.reverb_widgets, tk.NORMAL)
        else:
            self.set_widgets_state(self.reverb_widgets, tk.DISABLED)
    
    def toggle_chorus(self):
        if self.chorus_enabled.get():
            self.set_widgets_state(self.chorus_widgets, tk.NORMAL)
        else:
            self.set_widgets_state(self.chorus_widgets, tk.DISABLED)
    
    def browse_midi(self):
        filename = filedialog.askopenfilename(
            title="Select MIDI file",
            filetypes=[("MIDI files", "*.mid"), ("All files", "*.*")]
        )
        if filename:
            self.midi_path.set(filename)
            # Auto-suggest output path
            if not self.output_path.get():
                output = Path(filename).with_suffix('.flac')
                self.output_path.set(str(output))
    
    def browse_output(self):
        filename = filedialog.asksaveasfilename(
            title="Save FLAC file",
            defaultextension=".flac",
            filetypes=[("FLAC files", "*.flac"), ("All files", "*.*")]
        )
        if filename:
            self.output_path.set(filename)
    
    def get_parameters(self):
        """Get current ADSR, effects, and oscillator parameters"""
        adsr = {
            'attack': self.attack.get(),
            'decay': self.decay.get(),
            'sustain': self.sustain.get(),
            'release': self.release.get()
        }
        
        effects = {}
        if self.delay_enabled.get():
            effects['delay'] = {
                'delay_time': self.delay_time.get(),
                'feedback': self.delay_feedback.get(),
                'mix': self.delay_mix.get()
            }
        
        if self.reverb_enabled.get():
            effects['reverb'] = {
                'room_size': self.reverb_room_size.get(),
                'damping': self.reverb_damping.get(),
                'mix': self.reverb_mix.get()
            }
        
        if self.chorus_enabled.get():
            effects['chorus'] = {
                'rate': self.chorus_rate.get(),
                'depth': self.chorus_depth.get(),
                'mix': self.chorus_mix.get()
            }
        
        # Get oscillator settings
        oscillators = []
        for i in range(3):
            oscillators.append({
                'enabled': self.osc_enabled[i].get(),
                'waveform': self.osc_waveform[i].get(),
                'volume': self.osc_volume[i].get(),
                'pitch': self.osc_pitch[i].get()
            })
        
        return adsr, effects, oscillators
    
    def preview_audio_action(self):
        """Generate and play audio preview"""
        if not self.midi_path.get():
            messagebox.showerror("Error", "Please select a MIDI input file")
            return
        
        def preview_thread():
            try:
                self.status.set("Generating preview...")
                self.preview_button.config(state=tk.DISABLED)
                self.root.update()
                
                from pynth.midi import midi_to_audio
                
                adsr, effects, oscillators = self.get_parameters()
                
                audio, _ = midi_to_audio(
                    self.midi_path.get(),
                    adsr=adsr,
                    fx=effects if effects else None,
                    osc=oscillators
                )
                
                if audio is None:
                    self.status.set("No audio generated")
                    self.preview_button.config(state=tk.NORMAL)
                    return
                
                # Store for playback
                self.preview_audio = audio
                
                # Play audio
                self.status.set("Playing preview...")
                self.stop_button.config(state=tk.NORMAL)
                self.is_playing = True
                
                sd.play(audio, 44100)
                sd.wait()
                
                self.is_playing = False
                self.status.set("Preview complete")
                self.stop_button.config(state=tk.DISABLED)
                self.preview_button.config(state=tk.NORMAL)
                
            except Exception as e:
                self.status.set("Preview failed")
                messagebox.showerror("Error", f"Preview failed: {str(e)}")
                self.preview_button.config(state=tk.NORMAL)
                self.stop_button.config(state=tk.DISABLED)
        
        thread = threading.Thread(target=preview_thread, daemon=True)
        thread.start()
    
    def stop_audio(self):
        """Stop audio playback"""
        if self.is_playing:
            sd.stop()
            self.is_playing = False
            self.status.set("Playback stopped")
            self.stop_button.config(state=tk.DISABLED)
            self.preview_button.config(state=tk.NORMAL)
    
    def render_audio(self):
        """Render audio to file"""
        if not self.midi_path.get():
            messagebox.showerror("Error", "Please select a MIDI input file")
            return
        
        if not self.output_path.get():
            messagebox.showerror("Error", "Please specify an output file")
            return
        
        def render_thread():
            try:
                self.status.set("Rendering to file...")
                self.root.update()
                
                from pynth.midi import midi_to_flac
                
                adsr, effects, oscillators = self.get_parameters()
                
                midi_to_flac(
                    self.midi_path.get(),
                    self.output_path.get(),
                    adsr=adsr,
                    fx=effects if effects else None,
                    osc=oscillators
                )
                
                self.status.set("Render complete!")
                messagebox.showinfo("Success", f"Audio rendered to {self.output_path.get()}")
            except Exception as e:
                self.status.set("Error occurred")
                messagebox.showerror("Error", f"Rendering failed: {str(e)}")
        
        thread = threading.Thread(target=render_thread, daemon=True)
        thread.start()

def main():
    root = tk.Tk()
    app = PynthGUI(root)
    root.mainloop()

if __name__ == "__main__":
    main()