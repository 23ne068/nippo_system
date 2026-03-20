@echo off
echo ==================================================
echo   Camera Hardware Reset Script (Run as Admin)
echo ==================================================
echo.
echo Attempting to restart the problematic USB device...
echo Target ID: USB\VID_0000&PID_0002\5&7993a9c&0&3
echo.

pnputil /restart-device "USB\VID_0000&PID_0002\5&7993a9c&0&3"

echo.
echo --------------------------------------------------
echo Status: If you see "Successfully restarted", please try Step 3.
echo If you see "Failed" or "Access Denied", please ensure 
echo you ran as ADMINISTRATOR.
echo --------------------------------------------------
echo.
echo If the camera still shows "Unknown USB Device", 
echo please try the Static Discharge (30s Power Button) method.
echo.
pause
