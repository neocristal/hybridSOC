# ==============================
# AI-POWERED DOCKER IDS
# ==============================

Write-Host "Starting AI Docker IDS..." -ForegroundColor Cyan

# Threat weights (AI-like heuristic model)
$threatModel = @{
    "error" = 10
    "fail" = 10
    "failed" = 15
    "critical" = 25
    "fatal" = 30
    "exception" = 20
    "panic" = 35
    "segfault" = 40
    "denied" = 20
    "unauthorized" = 25
    "authentication" = 15
    "invalid" = 10
    "exploit" = 60
    "attack" = 60
    "injection" = 50
    "sql" = 25
    "jwt" = 20
    "token" = 15
}

# Risk classifier
function Get-RiskLevel($score) {
    if ($score -ge 75) { return "CRITICAL" }
    elseif ($score -ge 50) { return "HIGH" }
    elseif ($score -ge 25) { return "MEDIUM" }
    else { return "LOW" }
}

# Get containers
$containers = docker ps -q

if (-not $containers) {
    Write-Host "No running containers detected." -ForegroundColor Yellow
    exit
}

foreach ($c in $containers) {

    $name = docker inspect --format='{{.Name}}' $c | ForEach-Object { $_ -replace "/", "" }

    Start-Job -ScriptBlock {
        param($containerId, $containerName, $model)

        docker logs -f $containerId 2>&1 | ForEach-Object {

            $log = $_
            $score = 0
            $matched = @()

            foreach ($key in $model.Keys) {
                if ($log -match $key) {
                    $score += $model[$key]
                    $matched += $key
                }
            }

            # Behavioral heuristics (AI-like enhancement)
            if ($log.Length -gt 300) { $score += 5 }
            if ($log -match "stack trace") { $score += 20 }
            if ($log -match "403|401|500") { $score += 15 }

            if ($score -gt 0) {

                $risk = if ($score -ge 75) { "CRITICAL" }
                        elseif ($score -ge 50) { "HIGH" }
                        elseif ($score -ge 25) { "MEDIUM" }
                        else { "LOW" }

                $time = Get-Date -Format "yyyy-MM-dd HH:mm:ss"

                Write-Host ""
                Write-Host "===============================" -ForegroundColor DarkGray
                Write-Host "🚨 IDS ALERT" -ForegroundColor Red
                Write-Host "Time: $time"
                Write-Host "Container: $containerName"
                Write-Host "Risk Score: $score / 100"
                Write-Host "Severity: $risk"
                Write-Host "Signals: $($matched -join ', ')"
                Write-Host "Log: $log"
                Write-Host "===============================" -ForegroundColor DarkGray
            }
        }

    } -ArgumentList $c, $name, $threatModel
}

Write-Host "IDS running on $($containers.Count) containers..." -ForegroundColor Green

while ($true) {
    Start-Sleep -Seconds 5
}