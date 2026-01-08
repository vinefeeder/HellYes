# Install-media-tools.ps1
# Run in elevated PowerShell:
# Inside the VM:

# Open Start

# Type PowerShell

# Right-click Windows PowerShell → Run as administrator

# chdir to the location of this script

#   powershell -ExecutionPolicy Bypass -File .\Install-media-tools.ps1

$ErrorActionPreference = "Stop"

# Where to install (bin folder on PATH)
$BinDir = "C:\Tools\bin"
$ToolsRoot = "C:\Tools"
$SubtitleEditDir = Join-Path $ToolsRoot "SubtitleEdit"
$WorkDir = Join-Path $env:TEMP ("media-tools-" + [guid]::NewGuid().ToString("N"))

New-Item -ItemType Directory -Force -Path $BinDir | Out-Null
New-Item -ItemType Directory -Force -Path $WorkDir | Out-Null
New-Item -ItemType Directory -Force -Path $SubtitleEditDir | Out-Null

function Download-File([string]$Url, [string]$OutFile) {
  Write-Host "Downloading: $Url"
  Invoke-WebRequest -Uri $Url -OutFile $OutFile -UseBasicParsing
}

function Add-ToMachinePath([string]$PathToAdd) {
  $current = [Environment]::GetEnvironmentVariable("Path", "Machine")
  if (-not $current) { $current = "" }

  # Compare case-insensitively on Windows
  $parts = $current.Split(";", [System.StringSplitOptions]::RemoveEmptyEntries)
  $exists = $parts | Where-Object { $_.TrimEnd("\") -ieq $PathToAdd.TrimEnd("\") }

  if (-not $exists) {
    $newPath = ($current.TrimEnd(";") + ";" + $PathToAdd).TrimStart(";")
    [Environment]::SetEnvironmentVariable("Path", $newPath, "Machine")
    Write-Host "Added to MACHINE PATH: $PathToAdd"
    Write-Host "Restart your terminal/session to pick it up."
  } else {
    Write-Host "MACHINE PATH already contains: $PathToAdd"
  }
}

try {
  Push-Location $WorkDir

  # -----------------------------
  # Install FFmpeg (full build, Windows x64) from GitHub ZIP
  # -----------------------------
  $ffmpegZip = Join-Path $WorkDir "ffmpeg-full_build.zip"
  Download-File `
    "https://github.com/GyanD/codexffmpeg/releases/download/2025-12-14-git-3332b2db84/ffmpeg-2025-12-14-git-3332b2db84-full_build.zip" `
    $ffmpegZip

  $ffmpegExtract = Join-Path $WorkDir "ffmpeg"
  New-Item -ItemType Directory -Force -Path $ffmpegExtract | Out-Null
  Expand-Archive -Path $ffmpegZip -DestinationPath $ffmpegExtract -Force

  # Find the extracted "bin" folder (contains ffmpeg.exe etc.)
  $ffmpegBin = Get-ChildItem $ffmpegExtract -Recurse -Directory |
               Where-Object { $_.Name -ieq "bin" } |
               Select-Object -First 1

  if (-not $ffmpegBin) {
    throw "FFmpeg bin directory not found after extraction."
  }

  Get-ChildItem $ffmpegBin.FullName -File |
    Where-Object { $_.Name -match '^ff(mpeg|probe|play)\.exe$' } |
    ForEach-Object {
      Copy-Item -Force $_.FullName (Join-Path $BinDir $_.Name)
    }

  Write-Host "FFmpeg installed to $BinDir"


  # -----------------------------
  # Install Bento4 (mp4decrypt.exe, etc.)
  # -----------------------------
  $bentoZip = Join-Path $WorkDir "Bento4.zip"
  Download-File `
    "https://www.bok.net/Bento4/binaries/Bento4-SDK-1-6-0-641.x86_64-microsoft-win32.zip" `
    $bentoZip
  Expand-Archive -Path $bentoZip -DestinationPath (Join-Path $WorkDir "bento") -Force

  Get-ChildItem -Path (Join-Path $WorkDir "bento") -Recurse -File |
    Where-Object { $_.FullName -match "\\bin\\.*\.exe$" } |
    ForEach-Object { Copy-Item -Force $_.FullName $BinDir }

  # -----------------------------
  # Install MKVToolNix (Windows x64)
  # -----------------------------
  $mkvInstaller = Join-Path $WorkDir "mkvtoolnix-64-bit-96.0-setup.exe"
  Download-File `
    "https://mkvtoolnix.download/windows/releases/96.0/mkvtoolnix-64-bit-96.0-setup.exe" `
    $mkvInstaller

  # Silent install (NSIS): /S = silent
  # Note: no UI will appear; wait for it to finish.
  Start-Process -FilePath $mkvInstaller -ArgumentList "/S" -Wait

  # Optional: add MKVToolNix install dir to PATH if present
  $mkvDefaultPath = "C:\Program Files\MKVToolNix"
  if (Test-Path $mkvDefaultPath) {
    # If you kept Add-ToMachinePath, use that:
    Add-ToMachinePath $mkvDefaultPath

    # Or if you switched to Add-ToBestPath, use that instead:
    # Add-ToBestPath $mkvDefaultPath
  } else {
    Write-Host "MKVToolNix installed, but default path not found: $mkvDefaultPath (maybe different install location)"
  }
  
  # -----------------------------
  # Install N_m3u8DL-RE (Windows x64)
  # -----------------------------
  $nreZip = Join-Path $WorkDir "N_m3u8DL-RE.zip"
  Download-File `
    "https://github.com/nilaoda/N_m3u8DL-RE/releases/download/v0.3.0-beta/N_m3u8DL-RE_v0.3.0-beta_win-x64_20241203.zip" `
    $nreZip
  Expand-Archive -Path $nreZip -DestinationPath (Join-Path $WorkDir "nre") -Force

  Get-ChildItem (Join-Path $WorkDir "nre") -Recurse -File |
    Where-Object { $_.Name -match "^N_m3u8DL-RE(\.exe)?$" } |
    Select-Object -First 1 |
    ForEach-Object { Copy-Item -Force $_.FullName (Join-Path $BinDir "N_m3u8DL-RE.exe") }

  # -----------------------------
  # install dash-mpd-cli (windows x64 )
  # -----------------------------
  $dashMpdCliUrl = "https://github.com/emarsden/dash-mpd-cli/releases/download/v0.2.29/dash-mpd-cli-windows.exe"
  Download-File $dashMpdCliUrl (Join-Path $BinDir "dash-mpd-cli.exe") 
  
  # -----------------------------
  # Install uv (Python required)
  # -----------------------------
  python -m pip install --upgrade uv

  # PATH (Machine)
  Add-ToMachinePath $BinDir

  Write-Host "`nDone. Open a NEW terminal and try:"
  Write-Host "  mp4decrypt.exe --help"
  Write-Host "  N_m3u8DL-RE.exe --help"
  Write-Host "  ffmpeg --version"
  Write-Host "  mkvtoolnix --version"
  Write-Host "  dash-mpd-cli --version"
  Write-Host "  uv --version"

} finally {
  Pop-Location
  # Clean up temp work dir
  if (Test-Path $WorkDir) { Remove-Item -Recurse -Force $WorkDir }
}
