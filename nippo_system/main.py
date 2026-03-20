import os
import sys
import time
import threading
import subprocess
import customtkinter as ctk
from PIL import Image, ImageDraw
import pystray

# --- Auto Startup Setup ---
def get_startup_bat_path():
    appdata = os.environ.get('APPDATA')
    if not appdata: return ""
    return os.path.join(appdata, r"Microsoft\Windows\Start Menu\Programs\Startup\NippoSystem.bat")

def is_startup_enabled():
    path = get_startup_bat_path()
    return os.path.exists(path) if path else False

def toggle_startup():
    path = get_startup_bat_path()
    if not path: return False
    if is_startup_enabled():
        try: os.remove(path)
        except: pass
        return False
    else:
        is_frozen = getattr(sys, 'frozen', False)
        if is_frozen:
            exe_to_use = sys.executable
            # .exe 化されている場合はスクリプトのパスは不要
            cmd_line = f'start "" /B "{exe_to_use}" --tray\n'
        else:
            python_exe = sys.executable
            script_path = os.path.abspath(__file__)
            pythonw_exe = python_exe.replace("python.exe", "pythonw.exe")
            exe_to_use = pythonw_exe if os.path.exists(pythonw_exe) else python_exe
            cmd_line = f'start "" /B "{exe_to_use}" "{script_path}" --tray\n'
            
        try:
            with open(path, "w", encoding="utf-8") as f:
                f.write(f'@echo off\n{cmd_line}')
            return True
        except: return False

# --- Paths and Setup ---
current_dir = os.path.dirname(os.path.abspath(__file__))
parent_dir = os.path.dirname(current_dir)
python_exe = sys.executable

try:
    from nippo_system.core.config import ENABLE_INPUT_MONITOR, ENABLE_AUDIO, ENABLE_SCREEN_OCR, DATA_DIR, OCR_STREAM_DIR
except ImportError:
    sys.path.append(parent_dir)
    from nippo_system.core.config import ENABLE_INPUT_MONITOR, ENABLE_AUDIO, ENABLE_SCREEN_OCR, DATA_DIR, OCR_STREAM_DIR

try:
    from nippo_system.transformer.main_transformer import MainTransformer
    from nippo_system.reporter.aggregator import StoryAggregator
except ImportError:
    pass

# --- System Manager (Ported and upgraded from main.py) ---
class NippoSystemManager:
    def __init__(self):
        self.processes = []
        
    def start_all(self):
        # self.cleanup_zombies()
        
        if ENABLE_INPUT_MONITOR:
            self._spawn("nippo_system.input_monitor.run_input", "InputMonitor")
        if ENABLE_AUDIO:
            self._spawn("nippo_system.audio.run_audio", "AudioMonitor")
        if ENABLE_SCREEN_OCR:
            self._spawn("nippo_system.ocr.run_ocr", "ScreenOCR (WinRT/Tesseract)")

    def _spawn(self, module_name, friendly_name):
        creation_flags = 0x00000040 if os.name == 'nt' else 0 # IDLE_PRIORITY_CLASS
        
        # PyInstallerでパッケージ化されている場合（sys.frozenがTrue）
        is_frozen = getattr(sys, 'frozen', False)
        if is_frozen:
            cmd = [sys.executable, "--run-module", module_name]
            out_dest = subprocess.DEVNULL
            err_dest = subprocess.DEVNULL
        else:
            cmd = [python_exe, "-m", module_name]
            out_dest = sys.stdout
            err_dest = sys.stderr

        p = subprocess.Popen(
            cmd, 
            cwd=parent_dir,
            stdout=out_dest,
            stderr=err_dest,
            creationflags=creation_flags
        )
        self.processes.append((friendly_name, p))
        
    def stop_all(self):
        for name, p in self.processes:
            p.terminate()
        time.sleep(1)
        for name, p in self.processes:
            if p.poll() is None:
                p.kill()
        self.processes = []

    def cleanup_zombies(self):
        import os
        my_pid = os.getpid()
        ps_cmd = 'Get-CimInstance Win32_Process | Where-Object { $_.Name -like "python*" -and $_.CommandLine -like "*nippo_system*" } | Select-Object ProcessId'
        try:
            result = subprocess.run(["powershell", "-Command", ps_cmd], capture_output=True, text=True, timeout=10)
            lines = result.stdout.strip().split('\n')
            for line in lines:
                if "ProcessId" in line or "---" in line or not line.strip(): continue
                parts = line.strip().split()
                if not parts: continue
                try:
                    pid = int(parts[0])
                    if pid == my_pid: continue
                    subprocess.run(["taskkill", "/F", "/PID", str(pid)], stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL)
                except: pass
        except:
            pass

    def get_status(self):
        status_dict = {}
        for name, p in self.processes:
            status_dict[name] = "🟢 稼働中 (Running)" if p.poll() is None else "🔴 停止 (Stopped/Error)"
        return status_dict

