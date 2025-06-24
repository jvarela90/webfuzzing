#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Programador de Tareas Inteligente
Maneja la programación automática de tareas con horarios optimizados
"""

import asyncio
import logging
import schedule
import time
import subprocess
from datetime import datetime, timedelta
from pathlib import Path
from typing import Dict, List, Optional, Callable, Any
from dataclasses import dataclass
from enum import Enum
import crontab
import platform

class ScheduleType(Enum):
    """Tipos de programación"""
    IMMEDIATE = "immediate"
    CRON = "cron"
    INTERVAL = "interval"
    ADAPTIVE = "adaptive"
    CONDITIONAL = "conditional"

@dataclass
class ScheduledTask:
    """Definición de tarea programada"""
    id: str
    name: str
    schedule_type: ScheduleType
    pattern: str  # Cron pattern, interval string, etc.
    enabled: bool = True
    priority: str = "medium"
    conditions: Dict = None
    metadata: Dict = None
    last_run: Optional[datetime] = None
    next_run: Optional[datetime] = None
    run_count: int = 0
    
    def __post_init__(self):
        if self.conditions is None:
            self.conditions = {}
        if self.metadata is None:
            self.metadata = {}

class TaskScheduler:
    """
    Programador de tareas con funcionalidades avanzadas
    """
    
    def __init__(self, orchestrator=None, config: Dict = None):
        """
        Inicializar programador de tareas
        
        Args:
            orchestrator: Referencia al orquestador inteligente
            config: Configuración del sistema
        """
        self.orchestrator = orchestrator
        self.config = config or {}
        self.logger = logging.getLogger(__name__)
        
        # Estado del programador
        self.is_running = False
        self.scheduled_tasks = {}
        self.manual_tasks = []
        
        # Configuración de horarios por defecto
        self.default_schedules = {
            'full_scan': {
                'pattern': '0 8,13,18,23 * * *',  # 8 AM, 1 PM, 6 PM, 11 PM
                'priority': 'high',
                'enabled': True,
                'conditions': {'max_system_load': 0.8}
            },
            'quick_scan': {
                'pattern': '*/30 * * * *',  # Cada 30 minutos
                'priority': 'medium',
                'enabled': True,
                'conditions': {'max_system_load': 0.9}
            },
            'vulnerability_scan': {
                'pattern': '0 2 * * 0',  # Domingos a las 2 AM
                'priority': 'high',
                'enabled': True,
                'conditions': {'max_system_load': 0.5}
            },
            'subdomain_discovery': {
                'pattern': '0 */6 * * *',  # Cada 6 horas
                'priority': 'medium',
                'enabled': True,
                'conditions': {'max_system_load': 0.7}
            },
            'report_generation': {
                'pattern': '0 9,14 * * *',  # 9 AM y 2 PM
                'priority': 'medium',
                'enabled': True,
                'conditions': {}
            },
            'model_training': {
                'pattern': '0 2 * * 0',  # Domingos a las 2 AM
                'priority': 'low',
                'enabled': True,
                'conditions': {'max_system_load': 0.4, 'allowed_hours': [2, 3, 4]}
            },
            'health_check': {
                'pattern': '*/5 * * * *',  # Cada 5 minutos
                'priority': 'low',
                'enabled': True,
                'conditions': {}
            },
            'cleanup_tasks': {
                'pattern': '0 1 * * *',  # 1 AM diario
                'priority': 'low',
                'enabled': True,
                'conditions': {}
            },
            'backup_data': {
                'pattern': '0 0 * * 0',  # Domingos a medianoche
                'priority': 'medium',
                'enabled': True,
                'conditions': {'max_system_load': 0.3}
            }
        }
        
        # Configuración específica del sistema
        self.setup_system_specific_config()
        
        # Cargar programación desde configuración
        self.load_scheduled_tasks()
    
    def setup_system_specific_config(self):
        """Configurar horarios específicos según el sistema operativo"""
        system = platform.system().lower()
        
        if system == "windows":
            # Horarios más conservadores para Windows
            self.default_schedules['full_scan']['pattern'] = '0 9,14,18,22 * * *'
            self.default_schedules['quick_scan']['pattern'] = '*/45 * * * *'  # Cada 45 min
        elif system == "darwin":  # macOS
            # Horarios optimizados para macOS
            self.default_schedules['full_scan']['pattern'] = '0 8,13,17,22 * * *'
        
        self.logger.info(f"Configuración ajustada para {system}")
    
    def load_scheduled_tasks(self):
        """Cargar tareas programadas desde configuración"""
        # Combinar horarios por defecto con configuración personalizada
        schedules = self.config.get('schedules', {})
        
        for task_name, default_config in self.default_schedules.items():
            # Usar configuración personalizada si existe, sino usar por defecto
            task_config = schedules.get(task_name, default_config)
            
            # Crear tarea programada
            scheduled_task = ScheduledTask(
                id=f"scheduled_{task_name}",
                name=task_name,
                schedule_type=ScheduleType.CRON,
                pattern=task_config['pattern'],
                enabled=task_config.get('enabled', True),
                priority=task_config.get('priority', 'medium'),
                conditions=task_config.get('conditions', {}),
                metadata={'auto_generated': True}
            )
            
            self.scheduled_tasks[task_name] = scheduled_task
            
            if scheduled_task.enabled:
                self.register_cron_task(scheduled_task)
        
        self.logger.info(f"Cargadas {len(self.scheduled_tasks)} tareas programadas")
    
    def register_cron_task(self, task: ScheduledTask):
        """Registrar tarea con el scheduler de cron"""
        try:
            # Parsear patrón cron
            cron_parts = task.pattern.split()
            
            if len(cron_parts) == 5:
                minute, hour, day, month, weekday = cron_parts
                
                # Programar según el patrón
                if minute == "*/5":  # Cada 5 minutos
                    schedule.every(5).minutes.do(self._execute_scheduled_task, task.name)
                elif minute == "*/30":  # Cada 30 minutos
                    schedule.every(30).minutes.do(self._execute_scheduled_task, task.name)
                elif minute == "*/45":  # Cada 45 minutos
                    schedule.every(45).minutes.do(self._execute_scheduled_task, task.name)
                elif minute == "0" and hour != "*":  # Horarios específicos
                    hours = hour.split(',') if ',' in hour else [hour]
                    for h in hours:
                        if h.isdigit():
                            schedule.every().day.at(f"{h.zfill(2)}:00").do(
                                self._execute_scheduled_task, task.name
                            )
                elif minute == "0" and hour == "*/6":  # Cada 6 horas
                    schedule.every(6).hours.do(self._execute_scheduled_task, task.name)
                
                self.logger.debug(f"Tarea programada: {task.name} con patrón {task.pattern}")
            
        except Exception as e:
            self.logger.error(f"Error registrando tarea {task.name}: {e}")
    
    def _execute_scheduled_task(self, task_name: str):
        """Ejecutar tarea programada"""
        if not self.orchestrator:
            self.logger.error(f"No se puede ejecutar {task_name}: orchestrator no disponible")
            return
        
        task = self.scheduled_tasks.get(task_name)
        if not task:
            self.logger.error(f"Tarea {task_name} no encontrada")
            return
        
        # Verificar condiciones antes de ejecutar
        if not self._check_task_conditions(task):
            self.logger.info(f"Condiciones no cumplidas para {task_name}, saltando ejecución")
            return
        
        # Solicitar ejecución al orquestador
        try:
            self.orchestrator.schedule_task(
                task_name, 
                priority=task.priority,
                conditions=task.conditions
            )
            
            # Actualizar estadísticas de la tarea
            task.last_run = datetime.now()
            task.run_count += 1
            
            self.logger.info(f"Tarea {task_name} programada para ejecución")
            
        except Exception as e:
            self.logger.error(f"Error programando tarea {task_name}: {e}")
    
    def _check_task_conditions(self, task: ScheduledTask) -> bool:
        """Verificar condiciones para ejecutar tarea"""
        if not task.conditions:
            return True
        
        # Verificar carga del sistema si el orquestador está disponible
        if self.orchestrator:
            system_metrics = self.orchestrator._get_system_resources()
            
            max_load = task.conditions.get('max_system_load', 1.0)
            if system_metrics['cpu'] / 100.0 > max_load:
                return False
            
            # Verificar memoria
            max_memory = task.conditions.get('max_memory_usage', 1.0)
            if system_metrics['memory'] > max_memory:
                return False
        
        # Verificar horas permitidas
        allowed_hours = task.conditions.get('allowed_hours')
        if allowed_hours:
            current_hour = datetime.now().hour
            if current_hour not in allowed_hours:
                return False
        
        # Verificar alertas críticas
        max_critical = task.conditions.get('max_critical_alerts')
        if max_critical and self.orchestrator:
            critical_count = self.orchestrator._get_critical_alerts_count()
            if critical_count > max_critical:
                return False
        
        return True
    
    def schedule_manual_task(self, task_name: str, delay: int = 0, **kwargs) -> str:
        """
        Programar tarea manual para ejecución inmediata o con retraso
        
        Args:
            task_name: Nombre de la tarea
            delay: Retraso en segundos
            **kwargs: Argumentos adicionales para la tarea
            
        Returns:
            str: ID de la tarea programada
        """
        task_id = f"manual_{task_name}_{int(time.time())}"
        
        manual_task = {
            'id': task_id,
            'name': task_name,
            'scheduled_at': datetime.now(),
            'delay': delay,
            'kwargs': kwargs
        }
        
        self.manual_tasks.append(manual_task)
        
        if self.orchestrator:
            # Programar con el orquestador
            self.orchestrator.schedule_task(task_name, delay=delay, **kwargs)
            self.logger.info(f"Tarea manual {task_name} programada (ID: {task_id})")
        else:
            self.logger.warning(f"Orchestrator no disponible para tarea {task_name}")
        
        return task_id
    
    def enable_task(self, task_name: str):
        """Habilitar tarea programada"""
        if task_name in self.scheduled_tasks:
            self.scheduled_tasks[task_name].enabled = True
            self.register_cron_task(self.scheduled_tasks[task_name])
            self.logger.info(f"Tarea {task_name} habilitada")
        else:
            self.logger.error(f"Tarea {task_name} no encontrada")
    
    def disable_task(self, task_name: str):
        """Deshabilitar tarea programada"""
        if task_name in self.scheduled_tasks:
            self.scheduled_tasks[task_name].enabled = False
            # Remover del schedule (esto requiere una implementación más sofisticada)
            schedule.clear(task_name)
            self.logger.info(f"Tarea {task_name} deshabilitada")
        else:
            self.logger.error(f"Tarea {task_name} no encontrada")
    
    def update_task_schedule(self, task_name: str, new_pattern: str):
        """Actualizar patrón de horario de una tarea"""
        if task_name in self.scheduled_tasks:
            task = self.scheduled_tasks[task_name]
            old_pattern = task.pattern
            task.pattern = new_pattern
            
            # Re-registrar tarea
            schedule.clear(task_name)
            self.register_cron_task(task)
            
            self.logger.info(f"Horario de {task_name} actualizado: {old_pattern} -> {new_pattern}")
        else:
            self.logger.error(f"Tarea {task_name} no encontrada")
    
    def get_next_runs(self, hours_ahead: int = 24) -> List[Dict]:
        """Obtener próximas ejecuciones programadas"""
        next_runs = []
        current_time = datetime.now()
        end_time = current_time + timedelta(hours=hours_ahead)
        
        for task_name, task in self.scheduled_tasks.items():
            if not task.enabled:
                continue
            
            # Calcular próxima ejecución (simplificado)
            # En una implementación real usaríamos una librería como croniter
            try:
                next_run = self._calculate_next_run(task, current_time, end_time)
                if next_run:
                    next_runs.append({
                        'task_name': task_name,
                        'next_run': next_run,
                        'priority': task.priority,
                        'pattern': task.pattern
                    })
            except Exception as e:
                self.logger.error(f"Error calculando próxima ejecución para {task_name}: {e}")
        
        # Ordenar por tiempo de ejecución
        next_runs.sort(key=lambda x: x['next_run'])
        return next_runs
    
    def _calculate_next_run(self, task: ScheduledTask, start_time: datetime, end_time: datetime) -> Optional[datetime]:
        """Calcular próxima ejecución de una tarea (simplificado)"""
        # Esta es una implementación simplificada
        # En producción usarías croniter para parsing completo de cron
        
        pattern_parts = task.pattern.split()
        if len(pattern_parts) != 5:
            return None
        
        minute, hour, day, month, weekday = pattern_parts
        
        # Implementación básica para algunos patrones comunes
        if minute == "*/5":  # Cada 5 minutos
            next_time = start_time.replace(second=0, microsecond=0)
            next_time += timedelta(minutes=5 - (next_time.minute % 5))
            return next_time if next_time <= end_time else None
        
        elif minute == "*/30":  # Cada 30 minutos
            next_time = start_time.replace(second=0, microsecond=0)
            next_time += timedelta(minutes=30 - (next_time.minute % 30))
            return next_time if next_time <= end_time else None
        
        elif minute == "0" and hour != "*":  # Horarios específicos
            hours = hour.split(',') if ',' in hour else [hour]
            for h in hours:
                if h.isdigit():
                    next_time = start_time.replace(hour=int(h), minute=0, second=0, microsecond=0)
                    if next_time <= start_time:
                        next_time += timedelta(days=1)
                    if next_time <= end_time:
                        return next_time
        
        return None
    
    def setup_system_cron(self, install: bool = False) -> List[str]:
        """
        Generar y opcionalmente instalar trabajos de cron del sistema
        
        Args:
            install: Si True, instala automáticamente en crontab
            
        Returns:
            List[str]: Lista de líneas de cron generadas
        """
        script_path = Path(__file__).parent.parent / "main.py"
        script_path = script_path.resolve()
        
        cron_lines = [
            "# Sistema de Fuzzing Automatizado - Generado automáticamente",
            f"# Generado: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}",
            ""
        ]
        
        # Generar líneas de cron para tareas habilitadas
        for task_name, task in self.scheduled_tasks.items():
            if not task.enabled:
                continue
            
            log_file = f"/tmp/fuzzing_{task_name}.log"
            cron_line = f"{task.pattern} /usr/bin/python3 {script_path} --task {task_name} >> {log_file} 2>&1"
            cron_lines.append(f"# Tarea: {task_name} (Prioridad: {task.priority})")
            cron_lines.append(cron_line)
            cron_lines.append("")
        
        if install:
            try:
                self._install_cron_jobs(cron_lines)
                self.logger.info("✅ Trabajos de cron instalados correctamente")
            except Exception as e:
                self.logger.error(f"❌ Error instalando cron jobs: {e}")
        
        return cron_lines
    
    def _install_cron_jobs(self, cron_lines: List[str]):
        """Instalar trabajos de cron en el sistema"""
        # Obtener crontab actual
        try:
            result = subprocess.run(['crontab', '-l'], capture_output=True, text=True)
            current_cron = result.stdout if result.returncode == 0 else ""
        except subprocess.CalledProcessError:
            current_cron = ""
        
        # Filtrar líneas del sistema de fuzzing anterior
        filtered_lines = []
        skip_section = False
        
        for line in current_cron.split('\n'):
            if "Sistema de Fuzzing Automatizado" in line:
                skip_section = True
                continue
            elif skip_section and line.strip() == "":
                skip_section = False
                continue
            elif not skip_section:
                filtered_lines.append(line)
        
        # Combinar cron actual (filtrado) con nuevas líneas
        new_cron = '\n'.join(filtered_lines + cron_lines)
        
        # Instalar nueva crontab
        process = subprocess.Popen(['crontab', '-'], stdin=subprocess.PIPE, text=True)
        process.communicate(input=new_cron)
        
        if process.returncode != 0:
            raise Exception("Failed to install crontab")
    
    async def start(self):
        """Iniciar el programador de tareas"""
        self.is_running = True
        self.logger.info("🕐 Iniciando programador de tareas...")
        
        # Iniciar monitor de schedule en background
        asyncio.create_task(self._schedule_monitor())
        
        self.logger.info("✅ Programador de tareas iniciado")
    
    async def stop(self):
        """Detener el programador de tareas"""
        self.is_running = False
        schedule.clear()
        self.logger.info("🛑 Programador de tareas detenido")
    
    async def _schedule_monitor(self):
        """Monitor de horarios programados"""
        while self.is_running:
            try:
                schedule.run_pending()
                await asyncio.sleep(60)  # Verificar cada minuto
            except Exception as e:
                self.logger.error(f"Error en monitor de horarios: {e}")
                await asyncio.sleep(60)
    
    def get_status(self) -> Dict:
        """Obtener estado del programador"""
        enabled_tasks = sum(1 for task in self.scheduled_tasks.values() if task.enabled)
        
        return {
            'running': self.is_running,
            'total_scheduled_tasks': len(self.scheduled_tasks),
            'enabled_tasks': enabled_tasks,
            'manual_tasks_pending': len(self.manual_tasks),
            'next_runs': self.get_next_runs(6)  # Próximas 6 horas
        }
    
    def get_task_statistics(self) -> Dict:
        """Obtener estadísticas de ejecución de tareas"""
        stats = {}
        
        for task_name, task in self.scheduled_tasks.items():
            stats[task_name] = {
                'enabled': task.enabled,
                'pattern': task.pattern,
                'priority': task.priority,
                'run_count': task.run_count,
                'last_run': task.last_run.isoformat() if task.last_run else None,
                'conditions': task.conditions
            }
        
        return stats