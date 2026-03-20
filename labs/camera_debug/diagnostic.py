
import cv2
import time
import os

def test_camera(index, backend_name, backend_id):
    print(f"\n--- Testing Camera Index {index} with {backend_name} ---")
    cap = cv2.VideoCapture(index, backend_id)
    
    if not cap.isOpened():
        print("  Failed to open camera.")
        return
    
    # プロパティ取得
    width = cap.get(cv2.CAP_PROP_FRAME_WIDTH)
    height = cap.get(cv2.CAP_PROP_FRAME_HEIGHT)
    fps = cap.get(cv2.CAP_PROP_FPS)
    print(f"  Properties: {width}x{height} @ {fps}fps")
    
    # 安定性テスト: 連続読み出し
    print("  Starting stability test (reading 50 frames)...")
    success_count = 0
    start_time = time.time()
    
    try:
        for i in range(50):
            ret, frame = cap.read()
            if ret:
                success_count += 1
                if i % 10 == 0:
                    print(f"    Frame {i}: OK")
            else:
                print(f"    Frame {i}: Failed to read!")
                # 失敗しても少し待って再試行
                time.sleep(0.5)
    except Exception as e:
        print(f"  Error during loop: {e}")
    
    duration = time.time() - start_time
    print(f"  Test finished. Success: {success_count}/50. Duration: {duration:.2f}s")
    
    cap.release()

if __name__ == "__main__":
    print("OpenCV Version:", cv2.__version__)
    
    # インデックス0〜9をテスト
    for i in range(10):
        # MSMF (Default)
        test_camera(i, "Default (MSMF)", cv2.CAP_ANY)
        # DirectShow
        test_camera(i, "DirectShow", cv2.CAP_DSHOW)

    print("\n--- Diagnostic Complete ---")
