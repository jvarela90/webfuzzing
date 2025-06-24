REM ==========================================
REM start_api.bat - Iniciar API REST
REM ==========================================

@echo off
echo.
echo ==========================================
echo   🔌 Security Fuzzing System API
echo ==========================================
echo.

REM Verificar que estamos en el directorio correcto
if not exist "api\app.py" (
    echo ❌ Error: No se encuentra api\app.py
    echo Asegurate de haber creado el archivo api\app.py
    pause
    exit /b 1
)

REM Activar entorno virtual
if exist "venv\Scripts\activate.bat" (
    echo Activando entorno virtual...
    call venv\Scripts\activate.bat
) else (
    echo ⚠️ Entorno virtual no encontrado
    pause
    exit /b 1
)

REM Verificar dependencias
echo Verificando dependencias...
python -c "import flask, flask_restful, flask_cors; print('✅ API dependencies OK')" 2>nul
if errorlevel 1 (
    echo ❌ Faltan dependencias para la API
    pause
    exit /b 1
)

echo.
echo 🌐 Iniciando API en http://localhost:8000
echo Presiona Ctrl+C para detener
echo.

REM Iniciar API
python api\app.py

pause
