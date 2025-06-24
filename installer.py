#!/usr/bin/env python3
"""
Sistema de Instalación Completa - URLControl
Configura todos los parámetros necesarios para el sistema de fuzzing web
"""

import os
import sys
import json
import getpass
from pathlib import Path
from typing import Dict, List, Any
import colorama
from colorama import Fore, Back, Style

def initialize_colorama():
    """Inicializar colorama para colores en terminal"""
    colorama.init(autoreset=True)

def print_banner():
    """Mostrar banner de instalación"""
    banner = f"""
{Fore.CYAN}
╔══════════════════════════════════════════════════════════════╗
║                    {Fore.YELLOW}URLControl Security System{Fore.CYAN}                    ║
║                      {Fore.GREEN}Instalador Completo v2.0{Fore.CYAN}                     ║
╚══════════════════════════════════════════════════════════════╝
{Style.RESET_ALL}
"""
    print(banner)

def get_user_input(prompt: str, required: bool = True, default: str = None) -> str:
    """Obtener input del usuario con validación"""
    while True:
        if default:
            user_input = input(f"{Fore.YELLOW}{prompt} [{default}]: {Style.RESET_ALL}")
            if not user_input:
                return default
        else:
            user_input = input(f"{Fore.YELLOW}{prompt}: {Style.RESET_ALL}")
        
        if user_input or not required:
            return user_input
        
        print(f"{Fore.RED}Este campo es obligatorio. Por favor, ingrese un valor.{Style.RESET_ALL}")

def get_yes_no(prompt: str, default: bool = False) -> bool:
    """Obtener respuesta sí/no del usuario"""
    default_text = "S/n" if default else "s/N"
    while True:
        response = input(f"{Fore.YELLOW}{prompt} ({default_text}): {Style.RESET_ALL}").lower()
        
        if not response:
            return default
        
        if response in ['s', 'si', 'yes', 'y']:
            return True
        elif response in ['n', 'no']:
            return False
        
        print(f"{Fore.RED}Por favor, responda 's' para sí o 'n' para no.{Style.RESET_ALL}")

def get_multiple_inputs(prompt: str, description: str) -> List[str]:
    """Obtener múltiples entradas del usuario"""
    print(f"{Fore.CYAN}{description}{Style.RESET_ALL}")
    items = []
    
    while True:
        item = input(f"{Fore.YELLOW}{prompt} (Enter vacío para terminar): {Style.RESET_ALL}")
        if not item:
            break
        items.append(item.strip())
        print(f"{Fore.GREEN}Agregado: {item}{Style.RESET_ALL}")
    
    return items

def validate_url(url: str) -> bool:
    """Validar formato de URL básico"""
    return url.startswith(('http://', 'https://')) and '.' in url

def validate_email(email: str) -> bool:
    """Validar formato de email básico"""
    return '@' in email and '.' in email

def collect_basic_config() -> Dict[str, Any]:
    """Recopilar configuración básica del sistema"""
    print(f"\n{Fore.BLUE}{'='*60}")
    print(f"{Fore.BLUE}1. CONFIGURACIÓN BÁSICA DEL SISTEMA")
    print(f"{Fore.BLUE}{'='*60}{Style.RESET_ALL}")
    
    config = {}
    
    # Configuración del proyecto
    config['project_name'] = get_user_input("Nombre del proyecto", default="URLControl Security")
    config['admin_email'] = get_user_input("Email del administrador")
    
    while not validate_email(config['admin_email']):
        print(f"{Fore.RED}Por favor, ingrese un email válido.{Style.RESET_ALL}")
        config['admin_email'] = get_user_input("Email del administrador")
    
    # Configuración de la base de datos
    config['database_url'] = get_user_input(
        "URL de la base de datos", 
        default="sqlite:///urlcontrol.db"
    )
    
    # Puerto y host
    config['host'] = get_user_input("Host del servidor", default="127.0.0.1")
    config['port'] = int(get_user_input("Puerto del servidor", default="5000"))
    config['debug_mode'] = get_yes_no("¿Activar modo debug?", default=False)
    
    return config

