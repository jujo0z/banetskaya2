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
SetupIconFile=assets\icon.ico
WizardImageFile=assets\wizard_large.bmp
WizardSmallImageFile=assets\wizard_small.bmp
UninstallDisplayIcon={app}\icon.ico
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
Source: "assets\icon.ico"; DestDir: "{app}"; Flags: ignoreversion

[Icons]
Name: "{group}\Banetskaya.by"; Filename: "{app}\Banetskaya.exe"; IconFilename: "{app}\icon.ico"
Name: "{commondesktop}\Banetskaya.by"; Filename: "{app}\Banetskaya.exe"; IconFilename: "{app}\icon.ico"; Tasks: desktopicon

[Run]
Filename: "{app}\Banetskaya.exe"; Description: "Запустить Banetskaya.by"; Flags: nowait postinstall skipifsilent
