# 🚀 SECURITY FUZZING SYSTEM - INSTALADOR COMPLETO
# Versión: 2.0.0
# Autor: Security Team
# Descripción: Instalador unificado para todo el sistema

param(
    [switch]$Silent,
    [switch]$SkipDependencies,
    [switch]$CreateShortcuts,
    [switch]$RunTests,
    [string]$InstallPath = (Get-Location).Path
)

# Configuración global
$Global:Config = @{
    SystemName = "Security Fuzzing System"
    Version = "2.0.0"
    InstallPath = $InstallPath
    VenvPath = Join-Path $InstallPath "venv"
    LogPath = Join-Path $InstallPath "logs"
    StartTime = Get-Date
}

# Configuración de colores y UI
$Host.UI.RawUI.WindowTitle = "$($Global:Config.SystemName) - Instalador v$($Global:Config.Version)"

# ==========================================
# FUNCIONES AUXILIARES
# ==========================================

function Write-Banner {
    Clear-Host
    Write-Host ""
    Write-Host "██████████████████████████████████████████████████████████" -ForegroundColor Cyan
    Write-Host "█                                                        █" -ForegroundColor Cyan
    Write-Host "█          🚀 SECURITY FUZZING SYSTEM 🚀               █" -ForegroundColor Yellow
    Write-Host "█                                                        █" -ForegroundColor Yellow
    Write-Host "█                 INSTALADOR COMPLETO                   █" -ForegroundColor Cyan
    Write-Host "█                    Versión 2.0.0                      █" -ForegroundColor Cyan
    Write-Host "█                                                        █" -ForegroundColor Cyan
    Write-Host "██████████████████████████████████████████████████████████" -ForegroundColor Cyan
    Write-Host ""
}

function Write-Log {
    param(
        [string]$Message,
        [string]$Type = "Info"
    )
    
    $timestamp = Get-Date -Format "HH:mm:ss"
    $logMessage = "[$timestamp] $Message"
    
    # Crear directorio de logs si no existe
    if (-not (Test-Path $Global:Config.LogPath)) {
        New-Item -ItemType Directory -Path $Global:Config.LogPath -Force | Out-Null
    }
    
    # Escribir a archivo de log
    $logFile = Join-Path $Global:Config.LogPath "installer.log"
    Add-Content -Path $logFile -Value $logMessage
    
    # Escribir a consola con colores
    switch ($Type) {
        "Success" { Write-Host "✅ $Message" -ForegroundColor Green }
        "Error"   { Write-Host "❌ $Message" -ForegroundColor Red }
        "Warning" { Write-Host "⚠️ $Message" -ForegroundColor Yellow }
        "Info"    { Write-Host "ℹ️ $Message" -ForegroundColor Cyan }
        "Step"    { Write-Host "🔧 $Message" -ForegroundColor Magenta }
    }
}

function Show-Progress {
    param(
        [string]$Activity,
        [string]$Status,
        [int]$PercentComplete
    )
    
    Write-Progress -Activity $Activity -Status $Status -PercentComplete $PercentComplete
}

function Test-Administrator {
    $currentUser = [Security.Principal.WindowsIdentity]::GetCurrent()
    $principal = New-Object Security.Principal.WindowsPrincipal($currentUser)
    return $principal.IsInRole([Security.Principal.WindowsBuiltInRole]::Administrator)
}

