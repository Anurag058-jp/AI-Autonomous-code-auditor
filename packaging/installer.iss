#define AppName "Zero-Cost AI Code Auditor"
#define AppVersion "0.1.0"
#define AppPublisher "Zero-Cost AI Code Auditor"
#define AppExe "AI-Code-Auditor.exe"

[Setup]
AppId={{B1432C8A-94E5-40EB-8D99-B1E2432D3F2A}
AppName={#AppName}
AppVersion={#AppVersion}
AppPublisher={#AppPublisher}
DefaultDirName={autopf}\Zero-Cost AI Code Auditor
DefaultGroupName={#AppName}
OutputDir=..\outputs\windows\installer
OutputBaseFilename=Zero-Cost-AI-Code-Auditor-Setup-{#AppVersion}
Compression=lzma2
SolidCompression=yes
WizardStyle=modern
ArchitecturesInstallIn64BitMode=x64compatible

[Files]
Source: "..\outputs\windows\AI-Code-Auditor\*"; DestDir: "{app}"; Flags: ignoreversion recursesubdirs createallsubdirs
Source: "..\outputs\windows\audit\*"; DestDir: "{app}\cli"; Flags: ignoreversion recursesubdirs createallsubdirs

[Icons]
Name: "{autoprograms}\{#AppName}"; Filename: "{app}\{#AppExe}"
Name: "{autoprograms}\{#AppName} CLI"; Filename: "{app}\cli\audit.exe"; WorkingDir: "{userdocs}"
Name: "{autodesktop}\{#AppName}"; Filename: "{app}\{#AppExe}"; Tasks: desktopicon

[Tasks]
Name: "desktopicon"; Description: "Create a desktop shortcut"; GroupDescription: "Additional shortcuts:"

[Run]
Filename: "{app}\{#AppExe}"; Description: "Launch {#AppName}"; Flags: nowait postinstall skipifsilent
