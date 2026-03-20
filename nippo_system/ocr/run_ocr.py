import time
import sys
import os

# Add project root to path (robustness)
current_dir = os.path.dirname(os.path.abspath(__file__))
project_root = os.path.dirname(os.path.dirname(current_dir))
if project_root not in sys.path:
    sys.path.append(project_root)

from nippo_system.ocr.screen_ocr import ScreenOCR
from nippo_system.core.storage import StorageManager

def main():
    store = StorageManager()
    
    # Production Subclass: Saves to SQLite (via StorageManager)
    # The base ScreenOCR also saves JSON logs to DATA_DIR by default.
    class DBOCr(ScreenOCR):
        def on_text_detected(self, text):
            store.save_log("ocr", text)
            
    # Initialize normally (Production Defaults)
    ocr = DBOCr()
    ocr.start()
    print("Screen OCR Process Started (Production)")
    try:
        while True:
            time.sleep(1)
    except KeyboardInterrupt:
        ocr.stop()

if __name__ == "__main__":
    main()
