# -*- coding: utf-8 -*-
#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Sistema de Automatización y Orquestación Inteligente
Módulo principal que coordina todos los componentes del sistema de fuzzing

Estructura:
- scheduler.py: Programador de tareas con horarios y condiciones
- orchestrator.py: Orquestador inteligente con ML y adaptación
- workers.py: Workers para ejecución de tareas específicas

Características principales:
- Programación inteligente con aprendizaje automático
- Gestión de recursos y dependencias
- Monitoreo continuo de salud del sistema
- Escalado automático basado en carga
- Integración completa con el sistema de fuzzing
"""

import logging
from pathlib import Path
from typing import Dict, List, Optional

from .scheduler import TaskScheduler
from .orchestrator import IntelligentOrchestrator
from .workers import WorkerManager, FuzzingWorker, AlertWorker, ReportWorker

__version__ = "2.0.0"
__author__ = "Security Automation Team"

# Configurar logging para el módulo
logger = logging.getLogger(__name__)

class AutomationSystem:
    """
    Sistema principal de automatización que coordina todos los componentes
    """
    
    def __init__(self, config_path: Optional[str] = None):
        """
        Inicializar sistema de automatización
        
        Args:
            config_path: Ruta al archivo de configuración YAML
        """
        self.config_path = config_path or "automation_config.yaml"
        self.logger = logging.getLogger(__name__)
        
        # Componentes principales
        self.scheduler = None
        self.orchestrator = None
        self.worker_manager = None
        
        # Estado del sistema
        self.is_initialized = False
        self.is_running = False
        
        # Configuración
        self.config = {}
        
        self.logger.info("Sistema de automatización inicializado")
    
    def initialize(self, fuzzing_engine=None, alert_system=None, notification_manager=None):
        """
        Inicializar todos los componentes del sistema
        
        Args:
            fuzzing_engine: Motor de fuzzing
            alert_system: Sistema de alertas
            notification_manager: Gestor de notificaciones
        """
        try:
            self.logger.info("Inicializando componentes del sistema...")
            
            # Inicializar orquestador inteligente
            self.orchestrator = IntelligentOrchestrator(
                config_file=self.config_path,
                fuzzing_engine=fuzzing_engine,
                alert_system=alert_system,
                notification_manager=notification_manager
            )
            
            # Inicializar programador de tareas
            self.scheduler = TaskScheduler(
                orchestrator=self.orchestrator,
                config=self.orchestrator.config
            )
            
            # Inicializar gestor de workers
            self.worker_manager = WorkerManager(
                orchestrator=self.orchestrator,
                max_workers=self.orchestrator.config.get('max_concurrent_tasks', 5)
            )
            
            # Registrar workers especializados
            self.worker_manager.register_worker('fuzzing', FuzzingWorker(fuzzing_engine))
            self.worker_manager.register_worker('alerts', AlertWorker(alert_system))
            self.worker_manager.register_worker('reports', ReportWorker(notification_manager))
            
            self.is_initialized = True
            self.logger.info("✅ Sistema de automatización inicializado correctamente")
            
        except Exception as e:
            self.logger.error(f"❌ Error inicializando sistema: {e}")
            raise
    
    async def start(self):
        """Iniciar el sistema completo"""
        if not self.is_initialized:
            raise RuntimeError("Sistema no inicializado. Ejecutar initialize() primero.")
        
        self.logger.info("🚀 Iniciando sistema de automatización...")
        
        try:
            # Iniciar componentes en orden
            await self.orchestrator.start()
            await self.scheduler.start()
            await self.worker_manager.start()
            
            self.is_running = True
            self.logger.info("✅ Sistema de automatización iniciado")
            
        except Exception as e:
            self.logger.error(f"❌ Error iniciando sistema: {e}")
            await self.stop()
            raise
    
    async def stop(self):
        """Detener el sistema completo"""
        self.logger.info("🛑 Deteniendo sistema de automatización...")
        
        try:
            if self.worker_manager:
                await self.worker_manager.stop()
            
            if self.scheduler:
                await self.scheduler.stop()
            
            if self.orchestrator:
                await self.orchestrator.stop()
            
            self.is_running = False
            self.logger.info("✅ Sistema detenido correctamente")
            
        except Exception as e:
            self.logger.error(f"❌ Error deteniendo sistema: {e}")
    
    def get_status(self) -> Dict:
        """Obtener estado completo del sistema"""
        status = {
            'initialized': self.is_initialized,
            'running': self.is_running,
            'version': __version__
        }
        
        if self.orchestrator:
            status['orchestrator'] = self.orchestrator.get_system_status()
        
        if self.scheduler:
            status['scheduler'] = self.scheduler.get_status()
        
        if self.worker_manager:
            status['workers'] = self.worker_manager.get_status()
        
        return status
    
    def schedule_task(self, task_name: str, **kwargs):
        """Programar tarea manual"""
        if not self.scheduler:
            raise RuntimeError("Scheduler no disponible")
        
        return self.scheduler.schedule_manual_task(task_name, **kwargs)
    
    def get_task_history(self, limit: int = 100) -> List[Dict]:
        """Obtener historial de tareas"""
        if not self.orchestrator:
            raise RuntimeError("Orchestrator no disponible")
        
        return self.orchestrator.get_task_history(limit)
    
    def get_system_metrics(self) -> Dict:
        """Obtener métricas del sistema"""
        if not self.orchestrator:
            return {}
        
        return self.orchestrator.get_system_metrics()

# Funciones de conveniencia para importación directa
def create_automation_system(config_path: Optional[str] = None) -> AutomationSystem:
    """
    Crear nueva instancia del sistema de automatización
    
    Args:
        config_path: Ruta al archivo de configuración
        
    Returns:
        AutomationSystem: Instancia del sistema
    """
    return AutomationSystem(config_path)

def setup_logging(log_level: str = "INFO", log_file: Optional[str] = None):
    """
    Configurar logging para el sistema de automatización
    
    Args:
        log_level: Nivel de logging (DEBUG, INFO, WARNING, ERROR)
        log_file: Archivo de log opcional
    """
    handlers = [logging.StreamHandler()]
    
    if log_file:
        log_path = Path(log_file)
        log_path.parent.mkdir(parents=True, exist_ok=True)
        handlers.append(logging.FileHandler(log_file))
    
    logging.basicConfig(
        level=getattr(logging, log_level.upper()),
        format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
        handlers=handlers
    )

# Exportaciones principales
__all__ = [
    'AutomationSystem',
    'TaskScheduler',
    'IntelligentOrchestrator', 
    'WorkerManager',
    'FuzzingWorker',
    'AlertWorker',
    'ReportWorker',
    'create_automation_system',
    'setup_logging'
]