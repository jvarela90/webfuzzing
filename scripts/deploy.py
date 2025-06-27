# scripts/deploy.py
#!/usr/bin/env python3
"""
Script de deployment para WebFuzzing Pro
Soporta diferentes entornos: development, staging, production
"""

import os
import sys
import subprocess
import shutil
import json
import argparse
from pathlib import Path
import tempfile
import yaml

class Deployer:
    """Clase para manejar deployments"""
    
    def __init__(self, environment='development'):
        self.environment = environment
        self.base_dir = Path(__file__).parent.parent
        self.deploy_configs = {
            'development': {
                'debug': True,
                'workers': 1,
                'log_level': 'DEBUG',
                'max_workers': 2
            },
            'staging': {
                'debug': False,
                'workers': 2,
                'log_level': 'INFO',
                'max_workers': 5
            },
            'production': {
                'debug': False,
                'workers': 4,
                'log_level': 'WARNING',
                'max_workers': 10
            }
        }
    
    def validate_environment(self):
        """Validar entorno de deployment"""
        print(f"🔍 Validando entorno {self.environment}...")
        
        # Verificar Python
        if sys.version_info < (3, 8):
            raise Exception("Se requiere Python 3.8 o superior")
        
        # Verificar dependencias
        try:
            import flask, requests, schedule
            print("✅ Dependencias Python verificadas")
        except ImportError as e:
            raise Exception(f"Dependencia faltante: {e}")
        
        # Verificar estructura de directorios
        required_dirs = ['config', 'core', 'web', 'api', 'utils']
        for dir_name in required_dirs:
            if not (self.base_dir / dir_name).exists():
                raise Exception(f"Directorio faltante: {dir_name}")
        
        print("✅ Estructura de proyecto verificada")
    
    def setup_configuration(self):
        """Configurar para el entorno específico"""
        print(f"⚙️ Configurando para entorno {self.environment}...")
        
        config_file = self.base_dir / 'config.json'
        
        if config_file.exists():
            with open(config_file, 'r') as f:
                config = json.load(f)
        else:
            # Ejecutar setup si no existe configuración
            subprocess.run([sys.executable, 'scripts/install.py'], 
                          cwd=self.base_dir, check=True)
            with open(config_file, 'r') as f:
                config = json.load(f)
        
        # Aplicar configuración del entorno
        env_config = self.deploy_configs[self.environment]
        
        config['web']['debug'] = env_config['debug']
        config['system']['log_level'] = env_config['log_level']
        config['fuzzing']['max_workers'] = env_config['max_workers']
        
        # Configuraciones específicas por entorno
        if self.environment == 'production':
            config['web']['host'] = '0.0.0.0'
            config['api']['host'] = '0.0.0.0'
            config['notifications']['telegram']['enabled'] = True
            config['notifications']['email']['enabled'] = True
        
        # Guardar configuración actualizada
        with open(config_file, 'w') as f:
            json.dump(config, f, indent=2)
        
        print("✅ Configuración actualizada")
    
    def setup_systemd_service(self):
        """Configurar servicio systemd para Linux"""
        if os.name != 'posix':
            print("⚠️ Servicio systemd solo disponible en Linux")
            return
        
        print("🔧 Configurando servicio systemd...")
        
        service_content = f"""[Unit]
Description=WebFuzzing Pro - Sistema de Fuzzing Web
After=network.target
Wants=network.target

[Service]
Type=simple
User=webfuzzing
Group=webfuzzing
WorkingDirectory={self.base_dir}
Environment=PYTHONPATH={self.base_dir}
Environment=WF_ENV={self.environment}
ExecStart={sys.executable} {self.base_dir}/main.py --mode all
ExecReload=/bin/kill -HUP $MAINPID
KillMode=mixed
TimeoutStopSec=5
PrivateTmp=true
Restart=always
RestartSec=10

[Install]
WantedBy=multi-user.target
"""
        
        service_file = Path('/tmp/webfuzzing.service')
        with open(service_file, 'w') as f:
            f.write(service_content)
        
        print(f"✅ Archivo de servicio creado en {service_file}")
        print("Para instalar el servicio:")
        print(f"  sudo cp {service_file} /etc/systemd/system/")
        print("  sudo systemctl daemon-reload")
        print("  sudo systemctl enable webfuzzing.service")
        print("  sudo systemctl start webfuzzing.service")
    
    def create_docker_compose(self):
        """Generar docker-compose.yml optimizado para el entorno"""
        print("🐳 Generando configuración Docker...")
        
        env_config = self.deploy_configs[self.environment]
        
        compose_config = {
            'version': '3.8',
            'services': {
                'webfuzzing': {
                    'build': '.',
                    'container_name': f'webfuzzing-{self.environment}',
                    'restart': 'unless-stopped' if self.environment == 'production' else 'no',
                    'ports': [
                        '5000:5000',
                        '8000:8000'
                    ],
                    'volumes': [
                        './data:/app/data',
                        './logs:/app/logs',
                        './backups:/app/backups',
                        './config.json:/app/config.json:ro'
                    ],
                    'environment': [
                        f'FLASK_ENV={self.environment}',
                        f'WF_LOG_LEVEL={env_config["log_level"]}',
                        f'WF_MAX_WORKERS={env_config["max_workers"]}'
                    ]
                }
            }
        }
        
        # Agregar servicios adicionales para producción
        if self.environment == 'production':
            compose_config['services']['nginx'] = {
                'image': 'nginx:alpine',
                'container_name': 'webfuzzing-nginx',
                'restart': 'unless-stopped',
                'ports': ['80:80', '443:443'],
                'volumes': [
                    './docker/nginx.conf:/etc/nginx/nginx.conf:ro'
                ],
                'depends_on': ['webfuzzing']
            }
        
        # Guardar archivo
        compose_file = self.base_dir / f'docker-compose.{self.environment}.yml'
        with open(compose_file, 'w') as f:
            yaml.dump(compose_config, f, default_flow_style=False)
        
        print(f"✅ Docker Compose generado: {compose_file}")
    
    def run_tests(self):
        """Ejecutar tests antes del deployment"""
        print("🧪 Ejecutando tests...")
        
        test_result = subprocess.run([
            sys.executable, 'tests/test_fuzzing_engine.py'
        ], cwd=self.base_dir, capture_output=True, text=True)
        
        if test_result.returncode != 0:
            print("❌ Tests fallaron:")
            print(test_result.stdout)
            print(test_result.stderr)
            return False
        
        print("✅ Todos los tests pasaron")
        return True
    
    def backup_current_deployment(self):
        """Crear backup del deployment actual"""
        if self.environment == 'production':
            print("💾 Creando backup del deployment actual...")
            
            timestamp = datetime.now().strftime('%Y%m%d_%H%M%S')
            backup_dir = self.base_dir / 'backups' / f'deployment_{timestamp}'
            backup_dir.mkdir(parents=True, exist_ok=True)
            
            # Backup de configuración
            if (self.base_dir / 'config.json').exists():
                shutil.copy2(self.base_dir / 'config.json', backup_dir)
            
            # Backup de base de datos
            if (self.base_dir / 'webfuzzing.db').exists():
                shutil.copy2(self.base_dir / 'webfuzzing.db', backup_dir)
            
            print(f"✅ Backup creado en {backup_dir}")
    
    def deploy(self, run_tests=True, create_service=False, docker=False):
        """Ejecutar deployment completo"""
        print(f"🚀 Iniciando deployment para {self.environment}")
        print("=" * 50)
        
        try:
            # 1. Validar entorno
            self.validate_environment()
            
            # 2. Ejecutar tests
            if run_tests and not self.run_tests():
                raise Exception("Tests fallaron")
            
            # 3. Backup (solo producción)
            if self.environment == 'production':
                self.backup_current_deployment()
            
            # 4. Configurar entorno
            self.setup_configuration()
            
            # 5. Configurar servicio systemd
            if create_service:
                self.setup_systemd_service()
            
            # 6. Generar configuración Docker
            if docker:
                self.create_docker_compose()
            
            # 7. Finalizar
            print("\n" + "=" * 50)
            print(f"✅ Deployment {self.environment} completado exitosamente!")
            
            # Instrucciones finales
            print(f"\n📋 Próximos pasos para {self.environment}:")
            
            if docker:
                print(f"  docker-compose -f docker-compose.{self.environment}.yml up -d")
            else:
                print(f"  python main.py --mode all")
            
            print(f"  Dashboard: http://localhost:5000")
            print(f"  API: http://localhost:8000")
            
            if self.environment == 'production':
                print("\n⚠️ Recordatorios para producción:")
                print("  - Configurar HTTPS con certificados SSL")
                print("  - Configurar firewall y restricciones de acceso")
                print("  - Configurar monitoreo y alertas")
                print("  - Programar backups automáticos")
        
        except Exception as e:
            print(f"\n❌ Error durante deployment: {e}")
            return False
        
        return True

def main():
    """Función principal"""
    parser = argparse.ArgumentParser(description='Deploy WebFuzzing Pro')
    parser.add_argument('--env', choices=['development', 'staging', 'production'],
                       default='development', help='Entorno de deployment')
    parser.add_argument('--skip-tests', action='store_true', 
                       help='Saltar ejecución de tests')
    parser.add_argument('--systemd', action='store_true',
                       help='Crear servicio systemd')
    parser.add_argument('--docker', action='store_true',
                       help='Generar configuración Docker')
    
    args = parser.parse_args()
    
    deployer = Deployer(args.env)
    success = deployer.deploy(
        run_tests=not args.skip_tests,
        create_service=args.systemd,
        docker=args.docker
    )
    
    sys.exit(0 if success else 1)

if __name__ == "__main__":
    main()