# --- GUI App (CustomTkinter) ---
class NippoDashboard(ctk.CTk):
    def __init__(self, manager, tray_icon):
        super().__init__()
        self.manager = manager
        self.tray_icon = tray_icon
        
        # プレミアムでモダンなウィンドウ設定
        self.title("Nippo System 稼働ダッシュボード")
        self.geometry("1150x500")
        # 色設定
        ctk.set_appearance_mode("dark")  # ダークモード
        ctk.set_default_color_theme("blue")
        
        # UI レイアウト構築
        self.header = ctk.CTkLabel(self, text="Nippo System", font=("Segoe UI", 28, "bold"))
        self.header.pack(pady=(30, 10))
        
        self.subtitle = ctk.CTkLabel(self, text="バックグラウンドプロセス状況", font=("Segoe UI", 14), text_color="gray")
        self.subtitle.pack(pady=(0, 20))
        
        self.status_frame = ctk.CTkFrame(self, corner_radius=15)
        self.status_frame.pack(pady=10, padx=40, fill="both", expand=True)
        
        # --- Startup Toggle ---
        self.startup_var = ctk.BooleanVar(value=is_startup_enabled())
        self.startup_switch = ctk.CTkSwitch(
            self, text="PC起動時に背後で自動スタートする（スタートアップ登録）", 
            variable=self.startup_var, command=self.on_startup_toggle,
            font=("Segoe UI", 14, "bold")
        )
        self.startup_switch.pack(pady=10)
        
        self.btn_frame = ctk.CTkFrame(self, fg_color="transparent")
        self.btn_frame.pack(pady=15)
        
        # --- Add "Open Data Folder" Button ---
        self.open_folder_btn = ctk.CTkButton(self.btn_frame, text="📂 記録データを開く", font=("Segoe UI", 14, "bold"),
                                             width=180, height=40, command=self.open_data_folder)
        self.open_folder_btn.pack(side="left", padx=10)
        
        # --- Add "Generate YAML" Button ---
        self.generate_btn = ctk.CTkButton(self.btn_frame, text="📝 作業終了（YAML作成）", font=("Segoe UI", 14, "bold"),
                                          width=200, height=40, fg_color="#2E7D32", hover_color="#1B5E20", 
                                          command=self.generate_yaml)
        self.generate_btn.pack(side="left", padx=10)
        
        # --- Add "Copy Prompt" Button ---
        self.copy_btn = ctk.CTkButton(self.btn_frame, text="📋 プロンプト＋YAMLをコピー", font=("Segoe UI", 14, "bold"),
                                      width=230, height=40, fg_color="#1565C0", hover_color="#0D47A1", 
                                      command=self.copy_prompt)
        self.copy_btn.pack(side="left", padx=10)
        
        self.hide_btn = ctk.CTkButton(self.btn_frame, text="最小化して常駐 (トレイへ)", font=("Segoe UI", 14, "bold"), 
                                      width=200, height=40, command=self.hide_to_tray)
        self.hide_btn.pack(side="left", padx=10)
        
        self.quit_btn = ctk.CTkButton(self.btn_frame, text="完全に終了", fg_color="#C62828", hover_color="#8E0000",
                                      font=("Segoe UI", 14, "bold"), width=150, height=40, command=self.quit_app)
        self.quit_btn.pack(side="left", padx=10)
        
        # ウィンドウの[X]ボタンを押した時は終了せず、トレイに隠す
        self.protocol("WM_DELETE_WINDOW", self.hide_to_tray)

        self.update_status_ui()
        
    def update_status_ui(self):
        # 古いステータスを消去
        for widget in self.status_frame.winfo_children():
            widget.destroy()
            
        status = self.manager.get_status()
        if not status:
            l = ctk.CTkLabel(self.status_frame, text="有効なモジュールがありません", font=("Segoe UI", 16))
            l.pack(pady=20)
        else:
            for name, state in status.items():
                color = "#4CAF50" if "稼働中" in state else "#E53935"
                l = ctk.CTkLabel(self.status_frame, text=f"{name}  :  {state}", font=("Segoe UI", 18, "bold"), text_color=color)
                l.pack(pady=15)
                
        # 2秒ごとに自動更新
        self.after(2000, self.update_status_ui)
        
    def on_startup_toggle(self):
        new_state = toggle_startup()
        self.startup_var.set(new_state)
        
    def _run_generation_task(self, open_viewer=False, copy_to_clipboard=False):
        try:
            # 1. 意味付け処理 (Transformer)
            transformer = MainTransformer()
            transformer.run()
            
            # 2. YAML生成 (Aggregator)
            aggregator = StoryAggregator()
            story = aggregator.aggregate()
            yaml_path = aggregator.save_yaml(story)
            
            if open_viewer and os.path.exists(yaml_path):
                # 生成したファイルをWindowsの既定アプリ（エディタ）で開く
                if os.name == 'nt':
                    os.startfile(yaml_path)
                else:
                    subprocess.run(['xdg-open', yaml_path])
                    
            if copy_to_clipboard and os.path.exists(yaml_path):
                self._do_clipboard_copy(yaml_path)
                
        except Exception as e:
            print(f"Failed to generate YAML/Copy: {e}")
            if copy_to_clipboard:
                self.after(0, lambda: self.copy_btn.configure(text="❌ エラー発生", state="normal"))
                self.after(2000, lambda: self.copy_btn.configure(text="📋 プロンプト＋YAMLをコピー"))
        finally:
            if not copy_to_clipboard:
                # UI更新はメインスレッドで
                self.after(0, lambda: self.generate_btn.configure(text="📝 作業終了（YAML作成）", state="normal"))

    def generate_yaml(self):
        self.generate_btn.configure(text="⏳ 生成中...", state="disabled")
        # 画面が固まらないようにバックグラウンドスレッドで重い処理を実行
        threading.Thread(target=self._run_generation_task, kwargs={"open_viewer": True}, daemon=True).start()

    def copy_prompt(self):
        self.copy_btn.configure(text="⏳ 生成・コピー中...", state="disabled")
        threading.Thread(target=self._run_generation_task, kwargs={"copy_to_clipboard": True}, daemon=True).start()

    def _do_clipboard_copy(self, yaml_path):
        try:
            # 外部編集可能なベースディレクトリ（exeの隣）からプロンプトを探す
            from nippo_system.core.config import BASE_DIR
            prompt_path = os.path.join(BASE_DIR, "ai_prompts", "PROMPT_TEMPLATE.md")
            
            # 念のため、見つからない場合は従来のパスもフォールバックとして探す
            if not os.path.exists(prompt_path):
                prompt_path = os.path.join(current_dir, "ai_prompts", "PROMPT_TEMPLATE.md")
                
            with open(yaml_path, "r", encoding="utf-8") as f:
                yaml_content = f.read()
                
            prompt_content = "[ここに YAML ファイルの内容を貼り付けてください]"
            if os.path.exists(prompt_path):
                with open(prompt_path, "r", encoding="utf-8") as f:
                    prompt_content = f.read()
                    
            final_text = prompt_content.replace("[ここに YAML ファイルの内容を貼り付けてください]", yaml_content)
            
            self.clipboard_clear()
            self.clipboard_append(final_text)
            self.update()
            
            self.after(0, lambda: self.copy_btn.configure(text="✅ コピー完了！", state="normal"))
            self.after(3000, lambda: self.copy_btn.configure(text="📋 プロンプト＋YAMLをコピー"))
        except Exception as e:
            print(f"Failed to copy prompt: {e}")

    def open_data_folder(self):
        try:
            # 記録データのルートフォルダ（raw_streams 等）を開く
            target_dir = os.path.dirname(OCR_STREAM_DIR) if os.path.exists(os.path.dirname(OCR_STREAM_DIR)) else DATA_DIR
            if os.name == 'nt':
                os.startfile(target_dir)
            else:
                subprocess.run(['xdg-open', target_dir])
        except Exception as e:
            print(f"Failed to open folder: {e}")

    def hide_to_tray(self):
        self.withdraw()  # ウィンドウを隠す
        
    def show_window(self):
        self.deiconify() # ウィンドウを再表示
        self.focus_force()
        
    def quit_app(self):
        self.manager.stop_all() # 全ての子プロセスを終了
        self.tray_icon.stop()   # トレイアイコンを消す
        self.destroy()          # GUIを閉じる

