
import sounddevice as sd
import numpy as np
import scipy.io.wavfile as wav

def main():
    DURATION = 5  # seconds
    FS = 44100    # sample rate
    
    print(f"[1/3] listing audio devices...")
    print(sd.query_devices())

    print(f"\n[2/3] Recording for {DURATION} seconds... Please speak into the microphone.")
    try:
        myrecording = sd.rec(int(DURATION * FS), samplerate=FS, channels=1)
        sd.wait()  # Wait until recording is finished
        print(" -> Recording finished.")
    except Exception as e:
        print(f" -> Error during recording: {e}")
        return

    print("[3/3] Saving 'test_audio.wav'...")
    wav.write('test_audio.wav', FS, (myrecording * 32767).astype(np.int16))
    print(" -> Saved. Please play this file to check audio quality.")

if __name__ == "__main__":
    main()
