@echo off
echo Starting Security Fuzzing System...
echo.

REM Activar entorno virtual si existe
if exist venv\Scripts\activate.bat (
    call venv\Scripts\activate.bat
)

REM Iniciar sistema
D:\security_fuzzing_system\venv\Scripts\python.exe -m core.fuzzing_engine

pause
