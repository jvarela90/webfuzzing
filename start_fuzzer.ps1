param(
    [Parameter(Mandatory=$false)]
    [string]$Url,
    
    [Parameter(Mandatory=$false)]
    [string]$Payloads = "data\wordlists\common.txt",
    
    [Parameter(Mandatory=$false)]
    [string]$Output = "results",
    
    [Parameter(Mandatory=$false)]
    [string]$Format = "json"
)

Write-Host "⚡ Iniciando Fuzzing Engine..." -ForegroundColor Green
Write-Host "=" * 50

# Activar entorno virtual
if (Test-Path "venv\Scripts\Activate.ps1") {
    Write-Host "Activando entorno virtual..." -ForegroundColor Cyan
    & .\venv\Scripts\Activate.ps1
}

# Verificar que el módulo config existe
if (-not (Test-Path "config\settings.py")) {
    Write-Host "❌ Error: No se encuentra config\settings.py" -ForegroundColor Red
    Write-Host "Crea el archivo config\settings.py con el contenido proporcionado" -ForegroundColor Yellow
    exit 1
}

if ($Url) {
    Write-Host "🎯 Objetivo: $Url" -ForegroundColor Cyan
    Write-Host "📜 Payloads: $Payloads" -ForegroundColor Cyan
    Write-Host "📊 Formato: $Format" -ForegroundColor Cyan
    
    python -m core.fuzzing_engine --url $Url --payloads $Payloads --output $Output --format $Format
} else {
    Write-Host "Mostrando ayuda del fuzzer..." -ForegroundColor Cyan
    python -m core.fuzzing_engine --help
    Write-Host ""
    Write-Host "Ejemplo de uso:" -ForegroundColor Yellow
    Write-Host ".\start_fuzzer.ps1 -Url 'http://example.com/FUZZ' -Payloads 'data\wordlists\common.txt'" -ForegroundColor Gray
}