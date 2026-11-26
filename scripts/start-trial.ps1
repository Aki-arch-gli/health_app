param([switch]$OpenBrowser)

$ErrorActionPreference = 'Stop'
$trialRoot = Join-Path $env:LOCALAPPDATA 'KurashiTrial'
$runtime = Join-Path $env:LOCALAPPDATA 'Temp/kurashi-streamlit-167-py313'
$project = Split-Path $PSScriptRoot -Parent
$statePath = Join-Path $trialRoot 'running.json'
$localUrl = 'http://127.0.0.1:8503'
New-Item -ItemType Directory -Path $trialRoot -Force | Out-Null

function Get-TrialProcess($State, $Name) {
    if ($State -and $State.$Name) {
        $process = Get-Process -Id $State.$Name -ErrorAction SilentlyContinue
        if ($process -and $process.StartTime.ToUniversalTime().Ticks.ToString() -eq $State.($Name + 'Start')) {
            return $process
        }
    }
}

function Test-Health($Url) {
    try {
        return (Invoke-WebRequest "$Url/_stcore/health" -UseBasicParsing -TimeoutSec 3).Content.Trim() -eq 'ok'
    } catch {
        return $false
    }
}

function Show-TrialLink($Link) {
    Write-Output $Link
    if ($OpenBrowser) {
        $localLink = "$localUrl/$(([uri]$Link).Query)"
        try { Start-Process -FilePath $localLink }
        catch { Write-Warning "Open $localLink in your browser." }
    }
}

