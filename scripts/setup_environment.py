# scripts/setup_environment.py
import os
import sys
import json
import secrets
from pathlib import Path

def generate_secret_keys():
    """Generar claves secretas seguras"""
    print("🔐 Generando claves secretas...")
    
    base_dir = Path(__file__).parent.parent
    config_file = base_dir / "config.json"
    
    if not config_file.exists():
        print("❌ Error: config.json no encontrado. Ejecuta install.py primero.")
        sys.exit(1)
    
    # Cargar configuración
    with open(config_file, 'r', encoding='utf-8') as f:
        config = json.load(f)
    
    # Generar nuevas claves
    config['web']['secret_key'] = secrets.token_urlsafe(32)
    config['api']['api_key'] = secrets.token_urlsafe(32)
    
    # Guardar configuración actualizada
    with open(config_file, 'w', encoding='utf-8') as f:
        json.dump(config, f, indent=2, ensure_ascii=False)
    
    print("✅ Claves secretas generadas y guardadas en config.json")
    print(f"🔑 API Key: {config['api']['api_key']}")

def setup_telegram_bot():
    """Configurar bot de Telegram interactivamente"""
    print("\n🤖 Configuración de Bot de Telegram")
    print("Sigue estos pasos:")
    print("1. Abre Telegram y busca @BotFather")
    print("2. Envía /newbot y sigue las instrucciones")
    print("3. Copia el token del bot")
    print("4. Busca @userinfobot para obtener tu chat_id")
    
    bot_token = input("\nIngresa el token del bot (o Enter para omitir): ").strip()
    if not bot_token:
        return
    
    chat_id = input("Ingresa tu chat_id: ").strip()
    if not chat_id:
        return
    
    # Actualizar configuración
    base_dir = Path(__file__).parent.parent
    config_file = base_dir / "config.json"
    
    with open(config_file, 'r', encoding='utf-8') as f:
        config = json.load(f)
    
    config['notifications']['telegram']['enabled'] = True
    config['notifications']['telegram']['bot_token'] = bot_token
    config['notifications']['telegram']['chat_id'] = chat_id
    
    with open(config_file, 'w', encoding='utf-8') as f:
        json.dump(config, f, indent=2, ensure_ascii=False)
    
    print("✅ Configuración de Telegram guardada")
    
    # Probar bot
    try:
        import requests
        url = f"https://api.telegram.org/bot{bot_token}/sendMessage"
        data = {
            'chat_id': chat_id,
            'text': '🚀 WebFuzzing Pro configurado correctamente!'
        }
        response = requests.post(url, json=data, timeout=10)
        
        if response.status_code == 200:
            print("✅ Mensaje de prueba enviado exitosamente")
        else:
            print(f"⚠️ Error enviando mensaje de prueba: {response.text}")
    except Exception as e:
        print(f"⚠️ Error probando bot: {e}")

def setup_email():
    """Configurar email interactivamente"""
    print("\n📧 Configuración de Email")
    print("Para Gmail, necesitas una 'App Password':")
    print("1. Ve a https://myaccount.google.com/security")
    print("2. Activa verificación en 2 pasos")
    print("3. Genera una 'App Password' para esta aplicación")
    
    email = input("\nIngresa tu email (o Enter para omitir): ").strip()
    if not email:
        return
    
    password = input("Ingresa tu app password: ").strip()
    if not password:
        return
    
    smtp_server = input("Servidor SMTP (default: smtp.gmail.com): ").strip() or "smtp.gmail.com"
    smtp_port = input("Puerto SMTP (default: 587): ").strip() or "587"
    
    recipients = []
    print("Ingresa emails de destinatarios (Enter vacío para terminar):")
    while True:
        recipient = input("  Email: ").strip()
        if not recipient:
            break
        recipients.append(recipient)
    
    if not recipients:
        recipients = [email]
    
    # Actualizar configuración
    base_dir = Path(__file__).parent.parent
    config_file = base_dir / "config.json"
    
    with open(config_file, 'r', encoding='utf-8') as f:
        config = json.load(f)
    
    config['notifications']['email']['enabled'] = True
    config['notifications']['email']['smtp_server'] = smtp_server
    config['notifications']['email']['smtp_port'] = int(smtp_port)
    config['notifications']['email']['username'] = email
    config['notifications']['email']['password'] = password
    config['notifications']['email']['recipients'] = recipients
    
    with open(config_file, 'w', encoding='utf-8') as f:
        json.dump(config, f, indent=2, ensure_ascii=False)
    
    print("✅ Configuración de email guardada")

