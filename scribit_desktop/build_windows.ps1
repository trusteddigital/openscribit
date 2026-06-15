$ErrorActionPreference = "Stop"
Set-Location $PSScriptRoot
python -m venv .venv
. .\.venv\Scripts\Activate.ps1
python -m pip install --upgrade pip
pip install -r requirements.txt
$sep = ";"
pyinstaller --noconfirm --onefile --name ScribitDesktop `
  --add-data "static${sep}static" `
  --add-data "firmware${sep}firmware" `
  --add-data "..\vendor\mbc-wb_2.0.0\tools\espota.py${sep}vendor\mbc-wb_2.0.0\tools" `
  app.py
Write-Host "Built dist\ScribitDesktop.exe"