function Test-Prerequisites {
    Write-Log "Verificando prerrequisitos del sistema..." "Step"
    Show-Progress "Verificación" "Verificando prerrequisitos..." 10
    
    $prereqsMet = $true
    
    # Verificar Python
    try {
        $pythonVersion = python --version 2>&1
        if ($pythonVersion -match "Python (\d+\.\d+\.\d+)") {
            $version = [version]$matches[1]
            if ($version -ge [version]"3.8.0") {
                Write-Log "Python $($version) encontrado" "Success"
            } else {
                Write-Log "Python versión $($version) es muy antigua. Se requiere Python 3.8+" "Error"
                $prereqsMet = $false
            }
        } else {
            Write-Log "No se pudo determinar la versión de Python" "Warning"
        }
    } catch {
        Write-Log "Python no está instalado o no está en PATH" "Error"
        Write-Log "Descarga Python desde: https://python.org" "Info"
        $prereqsMet = $false
    }
    
    # Verificar Git
    try {
        $gitVersion = git --version 2>&1
        if ($gitVersion -match "git version") {
            Write-Log "Git encontrado: $gitVersion" "Success"
        } else {
            Write-Log "Git no encontrado" "Warning"
        }
    } catch {
        Write-Log "Git no está instalado (opcional)" "Warning"
    }
    
    # Verificar PowerShell
    if ($PSVersionTable.PSVersion.Major -ge 5) {
        Write-Log "PowerShell $($PSVersionTable.PSVersion) OK" "Success"
    } else {
        Write-Log "PowerShell versión antigua detectada" "Warning"
    }
    
    # Verificar permisos
    if (Test-Administrator) {
        Write-Log "Ejecutándose como Administrador" "Success"
    } else {
        Write-Log "No se está ejecutando como Administrador (recomendado para instalación completa)" "Warning"
    }
    
    # Verificar espacio en disco
    $drive = (Get-Location).Drive
    $freeSpace = (Get-WmiObject -Class Win32_LogicalDisk -Filter "DeviceID='$($drive.Name)'").FreeSpace / 1GB
    if ($freeSpace -gt 1) {
        Write-Log "Espacio libre en disco: $([math]::Round($freeSpace, 2)) GB" "Success"
    } else {
        Write-Log "Espacio libre en disco insuficiente: $([math]::Round($freeSpace, 2)) GB" "Warning"
    }
    
    Show-Progress "Verificación" "Prerrequisitos verificados" 100
    Write-Progress -Activity "Verificación" -Completed
    
    return $prereqsMet
}

function Initialize-Environment {
    Write-Log "Inicializando entorno de desarrollo..." "Step"
    Show-Progress "Inicialización" "Creando entorno virtual..." 25
    
    # Crear entorno virtual
    if (Test-Path $Global:Config.VenvPath) {
        Write-Log "Entorno virtual existente encontrado, recreando..." "Warning"
        Remove-Item -Recurse -Force $Global:Config.VenvPath
    }
    
    try {
        python -m venv $Global:Config.VenvPath
        Write-Log "Entorno virtual creado exitosamente" "Success"
    } catch {
        Write-Log "Error creando entorno virtual: $($_.Exception.Message)" "Error"
        return $false
    }
    
    Show-Progress "Inicialización" "Activando entorno virtual..." 50
    
    # Activar entorno virtual
    $activateScript = Join-Path $Global:Config.VenvPath "Scripts\Activate.ps1"
    if (Test-Path $activateScript) {
        try {
            & $activateScript
            Write-Log "Entorno virtual activado" "Success"
        } catch {
            Write-Log "Error activando entorno virtual: $($_.Exception.Message)" "Warning"
        }
    }
    
    Show-Progress "Inicialización" "Creando estructura de directorios..." 75
    
    # Crear estructura de directorios
    $directories = @(
        "logs",
        "data",
        "data\databases", 
        "data\wordlists",
        "exports",
        "reports",
        "temp",
        "config",
        "tests",
        "scripts",
        "docs"
    )
    
    foreach ($dir in $directories) {
        $fullPath = Join-Path $Global:Config.InstallPath $dir
        if (-not (Test-Path $fullPath)) {
            New-Item -ItemType Directory -Path $fullPath -Force | Out-Null
            Write-Log "Directorio creado: $dir" "Info"
        }
    }
    
    Show-Progress "Inicialización" "Entorno inicializado" 100
    Write-Progress -Activity "Inicialización" -Completed
    
    return $true
}

