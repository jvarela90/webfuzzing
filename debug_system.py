#!/usr/bin/env python3
"""
Script de Diagnóstico del Sistema URLControl
Identifica problemas de instalación y configuración
"""

import sys
import os
import subprocess
import socket
import importlib
import json
from pathlib import Path

def check_python_version():
    """Verificar versión de Python"""
    print(f"🐍 Python Version: {sys.version}")
    print(f"📁 Python Path: {sys.executable}")
    
def check_virtual_env():
    """Verificar si está en entorno virtual"""
    in_venv = hasattr(sys, 'real_prefix') or (hasattr(sys, 'base_prefix') and sys.base_prefix != sys.prefix)
    print(f"🔧 Virtual Environment: {'✅ Active' if in_venv else '❌ Not Active'}")
    if in_venv:
        print(f"📂 Venv Path: {sys.prefix}")

def check_required_packages():
    """Verificar paquetes requeridos"""
    required_packages = [
        'flask', 'flask_cors', 'flask_restful', 'flask_socketio',
        'requests', 'beautifulsoup4', 'colorama', 'tqdm'
    ]
    
    print("\n📦 Checking Required Packages:")
    print("-" * 50)
    
    missing_packages = []
    for package in required_packages:
        try:
            importlib.import_module(package)
            print(f"✅ {package}")
        except ImportError:
            print(f"❌ {package} - MISSING")
            missing_packages.append(package)
    
    if missing_packages:
        print(f"\n🚨 Missing Packages: {', '.join(missing_packages)}")
        print("📥 Install with: pip install " + " ".join(missing_packages))
    
    return missing_packages

def check_ports():
    """Verificar puertos disponibles"""
    ports_to_check = [5000, 8000, 8080, 3000]
    
    print("\n🔌 Checking Ports:")
    print("-" * 50)
    
    for port in ports_to_check:
        try:
            with socket.socket(socket.AF_INET, socket.SOCK_STREAM) as s:
                s.settimeout(1)
                result = s.connect_ex(('localhost', port))
                if result == 0:
                    print(f"🔴 Port {port}: OCCUPIED")
                else:
                    print(f"🟢 Port {port}: Available")
        except Exception as e:
            print(f"❓ Port {port}: Error - {e}")

def check_project_structure():
    """Verificar estructura del proyecto"""
    print("\n📁 Checking Project Structure:")
    print("-" * 50)
    
    required_files = [
        'web/app.py',
        'api/app.py', 
        'core/fuzzing_engine.py',
        'requirements.txt',
        'config/',
        'logs/',
        'data/'
    ]
    
    missing_files = []
    for file_path in required_files:
        path = Path(file_path)
        if path.exists():
            print(f"✅ {file_path}")
        else:
            print(f"❌ {file_path} - MISSING")
            missing_files.append(file_path)
    
    return missing_files

def check_config_files():
    """Verificar archivos de configuración"""
    print("\n⚙️ Checking Configuration Files:")
    print("-" * 50)
    
    config_files = ['.env', 'config/config.json', 'config/settings.yaml']
    
    for config_file in config_files:
        path = Path(config_file)
        if path.exists():
            print(f"✅ {config_file}")
            try:
                if config_file.endswith('.json'):
                    with open(path, 'r') as f:
                        json.load(f)
                    print(f"   📄 Valid JSON format")
                elif config_file == '.env':
                    with open(path, 'r') as f:
                        lines = f.readlines()
                    print(f"   📄 {len(lines)} environment variables")
            except Exception as e:
                print(f"   ❌ Error reading {config_file}: {e}")
        else:
            print(f"❌ {config_file} - MISSING")

def check_running_processes():
    """Verificar procesos corriendo"""
    print("\n🔄 Checking Running Processes:")
    print("-" * 50)
    
    try:
        # En Windows
        result = subprocess.run(['tasklist', '/FI', 'IMAGENAME eq python*'], 
                              capture_output=True, text=True)
        if result.returncode == 0:
            lines = result.stdout.strip().split('\n')
            python_processes = [line for line in lines if 'python' in line.lower()]
            
            if python_processes:
                print("🐍 Python Processes:")
                for process in python_processes:
                    print(f"   {process}")
            else:
                print("❌ No Python processes found")
        else:
            print("❌ Error checking processes")
            
    except Exception as e:
        print(f"❌ Error checking processes: {e}")

def test_flask_import():
    """Probar importación de Flask"""
    print("\n🧪 Testing Flask Import:")
    print("-" * 50)
    
    try:
        from flask import Flask
        app = Flask(__name__)
        
        @app.route('/test')
        def test():
            return {'status': 'ok', 'message': 'Flask is working'}
        
        print("✅ Flask import successful")
        print("✅ Flask app creation successful")
        
        # Probar inicio rápido
        try:
            import threading
            import time
            
            def start_test_server():
                app.run(host='127.0.0.1', port=5001, debug=False)
            
            thread = threading.Thread(target=start_test_server)
            thread.daemon = True
            thread.start()
            
            time.sleep(2)
            
            # Probar conexión
            import requests
            response = requests.get('http://127.0.0.1:5001/test', timeout=5)
            if response.status_code == 200:
                print("✅ Flask test server working")
            else:
                print(f"❌ Flask test server returned {response.status_code}")
                
        except Exception as e:
            print(f"❌ Flask test server error: {e}")
            
    except ImportError as e:
        print(f"❌ Flask import failed: {e}")
    except Exception as e:
        print(f"❌ Flask test error: {e}")

def generate_fix_commands():
    """Generar comandos de solución"""
    print("\n🔧 SOLUTION COMMANDS:")
    print("=" * 60)
    
    print("1. Install missing packages:")
    print("   pip install flask flask-cors flask-restful flask-socketio")
    print("   pip install -r requirements.txt")
    
    print("\n2. Check if dashboard starts manually:")
    print("   python -m web.app")
    
    print("\n3. Check if API is accessible:")
    print("   curl http://localhost:8000/health")
    
    print("\n4. Kill existing processes if needed:")
    print("   taskkill /PID 21728 /F")
    print("   taskkill /PID 6524 /F")
    
    print("\n5. Restart system:")
    print("   python start_system.py")

def main():
    """Función principal de diagnóstico"""
    print("🔍 URLControl System Diagnostics")
    print("=" * 60)
    
    check_python_version()
    check_virtual_env()
    
    missing_packages = check_required_packages()
    missing_files = check_project_structure()
    
    check_config_files()
    check_ports()
    check_running_processes()
    
    if not missing_packages:
        test_flask_import()
    
    generate_fix_commands()
    
    print("\n" + "=" * 60)
    print("🎯 SUMMARY:")
    if missing_packages:
        print(f"❌ Missing {len(missing_packages)} packages")
    else:
        print("✅ All packages installed")
        
    if missing_files:
        print(f"❌ Missing {len(missing_files)} files")
    else:
        print("✅ Project structure OK")
    
    print("\n🔧 Next Steps:")
    if missing_packages:
        print("1. Install missing packages")
        print("2. Restart the system")
    else:
        print("1. Try starting dashboard manually")
        print("2. Check logs for errors")

if __name__ == "__main__":
    main()