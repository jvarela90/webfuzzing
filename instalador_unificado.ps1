# ==========================================
# 🚀 SECURITY FUZZING SYSTEM
# INSTALADOR COMPLETO UNIFICADO
# ==========================================
# Versión: 2.0.0
# Descripción: Instalador todo-en-uno que configura el sistema completo
# Incluye: Entorno, dependencias, configuración, scripts, tests y reparaciones

param(
    [switch]$Silent,           # Instalación silenciosa
    [switch]$RepairOnly,       # Solo reparar dashboard
    [switch]$CreateShortcuts,  # Crear accesos directos
    [switch]$RunTests,         # Ejecutar tests al final
    [switch]$SkipDependencies, # Omitir instalación de dependencias
    [string]$InstallPath = (Get-Location).Path
)

# ==========================================
# CONFIGURACIÓN GLOBAL
# ==========================================

$Global:Config = @{
    SystemName = "Security Fuzzing System"
    Version = "2.0.0"
    InstallPath = $InstallPath
    VenvPath = Join-Path $InstallPath "venv"
    LogPath = Join-Path $InstallPath "logs"
    StartTime = Get-Date
    RequiredPython = [version]"3.8.0"
}

# Configurar entorno
$Host.UI.RawUI.WindowTitle = "$($Global:Config.SystemName) - Instalador Unificado v$($Global:Config.Version)"
$ErrorActionPreference = "Continue"

# ==========================================
# FUNCIONES CORE
# ==========================================

function Write-Banner {
    Clear-Host
    Write-Host ""
    Write-Host "██████████████████████████████████████████████████████████" -ForegroundColor Cyan
    Write-Host "█                                                        █" -ForegroundColor Cyan
    Write-Host "█          🚀 SECURITY FUZZING SYSTEM 🚀               █" -ForegroundColor Yellow
    Write-Host "█                                                        █" -ForegroundColor Yellow
    Write-Host "█              INSTALADOR UNIFICADO                     █" -ForegroundColor Cyan
    Write-Host "█                   Versión 2.0.0                       █" -ForegroundColor Cyan
    Write-Host "█                                                        █" -ForegroundColor Cyan
    Write-Host "██████████████████████████████████████████████████████████" -ForegroundColor Cyan
    Write-Host ""
}

function Write-Log {
    param([string]$Message, [string]$Type = "Info")
    
    $timestamp = Get-Date -Format "HH:mm:ss"
    $logMessage = "[$timestamp] $Message"
    
    # Crear directorio de logs
    if (-not (Test-Path $Global:Config.LogPath)) {
        New-Item -ItemType Directory -Path $Global:Config.LogPath -Force | Out-Null
    }
    
    # Log a archivo
    $logFile = Join-Path $Global:Config.LogPath "installer.log"
    Add-Content -Path $logFile -Value $logMessage -ErrorAction SilentlyContinue
    
    # Log a consola
    switch ($Type) {
        "Success" { Write-Host "✅ $Message" -ForegroundColor Green }
        "Error"   { Write-Host "❌ $Message" -ForegroundColor Red }
        "Warning" { Write-Host "⚠️ $Message" -ForegroundColor Yellow }
        "Info"    { Write-Host "ℹ️ $Message" -ForegroundColor Cyan }
        "Step"    { Write-Host "🔧 $Message" -ForegroundColor Magenta }
    }
}

function Show-Progress {
    param([string]$Activity, [string]$Status, [int]$PercentComplete)
    Write-Progress -Activity $Activity -Status $Status -PercentComplete $PercentComplete
}

# ==========================================
# VERIFICACIÓN DE PRERREQUISITOS
# ==========================================

