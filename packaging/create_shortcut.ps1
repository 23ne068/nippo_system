# PowerShell script to create a desktop shortcut for Nippo OCR
$WshShell = New-Object -ComObject WScript.Shell
$ShortcutPath = Join-Path ([Environment]::GetFolderPath("Desktop")) "Nippo OCR.lnk"
$TargetPath = "c:\Users\y86as\Nippo\dist\NippoOCR\NippoOCR.exe"
$WorkDir = "c:\Users\y86as\Nippo\dist\NippoOCR"

if (Test-Path $TargetPath) {
    $Shortcut = $WshShell.CreateShortcut($ShortcutPath)
    $Shortcut.TargetPath = $TargetPath
    $Shortcut.WorkingDirectory = $WorkDir
    $Shortcut.IconLocation = "$TargetPath, 0"
    $Shortcut.Save()
    Write-Host "Success: Desktop shortcut created at $ShortcutPath" -ForegroundColor Green
} else {
    Write-Host "Error: Could not find NippoOCR.exe at $TargetPath. Please build the app first." -ForegroundColor Red
}
