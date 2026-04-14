param(
    [string]$Model = "qwen3.6-plus",
    [string]$SmallFastModel = "qwen3.6-plus",
    [string]$BaseUrl = "https://dashscope.aliyuncs.com/apps/anthropic",
    [string]$AuthToken = "sk-bc6b4b383309408b8089876ed834ebe3",
    [switch]$PersistUser
)

function Set-EnvPair {
    param(
        [string]$Name,
        [string]$Value,
        [bool]$Persist
    )
    if ($Persist) {
        [System.Environment]::SetEnvironmentVariable($Name, $Value, "User")
    }
    else {
        Set-Item -Path "Env:$Name" -Value $Value
    }
}

if ([string]::IsNullOrWhiteSpace($AuthToken)) {
    $secure = Read-Host "Input ANTHROPIC_AUTH_TOKEN (hidden)" -AsSecureString
    if ($secure) {
        $bstr = [Runtime.InteropServices.Marshal]::SecureStringToBSTR($secure)
        try {
            $AuthToken = [Runtime.InteropServices.Marshal]::PtrToStringAuto($bstr)
        }
        finally {
            [Runtime.InteropServices.Marshal]::ZeroFreeBSTR($bstr)
        }
    }
}

if ([string]::IsNullOrWhiteSpace($AuthToken)) {
    Write-Host "ERROR: ANTHROPIC_AUTH_TOKEN is required." -ForegroundColor Red
    exit 1
}

$persist = $PersistUser.IsPresent
Set-EnvPair -Name "ANTHROPIC_MODEL" -Value $Model -Persist $persist
Set-EnvPair -Name "ANTHROPIC_SMALL_FAST_MODEL" -Value $SmallFastModel -Persist $persist
Set-EnvPair -Name "ANTHROPIC_BASE_URL" -Value $BaseUrl -Persist $persist
Set-EnvPair -Name "ANTHROPIC_AUTH_TOKEN" -Value $AuthToken -Persist $persist

Write-Host ""
if ($persist) {
    Write-Host "Done: variables saved at User scope." -ForegroundColor Green
    Write-Host "Please restart Cursor/terminal to take effect globally." -ForegroundColor Yellow
}
else {
    Write-Host "Done: variables set for current PowerShell session." -ForegroundColor Green
}

Write-Host ""
Write-Host "Current values:" -ForegroundColor Cyan
Write-Host "ANTHROPIC_MODEL=$env:ANTHROPIC_MODEL"
Write-Host "ANTHROPIC_SMALL_FAST_MODEL=$env:ANTHROPIC_SMALL_FAST_MODEL"
Write-Host "ANTHROPIC_BASE_URL=$env:ANTHROPIC_BASE_URL"
Write-Host "ANTHROPIC_AUTH_TOKEN=<hidden>"