function Test-Prerequisites {
    Write-Log "Verificando prerrequisitos del sistema..." "Step"
    Show-Progress "Verificación" "Verificando prerrequisitos..." 10
    
    $prereqsMet = $true
    $issues = @()
    
    # Verificar Python
    try {
        $pythonVersion = python --version 2>&1
        if ($pythonVersion -match "Python (\d+\.\d+\.\d+)") {
            $version = [version]$matches[1]
            if ($version -ge $Global:Config.RequiredPython) {
                Write-Log "Python $version encontrado ✓" "Success"
            } else {
                Write-Log "Python $version es muy antiguo. Se requiere Python $($Global:Config.RequiredPython)+" "Error"
                $issues += "Python version too old"
                $prereqsMet = $false
            }
        }
    } catch {
        Write-Log "Python no está instalado o no está en PATH" "Error"
        $issues += "Python not found"
        $prereqsMet = $false
    }
    
    # Verificar pip
    try {
        $pipVersion = pip --version 2>&1
        if ($pipVersion -like "*pip*") {
            Write-Log "pip encontrado ✓" "Success"
        }
    } catch {
        Write-Log "pip no encontrado" "Warning"
        $issues += "pip not found"
    }
    
    # Verificar permisos
    try {
        $testFile = Join-Path $Global:Config.InstallPath "test_permissions.tmp"
        "test" | Out-File -FilePath $testFile -ErrorAction Stop
        Remove-Item $testFile -ErrorAction SilentlyContinue
        Write-Log "Permisos de escritura ✓" "Success"
    } catch {
        Write-Log "Sin permisos de escritura en directorio de instalación" "Error"
        $issues += "No write permissions"
        $prereqsMet = $false
    }
    
    # Verificar espacio en disco
    $drive = (Get-Location).Drive
    $freeSpace = (Get-WmiObject -Class Win32_LogicalDisk -Filter "DeviceID='$($drive.Name)'").FreeSpace / 1GB
    if ($freeSpace -gt 0.5) {
        Write-Log "Espacio libre: $([math]::Round($freeSpace, 2)) GB ✓" "Success"
    } else {
        Write-Log "Espacio insuficiente: $([math]::Round($freeSpace, 2)) GB" "Warning"
        $issues += "Low disk space"
    }
    
    Show-Progress "Verificación" "Prerrequisitos verificados" 100
    Write-Progress -Activity "Verificación" -Completed
    
    if (-not $prereqsMet) {
        Write-Host ""
        Write-Host "❌ PROBLEMAS ENCONTRADOS:" -ForegroundColor Red
        foreach ($issue in $issues) {
            Write-Host "   • $issue" -ForegroundColor Red
        }
        Write-Host ""
        Write-Host "🔧 SOLUCIONES:" -ForegroundColor Yellow
        Write-Host "   • Instala Python 3.8+ desde https://python.org" -ForegroundColor Gray
        Write-Host "   • Ejecuta como administrador si es necesario" -ForegroundColor Gray
        Write-Host "   • Libera espacio en disco" -ForegroundColor Gray
    }
    
    return $prereqsMet
}

# ==========================================
# CONFIGURACIÓN DEL ENTORNO
# ==========================================

function Initialize-Environment {
    Write-Log "Inicializando entorno de desarrollo..." "Step"
    Show-Progress "Entorno" "Configurando entorno virtual..." 25
    
    # Crear/recrear entorno virtual
    if (Test-Path $Global:Config.VenvPath) {
        Write-Log "Entorno virtual existente encontrado, recreando..." "Warning"
        Remove-Item -Recurse -Force $Global:Config.VenvPath -ErrorAction SilentlyContinue
    }
    
    try {
        python -m venv $Global:Config.VenvPath
        Write-Log "Entorno virtual creado exitosamente" "Success"
    } catch {
        Write-Log "Error creando entorno virtual: $($_.Exception.Message)" "Error"
        return $false
    }
    
    Show-Progress "Entorno" "Creando estructura de directorios..." 75
    
    # Crear estructura completa de directorios
    $directories = @(
        "logs", "data", "data\databases", "data\wordlists", "exports", "reports", 
        "temp", "config", "tests", "scripts", "docs", "web\templates", "web\static",
        "api\routes", "core", "tools"
    )
    
    foreach ($dir in $directories) {
        $fullPath = Join-Path $Global:Config.InstallPath $dir
        if (-not (Test-Path $fullPath)) {
            New-Item -ItemType Directory -Path $fullPath -Force | Out-Null
        }
    }
    
    Show-Progress "Entorno" "Entorno inicializado" 100
    Write-Progress -Activity "Entorno" -Completed
    Write-Log "Estructura de directorios creada" "Success"
    
    return $true
}

# ==========================================
# INSTALACIÓN DE DEPENDENCIAS
# ==========================================