def collect_domains_config() -> Dict[str, Any]:
    """Recopilar configuración de dominios y URLs"""
    print(f"\n{Fore.BLUE}{'='*60}")
    print(f"{Fore.BLUE}2. CONFIGURACIÓN DE DOMINIOS Y URLs")
    print(f"{Fore.BLUE}{'='*60}{Style.RESET_ALL}")
    
    config = {}
    
    # Dominios principales
    domains = get_multiple_inputs(
        "Dominio/URL a monitorear",
        "Ingrese los dominios principales que desea monitorear:"
    )
    
    validated_domains = []
    for domain in domains:
        if not domain.startswith(('http://', 'https://')):
            domain = f"https://{domain}"
        
        if validate_url(domain):
            validated_domains.append(domain)
            print(f"{Fore.GREEN}✓ Dominio válido: {domain}{Style.RESET_ALL}")
        else:
            print(f"{Fore.RED}✗ Dominio inválido: {domain}{Style.RESET_ALL}")
    
    config['target_domains'] = validated_domains
    
    # Subdominios
    if get_yes_no("¿Desea configurar subdominios específicos?"):
        config['subdomains'] = get_multiple_inputs(
            "Subdominio",
            "Ingrese subdominios específicos a monitorear:"
        )
    else:
        config['subdomains'] = []
    
    # Paths específicos
    if get_yes_no("¿Desea configurar paths específicos para fuzzing?"):
        config['target_paths'] = get_multiple_inputs(
            "Path/directorio",
            "Ingrese paths específicos (ej: /admin, /api, /login):"
        )
    else:
        config['target_paths'] = ['/admin', '/api', '/login', '/dashboard', '/backup']
    
    return config

def collect_fuzzing_config() -> Dict[str, Any]:
    """Recopilar configuración de fuzzing"""
    print(f"\n{Fore.BLUE}{'='*60}")
    print(f"{Fore.BLUE}3. CONFIGURACIÓN DE FUZZING")
    print(f"{Fore.BLUE}{'='*60}{Style.RESET_ALL}")
    
    config = {}
    
    # Palabras clave personalizadas
    if get_yes_no("¿Desea agregar palabras clave personalizadas para fuzzing?"):
        custom_keywords = get_multiple_inputs(
            "Palabra clave",
            "Ingrese palabras clave adicionales para el fuzzing:"
        )
        config['custom_keywords'] = custom_keywords
    else:
        config['custom_keywords'] = []
    
    # Configuración de payloads
    default_payloads = [
        'admin', 'test', 'backup', 'config', 'database', 'db', 'sql',
        'login', 'panel', 'dashboard', 'cpanel', 'phpmyadmin',
        'wp-admin', 'administrator', 'manager', 'console'
    ]
    
    print(f"{Fore.CYAN}Payloads por defecto incluidos: {', '.join(default_payloads[:10])}...{Style.RESET_ALL}")
    
    if get_yes_no("¿Desea agregar payloads personalizados?"):
        custom_payloads = get_multiple_inputs(
            "Payload",
            "Ingrese payloads adicionales:"
        )
        config['payloads'] = default_payloads + custom_payloads
    else:
        config['payloads'] = default_payloads
    
    # Configuración de escaneo
    config['threads'] = int(get_user_input("Número de hilos concurrentes", default="10"))
    config['delay'] = float(get_user_input("Delay entre requests (segundos)", default="0.1"))
    config['timeout'] = int(get_user_input("Timeout por request (segundos)", default="10"))
    config['max_retries'] = int(get_user_input("Máximo de reintentos", default="3"))
    
    # User agents
    if get_yes_no("¿Usar múltiples User-Agents?", default=True):
        config['rotate_user_agents'] = True
    else:
        config['rotate_user_agents'] = False
    
    return config

