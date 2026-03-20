
import sys
import queue
import sounddevice as sd
import vosk
import json
import tkinter as tk
from tkinter import ttk
import threading
import numpy as np

# Config
MODEL_PATH = "model"
SAMPLERATE = 16000

class AudioVisualizer:
    def __init__(self, root):
        self.root = root
        self.root.title("Nippo Audio Verification")
        self.root.geometry("600x400")
        
        self.queue = queue.Queue()
        
        # UI Elements
        self.label_status = tk.Label(root, text="Initializing...", font=("Arial", 10))
        self.label_status.pack(pady=10)
        
        self.progress = ttk.Progressbar(root, orient="horizontal", length=400, mode="determinate")
        self.progress.pack(pady=10)
        
        self.label_level = tk.Label(root, text="Volume Level: 0")
        self.label_level.pack()
        
        self.text_area = tk.Text(root, height=10, width=60, font=("Meiryo", 11))
        self.text_area.pack(pady=20)
        
        self.btn_quit = tk.Button(root, text="Quit Verification", command=self.on_closing)
        self.btn_quit.pack(pady=10)
        
        self.model = None
        self.rec = None
        self.stream = None
        
        # Start background thread
        self.thread = threading.Thread(target=self.setup_vosk, daemon=True)
        self.thread.start()
        
        self.root.protocol("WM_DELETE_WINDOW", self.on_closing)
        self.update_ui()

    def setup_vosk(self):
        try:
            self.label_status.config(text="Loading Vosk Model... (Please wait)")
            self.model = vosk.Model(MODEL_PATH)
            self.rec = vosk.KaldiRecognizer(self.model, SAMPLERATE)
            self.label_status.config(text="Microphone: ACTIVE (Speak or tap)")
            
            def callback(indata, frames, time, status):
                self.queue.put(bytes(indata))
                # Level calculation: Convert buffer to float array
                data_np = np.frombuffer(indata, dtype=np.int16).astype(float)
                # Remove DC offset (center the signal)
                data_np -= np.mean(data_np)
                # Calculate normalized RMS
                rms = np.sqrt(np.mean((data_np / 32768.0)**2))
                # Adjust sensitivity: rms * 100 means full scale is 1.0 (unlikely)
                # Let's try rms * 1000 and show raw value
                level = min(100, int(rms * 1000)) 
                self.root.after(0, self.update_level, level, rms)

            self.stream = sd.RawInputStream(samplerate=SAMPLERATE, blocksize=4000, 
                                          device=None, dtype='int16', 
                                          channels=1, callback=callback)
            
            import time as pytime
            last_time_print = 0

            with self.stream:
                while True:
                    # Print timestamp every 1 second for high visibility
                    current_time = pytime.time()
                    if current_time - last_time_print >= 1:
                        timestamp = pytime.strftime("%H:%M:%S")
                        print(f"[{timestamp}] Monitoring... (Active)", flush=True)
                        last_time_print = current_time

                    try:
                        data = self.queue.get(timeout=0.1) # Added timeout to allow loop to run
                        if self.rec.AcceptWaveform(data):
                            res = json.loads(self.rec.Result())
                            if res['text']:
                                print(f"🗣️ (Terminal): {res['text']}", flush=True) # Output to terminal
                                self.root.after(0, self.append_text, res['text'])
                        else:
                            partial = json.loads(self.rec.PartialResult())
                            if partial['partial']:
                                # Optional: print partials to terminal too
                                print(f" > {partial['partial']}", end='\r', flush=True)
                                self.root.after(0, self.show_partial, partial['partial'])
                    except queue.Empty:
                        continue
        except Exception as e:
            self.root.after(0, self.append_text, f"Error: {e}")

    def update_level(self, level, rms):
        self.progress['value'] = level
        self.label_level.config(text=f"Volume Level: {level}% (Raw RMS: {rms:.5f})")

    def append_text(self, text):
        self.text_area.insert(tk.END, f"🗣️: {text}\n")
        self.text_area.see(tk.END)

    def show_partial(self, text):
        # We don't want to spam the main area, maybe a separate label?
        # For now, let's just make sure it's working.
        pass

    def update_ui(self):
        self.root.update_idletasks()
        self.root.after(100, self.update_ui)

    def on_closing(self):
        self.root.destroy()
        sys.exit()

if __name__ == "__main__":
    root = tk.Tk()
    app = AudioVisualizer(root)
    root.mainloop()