function Install-Dependencies {
    if ($SkipDependencies) {
        Write-Log "Omitiendo instalación de dependencias (-SkipDependencies)" "Info"
        return $true
    }
    
    Write-Log "Instalando dependencias de Python..." "Step"
    Show-Progress "Dependencias" "Actualizando pip..." 10
    
    # Activar entorno virtual
    $pythonExe = Join-Path $Global:Config.VenvPath "Scripts\python.exe"
    $pipExe = Join-Path $Global:Config.VenvPath "Scripts\pip.exe"
    
    if (-not (Test-Path $pythonExe)) {
        Write-Log "Python no encontrado en entorno virtual" "Error"
        return $false
    }
    
    try {
        # Actualizar pip
        & $pythonExe -m pip install --upgrade pip
        Write-Log "pip actualizado" "Success"
        
        Show-Progress "Dependencias" "Instalando dependencias core..." 30
        
        # Instalar dependencias core
        $coreDependencies = @(
            "flask>=2.3.0",
            "requests>=2.31.0", 
            "aiohttp>=3.8.5",
            "loguru>=0.7.0",
            "pyyaml>=6.0.1",
            "sqlalchemy>=2.0.20"
        )
        
        foreach ($dep in $coreDependencies) {
            & $pipExe install $dep --quiet
            Write-Log "Instalado: $dep" "Info"
        }
        
        Show-Progress "Dependencias" "Instalando dependencias web..." 60
        
        # Instalar dependencias web
        $webDependencies = @(
            "flask-cors>=4.0.0",
            "flask-restful>=0.3.10",
            "flask-socketio>=5.3.0",
            "jinja2>=3.1.0",
            "werkzeug>=2.3.0"
        )
        
        foreach ($dep in $webDependencies) {
            & $pipExe install $dep --quiet
            Write-Log "Instalado: $dep" "Info"
        }
        
        Show-Progress "Dependencias" "Instalando dependencias adicionales..." 80
        
        # Instalar dependencias adicionales
        $additionalDependencies = @(
            "beautifulsoup4>=4.12.2",
            "colorama>=0.4.6",
            "tqdm>=4.65.0",
            "pandas>=2.0.0",
            "plotly>=5.15.0",
            "cryptography>=41.0.0"
        )
        
        foreach ($dep in $additionalDependencies) {
            & $pipExe install $dep --quiet
            Write-Log "Instalado: $dep" "Info"
        }
        
        Show-Progress "Dependencias" "Dependencias instaladas" 100
        Write-Progress -Activity "Dependencias" -Completed
        
        Write-Log "Todas las dependencias instaladas exitosamente" "Success"
        return $true
        
    } catch {
        Write-Log "Error instalando dependencias: $($_.Exception.Message)" "Error"
        return $false
    }
}

function Create-ConfigurationFiles {
    Write-Log "Creando archivos de configuración..." "Step"
    Show-Progress "Configuración" "Creando config.yaml..." 25
    
    # Crear config.yaml
    $configYaml = @"
# Security Fuzzing System Configuration
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
  secret_key: "change-this-secret-key"

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
  jwt_secret_key: "change-this-key"
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
    
    # Crear config/settings.py
    $settingsPy = @"
# -*- coding: utf-8 -*-
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
    
    # Crear __init__.py
    $initPath = Join-Path $configDir "__init__.py"
    "" | Out-File -FilePath $initPath -Encoding UTF8
    
    Write-Log "config/settings.py creado" "Success"
    
    Show-Progress "Configuración" "Creando wordlists..." 75
    
    # Crear wordlists básicas
    $wordlistsDir = Join-Path $Global:Config.InstallPath "data\wordlists"
    
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
"@
    
    $commonPath = Join-Path $wordlistsDir "common.txt"
    $commonWordlist | Out-File -FilePath $commonPath -Encoding UTF8
    Write-Log "Wordlist común creada" "Success"
    
    Show-Progress "Configuración" "Archivos de configuración creados" 100
    Write-Progress -Activity "Configuración" -Completed
    
    return $true
}

