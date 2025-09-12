# =====================================
# BatchPrintPDF.ps1 (fixed) - Auto print PDFs
# =====================================
# --- Config ---
$WatchFolder = "G:\My Drive\In"               # đổi lại nếu bạn muốn thư mục khác
$DoneFolder  = Join-Path $WatchFolder "_printed"
$Printer     = "HP LaserJet M14-M17"          # để $null nếu muốn dùng máy in mặc định
$minAge      = [TimeSpan]::FromSeconds(0)    # bỏ qua file mới copy < 15s

# Đường dẫn mặc định cho SumatraPDF (thay đổi theo máy của bạn)
$defaultSumatraPath = "C:\Users\Admin\AppData\Local\SumatraPDF\SumatraPDF.exe"

# --- Prep ---
if (-not (Test-Path -LiteralPath $WatchFolder)) {
  New-Item -ItemType Directory -Path $WatchFolder -Force | Out-Null
}
New-Item -ItemType Directory -Path $DoneFolder -Force | Out-Null

# --- Find PDF printing app (SumatraPDF ưu tiên, rồi Adobe) ---
$sumatraPath = $null

# 1) Thử đường dẫn mặc định trước
if (Test-Path -LiteralPath $defaultSumatraPath) {
  $sumatraPath = $defaultSumatraPath
  Write-Host "Using default SumatraPDF path: $sumatraPath"
}

# 2) Nếu không có, thử tìm qua PATH
if (-not $sumatraPath) {
  try {
    $cmd = Get-Command "SumatraPDF.exe" -ErrorAction SilentlyContinue
    if ($cmd) { 
      $sumatraPath = $cmd.Source 
      Write-Host "Found SumatraPDF in PATH: $sumatraPath"
    }
  } catch {}
}

# 3) Quét vài vị trí phổ biến nếu chưa thấy
if (-not $sumatraPath) {
  $search = Get-ChildItem -Path @(
      "$env:ProgramFiles",
      "$env:ProgramFiles(x86)",
      "$env:LOCALAPPDATA",
      "$env:LOCALAPPDATA\Programs"
    ) -Recurse -Filter "SumatraPDF.exe" -ErrorAction SilentlyContinue | Select-Object -First 1
  if ($search) { $sumatraPath = $search.FullName }
}

# 4) Thử bản portable cố định
if (-not $sumatraPath -and (Test-Path 'C:\Tools\SumatraPDF.exe')) {
  $sumatraPath = 'C:\Tools\SumatraPDF.exe'
}

# Adobe Reader (dự phòng)
$acroPath = $null
if (-not $sumatraPath) {
  $asearch = Get-ChildItem -Path @("$env:ProgramFiles","$env:ProgramFiles(x86)") -Recurse -Filter "AcroRd32.exe" -ErrorAction SilentlyContinue | Select-Object -First 1
  if ($asearch) { $acroPath = $asearch.FullName }
}

if (-not $sumatraPath -and -not $acroPath) {
  Write-Host "No PDF print app found. Cài SumatraPDF (winget) hoặc đặt portable ở C:\Tools\SumatraPDF.exe."
  return
}

Write-Host "Watch: $WatchFolder"
Write-Host "Printer: $Printer"
Write-Host ("Using: " + ($(if ($sumatraPath) {"SumatraPDF -> $sumatraPath"} else {"Adobe Reader -> $acroPath"})))

# --- Collect files ---
$all = Get-ChildItem -LiteralPath $WatchFolder -Filter *.pdf -File -ErrorAction SilentlyContinue
$ready = $all | Where-Object { (Get-Date) - $_.LastWriteTime -ge $minAge }
Write-Host ("Found {0} PDF(s), {1} ready (> {2}s)" -f $all.Count, $ready.Count, [int]$minAge.TotalSeconds)



# --- Print loop ---
foreach ($f in $ready) {
  try {
    Write-Host ("Printing: {0}" -f $f.Name)

    if (-not (Test-Path $f.FullName)) { throw "File not found: $($f.FullName)" }
    if ($f.Extension -ne ".pdf")     { throw "Unsupported file format: $($f.Extension). Only PDF is supported." }
	Write-Host "0"
if ($sumatraPath -and (Test-Path $sumatraPath)) {
    # In bằng SumatraPDF (ưu tiên)
    $arg = if ($Printer) {
        "-print-to `"$Printer`" -silent `"$($f.FullName)`""
    } else {
        "-print-to-default -silent `"$($f.FullName)`""
    }
	Write-Host "1 dkdkdkdk"
    	Start-Process -FilePath $sumatraPath -ArgumentList $arg -NoNewWindow
	# rundll32 printui.dll,PrintUIEntry /k /n "HP LaserJet M14-M17"
	Write-Host "1"
}
    elseif ($acroPath -and (Test-Path $acroPath)) {
      # Dự phòng Acrobat Reader
      $arg = if ($Printer) {
        "/t `"$($f.FullName)`" `"$Printer`""
      } else {
        "/t `"$($f.FullName)`""
      }
Write-Host "2"
      Start-Process -FilePath $acroPath -ArgumentList $arg -NoNewWindow -Wait
Write-Host "2"
      Start-Sleep -Seconds 2
      Get-Process -Name "AcroRd32" -ErrorAction SilentlyContinue | Stop-Process -Force -ErrorAction SilentlyContinue
    }
    else {
      throw "Neither SumatraPDF nor Acrobat Reader found. Please install one of them or verify the paths."
    }

    # Di chuyển file sau khi in
    # Move-Item -LiteralPath $f.FullName -Destination (Join-Path $DoneFolder $f.Name) -Force
    Write-Host ("Done: {0}" -f $f.Name)
  }
  catch {
    Write-Host ("Error printing {0}: {1}" -f $f.FullName, $_.Exception.Message)
    Write-Host ("Error details: {0}" -f ($_.Exception | Format-List -Property * -Force | Out-String))
  }
}
