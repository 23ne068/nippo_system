import time
import sys
import os

from nippo_system.audio.audiolistener import AudioListener
from nippo_system.core.storage import StorageManager
from nippo_system.core.config import AUDIO_STREAM_DIR

def main():
    store = StorageManager()
    
    class DBListener(AudioListener):
        def on_speech_recognized(self, text):
            # 1. データベースへの保存（従来通り）
            store.save_log("audio", text)
            
            # 2. 未加工ストリームへの保存 (Stage 1)
            try:
                now = time.localtime()
                date_str = time.strftime('%Y-%m-%d', now)
                time_str = time.strftime('%H:%M:%S', now)
                
                output_path = os.path.join(AUDIO_STREAM_DIR, f"audio_stream_{date_str}.tsv")
                clean_text = text.replace('\n', '\\n').replace('\t', ' ')
                
                with open(output_path, "a", encoding="utf-8") as f:
                    f.write(f"{time_str}\t{clean_text}\n")
            except Exception as e:
                print(f"Failed to save audio stream: {e}")
            
    listener = DBListener()
    listener.start()
    print("Audio Listener Process Started")
    try:
        while True:
            time.sleep(1)
    except KeyboardInterrupt:
        listener.stop()

if __name__ == "__main__":
    main()
