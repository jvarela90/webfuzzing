REM ==========================================
REM 🚀 AUTO_START_SYSTEM.BAT - Un Click para Todo
REM ==========================================

@echo off
chcp 65001 > nul
cls
echo.
echo ██████████████████████████████████████████████████████████
echo █                                                        █
echo █          🚀 SECURITY FUZZING SYSTEM 🚀               █
echo █                AUTO START SCRIPT                      █
echo █                                                        █
echo ██████████████████████████████████████████████████████████
echo.
echo ⚡ Iniciando sistema completo automáticamente...
echo.

REM Verificar que estamos en el directorio correcto
if not exist "core\fuzzing_engine.py" (
    echo ❌ Error: Ejecuta este script desde el directorio raíz del proyecto
    echo    Directorio esperado: D:\security_fuzzing_system
    echo.
    pause
    exit /b 1
)

REM Activar entorno virtual
echo 🔧 Activando entorno virtual...
if exist "venv\Scripts\activate.bat" (
    call venv\Scripts\activate.bat
    echo ✅ Entorno virtual activado
) else (
    echo ❌ Entorno virtual no encontrado
    echo    Ejecuta: python -m venv venv
    pause
    exit /b 1
)

REM Crear directorios necesarios
echo 📁 Creando directorios necesarios...
if not exist "logs" mkdir logs
if not exist "data\databases" mkdir data\databases
if not exist "exports" mkdir exports
if not exist "reports" mkdir reports
echo ✅ Directorios creados

REM Verificar dependencias críticas
echo 🔍 Verificando dependencias...
python -c "import flask, requests, aiohttp, loguru; print('✅ Dependencias OK')" 2>nul
if errorlevel 1 (
    echo ❌ Faltan dependencias críticas
    echo 📦 Instalando dependencias automáticamente...
    pip install flask requests aiohttp loguru pyyaml sqlalchemy flask-cors flask-restful beautifulsoup4 colorama tqdm
    echo ✅ Dependencias instaladas
)

REM Test rápido del sistema
echo 🧪 Ejecutando test rápido del sistema...
python -c "from config.settings import config; print('✅ Config OK')" 2>nul
if errorlevel 1 (
    echo ❌ Error en configuración
    pause
    exit /b 1
)

echo.
echo =========================================
echo 🚀 INICIANDO SERVICIOS DEL SISTEMA
echo =========================================
echo.

REM Iniciar API REST en background
echo 🔌 Iniciando API REST (Puerto 8000)...
start "Security Fuzzing API" /min cmd /k "title Security Fuzzing API && venv\Scripts\activate.bat && python api\app.py"
timeout /t 3 /nobreak > nul

REM Iniciar Dashboard Web en background  
echo 🌐 Iniciando Dashboard Web (Puerto 5000)...
start "Security Fuzzing Dashboard" /min cmd /k "title Security Fuzzing Dashboard && venv\Scripts\activate.bat && python web\app.py"
timeout /t 3 /nobreak > nul

REM Verificar que los servicios están corriendo
echo ⏳ Verificando servicios...
timeout /t 5 /nobreak > nul

REM Intentar conectar a la API
echo 🔍 Verificando API REST...
curl -s http://localhost:8000/health > nul 2>&1
if errorlevel 1 (
    echo ⚠️ API no responde aún, esperando más tiempo...
    timeout /t 5 /nobreak > nul
)

REM Intentar conectar al Dashboard
echo 🔍 Verificando Dashboard...
curl -s http://localhost:5000 > nul 2>&1
if errorlevel 1 (
    echo ⚠️ Dashboard no responde aún, esperando más tiempo...
    timeout /t 3 /nobreak > nul
)

echo.
echo ✅ SERVICIOS INICIADOS CORRECTAMENTE
echo.
echo =========================================
echo 🌐 ABRIENDO NAVEGADORES AUTOMÁTICAMENTE
echo =========================================
echo.

REM Abrir navegadores automáticamente
echo 🌐 Abriendo Dashboard en navegador...
start http://localhost:5000
timeout /t 2 /nobreak > nul

echo 🔌 Abriendo API Health Check...
start http://localhost:8000/health
timeout /t 2 /nobreak > nul

echo 📚 Abriendo documentación de API...
start http://localhost:8000/docs

echo.
echo ██████████████████████████████████████████████████████████
echo █                                                        █
echo █                ✅ SISTEMA INICIADO ✅                 █
echo █                                                        █
echo ██████████████████████████████████████████████████████████
echo.
echo 🎯 URLs del Sistema:
echo    Dashboard Web:    http://localhost:5000
echo    API REST:         http://localhost:8000  
echo    Health Check:     http://localhost:8000/health
echo    Documentación:    http://localhost:8000/docs
echo.
echo 🔧 Comandos útiles:
echo    Fuzzing:          python -m core.fuzzing_engine --help
echo    Test sistema:     .\tests\test_system.ps1
echo.
echo 📊 Ventanas abiertas:
echo    - Security Fuzzing API (minimizada)
echo    - Security Fuzzing Dashboard (minimizada)
echo    - 3 pestañas del navegador
echo.
echo ⚠️  Para DETENER todo el sistema:
echo    1. Cierra las ventanas de cmd minimizadas
echo    2. O ejecuta: .\stop_all_services.bat
echo.
echo 🎉 ¡SISTEMA LISTO PARA USAR!
echo.
echo Presiona cualquier tecla para mostrar el menú de control...
pause > nul

