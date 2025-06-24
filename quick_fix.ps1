# quick_fix.ps1 - Reparación rápida del sistema
Write-Host "🔧 REPARACIÓN RÁPIDA DEL SISTEMA" -ForegroundColor Cyan
Write-Host ("=" * 50)

# Verificar que estamos en el directorio correcto
if (-not (Test-Path "core\fuzzing_engine.py")) {
    Write-Host "❌ Error: Ejecuta este script desde el directorio raíz del proyecto" -ForegroundColor Red
    exit 1
}

# Paso 1: Activar entorno virtual
Write-Host "Paso 1: Verificando entorno virtual..." -ForegroundColor Yellow
if (Test-Path "venv\Scripts\Activate.ps1") {
    Write-Host "✅ Activando entorno virtual" -ForegroundColor Green
    & .\venv\Scripts\Activate.ps1
} else {
    Write-Host "❌ Entorno virtual no encontrado" -ForegroundColor Red
    Write-Host "Creando nuevo entorno virtual..." -ForegroundColor Yellow
    python -m venv venv
    & .\venv\Scripts\Activate.ps1
}

# Paso 2: Instalar dependencias faltantes
Write-Host "Paso 2: Instalando dependencias faltantes..." -ForegroundColor Yellow
$dependencies = @(
    "loguru",
    "colorama", 
    "tqdm",
    "flask-restful",
    "flask-socketio",
    "beautifulsoup4",
    "flask-cors"
)

foreach ($dep in $dependencies) {
    Write-Host "Instalando $dep..." -ForegroundColor Gray
    try {
        pip install $dep --quiet
        Write-Host "✅ $dep instalado" -ForegroundColor Green
    } catch {
        Write-Host "⚠️ Error instalando $dep" -ForegroundColor Yellow
    }
}

# Paso 3: Verificar imports críticos
Write-Host "Paso 3: Verificando imports críticos..." -ForegroundColor Yellow
$critical_imports = @(
    "flask",
    "requests", 
    "aiohttp",
    "loguru",
    "yaml",
    "sqlalchemy"
)

$import_errors = @()
foreach ($import in $critical_imports) {
    try {
        $output = python -c "import $import; print('OK')" 2>&1
        if ($output -like "*OK*") {
            Write-Host "✅ $import OK" -ForegroundColor Green
        } else {
            Write-Host "❌ $import FAILED" -ForegroundColor Red
            $import_errors += $import
        }
    } catch {
        Write-Host "❌ $import ERROR" -ForegroundColor Red
        $import_errors += $import
    }
}

# Paso 4: Verificar estructura de archivos
Write-Host "Paso 4: Verificando estructura de archivos..." -ForegroundColor Yellow
$required_files = @(
    "core\fuzzing_engine.py",
    "web\app.py",
    "config.yaml"
)

$missing_files = @()
foreach ($file in $required_files) {
    if (Test-Path $file) {
        Write-Host "✅ $file existe" -ForegroundColor Green
    } else {
        Write-Host "❌ $file FALTANTE" -ForegroundColor Red
        $missing_files += $file
    }
}

# Paso 5: Test rápido del fuzzing engine
Write-Host "Paso 5: Probando fuzzing engine..." -ForegroundColor Yellow
try {
    $output = python -m core.fuzzing_engine --help 2>&1
    if ($output -like "*usage:*" -or $output -like "*URLControl*") {
        Write-Host "✅ Fuzzing engine funciona" -ForegroundColor Green
    } else {
        Write-Host "❌ Fuzzing engine ERROR: $output" -ForegroundColor Red
    }
} catch {
    Write-Host "❌ No se puede ejecutar fuzzing engine" -ForegroundColor Red
}

# Paso 6: Test rápido del dashboard
Write-Host "Paso 6: Probando dashboard..." -ForegroundColor Yellow
try {
    $process = Start-Process python -ArgumentList "web\app.py" -WindowStyle Hidden -PassThru
    Start-Sleep 3
    $response = Invoke-WebRequest -Uri "http://localhost:5000" -TimeoutSec 5 -UseBasicParsing 2>$null
    Stop-Process -Id $process.Id -Force 2>$null
    
    if ($response.StatusCode -eq 200) {
        Write-Host "✅ Dashboard funciona" -ForegroundColor Green
    } else {
        Write-Host "❌ Dashboard no responde" -ForegroundColor Red
    }
} catch {
    Write-Host "⚠️ No se pudo probar dashboard (normal si ya está ejecutándose)" -ForegroundColor Yellow
    try { Stop-Process -Id $process.Id -Force 2>$null } catch { }
}

# Resumen final
Write-Host ""
Write-Host ("=" * 50)
Write-Host "📊 RESUMEN DE REPARACIÓN" -ForegroundColor Cyan
Write-Host ("=" * 50)

if ($import_errors.Count -eq 0 -and $missing_files.Count -eq 0) {
    Write-Host "🎉 ¡SISTEMA REPARADO EXITOSAMENTE!" -ForegroundColor Green
    Write-Host ""
    Write-Host "Comandos listos para usar:" -ForegroundColor Yellow
    Write-Host "  start_dashboard.bat  - Iniciar dashboard" -ForegroundColor Gray
    Write-Host "  start_api.bat        - Iniciar API" -ForegroundColor Gray  
    Write-Host "  start_system.bat     - Sistema completo" -ForegroundColor Gray
    Write-Host ""
    Write-Host "Test del sistema:" -ForegroundColor Yellow
    Write-Host "  .\tests\test_system.ps1" -ForegroundColor Gray
    
} else {
    Write-Host "⚠️ PROBLEMAS RESTANTES:" -ForegroundColor Yellow
    
    if ($import_errors.Count -gt 0) {
        Write-Host "Dependencias faltantes: $($import_errors -join ', ')" -ForegroundColor Red
        Write-Host "Ejecuta: pip install $($import_errors -join ' ')" -ForegroundColor Yellow
    }
    
    if ($missing_files.Count -gt 0) {
        Write-Host "Archivos faltantes: $($missing_files -join ', ')" -ForegroundColor Red
        Write-Host "Revisa la estructura del proyecto" -ForegroundColor Yellow
    }
}

Write-Host ("=" * 50)