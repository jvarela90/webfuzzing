@echo off
echo Starting Security Fuzzing System...
echo.

REM Activar entorno virtual si existe
if exist venv\Scripts\activate.bat (
    call venv\Scripts\activate.bat
)

REM Iniciar sistema
C:\Users\jvarela\AppData\Local\Microsoft\WindowsApps\PythonSoftwareFoundation.Python.3.12_qbz5n2kfra8p0\python.exe -m core.fuzzing_engine

pause