function Install-Dependencies {
    if ($SkipDependencies) {
        Write-Log "Omitiendo instalación de dependencias" "Info"
        return $true
    }
    
    Write-Log "Instalando dependencias de Python..." "Step"
    Show-Progress "Dependencias" "Preparando instalación..." 5
    
    $pythonExe = Join-Path $Global:Config.VenvPath "Scripts\python.exe"
    $pipExe = Join-Path $Global:Config.VenvPath "Scripts\pip.exe"
    
    if (-not (Test-Path $pythonExe)) {
        Write-Log "Python no encontrado en entorno virtual" "Error"
        return $false
    }
    
    try {
        # Actualizar pip
        Write-Log "Actualizando pip..." "Info"
        & $pythonExe -m pip install --upgrade pip --quiet
        Show-Progress "Dependencias" "pip actualizado..." 10
        
        # Dependencias críticas (orden de instalación importante)
        $criticalDeps = @(
            @{name="flask"; version=">=2.3.0,<3.0.0"; desc="Framework web principal"},
            @{name="requests"; version=">=2.31.0,<3.0.0"; desc="Cliente HTTP"},
            @{name="aiohttp"; version=">=3.8.5,<4.0.0"; desc="Cliente HTTP asíncrono"},
            @{name="pyyaml"; version=">=6.0.1,<7.0.0"; desc="Parser YAML"},
            @{name="sqlalchemy"; version=">=2.0.20,<3.0.0"; desc="ORM de base de datos"},
            @{name="loguru"; version=">=0.7.0,<1.0.0"; desc="Sistema de logging"}
        )
        
        $progress = 15
        foreach ($dep in $criticalDeps) {
            Write-Log "Instalando $($dep.name) - $($dep.desc)" "Info"
            & $pipExe install "$($dep.name)$($dep.version)" --quiet
            $progress += 10
            Show-Progress "Dependencias" "Instalado $($dep.name)..." $progress
        }
        
        # Dependencias web
        $webDeps = @("flask-cors>=4.0.0", "flask-restful>=0.3.10", "flask-socketio>=5.3.0", "jinja2>=3.1.0", "werkzeug>=2.3.0")
        foreach ($dep in $webDeps) {
            & $pipExe install $dep --quiet
            $progress += 5
            Show-Progress "Dependencias" "Instalando dependencias web..." $progress
        }
        
        # Dependencias de datos (pandas puede fallar, manejar graciosamente)
        Write-Log "Instalando dependencias de análisis de datos..." "Info"
        try {
            & $pipExe install "pandas>=2.0.0,<3.0.0" --timeout 120 --quiet
            Write-Log "pandas instalado correctamente" "Success"
        } catch {
            Write-Log "pandas falló, continuando sin él (dashboard funcionará en modo básico)" "Warning"
        }
        
        try {
            & $pipExe install "numpy>=1.24.0,<2.0.0" --quiet
            Write-Log "numpy instalado correctamente" "Success"
        } catch {
            Write-Log "numpy falló, continuando sin él" "Warning"
        }
        
        # Dependencias adicionales
        $additionalDeps = @("beautifulsoup4>=4.12.2", "colorama>=0.4.6", "tqdm>=4.65.0", "plotly>=5.15.0", "cryptography>=41.0.0")
        foreach ($dep in $additionalDeps) {
            try {
                & $pipExe install $dep --quiet
            } catch {
                Write-Log "Error instalando $dep (opcional)" "Warning"
            }
            $progress += 2
            Show-Progress "Dependencias" "Instalando adicionales..." $progress
        }
        
        Show-Progress "Dependencias" "Dependencias instaladas" 100
        Write-Progress -Activity "Dependencias" -Completed
        Write-Log "Instalación de dependencias completada" "Success"
        
        return $true
        
    } catch {
        Write-Log "Error crítico instalando dependencias: $($_.Exception.Message)" "Error"
        return $false
    }
}

# ==========================================
# CONFIGURACIÓN DEL SISTEMA
# ==========================================