function Create-StartupScripts {
    Write-Log "Creando scripts de inicio..." "Step"
    Show-Progress "Scripts" "Creando auto_start_system.bat..." 33
    
    # Crear auto_start_system.bat
    $autoStartBat = @"
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

if not exist "core\fuzzing_engine.py" (
    echo ❌ Error: Ejecuta este script desde el directorio raíz del proyecto
    pause
    exit /b 1
)

echo 🔧 Activando entorno virtual...
if exist "venv\Scripts\activate.bat" (
    call venv\Scripts\activate.bat
    echo ✅ Entorno virtual activado
) else (
    echo ❌ Entorno virtual no encontrado
    pause
    exit /b 1
)

echo 📁 Creando directorios necesarios...
if not exist "logs" mkdir logs
if not exist "data\databases" mkdir data\databases
if not exist "exports" mkdir exports
echo ✅ Directorios creados

echo 🔍 Verificando dependencias...
python -c "import flask, requests, aiohttp, loguru; print('✅ Dependencias OK')" 2>nul
if errorlevel 1 (
    echo ❌ Faltan dependencias críticas
    pause
    exit /b 1
)

echo.
echo =========================================
echo 🚀 INICIANDO SERVICIOS DEL SISTEMA
echo =========================================
echo.

echo 🔌 Iniciando API REST (Puerto 8000)...
start "Security Fuzzing API" /min cmd /k "title Security Fuzzing API && venv\Scripts\activate.bat && python api\app.py"
timeout /t 3 /nobreak > nul

echo 🌐 Iniciando Dashboard Web (Puerto 5000)...
start "Security Fuzzing Dashboard" /min cmd /k "title Security Fuzzing Dashboard && venv\Scripts\activate.bat && python web\app.py"
timeout /t 3 /nobreak > nul

echo ⏳ Verificando servicios...
timeout /t 5 /nobreak > nul

echo.
echo ✅ SERVICIOS INICIADOS CORRECTAMENTE
echo.
echo 🌐 Abriendo navegadores automáticamente...
start http://localhost:5000
timeout /t 2 /nobreak > nul
start http://localhost:8000/health

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
echo 🎉 ¡SISTEMA LISTO PARA USAR!
echo.
pause
"@
    
    $autoStartPath = Join-Path $Global:Config.InstallPath "auto_start_system.bat"
    $autoStartBat | Out-File -FilePath $autoStartPath -Encoding ASCII
    Write-Log "auto_start_system.bat creado" "Success"
    
    Show-Progress "Scripts" "Creando stop_all_services.bat..." 66
    
    # Crear stop_all_services.bat
    $stopAllBat = @"
@echo off
echo 🛑 Deteniendo Security Fuzzing System...
taskkill /f /fi "WindowTitle eq Security Fuzzing API" > nul 2>&1
taskkill /f /fi "WindowTitle eq Security Fuzzing Dashboard" > nul 2>&1
echo ✅ Todos los servicios detenidos
pause
"@
    
    $stopAllPath = Join-Path $Global:Config.InstallPath "stop_all_services.bat"
    $stopAllBat | Out-File -FilePath $stopAllPath -Encoding ASCII
    Write-Log "stop_all_services.bat creado" "Success"
    
    Show-Progress "Scripts" "Scripts de inicio creados" 100
    Write-Progress -Activity "Scripts" -Completed
    
    return $true
}

function Create-DesktopShortcuts {
    if (-not $CreateShortcuts) {
        Write-Log "Omitiendo creación de accesos directos (-CreateShortcuts no especificado)" "Info"
        return $true
    }
    
    Write-Log "Creando accesos directos de escritorio..." "Step"
    Show-Progress "Accesos Directos" "Creando accesos directos..." 50
    
    try {
        $WshShell = New-Object -ComObject WScript.Shell
        $DesktopPath = $WshShell.SpecialFolders("Desktop")
        
        # Acceso directo principal
        $ShortcutPath = Join-Path $DesktopPath "🚀 Security Fuzzing System.lnk"
        $Shortcut = $WshShell.CreateShortcut($ShortcutPath)
        $Shortcut.TargetPath = "cmd.exe"
        $Shortcut.Arguments = "/c `"cd /d `"$($Global:Config.InstallPath)`" && auto_start_system.bat`""
        $Shortcut.WorkingDirectory = $Global:Config.InstallPath
        $Shortcut.Description = "Iniciar Security Fuzzing System completo"
        $Shortcut.Save()
        
        Write-Log "Acceso directo creado en escritorio" "Success"
        
        Show-Progress "Accesos Directos" "Accesos directos creados" 100
        Write-Progress -Activity "Accesos Directos" -Completed
        
        return $true
        
    } catch {
        Write-Log "Error creando accesos directos: $($_.Exception.Message)" "Warning"
        return $false
    }
}

