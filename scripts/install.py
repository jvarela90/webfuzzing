#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Script de Instalación del Sistema de Fuzzing
Instalación automatizada y configuración del entorno
"""

import os
import sys
import subprocess
import platform
import shutil
import urllib.request
import zipfile
import tarfile
from pathlib import Path
import json
import yaml


class SecurityFuzzingInstaller:
    """Instalador automático del sistema"""
    
    def __init__(self):
        self.platform = platform.system().lower()
        self.base_dir = Path.cwd()
        self.python_executable = sys.executable
        
        print(f"🚀 Security Fuzzing System Installer")
        print(f"📋 Platform: {platform.system()} {platform.release()}")
        print(f"🐍 Python: {platform.python_version()}")
        print(f"📁 Install Directory: {self.base_dir}")
        print("=" * 60)
    
    def run_installation(self):
        """Ejecutar instalación completa"""
        
        try:
            self.check_prerequisites()
            self.create_directory_structure()
            self.install_python_dependencies()
            self.download_external_tools()
            self.create_configuration_files()
            self.initialize_database()
            self.create_sample_data()
            self.setup_permissions()
            self.create_startup_scripts()
            
            print("\n🎉 ¡INSTALACIÓN COMPLETADA EXITOSAMENTE!")
            self.show_next_steps()
            
        except Exception as e:
            print(f"\n❌ Error durante la instalación: {e}")
            print("💡 Intenta ejecutar la instalación manual o reporta el problema")
            sys.exit(1)
    
    def check_prerequisites(self):
        """Verificar prerrequisitos del sistema"""
        
        print("🔍 Verificando prerrequisitos...")
        
        # Verificar Python version
        if sys.version_info < (3, 8):
            raise Exception("Python 3.8 o superior requerido")
        
        # Verificar pip
        try:
            subprocess.run([self.python_executable, "-m", "pip", "--version"], 
                         check=True, capture_output=True)
        except subprocess.CalledProcessError:
            raise Exception("pip no encontrado")
        
        # Verificar git (opcional pero recomendado)
        try:
            subprocess.run(["git", "--version"], check=True, capture_output=True)
            print("✅ Git disponible")
        except (subprocess.CalledProcessError, FileNotFoundError):
            print("⚠️  Git no encontrado (opcional)")
        
        # Verificar curl/wget para descargas
        has_curl = shutil.which("curl") is not None
        has_wget = shutil.which("wget") is not None
        
        if not (has_curl or has_wget):
            print("⚠️  curl/wget no encontrados (usando urllib como fallback)")
        
        print("✅ Prerrequisitos verificados")
    
    def create_directory_structure(self):
        """Crear estructura de directorios"""
        
        print("📁 Creando estructura de directorios...")
        
        directories = [
            "core", "modules", "api", "api/routes", "web", "web/static", 
            "web/static/css", "web/static/js", "web/static/img",
            "web/templates", "web/templates/components", "automation",
            "data", "data/config", "data/databases", "data/wordlists", "data/cache",
            "tools", "tools/ffuf", "tools/dirsearch", "tools/nuclei",
            "logs", "reports", "reports/html", "reports/json", "reports/pdf",
            "tests", "tests/unit", "tests/integration", "docs", "scripts"
        ]
        
        for directory in directories:
            dir_path = self.base_dir / directory
            dir_path.mkdir(parents=True, exist_ok=True)
            
            # Crear __init__.py para paquetes Python
            if any(pkg in str(dir_path) for pkg in ['core', 'modules', 'api', 'web', 'automation']):
                init_file = dir_path / "__init__.py"
                if not init_file.exists():
                    init_file.write_text("# -*- coding: utf-8 -*-\n")
        
        print("✅ Estructura de directorios creada")
    
    def install_python_dependencies(self):
        """Instalar dependencias de Python"""
        
        print("📦 Instalando dependencias de Python...")
        
        # Crear requirements.txt si no existe
        requirements_file = self.base_dir / "requirements.txt"
        if not requirements_file.exists():
            self.create_requirements_file()
        
        # Instalar dependencias
        try:
            subprocess.run([
                self.python_executable, "-m", "pip", "install", "-r", 
                str(requirements_file), "--upgrade"
            ], check=True)
            
            print("✅ Dependencias de Python instaladas")
            
        except subprocess.CalledProcessError as e:
            print(f"⚠️  Algunas dependencias fallaron: {e}")
            print("💡 Puedes instalar manualmente: pip install -r requirements.txt")
    
    def create_requirements_file(self):
        """Crear archivo requirements.txt"""
        
        requirements = [
            "# Core dependencies",
            "flask>=2.3.0",
            "requests>=2.31.0",
            "pyyaml>=6.0",
            "click>=8.0.0",
            "",
            "# Web interface", 
            "jinja2>=3.1.0",
            "werkzeug>=2.3.0",
            "",
            "# API",
            "flask-restful>=0.3.10",
            "flask-jwt-extended>=4.5.0",
            "flask-cors>=4.0.0",
            "flask-limiter>=3.0.0",
            "marshmallow>=3.19.0",
            "",
            "# ML and analytics",
            "scikit-learn>=1.3.0",
            "pandas>=2.0.0",
            "numpy>=1.24.0",
            "plotly>=5.15.0",
            "",
            "# Security and crypto",
            "cryptography>=41.0.0",
            "bcrypt>=4.0.0",
            "",
            "# Automation",
            "schedule>=1.2.0",
            "",
            "# Optional dependencies",
            "python-telegram-bot>=20.0.0",
            "pytest>=7.4.0",
            "black>=23.0.0"
        ]
        
        requirements_file = self.base_dir / "requirements.txt"
        requirements_file.write_text("\n".join(requirements))
    
    def download_external_tools(self):
        """Descargar herramientas externas"""
        
        print("🔧 Descargando herramientas externas...")
        
        tools_config = {
            "ffuf": {
                "windows": "https://github.com/ffuf/ffuf/releases/latest/download/ffuf_2.1.0_windows_amd64.zip",
                "linux": "https://github.com/ffuf/ffuf/releases/latest/download/ffuf_2.1.0_linux_amd64.tar.gz",
                "darwin": "https://github.com/ffuf/ffuf/releases/latest/download/ffuf_2.1.0_darwin_amd64.tar.gz"
            },
            "dirsearch": {
                "git": "https://github.com/maurosoria/dirsearch.git"
            }
        }
        
        # Descargar ffuf
        self.download_ffuf(tools_config["ffuf"])
        
        # Descargar dirsearch
        self.download_dirsearch(tools_config["dirsearch"])
        
        print("✅ Herramientas externas descargadas")
    
    def download_ffuf(self, urls):
        """Descargar ffuf según la plataforma"""
        
        if self.platform not in urls:
            print(f"⚠️  ffuf no disponible para {self.platform}")
            return
        
        url = urls[self.platform]
        ffuf_dir = self.base_dir / "tools" / "ffuf"
        
        try:
            print(f"📥 Descargando ffuf desde {url}")
            
            # Descargar archivo
            filename = url.split("/")[-1]
            file_path = ffuf_dir / filename
            
            urllib.request.urlretrieve(url, file_path)
            
            # Extraer archivo
            if filename.endswith(".zip"):
                with zipfile.ZipFile(file_path, 'r') as zip_ref:
                    zip_ref.extractall(ffuf_dir)
            elif filename.endswith(".tar.gz"):
                with tarfile.open(file_path, 'r:gz') as tar_ref:
                    tar_ref.extractall(ffuf_dir)
            
            # Hacer ejecutable en Unix
            if self.platform != "windows":
                ffuf_binary = ffuf_dir / "ffuf"
                if ffuf_binary.exists():
                    ffuf_binary.chmod(0o755)
            
            # Limpiar archivo descargado
            file_path.unlink()
            
            print("✅ ffuf descargado y configurado")
            
        except Exception as e:
            print(f"⚠️  Error descargando ffuf: {e}")
    
    def download_dirsearch(self, config):
        """Descargar dirsearch"""
        
        dirsearch_dir = self.base_dir / "tools" / "dirsearch"
        
        try:
            if shutil.which("git"):
                print("📥 Clonando dirsearch desde GitHub")
                subprocess.run([
                    "git", "clone", config["git"], str(dirsearch_dir)
                ], check=True, capture_output=True)
            else:
                print("⚠️  Git no disponible, descargando dirsearch manualmente")
                self.download_dirsearch_manual(dirsearch_dir)
            
            print("✅ dirsearch descargado")
            
        except Exception as e:
            print(f"⚠️  Error descargando dirsearch: {e}")
    
    def download_dirsearch_manual(self, target_dir):
        """Descargar dirsearch manualmente"""
        
        url = "https://github.com/maurosoria/dirsearch/archive/master.zip"
        zip_path = target_dir.parent / "dirsearch.zip"
        
        urllib.request.urlretrieve(url, zip_path)
        
        with zipfile.ZipFile(zip_path, 'r') as zip_ref:
            zip_ref.extractall(target_dir.parent)
        
        # Renombrar directorio
        extracted_dir = target_dir.parent / "dirsearch-master"
        if extracted_dir.exists():
            extracted_dir.rename(target_dir)
        
        zip_path.unlink()
    
    def create_configuration_files(self):
        """Crear archivos de configuración"""
        
        print("⚙️  Creando archivos de configuración...")
        
        # Crear config.yaml principal
        self.create_main_config()
        
        # Crear wordlists básicas
        self.create_base_wordlists()
        
        # Crear archivos .env de ejemplo
        self.create_env_files()
        
        print("✅ Archivos de configuración creados")
    
    def create_main_config(self):
        """Crear configuración principal"""
        
        config = {
            'system': {
                'name': 'Security Fuzzing System',
                'version': '2.0.0',
                'environment': 'production'
            },
            'database': {
                'path': 'data/databases/fuzzing.db',
                'backup_enabled': True,
                'backup_interval_hours': 24
            },
            'network': {
                'timeout': 15,
                'max_workers': 6 if self.platform == "windows" else 12,
                'verify_ssl': False
            },
            'security': {
                'jwt_secret_key': 'CHANGE_THIS_SECRET_KEY_IN_PRODUCTION',
                'session_timeout_hours': 8,
                'require_2fa_admin': True
            },
            'notifications': {
                'telegram': {
                    'enabled': False,
                    'bot_token': 'YOUR_BOT_TOKEN_HERE',
                    'chat_ids': ['YOUR_CHAT_ID_HERE']
                },
                'email': {
                    'enabled': False,
                    'smtp_server': 'smtp.gmail.com',
                    'smtp_port': 587,
                    'recipients': ['security@company.com']
                }
            },
            'tools': {
                'ffuf': {
                    'enabled': True,
                    'path': f"tools/ffuf/ffuf{'.exe' if self.platform == 'windows' else ''}"
                },
                'dirsearch': {
                    'enabled': True,
                    'path': 'tools/dirsearch/dirsearch.py'
                }
            }
        }
        
        config_file = self.base_dir / "config.yaml"
        with open(config_file, 'w', encoding='utf-8') as f:
            yaml.dump(config, f, default_flow_style=False, indent=2)
    
    def create_base_wordlists(self):
        """Crear wordlists básicas"""
        
        wordlists_dir = self.base_dir / "data" / "wordlists"
        
        # Wordlist base
        base_words = [
            "admin", "test", "api", "login", "panel", "config.php",
            "backup", "old", "dev", "staging", "private", "secret",
            "robots.txt", "sitemap.xml", "favicon.ico", "index.php",
            "wp-admin", "phpmyadmin", ".git", "config", "env", "logs",
            "database", "db", "mysql", "status", "health", "info"
        ]
        
        base_wordlist = wordlists_dir / "base.txt"
        base_wordlist.write_text("\n".join(base_words))
        
        # Crear archivo vacío para palabras descubiertas
        discovered_wordlist = wordlists_dir / "discovered.txt"
        discovered_wordlist.touch()
        
        print("✅ Wordlists básicas creadas")
    
    def create_env_files(self):
        """Crear archivos de entorno"""
        
        env_content = """# Security Fuzzing System Environment Variables