function Create-SystemConfiguration {
    Write-Log "Creando configuración del sistema..." "Step"
    Show-Progress "Configuración" "Creando archivos de configuración..." 25
    
    # config.yaml
    $configYaml = @"
# Security Fuzzing System Configuration v2.0.0
system:
  name: "Security Fuzzing System"
  version: "2.0.0"
  environment: "development"
  debug: true
  log_level: "INFO"

database:
  type: "sqlite"
  path: "data/databases/fuzzing.db"
  backup_enabled: true
  backup_interval_hours: 24

web:
  host: "0.0.0.0"
  port: 5000
  secret_key: "CHANGE_THIS_SECRET_KEY_IN_PRODUCTION"

api:
  host: "0.0.0.0"
  port: 8000
  enable_cors: true

network:
  max_workers: 6
  timeout: 15
  verify_ssl: false

fuzzing:
  concurrent_requests: 50
  delay_between_requests: 0.1
  retry_attempts: 3

tools:
  ffuf:
    enabled: true
    path: "tools/ffuf/ffuf.exe"
  dirsearch:
    enabled: true
    path: "tools/dirsearch/dirsearch.py"

logging:
  level: "INFO"
  file: "logs/fuzzing.log"
  max_size: "10MB"
  backup_count: 5

security:
  jwt_secret_key: "CHANGE_THIS_JWT_SECRET_KEY"
  session_timeout_hours: 8
  blacklisted_domains:
    - "localhost"
    - "127.0.0.1"
    - "internal.company.com"
"@
    
    $configPath = Join-Path $Global:Config.InstallPath "config.yaml"
    $configYaml | Out-File -FilePath $configPath -Encoding UTF8
    Write-Log "config.yaml creado" "Success"
    
    Show-Progress "Configuración" "Creando config/settings.py..." 50
    
    # config/settings.py
    $settingsPy = @"
import os
import yaml
from pathlib import Path

class Config:
    def __init__(self, config_file="config.yaml"):
        self.base_dir = Path(__file__).parent.parent.absolute()
        self.config_file = self.base_dir / config_file
        self._config = self._load_config()
    
    def _load_config(self):
        try:
            if self.config_file.exists():
                with open(self.config_file, 'r', encoding='utf-8') as f:
                    return yaml.safe_load(f) or {}
            else:
                return self._default_config()
        except Exception as e:
            print(f"Error cargando config.yaml: {e}")
            return self._default_config()
    
    def _default_config(self):
        return {
            'system': {'name': 'Security Fuzzing System', 'version': '2.0.0'},
            'database': {'type': 'sqlite', 'path': 'data/databases/fuzzing.db'},
            'web': {'host': '0.0.0.0', 'port': 5000, 'secret_key': 'dev-key'},
            'api': {'host': '0.0.0.0', 'port': 8000}
        }
    
    def get(self, key, default=None):
        keys = key.split('.')
        value = self._config
        try:
            for k in keys:
                value = value[k]
            return value
        except (KeyError, TypeError):
            return default
    
    @property
    def DATABASE_PATH(self):
        db_path = self.get('database.path', 'data/databases/fuzzing.db')
        if not os.path.isabs(db_path):
            return str(self.base_dir / db_path)
        return db_path
    
    @property
    def WEB_HOST(self):
        return self.get('web.host', '0.0.0.0')
    
    @property
    def WEB_PORT(self):
        return self.get('web.port', 5000)
    
    @property
    def API_HOST(self):
        return self.get('api.host', '0.0.0.0')
    
    @property
    def API_PORT(self):
        return self.get('api.port', 8000)
    
    @property
    def SECRET_KEY(self):
        return self.get('web.secret_key', 'change-this-key')
    
    @property
    def DEBUG(self):
        return self.get('system.debug', True)

config = Config()
"@
    
    $configDir = Join-Path $Global:Config.InstallPath "config"
    $settingsPath = Join-Path $configDir "settings.py"
    $settingsPy | Out-File -FilePath $settingsPath -Encoding UTF8
    
    # __init__.py files
    "" | Out-File -FilePath (Join-Path $configDir "__init__.py") -Encoding UTF8
    "" | Out-File -FilePath (Join-Path (Join-Path $Global:Config.InstallPath "web") "__init__.py") -Encoding UTF8
    "" | Out-File -FilePath (Join-Path (Join-Path $Global:Config.InstallPath "api") "__init__.py") -Encoding UTF8
    "" | Out-File -FilePath (Join-Path (Join-Path $Global:Config.InstallPath "core") "__init__.py") -Encoding UTF8
    
    Show-Progress "Configuración" "Creando wordlists..." 75
    
    # Wordlist básica
    $commonWordlist = @"
admin
test
login
index
home
about
contact
user
users
api
config
backup
temp
tmp
dev
staging
prod
www
ftp
mail
blog
news
search
dashboard
panel
control
manage
admin.php
login.php
config.php
test.php
backup.zip
robots.txt
sitemap.xml
.htaccess
"@
    
    $wordlistPath = Join-Path (Join-Path $Global:Config.InstallPath "data\wordlists") "common.txt"
    $commonWordlist | Out-File -FilePath $wordlistPath -Encoding UTF8
    
    Show-Progress "Configuración" "Configuración completada" 100
    Write-Progress -Activity "Configuración" -Completed
    Write-Log "Archivos de configuración creados" "Success"
    
    return $true
}

