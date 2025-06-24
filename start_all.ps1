Write-Host "🚀 Iniciando Security Fuzzing System completo..." -ForegroundColor Green
Write-Host "=" * 60

# Verificar estructura del proyecto
$required_files = @("web\app.py", "api\app.py", "core\fuzzing_engine.py", "config\settings.py")
$missing_files = @()

foreach ($file in $required_files) {
    if (-not (Test-Path $file)) {
        $missing_files += $file
    }
}

if ($missing_files.Count -gt 0) {
    Write-Host "❌ Archivos faltantes:" -ForegroundColor Red
    foreach ($file in $missing_files) {
        Write-Host "   - $file" -ForegroundColor Red
    }
    Write-Host "Crea los archivos faltantes antes de continuar" -ForegroundColor Yellow
    exit 1
}

# Activar entorno virtual
if (Test-Path "venv\Scripts\Activate.ps1") {
    Write-Host "Activando entorno virtual..." -ForegroundColor Cyan
    & .\venv\Scripts\Activate.ps1
} else {
    Write-Host "❌ Entorno virtual no encontrado. Ejecuta fix_environment.ps1 primero" -ForegroundColor Red
    exit 1
}

# Crear directorios necesarios
$dirs = @("logs", "data\databases", "data\wordlists", "exports", "reports", "config")
foreach ($dir in $dirs) {
    if (-not (Test-Path $dir)) {
        New-Item -ItemType Directory -Path $dir -Force | Out-Null
        Write-Host "📁 Creado: $dir" -ForegroundColor Gray
    }
}

# Iniciar servicios en background
Write-Host "🔌 Iniciando API REST..." -ForegroundColor Cyan
Start-Process powershell -ArgumentList "-File .\start_api.ps1 -Background" -WindowStyle Hidden

Start-Sleep 2

Write-Host "🌐 Iniciando Dashboard Web..." -ForegroundColor Cyan
Start-Process powershell -ArgumentList "-File .\start_dashboard.ps1 -Background" -WindowStyle Hidden

Start-Sleep 3

# Mostrar información del sistema
Write-Host ""
Write-Host "✅ SISTEMA INICIADO CORRECTAMENTE" -ForegroundColor Green
Write-Host "=" * 60
Write-Host "🌐 Dashboard Web:  http://localhost:5000" -ForegroundColor Yellow
Write-Host "🔌 API REST:       http://localhost:8000" -ForegroundColor Yellow
Write-Host "❤️ Health Check:   http://localhost:8000/health" -ForegroundColor Yellow
Write-Host "📚 API Docs:       http://localhost:8000/docs" -ForegroundColor Yellow
Write-Host ""
Write-Host "Para hacer fuzzing:" -ForegroundColor Cyan
Write-Host ".\start_fuzzer.ps1 -Url 'http://example.com/FUZZ' -Payloads 'data\wordlists\common.txt'" -ForegroundColor Gray
Write-Host ""
Write-Host "Para detener los servicios:" -ForegroundColor Red
Write-Host "Get-Process python | Stop-Process" -ForegroundColor Gray
Write-Host "=" * 60