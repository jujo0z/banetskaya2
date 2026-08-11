; Inno Setup script — собирает единый BanetskayaSetup.exe из сборки PyInstaller (onedir).
; Компилируется на Windows: iscc windows-package\installer\installer.iss
; Пути указаны относительно расположения этого .iss (корень проекта = ..\..).

[Setup]
AppName=Banetskaya.by
AppVersion=1.0
AppPublisher=Banetskaya.by
DefaultDirName={autopf}\Banetskaya
DefaultGroupName=Banetskaya.by
DisableProgramGroupPage=yes
OutputDir=..\..\installer_output
OutputBaseFilename=BanetskayaSetup
Compression=lzma2
SolidCompression=yes
ArchitecturesInstallIn64BitMode=x64
ArchitecturesAllowed=x64
PrivilegesRequired=admin
WizardStyle=modern

[Languages]
Name: "russian"; MessagesFile: "compiler:Languages\Russian.isl"

[Tasks]
Name: "desktopicon"; Description: "Создать ярлык на рабочем столе"; GroupDescription: "Дополнительно:"

[Files]
Source: "..\..\dist\Banetskaya\*"; DestDir: "{app}"; Flags: recursesubdirs createallsubdirs ignoreversion

[Icons]
Name: "{group}\Banetskaya.by"; Filename: "{app}\Banetskaya.exe"
Name: "{commondesktop}\Banetskaya.by"; Filename: "{app}\Banetskaya.exe"; Tasks: desktopicon

[Run]
Filename: "{app}\Banetskaya.exe"; Description: "Запустить Banetskaya.by"; Flags: nowait postinstall skipifsilent