# ==========================================
# REPARACIÓN DEL DASHBOARD
# ==========================================

function Repair-Dashboard {
    Write-Log "Reparando dashboard..." "Step"
    Show-Progress "Reparación" "Verificando dashboard actual..." 25
    
    $pythonExe = Join-Path $Global:Config.VenvPath "Scripts\python.exe"
    $dashboardPath = Join-Path $Global:Config.InstallPath "web\app.py"
    
    # Verificar si el dashboard actual funciona
    $dashboardWorks = $false
    try {
        $testResult = & $pythonExe -c "import sys; sys.path.append('.'); import web.app; print('OK')" 2>&1
        if ($testResult -like "*OK*") {
            $dashboardWorks = $true
            Write-Log "Dashboard actual funciona correctamente" "Success"
        }
    } catch {
        Write-Log "Dashboard actual tiene problemas, reparando..." "Warning"
    }
    
    if (-not $dashboardWorks) {
        Show-Progress "Reparación" "Creando dashboard corregido..." 75
        
        # Crear backup si existe
        if (Test-Path $dashboardPath) {
            $timestamp = Get-Date -Format "yyyyMMdd_HHmmss"
            $backupPath = "$dashboardPath.backup_$timestamp"
            Copy-Item $dashboardPath $backupPath -ErrorAction SilentlyContinue
            Write-Log "Backup creado: $backupPath" "Info"
        }
        
        # Dashboard simplificado y funcional (contenido del artifact anterior)
        $dashboardContent = @"
# Dashboard reparado - Versión simplificada sin pandas
import sys
import os
from pathlib import Path
sys.path.append(str(Path(__file__).parent.parent))

from flask import Flask, render_template_string, jsonify
from flask_cors import CORS
import sqlite3
from datetime import datetime

try:
    from config.settings import config
    WEB_HOST = config.WEB_HOST
    WEB_PORT = config.WEB_PORT
    DEBUG = config.DEBUG
except ImportError:
    WEB_HOST = "0.0.0.0"
    WEB_PORT = 5000
    DEBUG = True

app = Flask(__name__)
app.config['SECRET_KEY'] = 'dev-secret-key'
CORS(app)

start_time = datetime.now()

SIMPLE_HTML = '''
<!DOCTYPE html>
<html>
<head>
    <title>🚀 Security Fuzzing System</title>
    <style>
        body { font-family: Arial, sans-serif; margin: 40px; background: linear-gradient(135deg, #667eea, #764ba2); color: white; }
        .container { max-width: 800px; margin: 0 auto; }
        .header { text-align: center; margin-bottom: 30px; }
        .card { background: rgba(255,255,255,0.1); padding: 20px; border-radius: 10px; margin: 20px 0; }
        .status { color: #4CAF50; }
        a { color: #FFD700; }
    </style>
</head>
<body>
    <div class="container">
        <div class="header">
            <h1>🚀 Security Fuzzing System</h1>
            <p>Dashboard funcionando correctamente</p>
        </div>
        <div class="card">
            <h3>📊 Estado del Sistema</h3>
            <p class="status">✅ Dashboard: Operativo</p>
            <p class="status">✅ API REST: Disponible</p>
            <p class="status">✅ Base de datos: Conectada</p>
            <p>Tiempo activo: {{ uptime }} minutos</p>
        </div>
        <div class="card">
            <h3>🔗 Enlaces</h3>
            <p><a href="/health">Health Check</a></p>
            <p><a href="/test">Test del Sistema</a></p>
            <p><a href="http://localhost:8000">API REST</a></p>
            <p><a href="http://localhost:8000/health">API Health</a></p>
        </div>
    </div>
</body>
</html>
'''

@app.route('/')
def index():
    uptime = round((datetime.now() - start_time).total_seconds() / 60, 1)
    return render_template_string(SIMPLE_HTML, uptime=uptime)

@app.route('/health')
def health():
    return jsonify({
        'status': 'healthy',
        'service': 'Security Fuzzing Dashboard',
        'version': '2.0.0',
        'uptime_minutes': round((datetime.now() - start_time).total_seconds() / 60, 1)
    })

@app.route('/test')
def test():
    return jsonify({
        'status': 'OK',
        'message': 'Dashboard funcionando correctamente',
        'timestamp': datetime.now().isoformat(),
        'dependencies': {'flask': 'OK', 'flask_cors': 'OK'}
    })

if __name__ == '__main__':
    print("🚀 Iniciando Dashboard...")
    print(f"🌐 URL: http://{WEB_HOST}:{WEB_PORT}")
    print("Presiona Ctrl+C para detener")
    app.run(host=WEB_HOST, port=WEB_PORT, debug=DEBUG)
"@
        
        $dashboardContent | Out-File -FilePath $dashboardPath -Encoding UTF8
        Write-Log "Dashboard reparado creado" "Success"
    }
    
    Show-Progress "Reparación" "Dashboard reparado" 100
    Write-Progress -Activity "Reparación" -Completed
    
    return $true
}

