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
; При обновлении поверх работающего приложения — корректно закрыть его,
; чтобы заменить файлы (кнопка «Обновить приложение» скачивает и запускает этот же установщик).
CloseApplications=yes
RestartApplications=no

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
; Установить компонент Microsoft Edge WebView2 (нужен для нативного окна приложения).
; Bootstrapper скачивает рантайм онлайн; если уже установлен — быстро завершится.
Filename: "{app}\MicrosoftEdgeWebview2Setup.exe"; Parameters: "/silent /install"; StatusMsg: "Установка компонента WebView2..."; Flags: waituntilterminated
Filename: "{app}\Banetskaya.exe"; Description: "Запустить Banetskaya.by"; Flags: nowait postinstall skipifsilent