def collect_telegram_config() -> Dict[str, Any]:
    """Recopilar configuración de Telegram"""
    print(f"\n{Fore.BLUE}{'='*60}")
    print(f"{Fore.BLUE}4. CONFIGURACIÓN DE TELEGRAM")
    print(f"{Fore.BLUE}{'='*60}{Style.RESET_ALL}")
    
    config = {}
    
    if get_yes_no("¿Desea configurar notificaciones por Telegram?"):
        config['telegram_enabled'] = True
        config['telegram_bot_token'] = get_user_input("Token del bot de Telegram")
        
        # Chat IDs
        chat_ids = get_multiple_inputs(
            "Chat ID",
            "Ingrese los Chat IDs donde enviar notificaciones:"
        )
        config['telegram_chat_ids'] = chat_ids
        
        # Grupos
        if get_yes_no("¿Desea configurar grupos específicos?"):
            groups = get_multiple_inputs(
                "ID de grupo",
                "Ingrese los IDs de grupos de Telegram:"
            )
            config['telegram_groups'] = groups
        else:
            config['telegram_groups'] = []
        
        # Configuración de alertas
        config['alert_on_discovery'] = get_yes_no("¿Alertar al encontrar nuevos endpoints?", default=True)
        config['alert_on_vulnerability'] = get_yes_no("¿Alertar al detectar vulnerabilidades?", default=True)
        config['alert_on_error'] = get_yes_no("¿Alertar en caso de errores?", default=False)
        
    else:
        config['telegram_enabled'] = False
    
    return config

def collect_api_config() -> Dict[str, Any]:
    """Recopilar configuración de APIs externas"""
    print(f"\n{Fore.BLUE}{'='*60}")
    print(f"{Fore.BLUE}5. CONFIGURACIÓN DE APIs EXTERNAS")
    print(f"{Fore.BLUE}{'='*60}{Style.RESET_ALL}")
    
    config = {}
    
    # VirusTotal API
    if get_yes_no("¿Desea configurar VirusTotal API?"):
        config['virustotal_api_key'] = get_user_input("API Key de VirusTotal")
    
    # Shodan API
    if get_yes_no("¿Desea configurar Shodan API?"):
        config['shodan_api_key'] = get_user_input("API Key de Shodan")
    
    # SecurityTrails API
    if get_yes_no("¿Desea configurar SecurityTrails API?"):
        config['securitytrails_api_key'] = get_user_input("API Key de SecurityTrails")
    
    return config

def collect_monitoring_config() -> Dict[str, Any]:
    """Recopilar configuración de monitoreo"""
    print(f"\n{Fore.BLUE}{'='*60}")
    print(f"{Fore.BLUE}6. CONFIGURACIÓN DE MONITOREO")
    print(f"{Fore.BLUE}{'='*60}{Style.RESET_ALL}")
    
    config = {}
    
    # Programación de escaneos
    config['auto_scan_enabled'] = get_yes_no("¿Activar escaneos automáticos?", default=True)
    
    if config['auto_scan_enabled']:
        config['scan_interval_hours'] = int(get_user_input("Intervalo de escaneo (horas)", default="24"))
        config['scan_on_startup'] = get_yes_no("¿Ejecutar escaneo al iniciar?", default=False)
    
    # Logging
    config['log_level'] = get_user_input(
        "Nivel de logging (DEBUG/INFO/WARNING/ERROR)", 
        default="INFO"
    ).upper()
    
    config['max_log_files'] = int(get_user_input("Máximo de archivos de log", default="10"))
    config['log_rotation_mb'] = int(get_user_input("Rotación de logs (MB)", default="50"))
    
    return config

