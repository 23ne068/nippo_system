import cv2
import subprocess
import os
import sys

def check_pnp_devices():
    print("=== Windows PnP Camera Devices ===")
    try:
        # PowerShell command to list Cameras and Imaging devices
        cmd = "Get-PnpDevice -Class Camera,Image | Select-Object Status, Class, FriendlyName, InstanceId | Format-Table -AutoSize"
        result = subprocess.run(["powershell", "-Command", cmd], capture_output=True, text=True)
        print(result.stdout)
        
        # Check for problem devices
        cmd_err = "Get-PnpDevice -Class Camera,Image | Where-Object { $_.Status -ne 'OK' } | Select-Object FriendlyName, Status, StatusDescription"
        res_err = subprocess.run(["powershell", "-Command", cmd_err], capture_output=True, text=True)
        if res_err.stdout.strip():
            print("\n[!!!] PROBLEM DEVICES FOUND:")
            print(res_err.stdout)
        else:
            print("[OK] No PnP errors detected for Camera/Image devices.")
            
    except Exception as e:
        print(f"Error checking PnP: {e}")

def check_opencv_indices():
    print("\n=== OpenCV Camera Index Probe ===")
    available = []
    
    # Check first 5 indices
    for index in range(5):
        try:
            cap = cv2.VideoCapture(index, cv2.CAP_DSHOW) # Use DirectShow for Windows
            if cap.isOpened():
                ret, frame = cap.read()
                if ret:
                    w = cap.get(cv2.CAP_PROP_FRAME_WIDTH)
                    h = cap.get(cv2.CAP_PROP_FRAME_HEIGHT)
                    fps = cap.get(cv2.CAP_PROP_FPS)
                    print(f"[OK] Index {index}: Opened successfully. Res: {int(w)}x{int(h)} @ {fps}fps")
                    available.append(index)
                else:
                    print(f"[WARN] Index {index}: Opened but failed to read frame.")
                cap.release()
            else:
                print(f"[FAIL] Index {index}: Failed to open.")
        except Exception as e:
            print(f"[ERR] Index {index}: Error {e}")
            
    if not available:
        print("\n[CRITICAL] No usable camera indices found via OpenCV.")
    else:
        print(f"\nTime to update config.py? Found cameras at: {available}")

if __name__ == "__main__":
    check_pnp_devices()
    print("-" * 30)
    check_opencv_indices()
