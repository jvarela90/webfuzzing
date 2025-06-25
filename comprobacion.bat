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

REM ==========================================
REM install_dependencies.bat - Instalar dependencias
REM ==========================================

@echo off
echo.
echo ==========================================
echo   📦 Instalando Dependencias
echo ==========================================
echo.

REM Verificar Python
python --version >nul 2>&1
if errorlevel 1 (
    echo ❌ Python no está instalado o no está en PATH
    echo Instala Python desde https://python.org
    pause
    exit /b 1
)

REM Crear entorno virtual si no existe
if not exist "venv" (
    echo Creando entorno virtual...
    python -m venv venv
)

REM Activar entorno virtual
echo Activando entorno virtual...
call venv\Scripts\activate.bat

REM Actualizar pip
echo Actualizando pip...
python -m pip install --upgrade pip

REM Instalar dependencias esenciales
echo Instalando dependencias esenciales...
pip install flask requests aiohttp pyyaml sqlalchemy
pip install flask-cors flask-socketio flask-restful
pip install loguru colorama tqdm
pip install beautifulsoup4 pandas plotly jinja2
pip install cryptography

REM Verificar instalación
echo.
echo Verificando instalación...
python -c "import flask, requests, aiohttp, loguru; print('✅ Dependencias principales OK')"
python -c "import pandas, plotly; print('✅ Dependencias de análisis OK')"
python -c "import beautifulsoup4; print('✅ Dependencias de scraping OK')" 2>nul || echo "⚠️ beautifulsoup4 opcional"

echo.
echo ✅ INSTALACIÓN COMPLETADA
echo ==========================================
echo Ahora puedes ejecutar:
echo   start_dashboard.bat  - Dashboard web
echo   start_api.bat        - API REST  
echo   start_system.bat     - Sistema completo
echo ==========================================
pause

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