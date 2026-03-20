import os
import shutil
import PyInstaller.__main__

def build():
    # スクリプトの場所（packaging/）の親ディレクトリをルートとする
    root_dir = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
    main_script = os.path.join(root_dir, "nippo_system", "gui_app.py")
    
    hidden_imports = [
        "customtkinter",
        "pystray",
        "PIL",
        "numpy",
        "cv2",
        "pytesseract",
        "pynput",
        "winrt.windows.media.ocr",
        "winrt.windows.graphics.imaging",
        "winrt.windows.storage.streams",
        "win32gui",
        "win32process",
        "nippo_system.ocr.run_ocr",
        "nippo_system.input_monitor.run_input",
        "nippo_system.transformer.main_transformer",
        "nippo_system.reporter.aggregator",
        "nippo_system.transformer.annotators"
    ]
    
    args = [
        main_script,
        "--name=NippoSystem",
        "--onedir",
        "--noconsole",
        "--noconfirm",
        # "--clean",  # 次回以降のビルドを爆速にするためキャッシュを保持
        "--exclude-module=matplotlib",
        "--exclude-module=seaborn",
        "--exclude-module=IPython",
        "--exclude-module=PyQt5",
        "--exclude-module=PyQt6",
        "--exclude-module=tensorboard",
        "--exclude-module=torch",
        "--exclude-module=torchvision",
        "--exclude-module=ultralytics",
    ]
    
    for imp in hidden_imports:
        args.extend(["--hidden-import", imp])
        
    print(f"Running PyInstaller with args: {args}")
    PyInstaller.__main__.run(args)
    
    # 配布用フォルダの構築 (onedir モード)
    dist_dir = os.path.join(root_dir, "dist")
    build_output_dir = os.path.join(dist_dir, "NippoSystem")
    release_dir = os.path.join(dist_dir, "NippoSystem_Release")
    
    if os.path.exists(release_dir):
        shutil.rmtree(release_dir)
        
    if os.path.exists(build_output_dir):
        # build_output_dir をそのまま release_dir としてリネーム（またはコピー）
        shutil.copytree(build_output_dir, release_dir)
        
        # 必要な共有データを横にコピー
        for folder in ["data", "raw_streams", "ai_prompts", "reports"]:
            src = os.path.join(root_dir, "nippo_system", folder)
            dst = os.path.join(release_dir, folder)
            if os.path.exists(src):
                shutil.copytree(src, dst, dirs_exist_ok=True)
            else:
                os.makedirs(dst, exist_ok=True)
                
        print(f"\nBuild Complete!\nRelease Folder: {release_dir}\nPlease run NippoSystem.exe from there.")

if __name__ == "__main__":
    build()
