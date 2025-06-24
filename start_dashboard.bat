@echo off
echo Starting Web Dashboard...
echo Dashboard will be available at: http://localhost:5000
echo.

if exist venv\Scripts\activate.bat (
    call venv\Scripts\activate.bat
)

C:\Users\jvarela\AppData\Local\Microsoft\WindowsApps\PythonSoftwareFoundation.Python.3.12_qbz5n2kfra8p0\python.exe -m web.app

pause