# Copy this file to .env and modify the values

# Database
DATABASE_PATH=data/databases/fuzzing.db

# Security
JWT_SECRET_KEY=your-secret-key-here
ENCRYPTION_KEY=your-encryption-key-here

# Telegram Bot (optional)
TELEGRAM_BOT_TOKEN=your-bot-token-here
TELEGRAM_CHAT_ID=your-chat-id-here

# Email Configuration (optional)
EMAIL_SMTP_SERVER=smtp.gmail.com
EMAIL_SMTP_PORT=587
EMAIL_USERNAME=your-email@gmail.com
EMAIL_PASSWORD=your-app-password
EMAIL_FROM=security@yourcompany.com

# API Configuration
API_HOST=0.0.0.0
API_PORT=8000

# Web Interface
WEB_HOST=0.0.0.0
WEB_PORT=5000

# Development
DEBUG=False
FLASK_ENV=production
"""
        
        env_example = self.base_dir / ".env.example"
        env_example.write_text(env_content)
    
    def initialize_database(self):
        """Inicializar base de datos"""
        
        print("💾 Inicializando base de datos...")
        
        try:
            # Importar y inicializar el gestor de BD
            sys.path.insert(0, str(self.base_dir))
            
            from core.database import DatabaseManager
            
            db_manager = DatabaseManager()
            db_manager.init_database()
            
            print("✅ Base de datos inicializada")
            
        except Exception as e:
            print(f"⚠️  Error inicializando base de datos: {e}")
            print("💡 Puedes inicializar manualmente después")
    
    def create_sample_data(self):
        """Crear datos de ejemplo"""
        
        print("📊 Creando datos de ejemplo...")
        
        # Crear archivo de dominios de ejemplo
        domains_file = self.base_dir / "data" / "config" / "sample_domains.txt"
        domains_content = """# Dominios de ejemplo para testing