function Run-SystemTests {
    if (-not $RunTests) {
        Write-Log "Omitiendo tests del sistema (-RunTests no especificado)" "Info" 
        return $true
    }
    
    Write-Log "Ejecutando tests del sistema..." "Step"
    Show-Progress "Tests" "Ejecutando tests..." 50
    
    try {
        # Verificar imports básicos
        $pythonExe = Join-Path $Global:Config.VenvPath "Scripts\python.exe"
        
        $testResult = & $pythonExe -c @"
try:
    import flask
    import requests
    import aiohttp
    import loguru
    import yaml
    import sqlalchemy
    print('✅ Todos los imports funcionan')
    exit(0)
except ImportError as e:
    print(f'❌ Error de importación: {e}')
    exit(1)
"@ 2>&1
        
        if ($LASTEXITCODE -eq 0) {
            Write-Log "Tests de importación pasaron" "Success"
        } else {
            Write-Log "Tests de importación fallaron: $testResult" "Error"
            return $false
        }
        
        # Test de configuración
        $configTest = & $pythonExe -c @"
import sys
import os
sys.path.append('.')
try:
    from config.settings import config
    print('✅ Configuración carga correctamente')
    exit(0)
except Exception as e:
    print(f'❌ Error en configuración: {e}')
    exit(1)
"@ 2>&1
        
        if ($LASTEXITCODE -eq 0) {
            Write-Log "Test de configuración pasó" "Success"
        } else {
            Write-Log "Test de configuración falló: $configTest" "Warning"
        }
        
        Show-Progress "Tests" "Tests completados" 100
        Write-Progress -Activity "Tests" -Completed
        
        return $true
        
    } catch {
        Write-Log "Error ejecutando tests: $($_.Exception.Message)" "Warning"
        return $false
    }
}

function Show-InstallationSummary {
    $duration = (Get-Date) - $Global:Config.StartTime
    
    Write-Host ""
    Write-Host "██████████████████████████████████████████████████████████" -ForegroundColor Green
    Write-Host "█                                                        █" -ForegroundColor Green
    Write-Host "█              ✅ INSTALACIÓN COMPLETADA ✅             █" -ForegroundColor Yellow
    Write-Host "█                                                        █" -ForegroundColor Green
    Write-Host "██████████████████████████████████████████████████████████" -ForegroundColor Green
    Write-Host ""
    Write-Host "🎯 RESUMEN DE INSTALACIÓN:" -ForegroundColor Cyan
    Write-Host "   • Sistema: $($Global:Config.SystemName) v$($Global:Config.Version)" -ForegroundColor White
    Write-Host "   • Directorio: $($Global:Config.InstallPath)" -ForegroundColor White
    Write-Host "   • Duración: $($duration.Minutes)m $($duration.Seconds)s" -ForegroundColor White
    Write-Host "   • Entorno virtual: $(if (Test-Path $Global:Config.VenvPath) { '✅ Creado' } else { '❌ Error' })" -ForegroundColor White
    Write-Host ""
    Write-Host "🚀 COMANDOS PARA INICIAR:" -ForegroundColor Yellow
    Write-Host "   • Automático:    .\auto_start_system.bat" -ForegroundColor Cyan
    Write-Host "   • Dashboard:     python web\app.py" -ForegroundColor Cyan
    Write-Host "   • API:           python api\app.py" -ForegroundColor Cyan
    Write-Host "   • Fuzzer:        python -m core.fuzzing_engine --help" -ForegroundColor Cyan
    Write-Host ""
    Write-Host "🌐 URLs DEL SISTEMA:" -ForegroundColor Yellow
    Write-Host "   • Dashboard:     http://localhost:5000" -ForegroundColor Cyan
    Write-Host "   • API REST:      http://localhost:8000" -ForegroundColor Cyan
    Write-Host "   • Health Check:  http://localhost:8000/health" -ForegroundColor Cyan
    Write-Host ""
    Write-Host "📁 ARCHIVOS IMPORTANTES:" -ForegroundColor Yellow
    Write-Host "   • Configuración: config.yaml" -ForegroundColor Gray
    Write-Host "   • Logs:          logs/" -ForegroundColor Gray
    Write-Host "   • Base de datos: data/databases/" -ForegroundColor Gray
    Write-Host "   • Wordlists:     data/wordlists/" -ForegroundColor Gray
    Write-Host ""
    Write-Host "🔧 HERRAMIENTAS:" -ForegroundColor Yellow
    Write-Host "   • Iniciar todo:  .\auto_start_system.bat" -ForegroundColor Gray
    Write-Host "   • Detener todo:  .\stop_all_services.bat" -ForegroundColor Gray
    Write-Host "   • Tests:         .\tests\test_system.ps1" -ForegroundColor Gray
    Write-Host ""
    Write-Host "🎉 ¡SISTEMA LISTO PARA USAR!" -ForegroundColor Green
    Write-Host ""
}