def generate_env_file(config: Dict[str, Any]) -> None:
    """Generar archivo .env con toda la configuración"""
    env_content = f"""# URLControl Security System - Configuration
# Generated by installer.py

# === BASIC CONFIGURATION ===
PROJECT_NAME="{config.get('project_name', 'URLControl Security')}"
ADMIN_EMAIL="{config.get('admin_email', '')}"
DATABASE_URL="{config.get('database_url', 'sqlite:///urlcontrol.db')}"
HOST="{config.get('host', '127.0.0.1')}"
PORT={config.get('port', 5000)}
DEBUG={"true" if config.get('debug_mode', False) else "false"}

# === SECURITY ===
SECRET_KEY="{os.urandom(32).hex()}"
JWT_SECRET_KEY="{os.urandom(32).hex()}"

# === FUZZING CONFIGURATION ===
THREADS={config.get('threads', 10)}
DELAY={config.get('delay', 0.1)}
TIMEOUT={config.get('timeout', 10)}
MAX_RETRIES={config.get('max_retries', 3)}
ROTATE_USER_AGENTS={"true" if config.get('rotate_user_agents', True) else "false"}

# === TELEGRAM CONFIGURATION ===
TELEGRAM_ENABLED={"true" if config.get('telegram_enabled', False) else "false"}
TELEGRAM_BOT_TOKEN="{config.get('telegram_bot_token', '')}"
TELEGRAM_CHAT_IDS="{','.join(config.get('telegram_chat_ids', []))}"
TELEGRAM_GROUPS="{','.join(config.get('telegram_groups', []))}"
ALERT_ON_DISCOVERY={"true" if config.get('alert_on_discovery', True) else "false"}
ALERT_ON_VULNERABILITY={"true" if config.get('alert_on_vulnerability', True) else "false"}
ALERT_ON_ERROR={"true" if config.get('alert_on_error', False) else "false"}

# === API KEYS ===
VIRUSTOTAL_API_KEY="{config.get('virustotal_api_key', '')}"
SHODAN_API_KEY="{config.get('shodan_api_key', '')}"
SECURITYTRAILS_API_KEY="{config.get('securitytrails_api_key', '')}"

# === MONITORING ===
AUTO_SCAN_ENABLED={"true" if config.get('auto_scan_enabled', True) else "false"}
SCAN_INTERVAL_HOURS={config.get('scan_interval_hours', 24)}
SCAN_ON_STARTUP={"true" if config.get('scan_on_startup', False) else "false"}
LOG_LEVEL="{config.get('log_level', 'INFO')}"
MAX_LOG_FILES={config.get('max_log_files', 10)}
LOG_ROTATION_MB={config.get('log_rotation_mb', 50)}
"""
    
    with open('.env', 'w', encoding='utf-8') as f:
        f.write(env_content)
    
    print(f"{Fore.GREEN}✓ Archivo .env generado exitosamente{Style.RESET_ALL}")

def generate_config_json(config: Dict[str, Any]) -> None:
    """Generar archivo config.json con configuraciones específicas"""
    config_data = {
        "targets": {
            "domains": config.get('target_domains', []),
            "subdomains": config.get('subdomains', []),
            "paths": config.get('target_paths', [])
        },
        "fuzzing": {
            "payloads": config.get('payloads', []),
            "custom_keywords": config.get('custom_keywords', []),
            "threads": config.get('threads', 10),
            "delay": config.get('delay', 0.1),
            "timeout": config.get('timeout', 10)
        },
        "notifications": {
            "telegram": {
                "enabled": config.get('telegram_enabled', False),
                "chat_ids": config.get('telegram_chat_ids', []),
                "groups": config.get('telegram_groups', [])
            }
        }
    }
    
    os.makedirs('config', exist_ok=True)
    with open('config/config.json', 'w', encoding='utf-8') as f:
        json.dump(config_data, f, indent=2, ensure_ascii=False)
    
    print(f"{Fore.GREEN}✓ Archivo config/config.json generado exitosamente{Style.RESET_ALL}")