# --- System Tray Icon (pystray) ---
def create_image():
    # シンプルな仮アイコン画像（青い背景に白で"N"）
    image = Image.new('RGB', (64, 64), color = (0, 102, 204))
    d = ImageDraw.Draw(image)
    # デフォルトフォントで小さくなりますが後でデザイン変更できます
    d.text((25, 25), "N", fill=(255, 255, 255))
    return image

def setup_tray():
    # 後から app インスタンスを渡すためのクラスまたは変数の器を作る
    class TrayController:
        def __init__(self):
            self.app = None
            
        def show_action(self, icon, item):
            if self.app:
                # tkinterはメインスレッドから呼ばないとエラーになるため after を使う
                self.app.after(0, self.app.show_window)
            
        def quit_action(self, icon, item):
            if self.app:
                self.app.after(0, self.app.quit_app)

    controller = TrayController()
    image = create_image()
    menu = pystray.Menu(
        pystray.MenuItem('ダッシュボードを開く', controller.show_action, default=True),
        pystray.MenuItem('Nippoを完全に終了', controller.quit_action)
    )
    icon = pystray.Icon("Nippo", image, "Nippo System", menu)
    return icon, controller

if __name__ == "__main__":
    # --- PyInstaller向けモジュール起動モード ---
    if "--run-module" in sys.argv:
        try:
            mod_idx = sys.argv.index("--run-module") + 1
            mod_name = sys.argv[mod_idx]
            import runpy
            runpy.run_module(mod_name, run_name="__main__")
        except Exception as e:
            print(f"Failed to run module: {e}")
        sys.exit(0)

    # --- 二重起動防止 (GUIモードのみ適用) ---
    is_frozen = getattr(sys, 'frozen', False)
    if is_frozen:
        import subprocess
        my_pid = os.getpid()
        # 自身以外の同名プロセスを終了させる
        # /FI "PID ne {my_pid}" で自分を除外, /T で子プロセスも含めて終了
        subprocess.run(['taskkill', '/F', '/IM', 'NippoSystem.exe', '/FI', f'PID ne {my_pid}'], 
                       capture_output=True, creationflags=0x08000000) # CREATE_NO_WINDOW

    start_hidden = "--tray" in sys.argv

    try:
        print("1. Starting System Manager...", flush=True)
        # 1. バックグラウンドプロセスの起動
        manager = NippoSystemManager()
        manager.start_all()
        print("2. System Manager started. Setting up tray...", flush=True)
        
        # 2. トレイ常駐アイコンの準備
        icon, tray_controller = setup_tray()
        print("3. Tray setup OK. Creating Dashboard...", flush=True)
        
        # 3. GUIメイン画面の準備
        app = NippoDashboard(manager, icon)
        tray_controller.app = app
        print("4. Dashboard created. Running tray thread...", flush=True)
        
        # 4. pystray（常駐アイコン）を裏の監視スレッドで動かす
        tray_thread = threading.Thread(target=icon.run, daemon=True)
        tray_thread.start()
        print("5. Tray thread started. Entering mainloop...", flush=True)
        
        # 5. Tkinter（メイン画面）のループ開始
        if start_hidden:
            app.withdraw() # スタートアップ時は画面を出さずにトレイへ直行
            
        app.mainloop()
    except Exception as e:
        import traceback
        with open("error_log.txt", "w", encoding="utf-8") as f:
            f.write(str(e) + "\n" + traceback.format_exc())
        sys.exit(1)
