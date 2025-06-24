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
