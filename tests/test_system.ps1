# test_system.ps1 - Prueba completa del sistema
Write-Host "Testing Security Fuzzing System" -ForegroundColor Cyan
Write-Host ("=" * 60)

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
    Write-Host "Estructura de archivos OK" -ForegroundColor Green
    $tests_passed++
} else {
    Write-Host "Archivos faltantes: $($missing -join ', ')" -ForegroundColor Red
    $errors += "Archivos faltantes"
}

# Test 2: Verificar entorno virtual
Write-Host "Test 2: Verificando entorno virtual..." -ForegroundColor Yellow
if (Test-Path "venv\Scripts\python.exe") {
    Write-Host "Entorno virtual OK" -ForegroundColor Green
    $tests_passed++
} else {
    Write-Host "Entorno virtual no encontrado" -ForegroundColor Red
    $errors += "Entorno virtual faltante"
}

# Test 3: Verificar dependencias Python
Write-Host "Test 3: Verificando dependencias Python..." -ForegroundColor Yellow
try {
    $output = & .\venv\Scripts\python.exe -c "import flask, requests, aiohttp; print('Dependencies OK')" 2>&1
    if ($output -like "*Dependencies OK*") {
        Write-Host "Dependencias Python OK" -ForegroundColor Green
        $tests_passed++
    } else {
        Write-Host "Faltan dependencias Python" -ForegroundColor Red
        $errors += "Dependencias Python faltantes"
    }
} catch {
    Write-Host "Error verificando dependencias Python" -ForegroundColor Red
    $errors += "Error en dependencias Python"
}

# Test 4: Verificar loguru
Write-Host "Test 4: Verificando loguru..." -ForegroundColor Yellow
try {
    $output = & .\venv\Scripts\python.exe -c "import loguru; print('Loguru OK')" 2>&1
    if ($output -like "*Loguru OK*") {
        Write-Host "Loguru OK" -ForegroundColor Green
        $tests_passed++
    } else {
        Write-Host "Loguru no instalado" -ForegroundColor Red
        $errors += "Loguru faltante"
    }
} catch {
    Write-Host "Error verificando loguru" -ForegroundColor Red
    $errors += "Error en loguru"
}

# Test 5: Verificar módulo config
Write-Host "Test 5: Verificando modulo config..." -ForegroundColor Yellow
try {
    $output = & .\venv\Scripts\python.exe -c "from config.settings import config; print('Config module OK')" 2>&1
    if ($output -like "*Config module OK*") {
        Write-Host "Modulo config OK" -ForegroundColor Green
        $tests_passed++
    } else {
        Write-Host "Error en modulo config" -ForegroundColor Red
        $errors += "Modulo config con errores"
    }
} catch {
    Write-Host "Error verificando modulo config" -ForegroundColor Red
    $errors += "Error en modulo config"
}

# Test 6: Verificar fuzzing engine
Write-Host "Test 6: Verificando fuzzing engine..." -ForegroundColor Yellow
try {
    $output = & .\venv\Scripts\python.exe -m core.fuzzing_engine --help 2>&1
    if ($output -like "*URLControl Fuzzing Engine*" -or $output -like "*usage:*") {
        Write-Host "Fuzzing engine OK" -ForegroundColor Green
        $tests_passed++
    } else {
        Write-Host "Error en fuzzing engine" -ForegroundColor Red
        $errors += "Fuzzing engine con errores"
    }
} catch {
    Write-Host "Error ejecutando fuzzing engine" -ForegroundColor Red
    $errors += "Fuzzing engine no ejecutable"
}

# Test 7: Verificar config.yaml
Write-Host "Test 7: Verificando config.yaml..." -ForegroundColor Yellow
try {
    $output = & .\venv\Scripts\python.exe -c "import yaml; yaml.safe_load(open('config.yaml', 'r', encoding='utf-8')); print('YAML OK')" 2>&1
    if ($output -like "*YAML OK*") {
        Write-Host "Config.yaml OK" -ForegroundColor Green
        $tests_passed++
    } else {
        Write-Host "Error en config.yaml" -ForegroundColor Red
        $errors += "Config.yaml con errores de sintaxis"
    }
} catch {
    Write-Host "Error verificando config.yaml" -ForegroundColor Red
    $errors += "Error en config.yaml"
}

