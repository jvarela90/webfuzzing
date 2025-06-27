# scripts/install.py
import os
import sys
import subprocess
import platform
from pathlib import Path
import shutil

def check_python_version():
    """Verificar versión de Python"""
    if sys.version_info < (3, 8):
        print("❌ Error: Se requiere Python 3.8 o superior")
        print(f"Versión actual: {sys.version}")
        sys.exit(1)
    else:
        print(f"✅ Python {sys.version.split()[0]} detectado")

def install_requirements():
    """Instalar dependencias de Python"""
    print("\n📦 Instalando dependencias de Python...")
    
    requirements_file = Path(__file__).parent.parent / "requirements.txt"
    
    try:
        subprocess.check_call([
            sys.executable, "-m", "pip", "install", "-r", str(requirements_file)
        ])
        print("✅ Dependencias de Python instaladas correctamente")
    except subprocess.CalledProcessError as e:
        print(f"❌ Error instalando dependencias: {e}")
        sys.exit(1)

def install_external_tools():
    """Instalar herramientas externas"""
    print("\n🔧 Configurando herramientas externas...")
    
    system = platform.system().lower()
    
    # ffuf
    print("Instalando ffuf...")
    if system == "windows":
        print("  Para Windows: Descargar ffuf desde https://github.com/ffuf/ffuf/releases")
        print("  Agregar ffuf.exe al PATH del sistema")
    elif system == "linux":
        try:
            # Intentar instalar con apt
            subprocess.run(["sudo", "apt", "update"], check=False)
            result = subprocess.run(["sudo", "apt", "install", "-y", "ffuf"], check=False)
            if result.returncode != 0:
                print("  Instalación manual requerida: https://github.com/ffuf/ffuf/releases")
            else:
                print("  ✅ ffuf instalado via apt")
        except FileNotFoundError:
            print("  Instalación manual requerida: https://github.com/ffuf/ffuf/releases")
    
    # dirsearch
    print("Instalando dirsearch...")
    try:
        subprocess.check_call([
            sys.executable, "-m", "pip", "install", "dirsearch"
        ])
        print("  ✅ dirsearch instalado via pip")
    except subprocess.CalledProcessError:
        print("  ❌ Error instalando dirsearch")

def create_directories():
    """Crear directorios necesarios"""
    print("\n📁 Creando estructura de directorios...")
    
    base_dir = Path(__file__).parent.parent
    directories = [
        "data",
        "data/diccionarios",
        "data/resultados",
        "logs",
        "backups",
        "web/static",
        "web/templates"
    ]
    
    for directory in directories:
        dir_path = base_dir / directory
        dir_path.mkdir(parents=True, exist_ok=True)
        print(f"  ✅ {directory}")

def create_sample_files():
    """Crear archivos de ejemplo"""
    print("\n📄 Creando archivos de ejemplo...")
    
    base_dir = Path(__file__).parent.parent
    
    # Archivo de dominios de ejemplo
    domains_file = base_dir / "data" / "dominios.csv"
    if not domains_file.exists():
        with open(domains_file, 'w', encoding='utf-8') as f:
            f.write("# Archivo de dominios para fuzzing\n")
            f.write("# Formato: dominio[:puerto]\n")
            f.write("# Ejemplos:\n")
            f.write("# example.com\n")
            f.write("# test.example.com:8080\n")
            f.write("# https://api.example.com\n")
        print("  ✅ data/dominios.csv")
    
    # Diccionario básico
    dict_file = base_dir / "data" / "diccionarios" / "basic.txt"
    if not dict_file.exists():
        basic_paths = [
            "admin", "admin/", "administrator", "login", "panel",
            "config", "config.php", "wp-admin/", "backup", "test",
            "dev", "development", ".git/", ".env", "api", "api/",
            "dashboard", "phpmyadmin", "mysql", "database", "uploads",
            "files", "images", "docs", "documentation", "readme.txt",
            "robots.txt", "sitemap.xml", "phpinfo.php", "info.php"
        ]
        
        with open(dict_file, 'w', encoding='utf-8') as f:
            f.write("# Diccionario básico para fuzzing web\n")
            for path in basic_paths:
                f.write(path + "\n")
        print("  ✅ data/diccionarios/basic.txt")
    
    # Archivo de rutas descubiertas (vacío)
    discovered_file = base_dir / "data" / "descubiertos.txt"
    if not discovered_file.exists():
        discovered_file.touch()
        print("  ✅ data/descubiertos.txt")

