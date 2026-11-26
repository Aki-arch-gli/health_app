@echo off
powershell.exe -NoProfile -Command "$statePath=Join-Path $env:LOCALAPPDATA 'KurashiTrial/running.json'; if (Test-Path -LiteralPath $statePath) { $state=Get-Content -LiteralPath $statePath -Raw | ConvertFrom-Json; foreach ($field in @('tunnel','app')) { $process=Get-Process -Id $state.$field -ErrorAction SilentlyContinue; if ($process -and $process.StartTime.ToUniversalTime().Ticks.ToString() -eq $state.($field+'Start')) { Stop-Process -Id $process.Id -ErrorAction Stop } }; Write-Host 'Trial stopped.' } else { Write-Host 'No running trial was found.' }"
pause
