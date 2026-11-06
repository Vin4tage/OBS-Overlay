<#
 Optionale Installationshilfe / optional installer helper.
 Lädt den OFFIZIELLEN Python-Installer von python.org und installiert ihn still in ..\runtime\python
 (nur für den aktuellen Benutzer, inkl. Tcl/Tk, ohne PATH-Änderung).
 Downloads the OFFICIAL python.org installer and installs it silently into ..\runtime\python.
 Hinweis: Der Installer trägt Python zusätzlich in "Apps & Features" des Benutzers ein.
#>
$ErrorActionPreference = "Stop"
$Version = "3.12.10"
$Url = "https://www.python.org/ftp/python/$Version/python-$Version-amd64.exe"
$Target = Join-Path (Split-Path $PSScriptRoot -Parent) "runtime\python"
$Installer = Join-Path $env:TEMP "python-$Version-amd64.exe"

if (Test-Path (Join-Path $Target "python.exe")) {
    Write-Host "Python ist bereits vorhanden / already installed: $Target"
} else {
    Write-Host "Lade / downloading $Url ..."
    Invoke-WebRequest -Uri $Url -OutFile $Installer
    Write-Host "Installiere nach / installing to $Target ..."
    $args = @("/quiet", "InstallAllUsers=0", "TargetDir=`"$Target`"", "Include_tcltk=1",
              "Include_pip=0", "Include_test=0", "Include_doc=0", "Include_launcher=0",
              "InstallLauncherAllUsers=0", "Shortcuts=0", "PrependPath=0", "AssociateFiles=0")
    $p = Start-Process -FilePath $Installer -ArgumentList $args -Wait -PassThru
    if ($p.ExitCode -ne 0) { throw "Installer-Fehlercode / exit code $($p.ExitCode)" }
    Remove-Item $Installer -ErrorAction SilentlyContinue
}

$checker = Join-Path $PSScriptRoot "check_environment.py"
& (Join-Path $Target "python.exe") $checker
Write-Host ""
Write-Host "In OBS eintragen / enter in OBS (Werkzeuge/Tools > Skripte/Scripts > Python-Einstellungen):"
Write-Host "  $Target"
