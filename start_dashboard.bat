REM ==========================================
REM start_dashboard.bat - Iniciar Dashboard
REM ==========================================

@echo off
echo.
echo ==========================================
echo   🚀 Security Fuzzing System Dashboard
echo ==========================================
echo.

REM Verificar que estamos en el directorio correcto
if not exist "web\app.py" (
    echo ❌ Error: No se encuentra web\app.py
    echo Ejecuta este script desde el directorio raiz del proyecto
    pause
    exit /b 1
)

REM Activar entorno virtual
if exist "venv\Scripts\activate.bat" (
    echo Activando entorno virtual...
    call venv\Scripts\activate.bat
) else (
    echo ⚠️ Entorno virtual no encontrado
    echo Ejecuta: python -m venv venv
    pause
    exit /b 1
)

REM Crear directorios necesarios
if not exist "logs" mkdir logs
if not exist "data\databases" mkdir data\databases
if not exist "exports" mkdir exports

REM Verificar dependencias críticas
echo Verificando dependencias...
python -c "import flask, requests, aiohttp; print('✅ Dependencias OK')" 2>nul
if errorlevel 1 (
    echo ❌ Faltan dependencias. Ejecuta: pip install -r requirements.txt
    pause
    exit /b 1
)

echo.
echo 🌐 Iniciando Dashboard en http://localhost:5000
echo Presiona Ctrl+C para detener
echo.

REM Iniciar dashboard
python web\app.py

pause