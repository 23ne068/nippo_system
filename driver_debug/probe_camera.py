
import cv2

def test_camera(index, backend_name, backend_id):
    print(f"Testing Index {index} with {backend_name}...")
    cap = cv2.VideoCapture(index, backend_id)
    if not cap.isOpened():
        print(f" -> Failed to open.")
        return False
    
    ret, frame = cap.read()
    if ret:
        print(f" -> SUCCESS! Frame size: {frame.shape}")
        cap.release()
        return True
    else:
        print(f" -> Failed to read frame.")
        cap.release()
        return False

print("--- Camera Probe Start ---")
backends = [
    ("Default", cv2.CAP_ANY),
    ("MSMF", cv2.CAP_MSMF),
    ("DSHOW", cv2.CAP_DSHOW)
]

for name, bid in backends:
    for i in range(2):
        if test_camera(i, name, bid):
            print(f"*** FOUND WORKING CONFIG: Index {i}, Backend {name} ***")

print("--- Camera Probe End ---")
