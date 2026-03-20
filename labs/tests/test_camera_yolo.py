
import cv2
import sys
from ultralytics import YOLO

def main():
    print("[1/5] Initializing YOLOv8n-pose...")
    try:
        model = YOLO("yolov8n-pose.pt")
        print(" -> Model loaded successfully.")
    except Exception as e:
        print(f" -> Model load failed: {e}")
        return

    print("[2/5] Opening Camera (Index 0)...")
    cap = cv2.VideoCapture(0)
    
    if not cap.isOpened():
        print(" -> Error: Could not open camera.")
        return
    print(" -> Camera opened successfully.")

    print("[3/5] Reading frame...")
    ret, frame = cap.read()
    if not ret:
        print(" -> Error: Can't receive frame (stream end?).")
    else:
        print(f" -> Frame received! Size: {frame.shape}")
        
        print("[4/5] Running YOLO Inference...")
        results = model(frame, verbose=False)
        annotated_frame = results[0].plot()
        
        print("[5/5] Saving debug image...")
        cv2.imwrite("camera_test_result.jpg", annotated_frame)
        print(" -> Saved 'camera_test_result.jpg'. Check this file!")

    cap.release()
    print("Done.")

if __name__ == "__main__":
    main()