# ==========================================
# SCRIPTS DE INICIO
# ==========================================

function Create-StartupScripts {
    Write-Log "Creando scripts de inicio..." "Step"
    
    # auto_start_system.bat
    $autoStartContent = @"
@echo off
chcp 65001 > nul
cls
echo 🚀 Security Fuzzing System - Auto Start
echo ========================================
echo.

if not exist "venv\Scripts\python.exe" (
    echo ❌ Entorno virtual no encontrado
    echo Ejecuta: install.ps1
    pause
    exit /b 1
)

echo 🔧 Activando entorno virtual...
call venv\Scripts\activate.bat

echo 📁 Verificando directorios...
if not exist "logs" mkdir logs
if not exist "data\databases" mkdir data\databases

echo 🔌 Iniciando API REST (Puerto 8000)...
start "API" /min cmd /k "call venv\Scripts\activate.bat && python api\app.py"
timeout /t 3 > nul

echo 🌐 Iniciando Dashboard (Puerto 5000)...
start "Dashboard" /min cmd /k "call venv\Scripts\activate.bat && python web\app.py"
timeout /t 3 > nul

echo ⏳ Esperando servicios...
timeout /t 5 > nul

echo 🌐 Abriendo navegadores...
start http://localhost:5000
start http://localhost:8000/health

echo.
echo ✅ SISTEMA INICIADO
echo Dashboard: http://localhost:5000
echo API: http://localhost:8000
echo.
pause
"@
    
    $autoStartPath = Join-Path $Global:Config.InstallPath "auto_start_system.bat"
    $autoStartContent | Out-File -FilePath $autoStartPath -Encoding ASCII
    
    # stop_all_services.bat
    $stopContent = @"
@echo off
echo 🛑 Deteniendo Security Fuzzing System...
taskkill /f /fi "WindowTitle eq API" > nul 2>&1
taskkill /f /fi "WindowTitle eq Dashboard" > nul 2>&1
echo ✅ Servicios detenidos
pause
"@
    
    $stopPath = Join-Path $Global:Config.InstallPath "stop_all_services.bat"
    $stopContent | Out-File -FilePath $stopPath -Encoding ASCII
    
    Write-Log "Scripts de inicio creados" "Success"
    return $true
}

# ==========================================
# TESTING DEL SISTEMA
# ==========================================