# Formato: https://dominio o dominio:puerto

# Dominios seguros para pruebas
https://httpbin.org
https://jsonplaceholder.typicode.com
https://httpstat.us

# Ejemplos para uso real (descomentary y modificar):
# https://tu-empresa.com
# https://app.tu-empresa.com
# https://api.tu-empresa.com
"""
        
        domains_file.write_text(domains_content)
        print("✅ Datos de ejemplo creados")
    
    def setup_permissions(self):
        """Configurar permisos de archivos"""
        
        if self.platform == "windows":
            return  # Windows maneja permisos diferente
        
        print("🔒 Configurando permisos...")
        
        # Hacer ejecutables los scripts
        scripts_dir = self.base_dir / "scripts"
        for script in scripts_dir.glob("*.py"):
            script.chmod(0o755)
        
        # Proteger archivos de configuración
        config_dir = self.base_dir / "data" / "config"
        for config_file in config_dir.glob("*"):
            config_file.chmod(0o640)
        
        print("✅ Permisos configurados")
    
    def create_startup_scripts(self):
        """Crear scripts de inicio"""
        
        print("📜 Creando scripts de inicio...")
        
        # Script de inicio principal
        if self.platform == "windows":
            self.create_windows_scripts()
        else:
            self.create_unix_scripts()
        
        print("✅ Scripts de inicio creados")
    
    def create_windows_scripts(self):
        """Crear scripts para Windows"""
        
        # Script principal
        start_script = self.base_dir / "start_system.bat"
        start_content = f"""@echo off