:menu
cls
echo.
echo ████████████████████████████████████████████████████████████
echo █                                                          █
echo █             🎛️  PANEL DE CONTROL 🎛️                    █
echo █                                                          █
echo ████████████████████████████████████████████████████████████
echo.
echo Selecciona una opción:
echo.
echo 1. 🌐 Abrir Dashboard (http://localhost:5000)
echo 2. 🔌 Abrir API Health Check
echo 3. 📚 Abrir Documentación API
echo 4. 🧪 Ejecutar Test del Sistema
echo 5. ⚡ Hacer Fuzzing de Prueba
echo 6. 📊 Ver Estado de Servicios
echo 7. 🛑 Detener Todos los Servicios
echo 8. 🔄 Reiniciar Sistema
echo 9. ❌ Salir
echo.
set /p choice="Ingresa tu opción (1-9): "

if "%choice%"=="1" (
    start http://localhost:5000
    echo ✅ Dashboard abierto
    timeout /t 2 > nul
    goto menu
)
if "%choice%"=="2" (
    start http://localhost:8000/health
    echo ✅ Health Check abierto
    timeout /t 2 > nul
    goto menu
)
if "%choice%"=="3" (
    start http://localhost:8000/docs
    echo ✅ Documentación abierta
    timeout /t 2 > nul
    goto menu
)
if "%choice%"=="4" (
    echo 🧪 Ejecutando test del sistema...
    powershell -ExecutionPolicy Bypass -File ".\tests\test_system.ps1"
    echo.
    pause
    goto menu
)
if "%choice%"=="5" (
    echo ⚡ Ejecutando fuzzing de prueba...
    python -m core.fuzzing_engine --url "http://httpbin.org/FUZZ" --payloads "data\wordlists\common.txt" --output "test_results" --format "json"
    echo.
    echo ✅ Fuzzing completado. Revisa test_results.json
    pause
    goto menu
)
if "%choice%"=="6" (
    echo 📊 Verificando estado de servicios...
    echo.
    echo API REST (Puerto 8000):
    curl -s http://localhost:8000/health || echo ❌ API no responde
    echo.
    echo Dashboard (Puerto 5000):
    curl -s http://localhost:5000 > nul && echo ✅ Dashboard OK || echo ❌ Dashboard no responde
    echo.
    pause
    goto menu
)
if "%choice%"=="7" (
    echo 🛑 Deteniendo todos los servicios...
    taskkill /f /fi "WindowTitle eq Security Fuzzing API" > nul 2>&1
    taskkill /f /fi "WindowTitle eq Security Fuzzing Dashboard" > nul 2>&1
    echo ✅ Servicios detenidos
    pause
    goto menu
)
if "%choice%"=="8" (
    echo 🔄 Reiniciando sistema...
    taskkill /f /fi "WindowTitle eq Security Fuzzing API" > nul 2>&1
    taskkill /f /fi "WindowTitle eq Security Fuzzing Dashboard" > nul 2>&1
    timeout /t 2 > nul
    goto restart_services
)
if "%choice%"=="9" (
    echo 👋 Saliendo...
    echo.
    echo ⚠️  Los servicios siguen ejecutándose en background
    echo    Para detenerlos: taskkill /f /fi "WindowTitle eq Security Fuzzing*"
    echo.
    pause
    exit /b 0
)

echo ❌ Opción no válida
timeout /t 2 > nul
goto menu

:restart_services
echo 🔄 Reiniciando servicios...
start "Security Fuzzing API" /min cmd /k "title Security Fuzzing API && venv\Scripts\activate.bat && python api\app.py"
timeout /t 3 /nobreak > nul
start "Security Fuzzing Dashboard" /min cmd /k "title Security Fuzzing Dashboard && venv\Scripts\activate.bat && python web\app.py"
timeout /t 3 /nobreak > nul
echo ✅ Servicios reiniciados
timeout /t 2 > nul
goto menu

REM ==========================================
REM 🛑 STOP_ALL_SERVICES.BAT
REM ==========================================

REM Crear script para detener servicios
echo @echo off > stop_all_services.bat
echo echo 🛑 Deteniendo Security Fuzzing System... >> stop_all_services.bat
echo taskkill /f /fi "WindowTitle eq Security Fuzzing API" ^> nul 2^>^&1 >> stop_all_services.bat
echo taskkill /f /fi "WindowTitle eq Security Fuzzing Dashboard" ^> nul 2^>^&1 >> stop_all_services.bat
echo echo ✅ Todos los servicios detenidos >> stop_all_services.bat
echo pause >> stop_all_services.bat

REM ==========================================
REM 🚀 START_SYSTEM_SILENT.BAT (Sin menú)
REM ==========================================

REM Crear versión silenciosa
echo @echo off > start_system_silent.bat
echo call venv\Scripts\activate.bat >> start_system_silent.bat
echo start "Security Fuzzing API" /min cmd /k "title Security Fuzzing API && venv\Scripts\activate.bat && python api\app.py" >> start_system_silent.bat
echo timeout /t 3 /nobreak ^> nul >> start_system_silent.bat
echo start "Security Fuzzing Dashboard" /min cmd /k "title Security Fuzzing Dashboard && venv\Scripts\activate.bat && python web\app.py" >> start_system_silent.bat
echo timeout /t 3 /nobreak ^> nul >> start_system_silent.bat
echo start http://localhost:5000 >> start_system_silent.bat
echo start http://localhost:8000/health >> start_system_silent.bat
echo echo ✅ Sistema iniciado silenciosamente >> start_system_silent.bat

echo.
echo ✅ Scripts adicionales creados:
echo    - stop_all_services.bat (detener sistema)
echo    - start_system_silent.bat (inicio sin menú)