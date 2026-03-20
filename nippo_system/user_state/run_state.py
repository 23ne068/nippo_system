import time
import sys
import os

from nippo_system.user_state.user_state import UserStateMonitor
from nippo_system.core.storage import StorageManager

def main():
    store = StorageManager()
    
    class DBState(UserStateMonitor):
        def on_state_detected(self, state):
            store.save_log("state", state)
            
    mon = DBState()
    mon.start()
    print("User State Process Started")
    try:
        while True:
            time.sleep(1)
    except KeyboardInterrupt:
        mon.stop()

if __name__ == "__main__":
    main()