echo Starting Security Fuzzing System...
echo.

REM Activar entorno virtual si existe
if exist venv\\Scripts\\activate.bat (
    call venv\\Scripts\\activate.bat
)

REM Iniciar sistema
{self.python_executable} -m core.fuzzing_engine

pause
"""
        start_script.write_text(start_content)
        
        # Script de dashboard
        dashboard_script = self.base_dir / "start_dashboard.bat"
        dashboard_content = f"""@echo off
echo Starting Web Dashboard...
echo Dashboard will be available at: http://localhost:5000
echo.

if exist venv\\Scripts\\activate.bat (
    call venv\\Scripts\\activate.bat
)

{self.python_executable} -m web.app

pause
"""
        dashboard_script.write_text(dashboard_content)
    
    def create_unix_scripts(self):
        """Crear scripts para Unix/Linux/macOS"""
        
        # Script principal
        start_script = self.base_dir / "start_system.sh"
        start_content = f"""#!/bin/bash
echo "Starting Security Fuzzing System..."
echo

# Activar entorno virtual si existe
if [ -f "venv/bin/activate" ]; then
    source venv/bin/activate
fi

# Iniciar sistema
{self.python_executable} -m core.fuzzing_engine

echo "System stopped."
"""
        start_script.write_text(start_content)
        start_script.chmod(0o755)
        
        # Script de dashboard
        dashboard_script = self.base_dir / "start_dashboard.sh"
        dashboard_content = f"""#!/bin/bash