def create_config_file():
    """Crear archivo de configuración"""
    print("\n⚙️ Creando archivo de configuración...")
    
    base_dir = Path(__file__).parent.parent
    config_file = base_dir / "config.json"
    
    if config_file.exists():
        print("  ⚠️ config.json ya existe, se mantiene configuración actual")
        return
    
    import json
    
    config = {
        "system": {
            "name": "WebFuzzing Pro",
            "version": "2.0.0",
            "timezone": "America/Argentina/Buenos_Aires",
            "log_level": "INFO"
        },
        "fuzzing": {
            "max_workers": 10,
            "timeout": 5,
            "user_agent": "Mozilla/5.0 (WebFuzzer Pro 2.0)",
            "retry_count": 3,
            "delay_between_requests": 0.1,
            "status_codes_of_interest": [200, 201, 202, 301, 302, 403, 500],
            "critical_paths": [".git", "admin", "config.php", "backup", "panel", "test", "dev"],
            "max_path_length": 12,
            "alphabet": "abcdefghijklmnopqrstuvwxyzABCDEFGHIJKLMNOPQRSTUVWXYZ",
            "numbers": "0123456789",
            "special_chars": "_-"
        },
        "database": {
            "type": "sqlite",
            "name": "webfuzzing.db",
            "backup_interval": 86400,
            "cleanup_after_days": 30
        },
        "notifications": {
            "telegram": {
                "enabled": False,
                "bot_token": "YOUR_BOT_TOKEN_HERE",
                "chat_id": "YOUR_CHAT_ID_HERE",
                "critical_only": True
            },
            "email": {
                "enabled": False,
                "smtp_server": "smtp.gmail.com",
                "smtp_port": 587,
                "username": "your-email@gmail.com",
                "password": "your-app-password",
                "recipients": ["admin@yourcompany.com"]
            }
        },
        "schedules": {
            "general_scan": "0 8,13,18,23 * * *",
            "deep_scan": "0 2 * * 0",
            "report_times": ["09:00", "14:00"],
            "working_hours": {
                "start": "08:00",
                "end": "16:00"
            }
        },
        "tools": {
            "ffuf": {
                "enabled": True,
                "path": "ffuf",
                "default_options": ["-mc", "200,403", "-t", "50"]
            },
            "dirsearch": {
                "enabled": True,
                "path": "python3 -m dirsearch",
                "default_options": ["-t", "10", "--plain-text-report"]
            }
        },
        "files": {
            "domains_file": "data/dominios.csv",
            "dictionaries_dir": "data/diccionarios",
            "results_dir": "data/resultados",
            "discovered_paths": "data/descubiertos.txt",
            "backup_dir": "backups"
        },
        "web": {
            "host": "127.0.0.1",
            "port": 5000,
            "debug": False,
            "secret_key": "change-this-secret-key-in-production",
            "session_timeout": 3600
        },
        "api": {
            "host": "127.0.0.1",
            "port": 8000,
            "api_key": "change-this-api-key-in-production",
            "rate_limit": "100/hour"
        }
    }
    
    with open(config_file, 'w', encoding='utf-8') as f:
        json.dump(config, f, indent=2, ensure_ascii=False)
    
    print("  ✅ config.json creado")
    print("  ⚠️ IMPORTANTE: Edita config.json para configurar notificaciones y API keys")

def setup_windows_service():
    """Configurar como servicio de Windows (opcional)"""
    if platform.system().lower() != "windows":
        return
    
    print("\n🪟 Configuración para Windows:")
    print("  Para ejecutar como servicio de Windows:")
    print("  1. Instalar pywin32: pip install pywin32")
    print("  2. Usar NSSM o crear un servicio personalizado")
    print("  3. O usar Task Scheduler para ejecución automática")

def main():
    """Función principal de instalación"""
    print("🚀 WebFuzzing Pro - Instalador")
    print("=" * 50)
    
    # Verificar Python
    check_python_version()
    
    # Instalar dependencias
    install_requirements()
    
    # Instalar herramientas externas
    install_external_tools()
    
    # Crear directorios
    create_directories()
    
    # Crear archivos de ejemplo
    create_sample_files()
    
    # Crear configuración
    create_config_file()
    
    # Configuración específica de Windows
    setup_windows_service()
    
    print("\n✅ Instalación completada exitosamente!")
    print("\n📋 Próximos pasos:")
    print("1. Editar config.json para configurar notificaciones")
    print("2. Agregar dominios a data/dominios.csv")
    print("3. Ejecutar: python main.py --mode all")
    print("4. Acceder al dashboard: http://localhost:5000")
    print("5. Documentar API: http://localhost:8000/api/v1/health")
    
    print("\n🔧 Comandos útiles:")
    print("  Escaneo manual: python main.py --mode scan")
    print("  Solo dashboard: python main.py --mode web")
    print("  Solo API: python main.py --mode api")

if __name__ == "__main__":
    main()