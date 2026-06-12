; Inno Setup Script for Inventory POS Software
; Generate the Installer by opening this file in Inno Setup and clicking Compile

[Setup]
AppId={{8B3B5C1A-2D3E-4E5F-AF7B-1234567890AB}
AppName=Inventory POS Software
AppVersion=1.0
AppPublisher=Joachim Korang Amponsah
DefaultDirName={autopf}\InventoryPOS
DefaultGroupName=Inventory POS Software
LicenseFile=license_agreement.txt
AllowNoIcons=yes
OutputDir=setup_output
OutputBaseFilename=InventoryPOS_Setup
Compression=lzma
SolidCompression=yes
WizardStyle=modern

[Languages]
Name: "english"; MessagesFile: "compiler:Default.isl"

[Tasks]
Name: "desktopicon"; Description: "{cm:CreateDesktopIcon}"; GroupDescription: "{cm:AdditionalIcons}"; Flags: unchecked

[Files]
Source: "dist\InventoryPOS\*"; DestDir: "{app}"; Flags: ignoreversion recursesubdirs createallsubdirs
; NOTE: Don't include the .db file in the source if you want a clean install every time.
; The app will create a new one on startup if it doesn't exist.

[Icons]
Name: "{group}\Inventory POS"; Filename: "{app}\InventoryPOS.exe"
Name: "{autodesktop}\Inventory POS"; Filename: "{app}\InventoryPOS.exe"; Tasks: desktopicon

[Run]
Filename: "{app}\InventoryPOS.exe"; Description: "{cm:LaunchProgram,Inventory POS Software}"; Flags: nowait postinstall skipifsilent