def create_directories() -> None:
    """Crear directorios necesarios"""
    directories = [
        'config',
        'logs',
        'data',
        'reports',
        'backups',
        'temp'
    ]
    
    for directory in directories:
        os.makedirs(directory, exist_ok=True)
        print(f"{Fore.GREEN}✓ Directorio creado: {directory}{Style.RESET_ALL}")

def install_requirements() -> None:
    """Instalar dependencias de Python"""
    print(f"\n{Fore.BLUE}Instalando dependencias de Python...{Style.RESET_ALL}")
    
    try:
        import subprocess
        result = subprocess.run([sys.executable, '-m', 'pip', 'install', '-r', 'requirements.txt'], 
                              capture_output=True, text=True)
        
        if result.returncode == 0:
            print(f"{Fore.GREEN}✓ Dependencias instaladas exitosamente{Style.RESET_ALL}")
        else:
            print(f"{Fore.RED}✗ Error al instalar dependencias: {result.stderr}{Style.RESET_ALL}")
    except Exception as e:
        print(f"{Fore.RED}✗ Error durante la instalación: {str(e)}{Style.RESET_ALL}")

def show_summary(config: Dict[str, Any]) -> None:
    """Mostrar resumen de la configuración"""
    print(f"\n{Fore.GREEN}{'='*60}")
    print(f"{Fore.GREEN}RESUMEN DE CONFIGURACIÓN")
    print(f"{Fore.GREEN}{'='*60}{Style.RESET_ALL}")
    
    print(f"{Fore.CYAN}Proyecto: {Style.RESET_ALL}{config.get('project_name')}")
    print(f"{Fore.CYAN}Admin: {Style.RESET_ALL}{config.get('admin_email')}")
    print(f"{Fore.CYAN}Host: {Style.RESET_ALL}{config.get('host')}:{config.get('port')}")
    print(f"{Fore.CYAN}Dominios configurados: {Style.RESET_ALL}{len(config.get('target_domains', []))}")
    print(f"{Fore.CYAN}Telegram: {Style.RESET_ALL}{'Activado' if config.get('telegram_enabled') else 'Desactivado'}")
    print(f"{Fore.CYAN}Escaneo automático: {Style.RESET_ALL}{'Activado' if config.get('auto_scan_enabled') else 'Desactivado'}")
    
    print(f"\n{Fore.YELLOW}Para iniciar el sistema:{Style.RESET_ALL}")
    print(f"  python -m web.app")
    print(f"  python -m api.app")

def main():
    """Función principal del instalador"""
    initialize_colorama()
    print_banner()
    
    try:
        # Recopilar toda la configuración
        all_config = {}
        
        all_config.update(collect_basic_config())
        all_config.update(collect_domains_config())
        all_config.update(collect_fuzzing_config())
        all_config.update(collect_telegram_config())
        all_config.update(collect_api_config())
        all_config.update(collect_monitoring_config())
        
        # Generar archivos de configuración
        print(f"\n{Fore.BLUE}Generando archivos de configuración...{Style.RESET_ALL}")
        create_directories()
        generate_env_file(all_config)
        generate_config_json(all_config)
        
        # Instalar dependencias
        if get_yes_no("¿Desea instalar las dependencias de Python ahora?", default=True):
            install_requirements()
        
        # Mostrar resumen
        show_summary(all_config)
        
        print(f"\n{Fore.GREEN}🎉 ¡Instalación completada exitosamente!{Style.RESET_ALL}")
        
    except KeyboardInterrupt:
        print(f"\n{Fore.YELLOW}Instalación cancelada por el usuario.{Style.RESET_ALL}")
        sys.exit(1)
    except Exception as e:
        print(f"\n{Fore.RED}Error durante la instalación: {str(e)}{Style.RESET_ALL}")
        sys.exit(1)

if __name__ == "__main__":
    main()