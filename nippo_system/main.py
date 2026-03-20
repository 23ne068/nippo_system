import time
import subprocess
import sys
import os
import signal
import re

# nippo_system/main.py

def cleanup_zombies():
    """
    Starts up by killing any existing nippo_system processes to prevent
    duplicate/zombie processes (e.g. from previous crashes).
    """
    print("Checking for zombie processes...", flush=True)
    my_pid = os.getpid()
    
    # Use PowerShell to get command lines of python processes (more robust than tasklist on Windows)
    ps_cmd = "Get-CimInstance Win32_Process | Where-Object { $_.Name -like 'python*' -and $_.CommandLine -like '*nippo_system*' } | Select-Object ProcessId, CommandLine"
    
    try:
        # Run PowerShell command
        result = subprocess.run(
            ["powershell", "-Command", ps_cmd],
            capture_output=True,
            text=True
        )
        
        if result.returncode != 0:
            print("Warning: Could not check for zombies (PowerShell failed).", flush=True)
            return

        lines = result.stdout.strip().split('\n')
        # Skip header lines usually returned by PowerShell Select-Object
        # Format usually: ProcessId CommandLine
        #                 --------- -----------
        #                 1234      python ...
        
        for line in lines:
            line = line.strip()
            if not line: continue
            
            # Simple parsing: First continuous digits is PID
            parts = line.split(maxsplit=1)
            if len(parts) < 2: continue
            
            pid_str = parts[0]
            if not pid_str.isdigit(): continue
            
            pid = int(pid_str)
            
            if pid == my_pid:
                continue
                
            print(f"Killing zombie process {pid}: {parts[1][:50]}...", flush=True)
            try:
                subprocess.run(["taskkill", "/F", "/PID", str(pid)], stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL)
            except Exception as e:
                print(f"Failed to kill {pid}: {e}", flush=True)

    except Exception as e:
        print(f"Error during cleanup: {e}", flush=True)


def main():
    cleanup_zombies()
    python_exe = sys.executable
    # nippo_systemディレクトリ
    current_dir = os.path.dirname(os.path.abspath(__file__))
    # 親ディレクトリ (Nippo)
    parent_dir = os.path.dirname(current_dir)

    processes = []

    try:
        from nippo_system.core.config import ENABLE_INPUT_MONITOR, ENABLE_AUDIO, ENABLE_SCREEN_OCR, ENABLE_USER_STATE
    except ImportError:
        # 直接実行時等のフォールバック
        sys.path.append(parent_dir)
        from nippo_system.core.config import ENABLE_INPUT_MONITOR, ENABLE_AUDIO, ENABLE_SCREEN_OCR, ENABLE_USER_STATE

    def start_module(module_name):
        print(f"Starting module: {module_name} (Priority: Idle)", flush=True)
        # Windows specific: IDLE_PRIORITY_CLASS = 0x00000040
        # This makes the process only run when the CPU is not needed by other tasks.
        creation_flags = 0
        if os.name == 'nt':
            creation_flags = 0x00000040 # IDLE_PRIORITY_CLASS

        p = subprocess.Popen(
            [python_exe, "-m", module_name], 
            cwd=parent_dir,
            stdout=sys.stdout,
            stderr=sys.stderr,
            creationflags=creation_flags,
            bufsize=0
        )
        return p

    if ENABLE_INPUT_MONITOR:
        p = start_module("nippo_system.input_monitor.run_input")
        processes.append(("InputMonitor", p))
    
    if ENABLE_AUDIO:
        p = start_module("nippo_system.audio.run_audio")
        processes.append(("AudioMonitor", p))

    if ENABLE_SCREEN_OCR:
        # PENDING_FRAMES等、必要な変数はconfig読み込み時に作成済み
        p = start_module("nippo_system.ocr.run_ocr")
        processes.append(("ScreenOCR", p))

    # User requested to disable camera (User State) for now
    # if ENABLE_USER_STATE:
    #     p = start_module("nippo_system.run_state")
    #     processes.append(p)

    try:
        from nippo_system.core.config import DATA_DIR, OCR_STREAM_DIR
        last_log_pos = 0
        while True:
            time.sleep(10) # 10秒おきにステータス提示
            
            # --- 1. プロセス生存確認 ---
            module_status = []
            for name, p in processes:
                if p.poll() is None:
                    module_status.append(f"{name}: [ALIVE]")
                else:
                    module_status.append(f"{name}: [DEAD!]")
            
            # --- 2. Input/OCRの最新活動をログから抜粋 ---
            heartbeat_msg = f"--- Heartbeat [{time.strftime('%H:%M:%S')}] ---"
            print(f"\n{heartbeat_msg}", flush=True)
            print(" | ".join(module_status), flush=True)
            
            # Input Monitorの最新1行
            log_path = os.path.join(DATA_DIR, "input_monitor.log")
            if os.path.exists(log_path):
                try:
                    with open(log_path, "r", encoding="utf-8") as f:
                        lines = f.readlines()
                        if lines:
                            print(f" [Input] {lines[-1].strip()}", flush=True)
                except: pass

            # OCRの最新結果ファイル日付確認
            now = time.localtime()
            date_str = time.strftime('%Y-%m-%d', now)
            ocr_file = os.path.join(OCR_STREAM_DIR, f"ocr_stream_{date_str}.tsv")
            if os.path.exists(ocr_file):
                try:
                    mtime = time.strftime('%H:%M:%S', time.localtime(os.path.getmtime(ocr_file)))
                    print(f" [OCR  ] Stream file updated at: {mtime}", flush=True)
                except: pass
            
            print("-" * len(heartbeat_msg), flush=True)

            # 異常終了時の警告
            for name, p in processes:
                if p.poll() is not None:
                    print(f"CRITICAL: Process {name} (PID: {p.pid}) has stopped!", flush=True)
    except KeyboardInterrupt:
        print("Stopping all processes...", flush=True)
        for p in processes:
            p.terminate()
        time.sleep(1)
        for p in processes:
            if p.poll() is None:
                p.kill()

if __name__ == "__main__":
    main()
