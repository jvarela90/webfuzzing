param(
    [switch]$Background
)

Write-Host "🔌 Iniciando API REST..." -ForegroundColor Green
Write-Host "=" * 50

# Verificar que estamos en el directorio correcto
if (-not (Test-Path "api\app.py")) {
    Write-Host "❌ Error: No se encuentra api\app.py" -ForegroundColor Red
    Write-Host "Asegúrate de haber creado el archivo api\app.py" -ForegroundColor Yellow
    exit 1
}

# Activar entorno virtual
if (Test-Path "venv\Scripts\Activate.ps1") {
    Write-Host "Activando entorno virtual..." -ForegroundColor Cyan
    & .\venv\Scripts\Activate.ps1
} else {
    Write-Host "⚠️ Entorno virtual no encontrado. Ejecuta fix_environment.ps1 primero" -ForegroundColor Yellow
}

# Verificar dependencias
Write-Host "Verificando dependencias..." -ForegroundColor Cyan
try {
    python -c "import flask, flask_restful, flask_cors; print('✅ API dependencies OK')"
} catch {
    Write-Host "❌ Faltan dependencias para la API" -ForegroundColor Red
    exit 1
}

# Iniciar API
Write-Host "🌐 Iniciando API en http://localhost:8000" -ForegroundColor Green

if ($Background) {
    Start-Process python -ArgumentList "api\app.py" -WindowStyle Hidden
    Write-Host "API iniciada en background" -ForegroundColor Green
} else {
    python api\app.py
}
