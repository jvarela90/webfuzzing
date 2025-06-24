#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Sistema de Automatización y Orquestación Inteligente - Script Principal
Punto de entrada principal que integra todos los componentes del sistema

Uso:
    python main.py --help                    # Mostrar ayuda
    python main.py --setup                   # Configurar entorno inicial
    python main.py --start                   # Iniciar sistema completo
    python main.py --daemon                  # Ejecutar como daemon
    python main.py --task <nombre>           # Ejecutar tarea específica
    python main.py --status                  # Mostrar estado del sistema
    python main.py --config                  # Validar configuración
"""

import asyncio
import argparse
import logging
import signal
import sys
import os
import json
import yaml
from pathlib import Path
from datetime import datetime
import platform

# Agregar el directorio actual al path
sys.path.insert(0, str(Path(__file__).parent))

# Importar componentes consolidados
try:
    from automation import (
        AutomationSystem, 
        setup_logging,
        create_automation_system
    )
    from fuzzing_engine import (
        FuzzingConfig,
        ConsolidatedDatabaseManager,
        ConsolidatedDictionaryManager,
        ConsolidatedFuzzingEngine
    )
    from app import ConsolidatedDashboardManager
except ImportError as e:
    print(f"❌ Error importando módulos: {e}")
    print("💡 Asegúrate de que todos los archivos estén en el directorio correcto")
    sys.exit(1)

class MainSystemOrchestrator:
    """
    Orquestador principal que coordina todos los componentes del sistema
    """
    
    def __init__(self, config_path: str = "automation_config.yaml"):
        """
        Inicializar orquestador principal
        
        Args:
            config_path: Ruta al archivo de configuración
        """
        self.config_path = Path(config_path)
        self.logger = None
        self.config = {}
        
        # Componentes principales
        self.automation_system = None
        self.fuzzing_engine = None
        self.dashboard_manager = None
        self.alert_system = None
        self.notification_manager = None
        
        # Estado del sistema
        self.is_running = False
        self.startup_time = None
        self.shutdown_handlers = []
        
        # Configurar logging inicial
        self.setup_initial_logging()
        
        # Cargar configuración
        self.load_configuration()
        
        # Configurar logging definitivo
        self.setup_system_logging()
        
        # Configurar handlers de señales
        self.setup_signal_handlers()
    
    def setup_initial_logging(self):
        """Configurar logging inicial básico"""
        logging.basicConfig(
            level=logging.INFO,
            format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
        )
        self.logger = logging.getLogger(__name__)
    
    def load_configuration(self):
        """Cargar configuración del sistema"""
        try:
            if self.config_path.exists():
                with open(self.config_path, 'r', encoding='utf-8') as f:
                    self.config = yaml.safe_load(f) or {}
                self.logger.info(f"Configuración cargada desde {self.config_path}")
            else:
                self.logger.warning(f"Archivo de configuración no encontrado: {self.config_path}")
                self.create_default_config()
                
        except Exception as e:
            self.logger.error(f"Error cargando configuración: {e}")
            self.config = {}
    
    def create_default_config(self):
        """Crear configuración por defecto"""
        default_config = {
            'system': {
                'version': '2.0.0',
                'environment': 'development',
                'log_level': 'INFO'
            },
            'orchestrator': {
                'max_concurrent_tasks': 5,
                'health_check_interval': 300
            }
        }
        
        try:
            self.config_path.parent.mkdir(parents=True, exist_ok=True)
            with open(self.config_path, 'w', encoding='utf-8') as f:
                yaml.dump(default_config, f, default_flow_style=False, indent=2)
            
            self.config = default_config
            self.logger.info(f"Configuración por defecto creada en {self.config_path}")
            
        except Exception as e:
            self.logger.error(f"Error creando configuración por defecto: {e}")
    
    def setup_system_logging(self):
        """Configurar logging del sistema basado en configuración"""
        log_config = self.config.get('storage', {}).get('logs', {})
        log_level = self.config.get('system', {}).get('log_level', 'INFO')
        
        log_dir = Path(log_config.get('directory', 'logs'))
        log_file = log_dir / f"automation_system_{datetime.now().strftime('%Y%m%d')}.log"
        
        setup_logging(log_level, str(log_file))
        self.logger = logging.getLogger(__name__)
        
        self.logger.info("="*60)
        self.logger.info("🤖 SISTEMA DE AUTOMATIZACIÓN Y ORQUESTACIÓN INTELIGENTE")
        self.logger.info("="*60)
        self.logger.info(f"Versión: {self.config.get('system', {}).get('version', '2.0.0')}")
        self.logger.info(f"Entorno: {self.config.get('system', {}).get('environment', 'development')}")
        self.logger.info(f"Plataforma: {platform.system()} {platform.release()}")
        self.logger.info(f"Python: {platform.python_version()}")
        self.logger.info(f"Configuración: {self.config_path}")
        self.logger.info(f"Logs: {log_file}")
        self.logger.info("="*60)
    
    def setup_signal_handlers(self):
        """Configurar manejadores de señales del sistema"""
        def signal_handler(signum, frame):
            signal_name = signal.Signals(signum).name
            self.logger.info(f"Señal {signal_name} recibida, iniciando shutdown...")
            asyncio.create_task(self.shutdown())
        
        # Configurar señales en sistemas Unix
        if platform.system() != "Windows":
            signal.signal(signal.SIGTERM, signal_handler)
            signal.signal(signal.SIGINT, signal_handler)
            signal.signal(signal.SIGHUP, signal_handler)
        else:
            # En Windows solo SIGINT (Ctrl+C)
            signal.signal(signal.SIGINT, signal_handler)
    
    async def initialize_components(self):
        """Inicializar todos los componentes del sistema"""
        self.logger.info("🔧 Inicializando componentes del sistema...")
        
        try:
            # 1. Inicializar configuración de fuzzing
            self.logger.info("Inicializando motor de fuzzing...")
            fuzzing_config = FuzzingConfig()
            
            # 2. Inicializar base de datos
            self.logger.info("Inicializando base de datos...")
            db_manager = ConsolidatedDatabaseManager(fuzzing_config.DATABASE_FILE)
            
            # 3. Inicializar gestor de diccionarios
            self.logger.info("Inicializando gestor de diccionarios...")
            dict_manager = ConsolidatedDictionaryManager(fuzzing_config)
            
            # 4. Inicializar motor de fuzzing
            self.logger.info("Inicializando motor de fuzzing consolidado...")
            self.fuzzing_engine = ConsolidatedFuzzingEngine(
                fuzzing_config, db_manager, dict_manager
            )
            
            # 5. Inicializar dashboard manager
            self.logger.info("Inicializando dashboard manager...")
            self.dashboard_manager = ConsolidatedDashboardManager(fuzzing_config.DATABASE_FILE)
            
            # 6. Inicializar sistema de alertas (simulado)
            self.logger.info("Inicializando sistema de alertas...")
            self.alert_system = self._create_mock_alert_system()
            
            # 7. Inicializar gestor de notificaciones (simulado)
            self.logger.info("Inicializando gestor de notificaciones...")
            self.notification_manager = self._create_mock_notification_manager()
            
            # 8. Inicializar sistema de automatización
            self.logger.info("Inicializando sistema de automatización...")
            self.automation_system = create_automation_system(str(self.config_path))
            
            # 9. Conectar componentes
            self.logger.info("Conectando componentes...")
            self.automation_system.initialize(
                fuzzing_engine=self.fuzzing_engine,
                alert_system=self.alert_system,
                notification_manager=self.notification_manager
            )
            
            self.logger.info("✅ Todos los componentes inicializados correctamente")
            
        except Exception as e:
            self.logger.error(f"❌ Error inicializando componentes: {e}")
            raise
    
    def _create_mock_alert_system(self):
        """Crear sistema de alertas simulado"""
        class MockAlertSystem:
            def generate_intelligent_alerts(self, findings):
                return [
                    {
                        'id': f'alert_{i}',
                        'severity': 'critical' if finding.get('is_critical') else 'medium',
                        'message': f"Alert for {finding.get('url', 'unknown')}",
                        'finding': finding
                    }
                    for i, finding in enumerate(findings[:5])  # Máximo 5 alertas
                ]
            
            def retrain_models(self, days_back=30):
                return {'status': 'completed', 'models_updated': 2}
        
        return MockAlertSystem()
    
    def _create_mock_notification_manager(self):
        """Crear gestor de notificaciones simulado"""
        class MockNotificationManager:
            def send_notification(self, message, severity='info'):
                self.logger = logging.getLogger(__name__)
                self.logger.info(f"📱 Notificación ({severity}): {message}")
                return True
            
            def send_summary_report(self):
                self.logger = logging.getLogger(__name__)
                self.logger.info("📊 Enviando reporte de resumen")
                return True
            
            def send_no_findings_report(self):
                self.logger = logging.getLogger(__name__)
                self.logger.info("✅ Enviando reporte sin novedades")
                return True
        
        return MockNotificationManager()
    
    async def start_system(self):
        """Iniciar el sistema completo"""
        if self.is_running:
            self.logger.warning("El sistema ya está en ejecución")
            return
        
        try:
            self.logger.info("🚀 Iniciando sistema de automatización...")
            self.startup_time = datetime.now()
            
            # Inicializar componentes
            await self.initialize_components()
            
            # Iniciar sistema de automatización
            await self.automation_system.start()
            
            self.is_running = True
            
            # Mostrar estado inicial
            await self.show_system_status()
            
            self.logger.info("✅ Sistema iniciado correctamente")
            self.logger.info("🔗 Dashboard disponible en: http://localhost:5000")
            self.logger.info("⏹️  Para detener: Ctrl+C")
            
        except Exception as e:
            self.logger.error(f"❌ Error iniciando sistema: {e}")
            await self.shutdown()
            raise
    
    async def shutdown(self):
        """Detener el sistema de forma ordenada"""
        if not self.is_running:
            return
        
        self.logger.info("🛑 Deteniendo sistema...")
        
        try:
            # Detener sistema de automatización
            if self.automation_system:
                await self.automation_system.stop()
            
            # Ejecutar handlers de shutdown personalizados
            for handler in self.shutdown_handlers:
                try:
                    await handler()
                except Exception as e:
                    self.logger.error(f"Error en shutdown handler: {e}")
            
            self.is_running = False
            
            # Calcular tiempo de ejecución
            if self.startup_time:
                uptime = datetime.now() - self.startup_time
                self.logger.info(f"⏱️  Tiempo de ejecución: {uptime}")
            
            self.logger.info("✅ Sistema detenido correctamente")
            
        except Exception as e:
            self.logger.error(f"❌ Error durante shutdown: {e}")
    
    async def run_daemon(self):
        """Ejecutar como daemon (proceso en segundo plano)"""
        await self.start_system()
        
        try:
            # Mantener el sistema ejecutándose
            while self.is_running:
                await asyncio.sleep(60)  # Verificar cada minuto
                
                # Verificar salud del sistema
                if self.automation_system:
                    status = self.automation_system.get_status()
                    if not status.get('running', False):
                        self.logger.error("Sistema de automatización no está ejecutándose")
                        break
                        
        except asyncio.CancelledError:
            self.logger.info("Daemon cancelado")
        except KeyboardInterrupt:
            self.logger.info("Daemon interrumpido por usuario")
        finally:
            await self.shutdown()
    
    async def execute_manual_task(self, task_name: str, **kwargs):
        """Ejecutar tarea manual específica"""
        if not self.automation_system or not self.automation_system.is_initialized:
            await self.initialize_components()
        
        self.logger.info(f"🎯 Ejecutando tarea manual: {task_name}")
        
        try:
            task_id = self.automation_system.schedule_task(task_name, **kwargs)
            self.logger.info(f"✅ Tarea '{task_name}' programada con ID: {task_id}")
            
            # Esperar un momento para que se ejecute
            await asyncio.sleep(5)
            
            # Mostrar resultado
            history = self.automation_system.get_task_history(5)
            for task in history:
                if task['task_name'] == task_name:
                    status_icon = "✅" if task['status'] == 'completed' else "❌"
                    self.logger.info(f"{status_icon} Resultado: {task}")
                    break
            
        except Exception as e:
            self.logger.error(f"❌ Error ejecutando tarea '{task_name}': {e}")
    
    async def show_system_status(self):
        """Mostrar estado detallado del sistema"""
        self.logger.info("📊 ESTADO DEL SISTEMA")
        self.logger.info("="*50)
        
        try:
            if self.automation_system:
                status = self.automation_system.get_status()
                
                self.logger.info(f"🔧 Sistema inicializado: {status.get('initialized', False)}")
                self.logger.info(f"▶️  Sistema ejecutándose: {status.get('running', False)}")
                self.logger.info(f"📦 Versión: {status.get('version', 'N/A')}")
                
                if 'orchestrator' in status:
                    orch_status = status['orchestrator']
                    self.logger.info(f"🎭 Tareas activas: {orch_status.get('active_tasks', 0)}")
                    self.logger.info(f"📋 Tareas en cola: {orch_status.get('queue_size', 0)}")
                    self.logger.info(f"🔧 Workers máximos: {orch_status.get('max_concurrent_tasks', 0)}")
                
                if 'scheduler' in status:
                    sched_status = status['scheduler']
                    self.logger.info(f"⏰ Tareas programadas: {sched_status.get('total_scheduled_tasks', 0)}")
                    self.logger.info(f"✅ Tareas habilitadas: {sched_status.get('enabled_tasks', 0)}")
                
                if 'workers' in status:
                    workers_status = status['workers']
                    self.logger.info(f"👷 Workers registrados: {workers_status.get('registered_workers', 0)}")
                    self.logger.info(f"📈 Tasa de éxito: {workers_status.get('success_rate', 0):.2%}")
            
            # Mostrar métricas del sistema si están disponibles
            if self.automation_system:
                try:
                    metrics = self.automation_system.get_system_metrics()
                    if metrics:
                        current = metrics.get('current_metrics', {})
                        self.logger.info(f"💻 CPU: {current.get('cpu', 0):.1f}%")
                        self.logger.info(f"🧠 Memoria: {current.get('memory', 0)*100:.1f}%")
                        self.logger.info(f"💾 Disco: {current.get('disk', 0)*100:.1f}%")
                except Exception as e:
                    self.logger.debug(f"No se pudieron obtener métricas: {e}")
            
        except Exception as e:
            self.logger.error(f"Error obteniendo estado: {e}")
        
        self.logger.info("="*50)
    
    def validate_configuration(self):
        """Validar configuración del sistema"""
        self.logger.info("🔍 Validando configuración...")
        
        issues = []
        warnings = []
        
        # Validar estructura básica
        required_sections = ['system', 'orchestrator', 'scheduler']
        for section in required_sections:
            if section not in self.config:
                issues.append(f"Sección requerida faltante: {section}")
        
        # Validar configuración del orquestador
        orch_config = self.config.get('orchestrator', {})
        max_tasks = orch_config.get('max_concurrent_tasks', 5)
        if max_tasks < 1 or max_tasks > 20:
            warnings.append(f"max_concurrent_tasks ({max_tasks}) fuera del rango recomendado (1-20)")
        
        # Validar configuración del scheduler
        sched_config = self.config.get('scheduler', {})
        if not sched_config.get('enabled', True):
            warnings.append("Scheduler deshabilitado - no se ejecutarán tareas automáticas")
        
        # Validar variables de entorno
        env_vars = self.config.get('environment_variables', {})
        required_vars = env_vars.get('required', [])
        
        for var in required_vars:
            if not os.getenv(var):
                issues.append(f"Variable de entorno requerida no encontrada: {var}")
        
        # Mostrar resultados
        if issues:
            self.logger.error("❌ Problemas de configuración encontrados:")
            for issue in issues:
                self.logger.error(f"  • {issue}")
        
        if warnings:
            self.logger.warning("⚠️  Advertencias de configuración:")
            for warning in warnings:
                self.logger.warning(f"  • {warning}")
        
        if not issues and not warnings:
            self.logger.info("✅ Configuración válida")
        
        return len(issues) == 0
    
    def setup_environment(self):
        """Configurar entorno inicial del sistema"""
        self.logger.info("🛠️  Configurando entorno inicial...")
        
        try:
            # Crear directorios necesarios
            directories = [
                Path("data"),
                Path("logs"), 
                Path("reports"),
                Path("backups"),
                Path("templates")
            ]
            
            for directory in directories:
                directory.mkdir(exist_ok=True)
                self.logger.info(f"📁 Directorio creado/verificado: {directory}")
            
            # Crear archivos de configuración si no existen
            config_files = [
                "data/dominios.csv",
                "data/diccionario.txt"
            ]
            
            for config_file in config_files:
                file_path = Path(config_file)
                if not file_path.exists():
                    self._create_sample_file(file_path)
            
            # Verificar dependencias
            self._check_dependencies()
            
            self.logger.info("✅ Entorno configurado correctamente")
            
        except Exception as e:
            self.logger.error(f"❌ Error configurando entorno: {e}")
            raise
    
    def _create_sample_file(self, file_path: Path):
        """Crear archivo de muestra"""
        file_path.parent.mkdir(parents=True, exist_ok=True)
        
        if file_path.name == "dominios.csv":
            content = """# Archivo de dominios para fuzzing
                    # Formato: https://dominio o dominio:puerto
                    # IMPORTANTE: Solo use dominios propios o con autorización

                    # Dominios de prueba seguros
                    https://httpbin.org
                    https://jsonplaceholder.typicode.com

                    # Ejemplos para dominios reales:
                    # https://miempresa.com
                    # https://app.miempresa.com
                    # miempresa.com:8080
                    """
        elif file_path.name == "diccionario.txt":
            content = """# Diccionario de rutas para fuzzing
                        admin
                        login
                        panel
                        test
                        api
                        backup
                        config.php
                        robots.txt
                        sitemap.xml
                        .git
                        wp-admin
                        phpmyadmin
                        database
                        private
                        secret
                        """
        else:
            content = "# Archivo de configuración\n"
        
        with open(file_path, 'w', encoding='utf-8') as f:
            f.write(content)
        
        self.logger.info(f"📄 Archivo de muestra creado: {file_path}")
    
    def _check_dependencies(self):
        """Verificar dependencias del sistema"""
        self.logger.info("🔍 Verificando dependencias...")
        
        required_modules = [
            'requests', 'flask', 'yaml', 'pandas', 'plotly', 'psutil'
        ]
        
        missing = []
        for module in required_modules:
            try:
                __import__(module)
            except ImportError:
                missing.append(module)
        
        if missing:
            self.logger.warning(f"⚠️  Módulos faltantes: {', '.join(missing)}")
            self.logger.info(f"💡 Instalar con: pip install {' '.join(missing)}")
        else:
            self.logger.info("✅ Todas las dependencias están disponibles")

def main():
    """Función principal del script"""
    parser = argparse.ArgumentParser(
        description='Sistema de Automatización y Orquestación Inteligente v2.0',
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
Ejemplos de uso:
  python main.py --setup                 # Configurar entorno inicial
  python main.py --start                 # Iniciar sistema interactivo
  python main.py --daemon                # Ejecutar como daemon
  python main.py --task full_scan        # Ejecutar escaneo completo
  python main.py --task quick_scan       # Ejecutar escaneo rápido
  python main.py --status               # Mostrar estado del sistema
  python main.py --config               # Validar configuración
  
Variables de entorno importantes:
  TELEGRAM_BOT_TOKEN                     # Token del bot de Telegram
  TELEGRAM_CHAT_ID_SECURITY             # ID del chat de seguridad
        """
    )
    
    # Argumentos principales
    parser.add_argument('--setup', action='store_true',
                       help='Configurar entorno inicial del sistema')
    parser.add_argument('--start', action='store_true',
                       help='Iniciar sistema interactivo')
    parser.add_argument('--daemon', action='store_true',
                       help='Ejecutar como daemon en segundo plano')
    parser.add_argument('--task', type=str,
                       help='Ejecutar tarea específica')
    parser.add_argument('--status', action='store_true',
                       help='Mostrar estado del sistema')
    parser.add_argument('--config', action='store_true',
                       help='Validar configuración')
    
    # Argumentos de configuración
    parser.add_argument('--config-file', default='automation_config.yaml',
                       help='Archivo de configuración (default: automation_config.yaml)')
    parser.add_argument('--log-level', choices=['DEBUG', 'INFO', 'WARNING', 'ERROR'],
                       default='INFO', help='Nivel de logging')
    parser.add_argument('--dry-run', action='store_true',
                       help='Modo de prueba sin ejecutar acciones reales')
    
    args = parser.parse_args()
    
    # Crear orquestador principal
    orchestrator = MainSystemOrchestrator(args.config_file)
    
    try:
        if args.setup:
            orchestrator.setup_environment()
            
        elif args.config:
            orchestrator.validate_configuration()
            
        elif args.status:
            asyncio.run(orchestrator.show_system_status())
            
        elif args.task:
            asyncio.run(orchestrator.execute_manual_task(args.task))
            
        elif args.start:
            print("🤖 Iniciando Sistema de Automatización Inteligente...")
            print("📊 Características:")
            print("   • Fuzzing automatizado y programado")
            print("   • Orquestación inteligente con ML")
            print("   • Análisis de alertas en tiempo real")
            print("   • Dashboard web integrado")
            print("   • Generación automática de reportes")
            print("   • Escalado automático de recursos")
            print("")
            print("🔗 Dashboard web: http://localhost:5000")
            print("⏹️  Para detener: Ctrl+C")
            print("")
            
            asyncio.run(orchestrator.run_daemon())
            
        elif args.daemon:
            print("🔄 Ejecutando como daemon...")
            asyncio.run(orchestrator.run_daemon())
            
        else:
            parser.print_help()
            print("\n💡 Recomendación: Comience con --setup para configurar el entorno")
    
    except KeyboardInterrupt:
        print("\n🛑 Proceso interrumpido por el usuario")
    except Exception as e:
        print(f"\n❌ Error: {e}")
        sys.exit(1)

if __name__ == "__main__":
    main()