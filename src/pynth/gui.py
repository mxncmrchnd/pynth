import tkinter as tk
from tkinter import ttk, filedialog, messagebox
import threading
from pathlib import Path
import numpy as np
import matplotlib.pyplot as plt
from matplotlib.backends.backend_tkagg import FigureCanvasTkAgg
from matplotlib.figure import Figure
import sounddevice as sd

from pynth.defaults import DEFAULT_ADSR, DEFAULT_EFFECTS

class PynthGUI:
    def __init__(self, root):
        self.root = root
        self.root.title("Pynth - MIDI to Audio Synthesizer")
        self.root.geometry("1000x750")
        self.root.resizable(False, False)
        
        # Variables
        self.midi_path = tk.StringVar()
        self.output_path = tk.StringVar()
        self.waveform = tk.StringVar(value="sine")
        
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
        
        # Left column (controls)
        left_frame = ttk.Frame(main_frame)
        left_frame.grid(row=0, column=0, sticky=(tk.W, tk.E, tk.N, tk.S), padx=(0, 10))
        
        # Right column (ADSR visualization)
        right_frame = ttk.Frame(main_frame)
        right_frame.grid(row=0, column=1, sticky=(tk.W, tk.E, tk.N, tk.S))
        
        # File Selection Section
        file_frame = ttk.LabelFrame(left_frame, text="File Selection", padding="10")
        file_frame.grid(row=0, column=0, sticky=(tk.W, tk.E), pady=5)
        
        ttk.Label(file_frame, text="MIDI Input:").grid(row=0, column=0, sticky=tk.W, pady=5)
        ttk.Entry(file_frame, textvariable=self.midi_path, width=40).grid(row=0, column=1, padx=5)
        ttk.Button(file_frame, text="Browse", command=self.browse_midi).grid(row=0, column=2)
        
        ttk.Label(file_frame, text="FLAC Output:").grid(row=1, column=0, sticky=tk.W, pady=5)
        ttk.Entry(file_frame, textvariable=self.output_path, width=40).grid(row=1, column=1, padx=5)
        ttk.Button(file_frame, text="Browse", command=self.browse_output).grid(row=1, column=2)
        
        # Waveform Selection
        wave_frame = ttk.LabelFrame(left_frame, text="Waveform", padding="10")
        wave_frame.grid(row=1, column=0, sticky=(tk.W, tk.E), pady=5)
        
        waveforms = [("Sine", "sine"), ("Saw", "saw"), ("Square", "square"), ("Triangle", "triangle")]
        for i, (text, value) in enumerate(waveforms):
            ttk.Radiobutton(wave_frame, text=text, variable=self.waveform, 
                          value=value).grid(row=0, column=i, padx=10)
        
        # ADSR Section
        adsr_frame = ttk.LabelFrame(left_frame, text="ADSR Envelope", padding="10")
        adsr_frame.grid(row=2, column=0, sticky=(tk.W, tk.E), pady=5)
        
        self.create_knob(adsr_frame, "Attack", self.attack, 0.001, 1.0, 0)
        self.create_knob(adsr_frame, "Decay", self.decay, 0.001, 2.0, 1)
        self.create_knob(adsr_frame, "Sustain", self.sustain, 0.0, 1.0, 2)
        self.create_knob(adsr_frame, "Release", self.release, 0.001, 2.0, 3)
        
        # Add trace to update plot when ADSR changes
        self.attack.trace_add('write', lambda *args: self.update_adsr_plot())
        self.decay.trace_add('write', lambda *args: self.update_adsr_plot())
        self.sustain.trace_add('write', lambda *args: self.update_adsr_plot())
        self.release.trace_add('write', lambda *args: self.update_adsr_plot())
        
        # Effects Section
        effects_frame = ttk.LabelFrame(left_frame, text="Effects", padding="10")
        effects_frame.grid(row=3, column=0, sticky=(tk.W, tk.E), pady=5)
        
        # Delay
        delay_frame = ttk.Frame(effects_frame)
        delay_frame.grid(row=0, column=0, sticky=(tk.W, tk.E), pady=5)
        
        ttk.Checkbutton(delay_frame, text="Delay", variable=self.delay_enabled,
                       command=self.toggle_delay).grid(row=0, column=0, sticky=tk.W)
        
        self.delay_controls = ttk.Frame(delay_frame)
        self.delay_controls.grid(row=1, column=0, columnspan=4, sticky=(tk.W, tk.E))
        self.create_mini_knob(self.delay_controls, "Time (s)", self.delay_time, 0.01, 2.0, 0)
        self.create_mini_knob(self.delay_controls, "Feedback", self.delay_feedback, 0.0, 0.9, 1)
        self.create_mini_knob(self.delay_controls, "Mix", self.delay_mix, 0.0, 1.0, 2)
        self.delay_controls.grid_remove()
        
        # Reverb
        reverb_frame = ttk.Frame(effects_frame)
        reverb_frame.grid(row=1, column=0, sticky=(tk.W, tk.E), pady=5)
        
        ttk.Checkbutton(reverb_frame, text="Reverb", variable=self.reverb_enabled,
                       command=self.toggle_reverb).grid(row=0, column=0, sticky=tk.W)
        
        self.reverb_controls = ttk.Frame(reverb_frame)
        self.reverb_controls.grid(row=1, column=0, columnspan=4, sticky=(tk.W, tk.E))
        self.create_mini_knob(self.reverb_controls, "Room Size", self.reverb_room_size, 0.0, 1.0, 0)
        self.create_mini_knob(self.reverb_controls, "Damping", self.reverb_damping, 0.0, 1.0, 1)
        self.create_mini_knob(self.reverb_controls, "Mix", self.reverb_mix, 0.0, 1.0, 2)
        self.reverb_controls.grid_remove()
        
        # Chorus
        chorus_frame = ttk.Frame(effects_frame)
        chorus_frame.grid(row=2, column=0, sticky=(tk.W, tk.E), pady=5)
        
        ttk.Checkbutton(chorus_frame, text="Chorus", variable=self.chorus_enabled,
                       command=self.toggle_chorus).grid(row=0, column=0, sticky=tk.W)
        
        self.chorus_controls = ttk.Frame(chorus_frame)
        self.chorus_controls.grid(row=1, column=0, columnspan=4, sticky=(tk.W, tk.E))
        self.create_mini_knob(self.chorus_controls, "Rate (Hz)", self.chorus_rate, 0.1, 5.0, 0)
        self.create_mini_knob(self.chorus_controls, "Depth", self.chorus_depth, 0.0001, 0.01, 1)
        self.create_mini_knob(self.chorus_controls, "Mix", self.chorus_mix, 0.0, 1.0, 2)
        self.chorus_controls.grid_remove()
        
        # Buttons
        button_frame = ttk.Frame(left_frame)
        button_frame.grid(row=4, column=0, pady=20)
        
        self.preview_button = ttk.Button(button_frame, text="▶ Preview", command=self.preview_audio_action)
        self.preview_button.pack(side=tk.LEFT, padx=5)
        
        self.stop_button = ttk.Button(button_frame, text="⏹ Stop", command=self.stop_audio, state=tk.DISABLED)
        self.stop_button.pack(side=tk.LEFT, padx=5)
        
        ttk.Button(button_frame, text="💾 Render & Export", command=self.render_audio).pack(side=tk.LEFT, padx=5)
        
        # Status Bar
        self.status = tk.StringVar(value="Ready")
        status_bar = ttk.Label(left_frame, textvariable=self.status, relief=tk.SUNKEN, anchor=tk.W)
        status_bar.grid(row=5, column=0, sticky=(tk.W, tk.E))
        
        # ADSR Visualization (right column)
        viz_frame = ttk.LabelFrame(right_frame, text="ADSR Envelope Visualization", padding="10")
        viz_frame.grid(row=0, column=0, sticky=(tk.W, tk.E, tk.N, tk.S))
        
        # Create matplotlib figure
        self.fig = Figure(figsize=(5, 6), dpi=100)
        self.ax = self.fig.add_subplot(111)
        self.canvas = FigureCanvasTkAgg(self.fig, master=viz_frame)
        self.canvas.get_tk_widget().pack(fill=tk.BOTH, expand=True)
    
    def create_knob(self, parent, label, variable, min_val, max_val, column):
        """Create a labeled slider (knob) for ADSR parameters"""
        frame = ttk.Frame(parent)
        frame.grid(row=0, column=column, padx=10)
        
        ttk.Label(frame, text=label).pack()
        
        scale = ttk.Scale(frame, from_=max_val, to=min_val, orient=tk.VERTICAL,
                         variable=variable, length=150)
        scale.pack()
        
        value_label = ttk.Label(frame, text=f"{variable.get():.3f}")
        value_label.pack()
        
        # Update label when slider changes
        def update_label(*args):
            value_label.config(text=f"{variable.get():.3f}")
        variable.trace_add('write', update_label)
    
    def create_mini_knob(self, parent, label, variable, min_val, max_val, column):
        """Create a smaller horizontal slider for effect parameters"""
        frame = ttk.Frame(parent)
        frame.grid(row=0, column=column, padx=5, pady=5)
        
        ttk.Label(frame, text=label, width=10).pack(side=tk.LEFT)
        
        scale = ttk.Scale(frame, from_=min_val, to=max_val, orient=tk.HORIZONTAL,
                         variable=variable, length=100)
        scale.pack(side=tk.LEFT, padx=5)
        
        value_label = ttk.Label(frame, text=f"{variable.get():.3f}", width=6)
        value_label.pack(side=tk.LEFT)
        
        def update_label(*args):
            value_label.config(text=f"{variable.get():.3f}")
        variable.trace_add('write', update_label)
    
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
        self.ax.legend(loc='upper right', fontsize=8)
        
        self.canvas.draw()
    
    def toggle_delay(self):
        if self.delay_enabled.get():
            self.delay_controls.grid()
        else:
            self.delay_controls.grid_remove()
    
    def toggle_reverb(self):
        if self.reverb_enabled.get():
            self.reverb_controls.grid()
        else:
            self.reverb_controls.grid_remove()
    
    def toggle_chorus(self):
        if self.chorus_enabled.get():
            self.chorus_controls.grid()
        else:
            self.chorus_controls.grid_remove()
    
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
        """Get current ADSR and effects parameters"""
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
        
        return adsr, effects
    
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
                
                adsr, effects = self.get_parameters()
                
                audio, _ = midi_to_audio(
                    self.midi_path.get(),
                    wf=self.waveform.get(),
                    adsr=adsr,
                    fx=effects if effects else None
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
                
                adsr, effects = self.get_parameters()
                
                midi_to_flac(
                    self.midi_path.get(),
                    self.output_path.get(),
                    wf=self.waveform.get(),
                    adsr=adsr,
                    fx=effects if effects else None
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