; installer.iss — Inno Setup script for Ecology-BI
; Requires: Inno Setup 6 (https://jrsoftware.org/isdl.php)
; Run after build.bat: dist\Ecology-BI\ must exist

#define AppName      "Ecology-BI"
#define AppVersion   "2.0"
#define AppPublisher "Ecology-BI"
#define AppExeName   "Ecology-BI.exe"
#define SourceDir    "dist\Ecology-BI"

[Setup]
AppId={{A7B3C4D5-E6F7-4890-ABCD-EF1234567890}
AppName={#AppName}
AppVersion={#AppVersion}
AppPublisher={#AppPublisher}
AppPublisherURL=https://github.com/ynveyxv-beep/Ecology-BI2
DefaultDirName={autopf}\{#AppName}
DefaultGroupName={#AppName}
OutputDir=installer
OutputBaseFilename=Ecology-BI-Setup
Compression=lzma2/ultra64
SolidCompression=yes
WizardStyle=modern
DisableProgramGroupPage=yes
LicenseFile=
; Require Windows 10+
MinVersion=10.0
ArchitecturesAllowed=x64
ArchitecturesInstallIn64BitMode=x64
; Uninstall info
UninstallDisplayName={#AppName}
UninstallDisplayIcon={app}\{#AppExeName}
; Show "Installing..." in taskbar
ShowLanguageDialog=no
LanguageDetectionMethod=none

[Languages]
Name: "russian"; MessagesFile: "compiler:Languages\Russian.isl"

[Tasks]
Name: "desktopicon"; Description: "Создать ярлык на рабочем столе"

[Files]
; Все файлы из папки dist\Ecology-BI\
Source: "{#SourceDir}\*"; DestDir: "{app}"; Flags: ignoreversion recursesubdirs createallsubdirs

[Dirs]
; Папка для дашбордов — создаётся пустой, не удаляется при деинсталляции
Name: "{app}\templates"; Flags: uninsneveruninstall

[Icons]
; Ярлык в меню Пуск
Name: "{group}\{#AppName}"; Filename: "{app}\{#AppExeName}"
Name: "{group}\Удалить {#AppName}"; Filename: "{uninstallexe}"
; Ярлык на рабочем столе (если выбрано)
Name: "{autodesktop}\{#AppName}"; Filename: "{app}\{#AppExeName}"; Tasks: desktopicon

[Run]
; Запустить после установки
Filename: "{app}\{#AppExeName}"; Description: "Запустить Ecology-BI"; Flags: nowait postinstall skipifsilent

[UninstallRun]
; Ничего дополнительного

[Code]
// Предупреждение если приложение уже запущено
function InitializeSetup(): Boolean;
begin
  Result := True;
end;
