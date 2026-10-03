[CmdletBinding()]
param(
    [switch]$Train,
    [switch]$SkipData
)

$ErrorActionPreference = 'Stop'
$ProjectRoot = (Resolve-Path (Join-Path $PSScriptRoot '..')).Path

function Invoke-Checked {
    param(
        [Parameter(Mandatory)][string]$Label,
        [Parameter(Mandatory)][string]$Executable,
        [Parameter(Mandatory)][string[]]$Arguments
    )
    Write-Host "`n==> $Label" -ForegroundColor Cyan
    & $Executable @Arguments
    if ($LASTEXITCODE -ne 0) {
        throw "$Label failed with exit code $LASTEXITCODE. Correct the reported issue and rerun bootstrap."
    }
}

Push-Location $ProjectRoot
try {
    Write-Host 'Premier League AI — Windows setup' -ForegroundColor Green

    $Uv = (Get-Command uv -ErrorAction SilentlyContinue).Source
    if (-not $Uv) {
        throw 'uv is required. Install it with the official instructions at https://docs.astral.sh/uv/getting-started/installation/, then rerun this script.'
    }
    $Node = (Get-Command node -ErrorAction SilentlyContinue).Source
    $Npm = (Get-Command npm -ErrorAction SilentlyContinue).Source
    if (-not $Node -or -not $Npm) {
        throw 'Node.js 20.9 or newer and npm are required for the dashboard. Install the current Node.js LTS release, then rerun this script.'
    }
    $NodeParts = ((& $Node --version).Trim().TrimStart('v').Split('.') | ForEach-Object { [int]$_ })
    if ($NodeParts[0] -lt 20 -or ($NodeParts[0] -eq 20 -and $NodeParts[1] -lt 9)) {
        throw 'Node.js 20.9 or newer is required; upgrade Node.js and rerun bootstrap.'
    }
    $Git = Get-Command git -ErrorAction SilentlyContinue
    if (-not $Git) { Write-Warning 'Git is not on PATH. The project can run, but revision information will be unavailable.' }

    Write-Host "Node.js $(& $Node --version); npm $(& $Npm --version)"
    $Python312 = & $Uv python find 3.12 2>$null
    if ($LASTEXITCODE -ne 0 -or -not $Python312) {
        Write-Host 'Installing the uv-managed Python 3.12 runtime.'
        Invoke-Checked 'Install Python 3.12' $Uv @('python', 'install', '3.12')
        $Python312 = & $Uv python find 3.12
        if ($LASTEXITCODE -ne 0 -or -not $Python312) { throw 'Could not locate Python 3.12 after installation.' }
    }
    Write-Host "Python runtime: $Python312"

    if (-not (Test-Path -LiteralPath '.env')) {
        Copy-Item -LiteralPath '.env.example' -Destination '.env'
        Write-Host 'Created local .env from the safe template; existing .env files are preserved.'
    }

    foreach ($Directory in @('data/raw', 'data/processed', 'data/external', 'models', 'reports', 'mlruns', 'logs', 'work')) {
        New-Item -ItemType Directory -Force -Path $Directory | Out-Null
    }

    Invoke-Checked 'Create/sync Python 3.12 environment' $Uv @(
        'sync', '--locked', '--python', '3.12', '--extra', 'ml', '--extra', 'neural',
        '--extra', 'tracking', '--extra', 'api', '--extra', 'dev'
    )
    $Python = Join-Path $ProjectRoot '.venv\Scripts\python.exe'
    Invoke-Checked 'Install locked frontend dependencies' $Npm @('ci', '--prefix', 'frontend')

    Invoke-Checked 'Initialize SQLite and apply migrations' $Python @(
        '-c', 'from football_ai.config import Settings; from football_ai.database.repository import Repository; Repository(Settings()).migrate()'
    )

    if (-not $SkipData) {
        try {
            Invoke-Checked 'Download, validate, version, and prepare historical data' $Python @('-m', 'football_ai', 'update-data')
        }
        catch {
            Write-Warning 'Automatic historical data setup failed. The app is installed; import a compatible results CSV with football-ai update-data --csv PATH --season YYYY/YYYY.'
            Write-Warning $_.Exception.Message
        }
    }

    Invoke-Checked 'Run lightweight local API health check' $Python @(
        '-c', 'from fastapi.testclient import TestClient; from football_ai.api.main import create_app; from football_ai.config import Settings; response=TestClient(create_app(Settings())).get("/health"); print("API /health:", response.status_code, response.text); raise SystemExit(response.status_code != 200)'
    )
    Invoke-Checked 'Print project status' $Python @('-m', 'football_ai', 'status')

    if ($Train) {
        Invoke-Checked 'Train using the configured LIGHT CPU defaults' $Python @('-m', 'football_ai', 'train')
    }
    else {
        Write-Host "`nSetup complete. Expensive model training was skipped. Run '.\.venv\Scripts\python.exe -m football_ai train' when you want to train." -ForegroundColor Green
    }
    Write-Host 'Start the API with .\.venv\Scripts\python.exe -m football_ai api and the dashboard with npm run dev in frontend.'
}
finally {
    Pop-Location
}
