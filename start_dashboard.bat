@echo off
echo Starting Web Dashboard...
echo Dashboard will be available at: http://localhost:5000
echo.

if exist venv\Scripts\activate.bat (
    call venv\Scripts\activate.bat
)

D:\security_fuzzing_system\venv\Scripts\python.exe -m web.app

pause