REM ==========================================
REM test_simple.bat - Test básico del sistema
REM ==========================================

@echo off
echo.
echo ==========================================
echo   🧪 Test Básico del Sistema
echo ==========================================
echo.

REM Activar entorno virtual
if exist "venv\Scripts\activate.bat" (
    call venv\Scripts\activate.bat
) else (
    echo ❌ Entorno virtual no encontrado
    echo Ejecuta install_dependencies.bat primero
    pause
    exit /b 1
)

set /a tests_passed=0
set /a total_tests=5

echo Test 1: Verificando dependencias Python...
python -c "import flask, requests, aiohttp; print('✅ Core dependencies OK')" && set /a tests_passed+=1 || echo "❌ Core dependencies FAILED"

echo.
echo Test 2: Verificando módulo loguru...
python -c "import loguru; print('✅ Loguru OK')" && set /a tests_passed+=1 || echo "❌ Loguru FAILED - ejecuta: pip install loguru"

echo.
echo Test 3: Verificando estructura de archivos...
if exist "core\fuzzing_engine.py" if exist "web\app.py" (
    echo ✅ Archivos principales OK
    set /a tests_passed+=1
) else (
    echo ❌ Archivos principales FALTANTES
)

echo.
echo Test 4: Verificando configuración...
if exist "config\settings.py" (
    python -c "from config.settings import config; print('✅ Config module OK')" && set /a tests_passed+=1 || echo "❌ Config module FAILED"
) else (
    echo ❌ config\settings.py no existe
)

echo.
echo Test 5: Verificando fuzzing engine...
python -m core.fuzzing_engine --help >nul 2>&1 && (
    echo ✅ Fuzzing engine OK
    set /a tests_passed+=1
) || (
    echo ❌ Fuzzing engine FAILED
)

echo.
echo ==========================================
echo 📊 RESUMEN: %tests_passed%/%total_tests% tests passed
echo ==========================================

if %tests_passed% EQU %total_tests% (
    echo 🎉 ¡SISTEMA COMPLETAMENTE FUNCIONAL!
    echo.
    echo Comandos disponibles:
    echo   start_dashboard.bat
    echo   start_api.bat
    echo   start_system.bat
) else (
    echo ⚠️ Sistema con problemas. Ejecuta:
    echo   install_dependencies.bat
    echo   Y revisa los archivos faltantes
)

echo.
pause