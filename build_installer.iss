; Nippo OCR Application Installer Script
; Requires Inno Setup 6+

[Setup]
AppId={{C6E2A3F7-B0E1-4D88-B08F-E93C3B12D130}
AppName=Nippo OCR
AppVersion=1.0.0
AppPublisher=Nippo Team
DefaultDirName={autopf}\NippoOCR
DefaultGroupName=Nippo OCR
AllowNoIcons=yes
OutputDir=setup_output
OutputBaseFilename=Nippo_OCR_Setup
Compression=lzma
SolidCompression=yes
WizardStyle=modern

[Languages]
Name: "japanese"; MessagesFile: "compiler:Languages\Japanese.isl"

[Tasks]
Name: "desktopicon"; Description: "{cm:CreateDesktopIcon}"; GroupDescription: "{cm:AdditionalIcons}"; Flags: unchecked

[Files]
Source: "c:\Users\y86as\Nippo\dist\NippoOCR\*"; DestDir: "{app}"; Flags: igornereadonly uninsremovereadonly recursesubdirs createallsubdirs

[Icons]
Name: "{group}\Nippo OCR"; Filename: "{app}\NippoOCR.exe"
Name: "{group}\{cm:UninstallProgram,Nippo OCR}"; Filename: "{uninstallexe}"
Name: "{autodesktop}\Nippo OCR"; Filename: "{app}\NippoOCR.exe"; Tasks: desktopicon

[Run]
Filename: "{app}\NippoOCR.exe"; Description: "{cm:LaunchProgram,Nippo OCR}"; Flags: nowait postinstall skipifsilent
