
import sounddevice as sd
import numpy as np

def main():
    print("Checking audio input level... (Taps or clothes rustling should show values)")
    print("Press Ctrl+C to stop.")

    def callback(indata, frames, time, status):
        rms = np.sqrt(np.mean(indata**2))
        level = int(rms * 1000)
        bar = "#" * (level // 10)
        print(f"Level: [{bar:<50}] {level}", end='\r')

    with sd.InputStream(callback=callback, channels=1, samplerate=16000):
        while True:
            sd.sleep(100)

if __name__ == "__main__":
    try:
        main()
    except KeyboardInterrupt:
        print("\nDone.")
