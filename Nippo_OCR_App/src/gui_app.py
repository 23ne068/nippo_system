import tkinter as tk
from tkinter import ttk, messagebox
import mss
import subprocess
import os
import sys
import multiprocessing
import logging
import traceback
from datetime import datetime

# Windows Constants for process creation
CREATE_NEW_CONSOLE = 0x00000010

class NippoOCRGUI:
    def __init__(self, root):
        self.root = root
        self.root.title("Nippo OCR App")
        self.root.geometry("300x180")
        self.root.resizable(False, False)
        
        self.process = None
        self.monitors = self.get_monitors()
        
        self.create_widgets()

    def get_monitors(self):
        with mss.mss() as sct:
            # sct.monitors[0] is the bounding box of all monitors together.
            # Real monitors are 1-indexed.
            return [f"Display {i} ({m['width']}x{m['height']})" 
                    for i, m in enumerate(sct.monitors) if i > 0]

    def create_widgets(self):
        # Monitor Selection Frame
        frame_top = tk.Frame(self.root, pady=10)
        frame_top.pack(fill=tk.X, padx=20)
        
        tk.Label(frame_top, text="ターゲット画面 (Target Monitor):").pack(anchor=tk.W)
        
        self.monitor_var = tk.StringVar()
        self.monitor_cb = ttk.Combobox(frame_top, textvariable=self.monitor_var, values=self.monitors, state="readonly")
        if self.monitors:
            self.monitor_cb.current(0)
        self.monitor_cb.pack(fill=tk.X, pady=(5, 0))

        # Controls Frame
        frame_bottom = tk.Frame(self.root, pady=20)
        frame_bottom.pack(fill=tk.BOTH, expand=True, padx=20)

        self.btn_start = tk.Button(frame_bottom, text="▶ 開始 (Start)", bg="#d4edda", fg="#155724", 
                                   font=("Helvetica", 12, "bold"), command=self.start_ocr)
        self.btn_start.pack(side=tk.LEFT, fill=tk.BOTH, expand=True, padx=(0, 5))

        self.btn_stop = tk.Button(frame_bottom, text="■ 停止 (Stop)", bg="#f8d7da", fg="#721c24", 
                                  font=("Helvetica", 12, "bold"), command=self.stop_ocr, state=tk.DISABLED)
        self.btn_stop.pack(side=tk.RIGHT, fill=tk.BOTH, expand=True, padx=(5, 0))
        
        # Status Label
        self.status_var = tk.StringVar(value="状態: 待機中 (Stopped)")
        self.status_label = tk.Label(self.root, textvariable=self.status_var, fg="gray")
        self.status_label.pack(side=tk.BOTTOM, pady=5)

    def start_ocr(self):
        if self.process is not None:
            return

        selection_idx = self.monitor_cb.current() + 1 # 1-indexed

        # Determine path to screen_ocr.py based on whether we are frozen or not
        if getattr(sys, 'frozen', False):
            # Running as compiled executable
            # Case 1: Use the EXE itself as the "python" interpreter to run the worker mode
            cmd = [sys.executable, "--run-ocr", str(selection_idx)]
        else:
            # Running as plain Python script
            script_dir = os.path.dirname(os.path.abspath(__file__))
            ocr_script = os.path.join(script_dir, "screen_ocr.py")
            cmd = [sys.executable, ocr_script, str(selection_idx)]

        try:
            self.process = subprocess.Popen(
                cmd,
                creationflags=CREATE_NEW_CONSOLE
            )
            
            self.btn_start.config(state=tk.DISABLED)
            self.btn_stop.config(state=tk.NORMAL)
            self.monitor_cb.config(state=tk.DISABLED)
            self.status_var.set("状態: 実行中 (Running)")
            self.status_label.config(fg="green")
            
        except Exception as e:
            messagebox.showerror("Error", f"Failed to start OCR process:\n{e}")

    def stop_ocr(self):
        if self.process:
            try:
                self.process.terminate()
                self.process.wait(timeout=3)
            except subprocess.TimeoutExpired:
                self.process.kill()
            except Exception as e:
                print(f"Error stopping process: {e}")
            finally:
                self.process = None

        self.btn_start.config(state=tk.NORMAL)
        self.btn_stop.config(state=tk.DISABLED)
        self.monitor_cb.config(state="readonly")
        self.status_var.set("状態: 待機中 (Stopped)")
        self.status_label.config(fg="gray")

    def on_closing(self):
        self.stop_ocr()
        self.root.destroy()

