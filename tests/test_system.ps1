# test_system.ps1 - Prueba completa del sistema
Write-Host "🧪 TESTING SECURITY FUZZING SYSTEM" -ForegroundColor Cyan
Write-Host "=" * 60

$errors = @()
$tests_passed = 0
$total_tests = 8

# Test 1: Verificar estructura de archivos
Write-Host "Test 1: Verificando estructura de archivos..." -ForegroundColor Yellow
$required_files = @(
    "config\settings.py",
    "config\__init__.py", 
    "api\app.py",
    "web\app.py",
    "core\fuzzing_engine.py",
    "config.yaml"
)

$missing = @()
foreach ($file in $required_files) {
    if (-not (Test-Path $file)) {
        $missing += $file
    }
}

if ($missing.Count -eq 0) {
    Write-Host "✅ Estructura de archivos OK" -ForegroundColor Green
    $tests_passed++
} else {
    Write-Host "❌ Archivos faltantes: $($missing -join ', ')" -ForegroundColor Red
    $errors += "Archivos faltantes"
}

# Test 2: Verificar entorno virtual
Write-Host "Test 2: Verificando entorno virtual..." -ForegroundColor Yellow
if (Test-Path "venv\Scripts\python.exe") {
    Write-Host "✅ Entorno virtual OK" -ForegroundColor Green
    $tests_passed++
} else {
    Write-Host "❌ Entorno virtual no encontrado" -ForegroundColor Red
    $errors += "Entorno virtual faltante"
}

# Test 3: Verificar dependencias Python
Write-Host "Test 3: Verificando dependencias Python..." -ForegroundColor Yellow
try {
    & .\venv\Scripts\python.exe -c "import flask, requests, aiohttp, yaml, sqlalchemy; print('Dependencies OK')" 2>$null
    Write-Host "✅ Dependencias Python OK" -ForegroundColor Green
    $tests_passed++
} catch {
    Write-Host "❌ Faltan dependencias Python" -ForegroundColor Red
    $errors += "Dependencias Python faltantes"
}

# Test 4: Verificar módulo config
Write-Host "Test 4: Verificando módulo config..." -ForegroundColor Yellow
try {
    & .\venv\Scripts\python.exe -c "from config.settings import config; print('Config module OK')" 2>$null
    Write-Host "✅ Módulo config OK" -ForegroundColor Green
    $tests_passed++
} catch {
    Write-Host "❌ Error en módulo config" -ForegroundColor Red
    $errors += "Módulo config con errores"
}

# Test 5: Verificar fuzzing engine
Write-Host "Test 5: Verificando fuzzing engine..." -ForegroundColor Yellow
try {
    $output = & .\venv\Scripts\python.exe -m core.fuzzing_engine --help 2>&1
    if ($output -like "*URLControl Fuzzing Engine*") {
        Write-Host "✅ Fuzzing engine OK" -ForegroundColor Green
        $tests_passed++
    } else {
        Write-Host "❌ Error en fuzzing engine" -ForegroundColor Red
        $errors += "Fuzzing engine con errores"
    }
} catch {
    Write-Host "❌ Error ejecutando fuzzing engine" -ForegroundColor Red
    $errors += "Fuzzing engine no ejecutable"
}

# Test 6: Verificar API (inicio rápido)
Write-Host "Test 6: Verificando API..." -ForegroundColor Yellow
try {
    $api_process = Start-Process -FilePath ".\venv\Scripts\python.exe" -ArgumentList "api\app.py" -WindowStyle Hidden -PassThru
    Start-Sleep 3
    
    $response = Invoke-WebRequest -Uri "http://localhost:8000/health" -TimeoutSec 5 -UseBasicParsing 2>$null
    if ($response.StatusCode -eq 200) {
        Write-Host "✅ API OK" -ForegroundColor Green
        $tests_passed++
    } else {
        Write-Host "❌ API no responde correctamente" -ForegroundColor Red
        $errors += "API con problemas"
    }
    
    Stop-Process -Id $api_process.Id -Force 2>$null
} catch {
    Write-Host "❌ Error en API" -ForegroundColor Red
    $errors += "API no funciona"
}

# Test 7: Verificar Dashboard (inicio rápido)
Write-Host "Test 7: Verificando Dashboard..." -ForegroundColor Yellow
try {
    $web_process = Start-Process -FilePath ".\venv\Scripts\python.exe" -ArgumentList "web\app.py" -WindowStyle Hidden -PassThru
    Start-Sleep 3
    
    $response = Invoke-WebRequest -Uri "http://localhost:5000" -TimeoutSec 5 -UseBasicParsing 2>$null
    if ($response.StatusCode -eq 200) {
        Write-Host "✅ Dashboard OK" -ForegroundColor Green
        $tests_passed++
    } else {
        Write-Host "❌ Dashboard no responde" -ForegroundColor Red
        $errors += "Dashboard con problemas"
    }
    
    Stop-Process -Id $web_process.Id -Force 2>$null
} catch {
    Write-Host "❌ Error en Dashboard" -ForegroundColor Red
    $errors += "Dashboard no funciona"
}

# Test 8: Verificar config.yaml
Write-Host "Test 8: Verificando config.yaml..." -ForegroundColor Yellow
try {
    & .\venv\Scripts\python.exe -c "import yaml; yaml.safe_load(open('config.yaml', 'r', encoding='utf-8')); print('YAML OK')" 2>$null
    Write-Host "✅ Config.yaml OK" -ForegroundColor Green
    $tests_passed++
} catch {
    Write-Host "❌ Error en config.yaml" -ForegroundColor Red
    $errors += "Config.yaml con errores de sintaxis"
}

# Resumen final
Write-Host ""
Write-Host "=" * 60
Write-Host "📊 RESUMEN DE PRUEBAS" -ForegroundColor Cyan
Write-Host "=" * 60
Write-Host "✅ Pruebas exitosas: $tests_passed/$total_tests" -ForegroundColor Green

if ($errors.Count -eq 0) {
    Write-Host "🎉 ¡SISTEMA COMPLETAMENTE FUNCIONAL!" -ForegroundColor Green
    Write-Host ""
    Write-Host "Comandos para usar:" -ForegroundColor Yellow
    Write-Host "  • Dashboard: python web\app.py" -ForegroundColor Gray
    Write-Host "  • API: python api\app.py" -ForegroundColor Gray
    Write-Host "  • Fuzzer: python -m core.fuzzing_engine --help" -ForegroundColor Gray
} else {
    Write-Host "❌ Errores encontrados:" -ForegroundColor Red
    foreach ($error in $errors) {
        Write-Host "   - $error" -ForegroundColor Red
    }
    Write-Host ""
    Write-Host "🔧 Soluciones recomendadas:" -ForegroundColor Yellow
    Write-Host "   1. Ejecutar fix_environment.ps1" -ForegroundColor Gray
    Write-Host "   2. Crear archivos faltantes" -ForegroundColor Gray
    Write-Host "   3. Instalar dependencias: pip install -r requirements.txt" -ForegroundColor Gray
}

Write-Host "=" * 60