# Test 8: Test de importación completa (corregido)
Write-Host "Test 8: Test de importacion completa..." -ForegroundColor Yellow
try {
    # Crear archivo temporal para el test
    $test_code = @"
import sys
import os
sys.path.append('.')
try:
    from config.settings import config
    from core.fuzzing_engine import *
    import flask, requests, aiohttp, loguru
    print('Complete import test OK')
except Exception as e:
    print(f'Import error: {e}')
"@
    
    $temp_file = "temp_test.py"
    $test_code | Out-File -FilePath $temp_file -Encoding UTF8
    
    $output = & .\venv\Scripts\python.exe $temp_file 2>&1
    
    # Limpiar archivo temporal
    Remove-Item $temp_file -ErrorAction SilentlyContinue
    
    if ($output -like "*Complete import test OK*") {
        Write-Host "Importacion completa OK" -ForegroundColor Green
        $tests_passed++
    } else {
        Write-Host "Error en importacion completa: $output" -ForegroundColor Red
        $errors += "Error en importacion completa"
    }
} catch {
    Write-Host "Error en test de importacion" -ForegroundColor Red
    $errors += "Error en test de importacion"
    # Limpiar archivo temporal en caso de error
    Remove-Item "temp_test.py" -ErrorAction SilentlyContinue
}

# Resumen final
Write-Host ""
Write-Host ("=" * 60)
Write-Host "Resumen de Pruebas" -ForegroundColor Cyan
Write-Host ("=" * 60)
Write-Host "Pruebas exitosas: $tests_passed/$total_tests" -ForegroundColor Green

if ($errors.Count -eq 0) {
    Write-Host ""
    Write-Host "SISTEMA 100% FUNCIONAL!" -ForegroundColor Green -BackgroundColor DarkGreen
    Write-Host ""
    Write-Host "Comandos listos para usar:" -ForegroundColor Yellow
    Write-Host "  Dashboard:     python web\app.py" -ForegroundColor Gray
    Write-Host "  API REST:      python api\app.py" -ForegroundColor Gray
    Write-Host "  Fuzzer:        python -m core.fuzzing_engine --help" -ForegroundColor Gray
    Write-Host "  Scripts BAT:   start_dashboard.bat" -ForegroundColor Gray
    Write-Host ""
    Write-Host "URLs del sistema:" -ForegroundColor Yellow
    Write-Host "  Dashboard:     http://localhost:5000" -ForegroundColor Cyan
    Write-Host "  API REST:      http://localhost:8000" -ForegroundColor Cyan
    Write-Host "  Health Check:  http://localhost:8000/health" -ForegroundColor Cyan
    
} else {
    Write-Host "Errores encontrados ($($errors.Count)):" -ForegroundColor Red
    for ($i = 0; $i -lt $errors.Count; $i++) {
        Write-Host "   $($i + 1). $($errors[$i])" -ForegroundColor Red
    }
    Write-Host ""
    Write-Host "Soluciones recomendadas:" -ForegroundColor Yellow
    Write-Host "   1. Crear archivo api\app.py" -ForegroundColor Gray
    Write-Host "   2. Verificar imports en core\fuzzing_engine.py" -ForegroundColor Gray
    Write-Host "   3. Ejecutar: pip install -r requirements.txt" -ForegroundColor Gray
}

Write-Host ("=" * 60)

# Mostrar siguiente paso recomendado
if ($tests_passed -lt $total_tests) {
    Write-Host ""
    Write-Host "Proximo Paso:" -ForegroundColor Cyan
    if ($errors -contains "Archivos faltantes") {
        Write-Host "Crear archivo: api\app.py" -ForegroundColor Yellow
    } else {
        Write-Host "Revisar errores especificos mostrados arriba" -ForegroundColor Yellow
    }
} else {
    Write-Host ""
    Write-Host "SISTEMA LISTO!" -ForegroundColor Green
    Write-Host "Ejecuta: start_dashboard.bat" -ForegroundColor Yellow
}