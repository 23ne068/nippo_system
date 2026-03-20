
import sys
import os
import queue
import sounddevice as sd
import vosk
import json

# Voskモデルのパス
MODEL_PATH = "model" 

def main():
    print("[1/4] Checking model directory...")
    if not os.path.exists(MODEL_PATH):
        print(f" -> Error: Model folder '{MODEL_PATH}' not found.")
        return
    print(" -> Found.")

    q = queue.Queue()

    def callback(indata, frames, time, status):
        if status:
            print(f"Callback status: {status}", file=sys.stderr)
        q.put(bytes(indata))

    print("[2/4] Loading Vosk Model (this may take a few seconds)...")
    try:
        model = vosk.Model(MODEL_PATH)
        print(" -> Model loaded.")
    except Exception as e:
        print(f" -> Model load error: {e}")
        return
    
    print("[3/4] Opening Microphone stream...")
    try:
        device_info = sd.query_devices(None, 'input')
        print(f" -> Target device: {device_info['name']}")
    except Exception as e:
        print(f" -> Device query error: {e}")

    try:
        with sd.RawInputStream(samplerate=16000, blocksize=8000, device=None, dtype='int16',
                               channels=1, callback=callback):
            print(" -> Stream opened. [4/4] Starting recognition loop...")
            print("==================================================")
            print("  リアルタイム音声認識 (10秒後に自動終了します)")
            print("  何か音を立ててください...")
            print("==================================================")

            rec = vosk.KaldiRecognizer(model, 16000)
            
            # 10秒間だけループして終了するように変更（テスト用）
            import time as pytime
            start_time = pytime.time()
            
            while pytime.time() - start_time < 10:
                try:
                    data = q.get(timeout=1)
                    if rec.AcceptWaveform(data):
                        result = json.loads(rec.Result())
                        text = result.get('text', '')
                        if text:
                            print(f"🗣️  : {text}")
                    else:
                        partial = json.loads(rec.PartialResult())
                except queue.Empty:
                    continue
            print("\nTest finished.")

    except Exception as e:
        print(f" -> Stream error: {e}")

if __name__ == "__main__":
    main()