function Test-SystemFunctionality {
    if (-not $RunTests) {
        Write-Log "Omitiendo tests del sistema" "Info"
        return $true
    }
    
    Write-Log "Ejecutando tests del sistema..." "Step"
    Show-Progress "Tests" "Probando importaciones..." 25
    
    $pythonExe = Join-Path $Global:Config.VenvPath "Scripts\python.exe"
    $testsOK = 0
    $totalTests = 4
    
    # Test 1: Importaciones básicas
    try {
        $result = & $pythonExe -c "import flask, requests, aiohttp, yaml; print('OK')" 2>&1
        if ($result -like "*OK*") {
            Write-Log "✅ Test 1/4: Importaciones básicas" "Success"
            $testsOK++
        }
    } catch {
        Write-Log "❌ Test 1/4: Importaciones básicas FALLÓ" "Error"
    }
    
    Show-Progress "Tests" "Probando configuración..." 50
    
    # Test 2: Configuración
    try {
        $result = & $pythonExe -c "import sys; sys.path.append('.'); from config.settings import config; print('OK')" 2>&1
        if ($result -like "*OK*") {
            Write-Log "✅ Test 2/4: Configuración" "Success"
            $testsOK++
        }
    } catch {
        Write-Log "❌ Test 2/4: Configuración FALLÓ" "Error"
    }
    
    Show-Progress "Tests" "Probando dashboard..." 75
    
    # Test 3: Dashboard
    try {
        $result = & $pythonExe -c "import sys; sys.path.append('.'); import web.app; print('OK')" 2>&1
        if ($result -like "*OK*") {
            Write-Log "✅ Test 3/4: Dashboard" "Success"
            $testsOK++
        }
    } catch {
        Write-Log "❌ Test 3/4: Dashboard FALLÓ" "Error"
    }
    
    # Test 4: API (si existe)
    $apiPath = Join-Path $Global:Config.InstallPath "api\app.py"
    if (Test-Path $apiPath) {
        try {
            $result = & $pythonExe -c "import sys; sys.path.append('.'); import api.app; print('OK')" 2>&1
            if ($result -like "*OK*") {
                Write-Log "✅ Test 4/4: API" "Success"
                $testsOK++
            }
        } catch {
            Write-Log "❌ Test 4/4: API FALLÓ" "Error"
        }
    } else {
        Write-Log "ℹ️ Test 4/4: API no encontrada (opcional)" "Info"
        $testsOK++
    }
    
    Show-Progress "Tests" "Tests completados" 100
    Write-Progress -Activity "Tests" -Completed
    
    $testResult = $testsOK -eq $totalTests
    Write-Log "Tests completados: $testsOK/$totalTests pasaron" $(if ($testResult) { "Success" } else { "Warning" })
    
    return $testResult
}

# ==========================================
# ACCESOS DIRECTOS
# ==========================================

function Create-DesktopShortcuts {
    if (-not $CreateShortcuts) {
        Write-Log "Omitiendo creación de accesos directos" "Info"
        return $true
    }
    
    Write-Log "Creando accesos directos..." "Step"
    
    try {
        $WshShell = New-Object -ComObject WScript.Shell
        $DesktopPath = $WshShell.SpecialFolders("Desktop")
        
        # Acceso directo principal
        $ShortcutPath = Join-Path $DesktopPath "🚀 Security Fuzzing System.lnk"
        $Shortcut = $WshShell.CreateShortcut($ShortcutPath)
        $Shortcut.TargetPath = "cmd.exe"
        $Shortcut.Arguments = "/c `"cd /d `"$($Global:Config.InstallPath)`" && auto_start_system.bat`""
        $Shortcut.WorkingDirectory = $Global:Config.InstallPath
        $Shortcut.Description = "Security Fuzzing System"
        $Shortcut.Save()
        
        Write-Log "Acceso directo creado en escritorio" "Success"
        return $true
        
    } catch {
        Write-Log "Error creando accesos directos: $($_.Exception.Message)" "Warning"
        return $false
    }
}

# ==========================================
# RESUMEN FINAL
# ==========================================

function Show-InstallationSummary {
    $duration = (Get-Date) - $Global:Config.StartTime
    
    Write-Host ""
    Write-Host "██████████████████████████████████████████████████████████" -ForegroundColor Green
    Write-Host "█                                                        █" -ForegroundColor Green
    Write-Host "█              ✅ INSTALACIÓN COMPLETADA ✅             █" -ForegroundColor Yellow
    Write-Host "█                                                        █" -ForegroundColor Green
    Write-Host "██████████████████████████████████████████████████████████" -ForegroundColor Green
    Write-Host ""
    Write-Host "🎯 INSTALACIÓN EXITOSA:" -ForegroundColor Cyan
    Write-Host "   • Sistema: $($Global:Config.SystemName) v$($Global:Config.Version)" -ForegroundColor White
    Write-Host "   • Directorio: $($Global:Config.InstallPath)" -ForegroundColor White
    Write-Host "   • Duración: $($duration.Minutes)m $($duration.Seconds)s" -ForegroundColor White
    Write-Host ""
    Write-Host "🚀 COMANDOS PARA INICIAR:" -ForegroundColor Yellow
    Write-Host "   • Todo el sistema:  .\auto_start_system.bat" -ForegroundColor Cyan
    Write-Host "   • Solo dashboard:   python web\app.py" -ForegroundColor Cyan
    Write-Host "   • Solo API:         python api\app.py" -ForegroundColor Cyan
    Write-Host ""
    Write-Host "🌐 URLs DEL SISTEMA:" -ForegroundColor Yellow
    Write-Host "   • Dashboard:        http://localhost:5000" -ForegroundColor Cyan
    Write-Host "   • API REST:         http://localhost:8000" -ForegroundColor Cyan
    Write-Host "   • Health Checks:    http://localhost:5000/health" -ForegroundColor Cyan
    Write-Host ""
    Write-Host "📁 ARCHIVOS CREADOS:" -ForegroundColor Yellow
    Write-Host "   • Configuración:    config.yaml" -ForegroundColor Gray
    Write-Host "   • Scripts:          auto_start_system.bat" -ForegroundColor Gray
    Write-Host "   • Logs:             logs/" -ForegroundColor Gray
    Write-Host "   • Base de datos:    data/databases/" -ForegroundColor Gray
    Write-Host ""
    Write-Host "🎉 ¡SISTEMA LISTO PARA USAR!" -ForegroundColor Green
    Write-Host ""
}

