# PowerShell script to run experiments in background
# Usage: .\tools\run_experiments_background.ps1

$ErrorActionPreference = "Stop"

Write-Host "========================================" -ForegroundColor Cyan
Write-Host "  Running Experiments in Background" -ForegroundColor Cyan
Write-Host "========================================" -ForegroundColor Cyan
Write-Host ""

$projectRoot = Split-Path -Parent $PSScriptRoot
$logDir = Join-Path $projectRoot "logs"
$timestamp = Get-Date -Format "yyyyMMdd_HHmmss"

# Create logs directory
if (-not (Test-Path $logDir)) {
    New-Item -ItemType Directory -Path $logDir | Out-Null
}

Write-Host "Logs will be saved to: $logDir" -ForegroundColor Yellow
Write-Host "Timestamp: $timestamp" -ForegroundColor Yellow
Write-Host ""

# Define experiments
$experiments = @(
    @{
        Name = "run_predefined_scenarios"
        Script = "run_predefined_scenarios.py"
        Description = "Main Scale Generation (3 scenarios)"
        LogFile = "run_predefined_scenarios_$timestamp.log"
    },
    @{
        Name = "run_ablation_minimal"
        Script = "run_ablation_minimal.py"
        Description = "Ablation Study (4 variants)"
        LogFile = "run_ablation_minimal_$timestamp.log"
    },
    @{
        Name = "run_baseline_comparison"
        Script = "run_baseline_comparison.py"
        Description = "Baseline Comparison (PETS & RoPE)"
        LogFile = "run_baseline_comparison_$timestamp.log"
    }
)

Write-Host "Experiments to run:" -ForegroundColor Green
foreach ($exp in $experiments) {
    Write-Host "  - $($exp.Description)" -ForegroundColor White
}
Write-Host ""

$response = Read-Host "Start running experiments? (Y/N)"
if ($response -ne "Y" -and $response -ne "y") {
    Write-Host "Cancelled." -ForegroundColor Yellow
    exit
}

# Run experiments sequentially
foreach ($exp in $experiments) {
    $logPath = Join-Path $logDir $exp.LogFile
    
    Write-Host ""
    Write-Host "========================================" -ForegroundColor Cyan
    Write-Host "  Running: $($exp.Description)" -ForegroundColor Cyan
    Write-Host "========================================" -ForegroundColor Cyan
    Write-Host "Log file: $logPath" -ForegroundColor Yellow
    Write-Host "Start time: $(Get-Date -Format 'yyyy-MM-dd HH:mm:ss')" -ForegroundColor Yellow
    Write-Host ""
    
    try {
        # Run the script
        $process = Start-Process python -ArgumentList "$($exp.Script)" -WorkingDirectory $projectRoot -NoNewWindow -PassThru -RedirectStandardOutput $logPath -RedirectStandardError $logPath
        
        Write-Host "Process started (PID: $($process.Id))" -ForegroundColor Green
        Write-Host "Monitoring progress... (Press Ctrl+C to stop)" -ForegroundColor Yellow
        Write-Host ""
        
        # Monitor progress
        $lastSize = 0
        $noChangeCount = 0
        while (-not $process.HasExited) {
            Start-Sleep -Seconds 10
            
            if (Test-Path $logPath) {
                $currentSize = (Get-Item $logPath).Length
                if ($currentSize -eq $lastSize) {
                    $noChangeCount++
                    if ($noChangeCount -gt 60) {  # 10 minutes no change
                        Write-Host "Warning: No output for 10 minutes. Process may be stuck." -ForegroundColor Red
                        $noChangeCount = 0
                    }
                } else {
                    $noChangeCount = 0
                    $lastSize = $currentSize
                    
                    # Show last few lines
                    $lastLines = Get-Content $logPath -Tail 3
                    foreach ($line in $lastLines) {
                        Write-Host "  $line" -ForegroundColor Gray
                    }
                }
            }
        }
        
        # Check exit code
        if ($process.ExitCode -eq 0) {
            Write-Host ""
            Write-Host "✓ $($exp.Description) completed successfully!" -ForegroundColor Green
        } else {
            Write-Host ""
            Write-Host "✗ $($exp.Description) failed with exit code $($process.ExitCode)" -ForegroundColor Red
            Write-Host "Check log file for details: $logPath" -ForegroundColor Yellow
            
            $continue = Read-Host "Continue with next experiment? (Y/N)"
            if ($continue -ne "Y" -and $continue -ne "y") {
                Write-Host "Stopped." -ForegroundColor Yellow
                exit
            }
        }
        
    } catch {
        Write-Host ""
        Write-Host "Error running $($exp.Script): $_" -ForegroundColor Red
        $continue = Read-Host "Continue with next experiment? (Y/N)"
        if ($continue -ne "Y" -and $continue -ne "y") {
            Write-Host "Stopped." -ForegroundColor Yellow
            exit
        }
    }
}

Write-Host ""
Write-Host "========================================" -ForegroundColor Cyan
Write-Host "  All Experiments Completed" -ForegroundColor Cyan
Write-Host "========================================" -ForegroundColor Cyan
Write-Host "End time: $(Get-Date -Format 'yyyy-MM-dd HH:mm:ss')" -ForegroundColor Yellow
Write-Host "Check logs in: $logDir" -ForegroundColor Yellow