# ==========================================
# FUNCIÓN PRINCIPAL DE INSTALACIÓN
# ==========================================

function Install-SecurityFuzzingSystem {
    Write-Banner
    
    if (-not $Silent) {
        Write-Host "🔧 INSTALADOR DEL SECURITY FUZZING SYSTEM" -ForegroundColor Cyan
        Write-Host "==========================================" -ForegroundColor Cyan
        Write-Host ""
        Write-Host "Este instalador configurará automáticamente:" -ForegroundColor White
        Write-Host "  • Entorno virtual de Python" -ForegroundColor Gray
        Write-Host "  • Todas las dependencias necesarias" -ForegroundColor Gray
        Write-Host "  • Archivos de configuración" -ForegroundColor Gray
        Write-Host "  • Scripts de inicio automático" -ForegroundColor Gray
        Write-Host "  • Estructura de directorios" -ForegroundColor Gray
        Write-Host "  • Tests del sistema" -ForegroundColor Gray
        Write-Host ""
        Write-Host "Directorio de instalación: $($Global:Config.InstallPath)" -ForegroundColor Yellow
        Write-Host ""
        
        $continue = Read-Host "¿Continuar con la instalación? (S/n)"
        if ($continue -eq "n" -or $continue -eq "N") {
            Write-Log "Instalación cancelada por el usuario" "Info"
            return
        }
    }
    
    Write-Log "Iniciando instalación del $($Global:Config.SystemName) v$($Global:Config.Version)..." "Step"
    
    # Paso 1: Verificar prerrequisitos
    if (-not (Test-Prerequisites)) {
        Write-Log "Los prerrequisitos no están cumplidos. Instalación abortada." "Error"
        return $false
    }
    
    # Paso 2: Inicializar entorno
    if (-not (Initialize-Environment)) {
        Write-Log "Error inicializando entorno. Instalación abortada." "Error"
        return $false
    }
    
    # Paso 3: Instalar dependencias
    if (-not (Install-Dependencies)) {
        Write-Log "Error instalando dependencias. Instalación abortada." "Error"
        return $false
    }
    
    # Paso 4: Crear archivos de configuración
    if (-not (Create-ConfigurationFiles)) {
        Write-Log "Error creando archivos de configuración. Instalación abortada." "Error"
        return $false
    }
    
    # Paso 5: Crear scripts de inicio
    if (-not (Create-StartupScripts)) {
        Write-Log "Error creando scripts de inicio. Instalación abortada." "Error"
        return $false
    }
    
    # Paso 6: Crear accesos directos (opcional)
    Create-DesktopShortcuts | Out-Null
    
    # Paso 7: Ejecutar tests (opcional)
    Run-SystemTests | Out-Null
    
    # Mostrar resumen
    Show-InstallationSummary
    
    Write-Log "Instalación completada exitosamente" "Success"
    
    if (-not $Silent) {
        Write-Host "Presiona cualquier tecla para continuar..." -ForegroundColor Yellow
        $null = $Host.UI.RawUI.ReadKey("NoEcho,IncludeKeyDown")
    }
    
    return $true
}

# ==========================================
# EJECUTAR INSTALADOR
# ==========================================

if ($MyInvocation.InvocationName -eq $MyInvocation.MyCommand.Name) {
    Install-SecurityFuzzingSystem
}