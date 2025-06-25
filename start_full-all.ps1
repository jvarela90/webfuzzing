# ==========================================
# start_dashboard.ps1
# ==========================================

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

# ==========================================
# start_api.ps1
# ==========================================

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

# ==========================================
# start_fuzzer.ps1
# ==========================================

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

# ==========================================
# start_all.ps1 - Iniciar todo el sistema
# ==========================================

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

# ==========================================
# stop_all.ps1 - Detener todos los servicios
# ==========================================

Write-Host "🛑 Deteniendo Security Fuzzing System..." -ForegroundColor Red
Write-Host "=" * 50

# Buscar y detener procesos de Python relacionados
$python_processes = Get-Process python -ErrorAction SilentlyContinue | Where-Object {
    $_.CommandLine -like "*web\app.py*" -or 
    $_.CommandLine -like "*api\app.py*" -or
    $_.CommandLine -like "*fuzzing_engine*"
}

if ($python_processes) {
    Write-Host "Deteniendo procesos de Python..." -ForegroundColor Yellow
    $python_processes | Stop-Process -Force
    Write-Host "✅ Procesos detenidos" -ForegroundColor Green
} else {
    Write-Host "No se encontraron procesos de Python ejecutándose" -ForegroundColor Gray
}

Write-Host "🔚 Sistema detenido" -ForegroundColor Green