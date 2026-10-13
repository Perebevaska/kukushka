# Скачивает переносной (embeddable) Python 3.12 с python.org в runtime\python.
# Ничего не устанавливает в систему: чтобы удалить — удалите папку runtime.
$ErrorActionPreference = 'Stop'
$ProgressPreference = 'SilentlyContinue'
[Net.ServicePointManager]::SecurityProtocol = [Net.SecurityProtocolType]::Tls12
$ver = '3.12.10'
$arch = switch ($env:PROCESSOR_ARCHITECTURE) { 'ARM64' { 'arm64' } 'x86' { 'win32' } default { 'amd64' } }
$root = Split-Path -Parent $PSScriptRoot
$dest = Join-Path $root 'runtime\python'
$zip = Join-Path $env:TEMP "python-$ver-embed-$arch.zip"
$url = "https://www.python.org/ftp/python/$ver/python-$ver-embed-$arch.zip"
try {
    Write-Host "Скачиваю $url"
    Invoke-WebRequest -Uri $url -OutFile $zip -UseBasicParsing
    New-Item -ItemType Directory -Force -Path $dest | Out-Null
    Expand-Archive -Path $zip -DestinationPath $dest -Force
    Remove-Item $zip -ErrorAction SilentlyContinue
    Write-Host 'Готово.'
} catch {
    Write-Host "Ошибка: $($_.Exception.Message)"
    exit 1
}
