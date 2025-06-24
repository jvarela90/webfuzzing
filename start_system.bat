REM ==========================================
REM start_system.bat - Iniciar sistema completo
REM ==========================================

@echo off
echo.
echo ==========================================
echo   🚀 Security Fuzzing System Complete
echo ==========================================
echo.

REM Activar entorno virtual
if exist "venv\Scripts\activate.bat" (
    echo Activando entorno virtual...
    call venv\Scripts\activate.bat
) else (
    echo ❌ Entorno virtual no encontrado
    echo Ejecuta: python -m venv venv
    pause
    exit /b 1
)

REM Verificar archivos principales
set "missing_files="
if not exist "core\fuzzing_engine.py" set "missing_files=%missing_files% core\fuzzing_engine.py"
if not exist "web\app.py" set "missing_files=%missing_files% web\app.py"
if not exist "config\settings.py" set "missing_files=%missing_files% config\settings.py"

if not "%missing_files%"=="" (
    echo ❌ Archivos faltantes: %missing_files%
    echo Revisa la estructura del proyecto
    pause
    exit /b 1
)

REM Crear directorios necesarios
if not exist "logs" mkdir logs
if not exist "data\databases" mkdir data\databases
if not exist "exports" mkdir exports
if not exist "reports" mkdir reports

echo.
echo ✅ SISTEMA LISTO
echo ==========================================
echo 🌐 Dashboard: http://localhost:5000
echo 🔌 API: http://localhost:8000
echo ==========================================
echo.
echo Para hacer fuzzing:
echo python -m core.fuzzing_engine --help
echo.
echo Presiona cualquier tecla para iniciar dashboard...
pause >nul

REM Iniciar dashboard
start "API Server" cmd /k "venv\Scripts\activate.bat && python api\app.py"
timeout /t 3 >nul
python web\app.py