echo "Starting Web Dashboard..."
echo "Dashboard will be available at: http://localhost:5000"
echo

if [ -f "venv/bin/activate" ]; then
    source venv/bin/activate
fi

{self.python_executable} -m web.app

echo "Dashboard stopped."
"""
        dashboard_script.write_text(dashboard_content)
        dashboard_script.chmod(0o755)
    
    def show_next_steps(self):
        """Mostrar próximos pasos al usuario"""
        
        print("\n" + "="*60)
        print("🎯 PRÓXIMOS PASOS:")
        print("="*60)
        
        print("\n1. 📝 CONFIGURACIÓN:")
        print("   • Edita config.yaml con tus configuraciones")
        print("   • Configura notificaciones en config.yaml")
        print("   • Revisa data/config/sample_domains.txt")
        
        print("\n2. 🚀 EJECUTAR SISTEMA:")
        if self.platform == "windows":
            print("   • start_system.bat - Ejecutar escaneo")
            print("   • start_dashboard.bat - Iniciar dashboard web")
        else:
            print("   • ./start_system.sh - Ejecutar escaneo")
            print("   • ./start_dashboard.sh - Iniciar dashboard web")
        
        print("\n3. 🌐 ACCESO WEB:")
        print("   • Dashboard: http://localhost:5000")
        print("   • API: http://localhost:8000")
        
        print("\n4. 📚 DOCUMENTACIÓN:")
        print("   • README.md - Guía completa")
        print("   • docs/ - Documentación detallada")
        
        print("\n5. 🔧 COMANDOS ÚTILES:")
        print("   • python -m core.fuzzing_engine --help")
        print("   • python -m web.app --help")
        print("   • python scripts/setup_environment.py")
        
        print("\n" + "="*60)
        print("✨ ¡El sistema está listo para usar!")
        print("="*60)


def main():
    """Función principal del instalador"""
    
    if len(sys.argv) > 1 and sys.argv[1] in ['-h', '--help']:
        print("Security Fuzzing System Installer")
        print("\nUsage: python scripts/install.py")
        print("\nThis script will:")
        print("  • Create directory structure")
        print("  • Install Python dependencies") 
        print("  • Download external tools (ffuf, dirsearch)")
        print("  • Create configuration files")
        print("  • Initialize database")
        print("  • Setup startup scripts")
        return
    
    installer = SecurityFuzzingInstaller()
    installer.run_installation()


if __name__ == "__main__":
    main()