$launchLock = [IO.File]::Open((Join-Path $trialRoot 'start.lock'), 'OpenOrCreate', 'ReadWrite', 'None')
$app = $null
$tunnel = $null
try {
    $previous = if (Test-Path -LiteralPath $statePath) {
        Get-Content -LiteralPath $statePath -Raw | ConvertFrom-Json
    }
    $previousApp = Get-TrialProcess $previous 'app'
    $previousTunnel = Get-TrialProcess $previous 'tunnel'
    if ($previousApp -and $previousTunnel -and $previous.link -and (Test-Health $localUrl)) {
        $tunnelLog = Join-Path $previous.run 'tunnel.err.log'
        $recent = if (Test-Path -LiteralPath $tunnelLog) { Get-Content -LiteralPath $tunnelLog -Tail 40 }
        if ((Test-Health $previous.url) -or -not ($recent -match 'Unauthorized: Tunnel not found')) {
            Show-TrialLink $previous.link
            return
        }
    }

    $python = Join-Path $env:LOCALAPPDATA 'Programs/Python/Python313/python.exe'
    if (Test-Path -LiteralPath (Join-Path $runtime 'streamlit/__init__.py')) {
        $env:PYTHONPATH = $runtime
    } else {
        $venvPython = Join-Path $project '.venv/Scripts/python.exe'
        if (Test-Path -LiteralPath $venvPython) { $python = $venvPython }
    }
    if (!(Test-Path -LiteralPath $python)) { $python = (Get-Command python.exe -CommandType Application).Source }
    $env:PYTHONUTF8 = '1'
    $env:PYTHONDONTWRITEBYTECODE = '1'
    $env:KURASHI_TRIAL_MODE = '1'
    $env:KURASHI_DATA_DIR = Join-Path $trialRoot 'data'

    $cloud = Get-Command cloudflared.exe -CommandType Application -ErrorAction SilentlyContinue
    $cloudExe = if ($cloud) { $cloud.Source } else { Join-Path $runtime 'trial-tools/cloudflared-2026.11.1.exe' }
    if (!(Test-Path -LiteralPath $cloudExe)) { throw 'Install cloudflared and run this file again. See README.md.' }
    if (!$cloud) {
        $file = [IO.File]::OpenRead($cloudExe)
        $sha256 = [Security.Cryptography.SHA256]::Create()
        try {
            $hash = [BitConverter]::ToString($sha256.ComputeHash($file)).Replace('-', '')
            if ($hash -ne '341deda3db5ec498a0482254d6c38c0b7cf01a30c37bb5dd95d2216d08955e35') {
                throw 'The cached cloudflared executable failed verification.'
            }
        } finally {
            $sha256.Dispose()
            $file.Dispose()
        }
    }
    Push-Location -LiteralPath $project
    try {
        & $python -c 'import streamlit, reportlab, PIL'
        if ($LASTEXITCODE -ne 0) { throw 'Install the Python packages in requirements.txt first.' }
        $env:KURASHI_TRIAL_CODE = (& $python -c 'import secrets; print(secrets.token_urlsafe(18))').Trim()
        if ($env:KURASHI_TRIAL_CODE -notmatch '^[a-zA-Z0-9_-]{24}$') { throw 'Could not generate a trial invitation.' }
        $token = (@'
import os
from modules.trial_ui import trial_link_token
print(trial_link_token(os.environ["KURASHI_TRIAL_CODE"]))
'@ | & $python -).Trim()
        if ($token -notmatch '^[0-9a-f]{32}$') { throw 'Could not generate a trial link.' }
    } finally {
        Pop-Location
    }

    if ($previousTunnel) { Stop-Process -Id $previousTunnel.Id }
    if ($previousApp) {
        Stop-Process -Id $previousApp.Id
        if (!$previousApp.WaitForExit(4000)) { throw 'The previous trial app is still running.' }
    }
    $portCheck = [Net.Sockets.TcpListener]::new([Net.IPAddress]::Loopback, 8503)
    $portCheck.ExclusiveAddressUse = $true
    try { $portCheck.Start() }
    catch { throw 'Port 8503 is already in use.' }
    finally { $portCheck.Stop() }

    $run = Join-Path $trialRoot ([guid]::NewGuid().ToString('N'))
    New-Item -ItemType Directory -Path $run | Out-Null
    $appArgs = @('-m','streamlit','run','app.py','--server.address=127.0.0.1','--server.port=8503','--server.headless=true','--server.enableXsrfProtection=true','--server.enableAgentApi=false','--server.fileWatcherType=none','--server.maxUploadSize=10','--client.showErrorDetails=none')
    $app = Start-Process -FilePath $python -ArgumentList $appArgs -WorkingDirectory $project -WindowStyle Hidden -RedirectStandardOutput (Join-Path $run 'app.out.log') -RedirectStandardError (Join-Path $run 'app.err.log') -PassThru
    Remove-Item Env:KURASHI_TRIAL_CODE
    $ready = $false
    for ($attempt = 0; $attempt -lt 16 -and !$app.HasExited; $attempt++) {
        if (Test-Health $localUrl) { $ready = $true; break }
        Start-Sleep -Milliseconds 500
    }
    if (!$ready) { throw "Streamlit did not start. See $run." }

    $tunnelLog = Join-Path $run 'tunnel.err.log'
    $tunnel = Start-Process -FilePath $cloudExe -ArgumentList @('tunnel','--url',$localUrl,'--no-autoupdate','--protocol','http2') -WorkingDirectory $run -WindowStyle Hidden -RedirectStandardOutput (Join-Path $run 'tunnel.out.log') -RedirectStandardError $tunnelLog -PassThru
    $url = $null
    $deadline = [DateTime]::UtcNow.AddSeconds(55)
    while (!$tunnel.HasExited -and [DateTime]::UtcNow -lt $deadline) {
        $log = [string](Get-Content -LiteralPath $tunnelLog -Raw)
        $assigned = [regex]::Match($log, 'https://[a-z0-9-]+\.trycloudflare\.com')
        if ($assigned.Success -and $log -match 'Registered tunnel connection') {
            $url = $assigned.Value
            break
        }
        Start-Sleep -Milliseconds 700
    }
    if (!$url) { throw "Cloudflare did not register the tunnel. See $tunnelLog." }

    $env:KURASHI_QR_LINK = "$url/?join=$token"
    $env:KURASHI_QR_PROJECT = $project
    @'
from pathlib import Path
import os
from PIL import Image, ImageDraw
from reportlab.graphics.barcode.qr import qrencoder

code = qrencoder.QRCode(None, qrencoder.QRErrorCorrectLevel.M)
code.addData(os.environ["KURASHI_QR_LINK"])
code.make()
box, margin = 14, 4
side = (len(code.modules) + 2 * margin) * box
image = Image.new("1", (side, side), 1)
draw = ImageDraw.Draw(image)
for row, modules in enumerate(code.modules, margin):
    for col, filled in enumerate(modules, margin):
        if filled:
            x, y = col * box, row * box
            draw.rectangle((x, y, x + box - 1, y + box - 1), fill=0)
target = Path(os.environ["KURASHI_QR_PROJECT"]) / "\u8a66\u7528\u7248QR.png"
temporary = target.with_suffix(".png.tmp")
image.save(temporary, format="PNG")
temporary.replace(target)
'@ | & $python -
    if ($LASTEXITCODE -ne 0) { throw 'Could not create the trial QR image.' }

    @{
        port = 8503; url = $url; link = $env:KURASHI_QR_LINK; run = $run
        app = $app.Id; appStart = $app.StartTime.ToUniversalTime().Ticks.ToString()
        tunnel = $tunnel.Id; tunnelStart = $tunnel.StartTime.ToUniversalTime().Ticks.ToString()
    } | ConvertTo-Json -Compress | Set-Content -LiteralPath $statePath -Encoding UTF8
    Show-TrialLink $env:KURASHI_QR_LINK
    Write-Output 'The QR image was updated in the project folder.'
} catch {
    if ($tunnel -and !$tunnel.HasExited) { Stop-Process -Id $tunnel.Id }
    if ($app -and !$app.HasExited) { Stop-Process -Id $app.Id }
    throw
} finally {
    $launchLock.Dispose()
}