def run_tesseract_diagnostic():
    """Isolated function to test Tesseract paths and loading in the frozen environment."""
    print("\n[DIAGNOSTIC] Starting Tesseract Isolation Test...")
    try:
        from ocr_engine_v2 import ProductionOCRBaseline
        import pytesseract
        
        print(f"[DIAGNOSTIC] Tesseract Command: {pytesseract.pytesseract.tesseract_cmd}")
        print(f"[DIAGNOSTIC] TESSDATA_PREFIX: {os.environ.get('TESSDATA_PREFIX', 'NOT SET')}")
        
        engine = ProductionOCRBaseline()
        print(f"[DIAGNOSTIC] Engine initialized. Tessdata path: {engine.tessdata_path}")
        
        # Test a simple version check
        ver = pytesseract.get_tesseract_version()
        print(f"[DIAGNOSTIC] Tesseract Version detected: {ver}")
        print("[DIAGNOSTIC] SUCCESS: Tesseract setup appears valid.")
        return True
    except Exception:
        print("[DIAGNOSTIC] FAILURE: Tesseract setup failed.")
        print(traceback.format_exc())
        return False

if __name__ == "__main__":
    # Crucial for PyInstaller multiprocessing
    multiprocessing.freeze_support()
    
    # Check if we are being called as a worker process
    if "--run-ocr" in sys.argv or "--test-tess" in sys.argv:
        is_debug_cmd = "--debug-cmd" in sys.argv
        is_test_mode = "--test-tess" in sys.argv
        
        # Standard Environment Setup
        if getattr(sys, 'frozen', False):
            base_path = sys._MEIPASS
            
            # Diagnostic Prints (Capturable by AI in --debug-cmd mode)
            print(f"--- Environment Diagnostics ({datetime.now()}) ---")
            print(f"Executable: {sys.executable}")
            print(f"MEIPASS (Bundle Root): {base_path}")
            print(f"Arguments: {sys.argv}")
            
            if not is_debug_cmd:
                try:
                    import ctypes
                    ctypes.windll.kernel32.AllocConsole()
                    sys.stdout = open('CONOUT$', 'w', encoding='utf-8')
                    sys.stderr = open('CONOUT$', 'w', encoding='utf-8')
                except Exception as e:
                    print(f"Failed to allocate console: {e}")
            
            # Ensure src is in path for imports
            src_path = os.path.join(base_path, 'src')
            if src_path not in sys.path:
                sys.path.append(src_path)
        
        if is_test_mode:
            success = run_tesseract_diagnostic()
            sys.exit(0 if success else 1)

        # Standard Worker Startup
        try:
            print("[WORKER] Importing ScreenOCR...")
            from screen_ocr import ScreenOCR
            logging.basicConfig(level=logging.INFO)
            
            print("====================================")
            print(" Nippo OCR Worker process started ")
            print("====================================")
            
            m_id = 1
            for i, arg in enumerate(sys.argv):
                if arg == "--run-ocr" and i + 1 < len(sys.argv):
                    try:
                        m_id = int(sys.argv[i+1])
                    except ValueError: pass
            
            print(f"[WORKER] Initializing ScreenOCR for Monitor {m_id}...")
            ocr = ScreenOCR(monitor_id=m_id)
            
            print("[WORKER] Starting OCR loop...")
            ocr.start()
            
            import time
            while True:
                time.sleep(1)
        except KeyboardInterrupt:
            print("[WORKER] Interrupted by user.")
        except Exception:
            print("Critical failure in Worker process:")
            print(traceback.format_exc())
            sys.exit(1)
    else:
        # Standard GUI launch
        try:
            root = tk.Tk()
            app = NippoOCRGUI(root)
            root.protocol("WM_DELETE_WINDOW", app.on_closing)
            root.mainloop()
        except Exception:
            print("Critical failure in GUI process:")
            print(traceback.format_exc())
