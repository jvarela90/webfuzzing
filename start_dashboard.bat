param(
    [switch]$Background
)

Write-Host "🚀 Iniciando Dashboard de Seguridad..." -ForegroundColor Green
Write-Host "=" * 50

# Verificar que estamos en el directorio correcto
if (-not (Test-Path "web\app.py")) {
    Write-Host "❌ Error: No se encuentra web\app.py" -ForegroundColor Red
    Write-Host "Ejecuta este script desde el directorio raíz del proyecto" -ForegroundColor Yellow
    exit 1
}

# Activar entorno virtual
if (Test-Path "venv\Scripts\Activate.ps1") {
    Write-Host "Activando entorno virtual..." -ForegroundColor Cyan
    & .\venv\Scripts\Activate.ps1
} else {
    Write-Host "⚠️ Entorno virtual no encontrado. Ejecuta fix_environment.ps1 primero" -ForegroundColor Yellow
}

# Crear directorios necesarios
$dirs = @("logs", "data\databases", "exports", "reports")
foreach ($dir in $dirs) {
    if (-not (Test-Path $dir)) {
        New-Item -ItemType Directory -Path $dir -Force | Out-Null
        Write-Host "📁 Creado directorio: $dir" -ForegroundColor Gray
    }
}

# Verificar dependencias críticas
Write-Host "Verificando dependencias..." -ForegroundColor Cyan
try {
    python -c "import flask, requests, aiohttp, yaml; print('✅ Dependencias OK')"
} catch {
    Write-Host "❌ Faltan dependencias. Ejecuta: pip install -r requirements.txt" -ForegroundColor Red
    exit 1
}

# Iniciar dashboard
Write-Host "🌐 Iniciando servidor web en http://localhost:5000" -ForegroundColor Green

if ($Background) {
    Start-Process python -ArgumentList "web\app.py" -WindowStyle Hidden
    Write-Host "Dashboard iniciado en background" -ForegroundColor Green
} else {
    python web\app.py
}