def create_startup_scripts():
    """Crear scripts de inicio"""
    print("\n📝 Creando scripts de inicio...")
    
    base_dir = Path(__file__).parent.parent
    
    # Script para Windows
    bat_content = f"""@echo off
cd /d "{base_dir}"
python main.py --mode all
pause
"""
    
    bat_file = base_dir / "start_webfuzzing.bat"
    with open(bat_file, 'w', encoding='utf-8') as f:
        f.write(bat_content)
    
    print("✅ start_webfuzzing.bat creado")
    
    # Script para Linux/Mac
    sh_content = f"""#!/bin/bash
cd "{base_dir}"
python3 main.py --mode all
"""
    
    sh_file = base_dir / "start_webfuzzing.sh"
    with open(sh_file, 'w', encoding='utf-8') as f:
        f.write(sh_content)
    
    # Hacer ejecutable en sistemas Unix
    try:
        os.chmod(str(sh_file), 0o755)
        print("✅ start_webfuzzing.sh creado")
    except:
        print("✅ start_webfuzzing.sh creado (sin permisos de ejecución)")

def setup_scheduled_tasks():
    """Configurar tareas programadas del sistema"""
    print("\n⏰ Configuración de tareas programadas")
    
    system = os.name
    base_dir = Path(__file__).parent.parent
    
    if system == 'nt':  # Windows
        print("Para Windows - Task Scheduler:")
        print(f"1. Abrir Task Scheduler")
        print(f"2. Crear tarea básica")
        print(f"3. Comando: python")
        print(f"4. Argumentos: {base_dir}/main.py --mode all")
        print(f"5. Directorio: {base_dir}")
        print(f"6. Configurar para ejecutar al inicio")
    else:  # Linux/Mac
        print("Para Linux - Crontab:")
        cron_entry = f"@reboot cd {base_dir} && python3 main.py --mode all"
        print(f"1. Ejecutar: crontab -e")
        print(f"2. Agregar línea: {cron_entry}")
        
        # Crear archivo de servicio systemd
        service_content = f"""[Unit]
Description=WebFuzzing Pro Service
After=network.target

[Service]
Type=simple
User={os.getenv('USER', 'root')}
WorkingDirectory={base_dir}
ExecStart={sys.executable} {base_dir}/main.py --mode all
Restart=always
RestartSec=10

[Install]
WantedBy=multi-user.target
"""
        
        service_file = base_dir / "webfuzzing.service"
        with open(service_file, 'w', encoding='utf-8') as f:
            f.write(service_content)
        
        print(f"3. O copiar {service_file} a /etc/systemd/system/")
        print("4. sudo systemctl enable webfuzzing.service")
        print("5. sudo systemctl start webfuzzing.service")

def main():
    """Función principal de configuración"""
    print("⚙️ WebFuzzing Pro - Configuración del Entorno")
    print("=" * 50)
    
    # Generar claves secretas
    generate_secret_keys()
    
    # Configurar notificaciones
    setup_telegram = input("\n¿Configurar notificaciones de Telegram? (y/N): ").lower().startswith('y')
    if setup_telegram:
        setup_telegram_bot()
    
    setup_email_opt = input("\n¿Configurar notificaciones por email? (y/N): ").lower().startswith('y')
    if setup_email_opt:
        setup_email()
    
    # Crear scripts de inicio
    create_startup_scripts()
    
    # Configurar tareas programadas
    setup_tasks = input("\n¿Ver instrucciones para tareas programadas? (y/N): ").lower().startswith('y')
    if setup_tasks:
        setup_scheduled_tasks()
    
    print("\n✅ Configuración del entorno completada!")
    print("\n🚀 Para iniciar el sistema:")
    print("  Windows: Ejecutar start_webfuzzing.bat")
    print("  Linux/Mac: ./start_webfuzzing.sh")
    print("  Manual: python main.py --mode all")

if __name__ == "__main__":
    main()