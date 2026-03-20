import time
import sys
import os

from nippo_system.input_monitor.input_monitor import InputMonitor
from nippo_system.core.storage import StorageManager
from nippo_system.core.config import INPUT_STREAM_DIR, DATA_DIR as NIPPO_DATA_DIR
from datetime import datetime
import logging

# ロギング設定 (ファイルへの書き出し)
LOG_FILE = os.path.join(NIPPO_DATA_DIR, "input_monitor.log")
logging.basicConfig(
    filename=LOG_FILE,
    level=logging.INFO,
    format='%(asctime)s [%(levelname)s] %(message)s',
    encoding='utf-8'
)
logger = logging.getLogger(__name__)

def main():
    logger.info("--- Input Monitor Starting ---")
    try:
        store = StorageManager()
        monitor = InputMonitor()
        monitor.start()
        logger.info("Input Monitor Process Started and listeners active.")
    except Exception as e:
        logger.error(f"Failed to initialize InputMonitor: {e}", exc_info=True)
        return
    try:
        while True:
            time.sleep(5)
            stats = monitor.get_stats()
            if stats['keys'] > 0 or stats['mouse'] > 0:
                logger.info(f"Captured activity: keys={stats['keys']}, mouse={stats['mouse']}, events={len(stats['events'])}")
                # 1. データベースへの保存
                store.save_log("input", f"Keys: {stats['keys']}, Mouse: {stats['mouse']}", {"window": stats['window']})
                
                # 2. 未加工ストリームへの保存 (Stage 1)
                try:
                    now = time.localtime()
                    date_str = time.strftime('%Y-%m-%d', now)
                    
                    kb_path = os.path.join(INPUT_STREAM_DIR, f"keyboard_events_{date_str}.tsv")
                    ms_path = os.path.join(INPUT_STREAM_DIR, f"mouse_events_{date_str}.tsv")
                    
                    with open(kb_path, "a", encoding="utf-8") as f_kb, \
                         open(ms_path, "a", encoding="utf-8") as f_ms:
                        
                        for ev in stats['events']:
                            time_str = datetime.fromtimestamp(ev['time']).strftime('%H:%M:%S.%f')[:-3]
                            win = ev['window'].replace('\t', ' ').replace('\n', ' ')
                            
                            if ev['type'] == 'key':
                                # [時刻] [Window] [Key]
                                f_kb.write(f"{time_str}\t{win}\t{ev['val']}\n")
                            elif ev['type'] == 'click':
                                # [時刻] [Window] [X] [Y] [Button]
                                x, y = ev['pos']
                                f_ms.write(f"{time_str}\t{win}\t{x}\t{y}\t{ev['val']}\n")
                except Exception as e:
                    logger.error(f"Failed to save input stream: {e}", exc_info=True)
    except KeyboardInterrupt:
        logger.info("Input Monitor received KeyboardInterrupt.")
        monitor.stop()
    except Exception as e:
        logger.critical(f"Input Monitor crashed: {e}", exc_info=True)

if __name__ == "__main__":
    main()
