import time
import sys
import os

# --- ENVIRONMENT SETUP ---
# Add project root to path so we can import modules
current_dir = os.path.dirname(os.path.abspath(__file__))
project_root = os.path.dirname(current_dir)
if project_root not in sys.path:
    sys.path.append(project_root)

# Import Core Module
from nippo_system.modules.screen_ocr import ScreenOCR

# Define Isolated Output Directory
LAB_DATA_DIR = os.path.join(current_dir, "data")
if not os.path.exists(LAB_DATA_DIR):
    os.makedirs(LAB_DATA_DIR)

def main():
    print("=== Nippo OCR Lab (Test Environment) ===")
    print(f"Project Root: {project_root}")
    print(f"Lab Data Dir: {LAB_DATA_DIR}")
    print("----------------------------------------")
    print("Running OCR in ISOLATED mode.")
    print("Production data (nippo_system/data) will NOT be touched.")
    print("----------------------------------------")

    # Create timestamped session folder
    timestamp = time.strftime('%Y%m%d_%H%M%S')
    session_dir = os.path.join(LAB_DATA_DIR, f"session_{timestamp}")
    os.makedirs(session_dir, exist_ok=True)
    
    print(f"Saving test data to: {session_dir}")

    # Initialize ScreenOCR with OVERRIDDEN output directory
    # - output_dir: Redirects JSON logs to lab folder
    # - save_debug_images=True: Saves images for dataset creation
    ocr = ScreenOCR(output_dir=session_dir, save_debug_images=True)
    
    ocr.start()
    
    try:
        # Default Run: 60 seconds
        duration = 60
        # Allow arg override
        if len(sys.argv) > 1:
            try:
                duration = int(sys.argv[1])
            except ValueError:
                pass
        
        print(f"Collecting data for {duration} seconds...")
        for i in range(duration):
            remaining = duration - i
            print(f"Running... {remaining}s remaining", end='\r', flush=True)
            time.sleep(1)
            
    except KeyboardInterrupt:
        print("\nAborted by user.")
    finally:
        ocr.stop()
        print("\nTest Complete.")
        print(f"Data saved to: {session_dir}")

if __name__ == "__main__":
    main()