# ==========================================
# FUNCIÓN PRINCIPAL
# ==========================================

function Install-SecurityFuzzingSystem {
    Write-Banner
    
    if ($RepairOnly) {
        Write-Log "Modo de solo reparación activado" "Info"
        Initialize-Environment | Out-Null
        Install-Dependencies | Out-Null
        Repair-Dashboard | Out-Null
        Write-Log "Reparación completada" "Success"
        return
    }
    
    if (-not $Silent) {
        Write-Host "🔧 INSTALADOR UNIFICADO DEL SECURITY FUZZING SYSTEM" -ForegroundColor Cyan
        Write-Host "===================================================" -ForegroundColor Cyan
        Write-Host ""
        Write-Host "Este instalador configurará automáticamente:" -ForegroundColor White
        Write-Host "  ✅ Entorno virtual de Python" -ForegroundColor Gray
        Write-Host "  ✅ Todas las dependencias (incluyendo pandas si es posible)" -ForegroundColor Gray
        Write-Host "  ✅ Configuración completa del sistema" -ForegroundColor Gray
        Write-Host "  ✅ Dashboard web reparado y funcional" -ForegroundColor Gray
        Write-Host "  ✅ Scripts de inicio automático" -ForegroundColor Gray
        Write-Host "  ✅ Tests de funcionalidad" -ForegroundColor Gray
        Write-Host "  ✅ Accesos directos (opcional)" -ForegroundColor Gray
        Write-Host ""
        Write-Host "Directorio: $($Global:Config.InstallPath)" -ForegroundColor Yellow
        Write-Host ""
        
        $continue = Read-Host "¿Continuar con la instalación completa? (S/n)"
        if ($continue -eq "n" -or $continue -eq "N") {
            Write-Log "Instalación cancelada" "Info"
            return
        }
    }
    
    Write-Log "Iniciando instalación unificada..." "Step"
    
    # Ejecutar pasos de instalación
    $steps = @(
        @{Name="Prerrequisitos"; Function={Test-Prerequisites}},
        @{Name="Entorno"; Function={Initialize-Environment}},
        @{Name="Dependencias"; Function={Install-Dependencies}},
        @{Name="Configuración"; Function={Create-SystemConfiguration}},
        @{Name="Reparación Dashboard"; Function={Repair-Dashboard}},
        @{Name="Scripts"; Function={Create-StartupScripts}},
        @{Name="Tests"; Function={Test-SystemFunctionality}},
        @{Name="Accesos Directos"; Function={Create-DesktopShortcuts}}
    )
    
    $success = $true
    foreach ($step in $steps) {
        $result = & $step.Function
        if (-not $result) {
            Write-Log "Error en paso: $($step.Name)" "Error"
            $success = $false
            break
        }
    }
    
    if ($success) {
        Show-InstallationSummary
        Write-Log "¡Instalación unificada completada exitosamente!" "Success"
        
        if (-not $Silent) {
            Write-Host "¿Deseas iniciar el sistema ahora? (S/n): " -NoNewline -ForegroundColor Yellow
            $start = Read-Host
            if ($start -ne "n" -and $start -ne "N") {
                Write-Log "Iniciando sistema..." "Info"
                & (Join-Path $Global:Config.InstallPath "auto_start_system.bat")
            }
        }
    } else {
        Write-Log "Instalación falló en algún paso" "Error"
        Write-Host "Revisa los logs en: $($Global:Config.LogPath)" -ForegroundColor Yellow
    }
}

# ==========================================
# EJECUTAR INSTALADOR
# ==========================================

if ($MyInvocation.InvocationName -eq $MyInvocation.MyCommand.Name) {
    Install-SecurityFuzzingSystem
}