#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Orquestador Inteligente
Sistema avanzado de orquestación con IA, aprendizaje automático y optimización adaptativa
"""

import asyncio
import sqlite3
import json
import time
import logging
import threading
import psutil
import os
from datetime import datetime, timedelta
from pathlib import Path
from typing import Dict, List, Optional, Callable, Any
from dataclasses import dataclass, field
from enum import Enum
from concurrent.futures import ThreadPoolExecutor, as_completed
import yaml
import hashlib

try:
    import pandas as pd
    PANDAS_AVAILABLE = True
except ImportError:
    PANDAS_AVAILABLE = False

class TaskPriority(Enum):
    """Prioridades de tareas"""
    CRITICAL = 1
    HIGH = 2
    MEDIUM = 3
    LOW = 4

class TaskStatus(Enum):
    """Estados de tareas"""
    PENDING = "pending"
    RUNNING = "running"
    COMPLETED = "completed"
    FAILED = "failed"
    CANCELLED = "cancelled"
    RETRYING = "retrying"

@dataclass
class Task:
    """Definición completa de tarea"""
    id: str
    name: str
    function: Callable
    args: tuple = field(default_factory=tuple)
    kwargs: dict = field(default_factory=dict)
    priority: TaskPriority = TaskPriority.MEDIUM
    max_retries: int = 3
    timeout: int = 3600
    dependencies: List[str] = field(default_factory=list)
    conditions: Dict[str, Any] = field(default_factory=dict)
    metadata: Dict[str, Any] = field(default_factory=dict)
    created_at: datetime = field(default_factory=datetime.now)
    
    def __post_init__(self):
        if isinstance(self.priority, str):
            self.priority = TaskPriority[self.priority.upper()]

@dataclass
class TaskExecution:
    """Información de ejecución de tarea"""
    task_id: str
    task_name: str
    status: TaskStatus = TaskStatus.PENDING
    started_at: Optional[datetime] = None
    completed_at: Optional[datetime] = None
    duration: Optional[float] = None
    result: Any = None
    error: Optional[str] = None
    retries: int = 0
    resource_usage: Dict[str, float] = field(default_factory=dict)
    worker_id: Optional[str] = None

class IntelligentOrchestrator:
    """
    Orquestador inteligente con capacidades avanzadas de ML y optimización
    """
    
    def __init__(self, config_file: str = "automation_config.yaml", 
                 fuzzing_engine=None, alert_system=None, notification_manager=None):
        """
        Inicializar orquestador inteligente
        
        Args:
            config_file: Archivo de configuración YAML
            fuzzing_engine: Motor de fuzzing
            alert_system: Sistema de alertas
            notification_manager: Gestor de notificaciones
        """
        self.config_file = Path(config_file)
        self.logger = logging.getLogger(__name__)
        
        # Componentes externos
        self.fuzzing_engine = fuzzing_engine
        self.alert_system = alert_system
        self.notification_manager = notification_manager
        
        # Estado del orquestador
        self.is_running = False
        self.task_queue = asyncio.Queue()
        self.running_tasks = {}
        self.completed_tasks = []
        
        # Sistema de aprendizaje
        self.adaptive_learning = {}
        self.performance_metrics = {}
        self.optimization_data = {}
        
        # Configuración
        self.config = self.load_config()
        self.max_concurrent_tasks = self.config.get('max_concurrent_tasks', 5)
        self.health_check_interval = self.config.get('health_check_interval', 300)
        
        # Base de datos para persistencia
        self.db_path = Path("data/orchestrator.db")
        self.init_database()
        
        # Executor para tareas
        self.executor = ThreadPoolExecutor(max_workers=self.max_concurrent_tasks)
        
        # Métricas del sistema
        self.system_metrics = {}
        self.last_health_check = datetime.now()
        
        # Tareas registradas
        self.registered_tasks = {}
        self.register_default_tasks()
        
        self.logger.info("Orquestador inteligente inicializado")
    
    def load_config(self) -> Dict:
        """Cargar configuración de automatización"""
        default_config = {
            'max_concurrent_tasks': 5,
            'health_check_interval': 300,
            'auto_scaling': True,
            'intelligent_scheduling': True,
            'resource_monitoring': True,
            'adaptive_learning': {
                'enabled': True,
                'learning_period_days': 7,
                'optimization_targets': ['response_time', 'resource_usage', 'success_rate']
            },
            'resource_limits': {
                'cpu_threshold': 0.8,
                'memory_threshold': 0.85,
                'disk_threshold': 0.9
            },
            'task_priorities': {
                'security_scan': 'high',
                'vulnerability_scan': 'critical',
                'report_generation': 'medium',
                'model_training': 'low',
                'health_check': 'low',
                'cleanup': 'low'
            }
        }
        
        if self.config_file.exists():
            try:
                with open(self.config_file, 'r', encoding='utf-8') as f:
                    loaded_config = yaml.safe_load(f)
                    if loaded_config:
                        default_config.update(loaded_config)
            except Exception as e:
                self.logger.error(f"Error cargando configuración: {e}")
        else:
            # Crear archivo de configuración por defecto
            self.config_file.parent.mkdir(parents=True, exist_ok=True)
            with open(self.config_file, 'w', encoding='utf-8') as f:
                yaml.dump(default_config, f, default_flow_style=False, indent=2)
            self.logger.info(f"Archivo de configuración creado: {self.config_file}")
        
        return default_config
    
    def init_database(self):
        """Inicializar base de datos del orquestador"""
        self.db_path.parent.mkdir(parents=True, exist_ok=True)
        
        with sqlite3.connect(self.db_path) as conn:
            cursor = conn.cursor()
            
            # Tabla de ejecuciones de tareas
            cursor.execute('''
                CREATE TABLE IF NOT EXISTS task_executions (
                    id TEXT PRIMARY KEY,
                    task_name TEXT NOT NULL,
                    status TEXT NOT NULL,
                    started_at DATETIME,
                    completed_at DATETIME,
                    duration_seconds REAL,
                    success_rate REAL,
                    error_message TEXT,
                    resource_usage TEXT,
                    worker_id TEXT,
                    metadata TEXT,
                    created_at DATETIME DEFAULT CURRENT_TIMESTAMP
                )
            ''')
            
            # Tabla de métricas del sistema
            cursor.execute('''
                CREATE TABLE IF NOT EXISTS system_metrics (
                    timestamp DATETIME PRIMARY KEY,
                    cpu_usage REAL,
                    memory_usage REAL,
                    disk_usage REAL,
                    network_io TEXT,
                    active_tasks INTEGER,
                    queue_size INTEGER,
                    response_time REAL,
                    health_score REAL
                )
            ''')
            
            # Tabla de aprendizaje adaptativo
            cursor.execute('''
                CREATE TABLE IF NOT EXISTS adaptive_learning (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    date DATE,
                    hour INTEGER,
                    task_type TEXT,
                    success_rate REAL,
                    avg_duration REAL,
                    avg_cpu_usage REAL,
                    avg_memory_usage REAL,
                    optimal_conditions TEXT,
                    created_at DATETIME DEFAULT CURRENT_TIMESTAMP
                )
            ''')
            
            # Tabla de optimizaciones
            cursor.execute('''
                CREATE TABLE IF NOT EXISTS optimizations (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    optimization_type TEXT,
                    target_metric TEXT,
                    before_value REAL,
                    after_value REAL,
                    improvement_percent REAL,
                    config_changes TEXT,
                    applied_at DATETIME DEFAULT CURRENT_TIMESTAMP
                )
            ''')
            
            # Crear índices para optimizar consultas
            indexes = [
                "CREATE INDEX IF NOT EXISTS idx_task_executions_name ON task_executions(task_name)",
                "CREATE INDEX IF NOT EXISTS idx_task_executions_status ON task_executions(status)",
                "CREATE INDEX IF NOT EXISTS idx_task_executions_date ON task_executions(started_at)",
                "CREATE INDEX IF NOT EXISTS idx_adaptive_learning_date ON adaptive_learning(date, hour)",
                "CREATE INDEX IF NOT EXISTS idx_system_metrics_timestamp ON system_metrics(timestamp)"
            ]
            
            for index_sql in indexes:
                cursor.execute(index_sql)
            
            conn.commit()
    
    def register_default_tasks(self):
        """Registrar tareas por defecto del sistema"""
        default_tasks = {
            'full_scan': {
                'function': self._run_full_scan,
                'priority': 'high',
                'timeout': 7200,
                'max_retries': 2
            },
            'quick_scan': {
                'function': self._run_quick_scan,
                'priority': 'medium',
                'timeout': 1800,
                'max_retries': 3
            },
            'vulnerability_scan': {
                'function': self._run_vulnerability_scan,
                'priority': 'critical',
                'timeout': 10800,
                'max_retries': 1
            },
            'subdomain_discovery': {
                'function': self._run_subdomain_discovery,
                'priority': 'medium',
                'timeout': 3600,
                'max_retries': 2
            },
            'model_training': {
                'function': self._run_model_training,
                'priority': 'low',
                'timeout': 3600,
                'max_retries': 1
            },
            'report_generation': {
                'function': self._run_report_generation,
                'priority': 'medium',
                'timeout': 600,
                'max_retries': 2
            },
            'health_check': {
                'function': self._run_health_check,
                'priority': 'low',
                'timeout': 300,
                'max_retries': 1
            },
            'cleanup_tasks': {
                'function': self._run_cleanup_tasks,
                'priority': 'low',
                'timeout': 1800,
                'max_retries': 1
            },
            'backup_data': {
                'function': self._run_backup_data,
                'priority': 'medium',
                'timeout': 3600,
                'max_retries': 1
            }
        }
        
        for task_name, config in default_tasks.items():
            self.register_task(task_name, **config)
    
    def register_task(self, name: str, function: Callable, priority: str = 'medium', 
                     timeout: int = 3600, max_retries: int = 3, 
                     dependencies: List[str] = None, conditions: Dict = None):
        """Registrar nueva tarea en el orquestador"""
        task_id = f"{name}_{int(time.time())}_{hashlib.md5(name.encode()).hexdigest()[:8]}"
        
        task = Task(
            id=task_id,
            name=name,
            function=function,
            priority=TaskPriority[priority.upper()],
            timeout=timeout,
            max_retries=max_retries,
            dependencies=dependencies or [],
            conditions=conditions or {}
        )
        
        self.registered_tasks[name] = task
        self.logger.info(f"Tarea registrada: {name} (Prioridad: {priority})")
    
    def schedule_task(self, task_name: str, delay: int = 0, priority: Optional[str] = None, 
                     conditions: Optional[Dict] = None, **kwargs) -> str:
        """
        Programar tarea para ejecución
        
        Args:
            task_name: Nombre de la tarea registrada
            delay: Retraso en segundos
            priority: Prioridad opcional (sobrescribe la predeterminada)
            conditions: Condiciones adicionales
            **kwargs: Argumentos para la tarea
            
        Returns:
            str: ID de la ejecución de la tarea
        """
        if task_name not in self.registered_tasks:
            raise ValueError(f"Tarea '{task_name}' no está registrada")
        
        base_task = self.registered_tasks[task_name]
        execution_id = f"exec_{task_name}_{int(time.time())}_{os.getpid()}"
        
        # Crear ejecución específica
        execution = TaskExecution(
            task_id=execution_id,
            task_name=task_name
        )
        
        # Aplicar configuración
        if priority:
            base_task.priority = TaskPriority[priority.upper()]
        
        if conditions:
            base_task.conditions.update(conditions)
        
        if kwargs:
            base_task.kwargs.update(kwargs)
        
        # Agregar a la cola
        if delay > 0:
            # Programar con retraso
            threading.Timer(delay, lambda: asyncio.create_task(
                self.task_queue.put((base_task, execution))
            )).start()
        else:
            # Agregar inmediatamente
            asyncio.create_task(self.task_queue.put((base_task, execution)))
        
        self.logger.info(f"Tarea '{task_name}' programada (ID: {execution_id}, Delay: {delay}s)")
        return execution_id
    
    async def execute_task(self, task: Task, execution: TaskExecution) -> TaskExecution:
        """Ejecutar tarea individual con monitoreo completo"""
        execution.started_at = datetime.now()
        execution.status = TaskStatus.RUNNING
        
        self.running_tasks[execution.task_id] = execution
        
        try:
            # Verificar condiciones previas
            if not await self._check_task_conditions(task):
                execution.status = TaskStatus.CANCELLED
                execution.error = "Conditions not met"
                execution.completed_at = datetime.now()
                return execution
            
            # Verificar dependencias
            if not await self._check_dependencies(task):
                execution.status = TaskStatus.CANCELLED
                execution.error = "Dependencies not satisfied"
                execution.completed_at = datetime.now()
                return execution
            
            # Monitorear recursos antes de la ejecución
            initial_resources = self._get_system_resources()
            
            self.logger.info(f"Ejecutando tarea: {task.name} (ID: {execution.task_id})")
            
            # Ejecutar la función de la tarea con timeout
            loop = asyncio.get_event_loop()
            start_time = time.time()
            
            try:
                result = await asyncio.wait_for(
                    loop.run_in_executor(self.executor, task.function, *task.args, **task.kwargs),
                    timeout=task.timeout
                )
                
                execution.result = result
                execution.status = TaskStatus.COMPLETED
                
            except asyncio.TimeoutError:
                execution.error = f"Timeout after {task.timeout} seconds"
                execution.status = TaskStatus.FAILED
            except Exception as e:
                execution.error = str(e)
                execution.status = TaskStatus.FAILED
                
                # Reintentar si es necesario
                if execution.retries < task.max_retries:
                    execution.retries += 1
                    execution.status = TaskStatus.RETRYING
                    self.logger.warning(f"Reintentando tarea {task.name} (intento {execution.retries})")
                    
                    # Esperar antes de reintentar (backoff exponencial)
                    await asyncio.sleep(2 ** execution.retries)
                    return await self.execute_task(task, execution)
            
            # Calcular métricas finales
            end_time = time.time()
            execution.duration = end_time - start_time
            execution.completed_at = datetime.now()
            
            # Monitorear recursos después de la ejecución
            final_resources = self._get_system_resources()
            execution.resource_usage = {
                'cpu_delta': final_resources['cpu'] - initial_resources['cpu'],
                'memory_delta': final_resources['memory'] - initial_resources['memory'],
                'duration': execution.duration,
                'peak_cpu': max(initial_resources['cpu'], final_resources['cpu']),
                'peak_memory': max(initial_resources['memory'], final_resources['memory'])
            }
            
            if execution.status == TaskStatus.COMPLETED:
                self.logger.info(f"Tarea completada: {task.name} ({execution.duration:.2f}s)")
            else:
                self.logger.error(f"Tarea falló: {task.name} - {execution.error}")
            
        except Exception as e:
            execution.status = TaskStatus.FAILED
            execution.error = f"Unexpected error: {str(e)}"
            execution.completed_at = datetime.now()
            self.logger.error(f"Error inesperado ejecutando {task.name}: {e}")
        
        finally:
            # Limpiar tarea en ejecución
            if execution.task_id in self.running_tasks:
                del self.running_tasks[execution.task_id]
            
            # Guardar en historial
            self.completed_tasks.append(execution)
            await self._save_task_execution(execution)
            
            # Actualizar datos de aprendizaje adaptativo
            if self.config.get('adaptive_learning', {}).get('enabled'):
                await self._update_adaptive_learning(execution)
        
        return execution
    
    async def _check_task_conditions(self, task: Task) -> bool:
        """Verificar condiciones para ejecutar tarea"""
        if not task.conditions:
            return True
        
        system_resources = self._get_system_resources()
        
        # Verificar límites de recursos
        resource_limits = self.config.get('resource_limits', {})
        
        if system_resources['cpu'] / 100.0 > resource_limits.get('cpu_threshold', 0.8):
            self.logger.warning(f"CPU usage too high: {system_resources['cpu']}%")
            return False
        
        if system_resources['memory'] > resource_limits.get('memory_threshold', 0.85):
            self.logger.warning(f"Memory usage too high: {system_resources['memory']*100:.1f}%")
            return False
        
        # Verificar condiciones específicas de la tarea
        max_load = task.conditions.get('max_system_load', 1.0)
        if system_resources['cpu'] / 100.0 > max_load:
            return False
        
        allowed_hours = task.conditions.get('allowed_hours')
        if allowed_hours:
            current_hour = datetime.now().hour
            if current_hour not in allowed_hours:
                return False
        
        # Verificar alertas críticas
        max_critical = task.conditions.get('max_critical_alerts')
        if max_critical:
            critical_count = self._get_critical_alerts_count()
            if critical_count > max_critical:
                return False
        
        return True
    
    async def _check_dependencies(self, task: Task) -> bool:
        """Verificar que las dependencias estén satisfechas"""
        if not task.dependencies:
            return True
        
        for dep_task_name in task.dependencies:
            if not await self._is_dependency_satisfied(dep_task_name):
                self.logger.warning(f"Dependency not satisfied: {dep_task_name}")
                return False
        
        return True
    
    async def _is_dependency_satisfied(self, task_name: str, hours_back: int = 24) -> bool:
        """Verificar si una dependencia fue satisfecha recientemente"""
        try:
            with sqlite3.connect(self.db_path) as conn:
                cursor = conn.cursor()
                
                cursor.execute('''
                    SELECT status FROM task_executions 
                    WHERE task_name = ? AND started_at > datetime('now', '-{} hours')
                    AND status = ?
                    ORDER BY started_at DESC LIMIT 1
                '''.format(hours_back), (task_name, TaskStatus.COMPLETED.value))
                
                result = cursor.fetchone()
                return result is not None
                
        except Exception as e:
            self.logger.error(f"Error verificando dependencia {task_name}: {e}")
            return False
    
    def _get_system_resources(self) -> Dict[str, float]:
        """Obtener métricas actuales de recursos del sistema"""
        try:
            cpu_percent = psutil.cpu_percent(interval=1)
            memory = psutil.virtual_memory()
            disk = psutil.disk_usage('/')
            
            # Métricas de red
            net_io = psutil.net_io_counters()
            
            resources = {
                'cpu': cpu_percent,
                'memory': memory.percent / 100.0,
                'disk': disk.percent / 100.0,
                'available_memory_gb': memory.available / (1024**3),
                'network_bytes_sent': net_io.bytes_sent,
                'network_bytes_recv': net_io.bytes_recv,
                'load_avg': os.getloadavg()[0] if hasattr(os, 'getloadavg') else 0,
                'timestamp': time.time()
            }
            
            # Actualizar métricas del sistema
            self.system_metrics = resources
            
            return resources
            
        except Exception as e:
            self.logger.error(f"Error obteniendo recursos del sistema: {e}")
            return {
                'cpu': 0, 'memory': 0, 'disk': 0, 
                'available_memory_gb': 0, 'load_avg': 0,
                'network_bytes_sent': 0, 'network_bytes_recv': 0,
                'timestamp': time.time()
            }
    
    def _get_critical_alerts_count(self) -> int:
        """Obtener número de alertas críticas pendientes"""
        try:
            if self.fuzzing_engine and hasattr(self.fuzzing_engine, 'config'):
                db_path = self.fuzzing_engine.config.DATABASE_FILE
                with sqlite3.connect(db_path) as conn:
                    cursor = conn.cursor()
                    cursor.execute("""
                        SELECT COUNT(*) FROM alertas 
                        WHERE estado = 'pendiente' AND tipo_alerta = 'critica'
                    """)
                    return cursor.fetchone()[0]
        except Exception as e:
            self.logger.error(f"Error obteniendo alertas críticas: {e}")
        
        return 0
    
    async def _save_task_execution(self, execution: TaskExecution):
        """Guardar ejecución de tarea en base de datos"""
        try:
            with sqlite3.connect(self.db_path) as conn:
                cursor = conn.cursor()
                
                success_rate = 1.0 if execution.status == TaskStatus.COMPLETED else 0.0
                
                cursor.execute('''
                    INSERT INTO task_executions
                    (id, task_name, status, started_at, completed_at, duration_seconds, 
                     success_rate, error_message, resource_usage, worker_id, metadata)
                    VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
                ''', (
                    execution.task_id,
                    execution.task_name,
                    execution.status.value,
                    execution.started_at.isoformat() if execution.started_at else None,
                    execution.completed_at.isoformat() if execution.completed_at else None,
                    execution.duration,
                    success_rate,
                    execution.error,
                    json.dumps(execution.resource_usage),
                    execution.worker_id,
                    json.dumps({'retries': execution.retries})
                ))
                
                conn.commit()
                
        except Exception as e:
            self.logger.error(f"Error guardando ejecución de tarea: {e}")
    
    async def _update_adaptive_learning(self, execution: TaskExecution):
        """Actualizar datos de aprendizaje adaptativo"""
        if not execution.started_at:
            return
        
        try:
            with sqlite3.connect(self.db_path) as conn:
                cursor = conn.cursor()
                
                success_rate = 1.0 if execution.status == TaskStatus.COMPLETED else 0.0
                
                cursor.execute('''
                    INSERT INTO adaptive_learning
                    (date, hour, task_type, success_rate, avg_duration, 
                     avg_cpu_usage, avg_memory_usage, optimal_conditions)
                    VALUES (?, ?, ?, ?, ?, ?, ?, ?)
                ''', (
                    execution.started_at.date(),
                    execution.started_at.hour,
                    execution.task_name,
                    success_rate,
                    execution.duration or 0,
                    execution.resource_usage.get('peak_cpu', 0),
                    execution.resource_usage.get('peak_memory', 0),
                    json.dumps({
                        'system_load': self.system_metrics.get('cpu', 0),
                        'available_memory': self.system_metrics.get('available_memory_gb', 0)
                    })
                ))
                
                conn.commit()
                
        except Exception as e:
            self.logger.error(f"Error actualizando aprendizaje adaptativo: {e}")
    
    async def task_processor(self):
        """Procesador principal de tareas"""
        self.logger.info("Procesador de tareas iniciado")
        
        while self.is_running:
            try:
                # Obtener tarea de la cola con timeout
                task, execution = await asyncio.wait_for(
                    self.task_queue.get(), timeout=1.0
                )
                
                # Verificar si podemos ejecutar más tareas
                if len(self.running_tasks) >= self.max_concurrent_tasks:
                    # Devolver tarea a la cola
                    await self.task_queue.put((task, execution))
                    await asyncio.sleep(1)
                    continue
                
                # Ejecutar tarea en background
                asyncio.create_task(self.execute_task(task, execution))
                
            except asyncio.TimeoutError:
                # Normal - no hay tareas en cola
                continue
            except Exception as e:
                self.logger.error(f"Error en procesador de tareas: {e}")
                await asyncio.sleep(1)
    
    async def health_monitor(self):
        """Monitor de salud del sistema"""
        while self.is_running:
            try:
                await self._perform_health_check()
                await asyncio.sleep(self.health_check_interval)
            except Exception as e:
                self.logger.error(f"Error en monitor de salud: {e}")
                await asyncio.sleep(60)
    
    async def _perform_health_check(self):
        """Realizar verificación de salud del sistema"""
        resources = self._get_system_resources()
        
        # Calcular score de salud
        health_score = self._calculate_health_score(resources)
        
        # Guardar métricas
        await self._save_system_metrics(resources, health_score)
        
        # Auto-escalado si está habilitado
        if self.config.get('auto_scaling'):
            await self._auto_scale_system(resources, health_score)
        
        self.last_health_check = datetime.now()
    
    def _calculate_health_score(self, resources: Dict[str, float]) -> float:
        """Calcular score de salud del sistema (0-1)"""
        cpu_score = max(0, 1 - (resources['cpu'] / 100.0))
        memory_score = max(0, 1 - resources['memory'])
        disk_score = max(0, 1 - resources['disk'])
        
        # Penalizar si hay muchas tareas fallando
        failed_tasks_penalty = 0
        if self.completed_tasks:
            recent_tasks = [t for t in self.completed_tasks[-10:]]
            failed_count = len([t for t in recent_tasks if t.status == TaskStatus.FAILED])
            failed_tasks_penalty = failed_count / len(recent_tasks) * 0.3
        
        health_score = (cpu_score + memory_score + disk_score) / 3 - failed_tasks_penalty
        return max(0, min(1, health_score))
    
    async def _save_system_metrics(self, resources: Dict[str, float], health_score: float):
        """Guardar métricas del sistema"""
        try:
            with sqlite3.connect(self.db_path) as conn:
                cursor = conn.cursor()
                
                cursor.execute('''
                    INSERT INTO system_metrics
                    (timestamp, cpu_usage, memory_usage, disk_usage, network_io,
                     active_tasks, queue_size, health_score)
                    VALUES (?, ?, ?, ?, ?, ?, ?, ?)
                ''', (
                    datetime.now(),
                    resources['cpu'],
                    resources['memory'] * 100,
                    resources['disk'] * 100,
                    json.dumps({
                        'bytes_sent': resources['network_bytes_sent'],
                        'bytes_recv': resources['network_bytes_recv']
                    }),
                    len(self.running_tasks),
                    self.task_queue.qsize(),
                    health_score
                ))
                
                conn.commit()
                
        except Exception as e:
            self.logger.error(f"Error guardando métricas del sistema: {e}")
    
    async def _auto_scale_system(self, resources: Dict[str, float], health_score: float):
        """Auto-escalado del sistema basado en métricas"""
        current_workers = self.max_concurrent_tasks
        
        # Escalar hacia arriba si el sistema está saludable y hay cola
        if (health_score > 0.7 and 
            self.task_queue.qsize() > current_workers and 
            resources['cpu'] < 60 and 
            resources['memory'] < 0.7):
            
            new_workers = min(current_workers + 1, 10)
            if new_workers != current_workers:
                self.max_concurrent_tasks = new_workers
                self.logger.info(f"Auto-escalado hacia arriba: {current_workers} -> {new_workers} workers")
        
        # Escalar hacia abajo si el sistema está sobrecargado
        elif (health_score < 0.4 or 
              resources['cpu'] > 80 or 
              resources['memory'] > 0.8):
            
            new_workers = max(current_workers - 1, 2)
            if new_workers != current_workers:
                self.max_concurrent_tasks = new_workers
                self.logger.info(f"Auto-escalado hacia abajo: {current_workers} -> {new_workers} workers")
    
    # Métodos de tareas específicas
    
    def _run_full_scan(self, *args, **kwargs) -> Dict:
        """Ejecutar escaneo completo de fuzzing"""
        if not self.fuzzing_engine:
            raise Exception("Fuzzing engine no disponible")
        
        start_time = time.time()
        findings = self.fuzzing_engine.run_comprehensive_scan()
        duration = time.time() - start_time
        
        critical_findings = [f for f in findings if f.get('is_critical')]
        
        result = {
            'scan_type': 'full',
            'total_findings': len(findings),
            'critical_findings': len(critical_findings),
            'duration': duration,
            'success': True
        }
        
        # Generar alertas si hay hallazgos críticos
        if critical_findings and self.alert_system:
            alerts = self.alert_system.generate_intelligent_alerts(critical_findings)
            result['alerts_generated'] = len(alerts)
        
        return result
    
    def _run_quick_scan(self, *args, **kwargs) -> Dict:
        """Ejecutar escaneo rápido"""
        # Simular escaneo rápido
        time.sleep(10)
        
        return {
            'scan_type': 'quick',
            'domains_scanned': 3,
            'paths_tested': 50,
            'findings': 2,
            'duration': 10,
            'success': True
        }
    
    def _run_vulnerability_scan(self, *args, **kwargs) -> Dict:
        """Ejecutar escaneo de vulnerabilidades avanzado"""
        time.sleep(30)  # Simular trabajo intensivo
        
        return {
            'scan_type': 'vulnerability',
            'vulnerabilities_found': 5,
            'critical_vulns': 1,
            'duration': 30,
            'success': True
        }
    
    def _run_subdomain_discovery(self, *args, **kwargs) -> Dict:
        """Ejecutar descubrimiento de subdominios"""
        time.sleep(15)
        
        return {
            'scan_type': 'subdomain_discovery',
            'subdomains_found': 12,
            'new_subdomains': 3,
            'duration': 15,
            'success': True
        }
    
    def _run_model_training(self, *args, **kwargs) -> Dict:
        """Ejecutar entrenamiento de modelos ML"""
        if not self.alert_system:
            raise Exception("Alert system no disponible")
        
        start_time = time.time()
        
        # Simular entrenamiento
        time.sleep(45)
        
        duration = time.time() - start_time
        
        return {
            'training_completed': True,
            'duration': duration,
            'models_updated': ['anomaly_detector', 'priority_classifier'],
            'success': True
        }
    
    def _run_report_generation(self, *args, **kwargs) -> Dict:
        """Generar reportes automáticos"""
        start_time = time.time()
        
        # Simular generación de reporte
        time.sleep(5)
        
        return {
            'report_generated': True,
            'format': 'html',
            'duration': time.time() - start_time,
            'size_mb': 2.5,
            'success': True
        }
    
    def _run_health_check(self, *args, **kwargs) -> Dict:
        """Ejecutar verificación de salud"""
        resources = self._get_system_resources()
        health_score = self._calculate_health_score(resources)
        
        components_status = {
            'database': self._check_database_health(),
            'fuzzing_engine': self.fuzzing_engine is not None,
            'alert_system': self.alert_system is not None,
            'notification_manager': self.notification_manager is not None,
            'task_processor': self.is_running
        }
        
        return {
            'health_score': health_score,
            'components_status': components_status,
            'system_metrics': resources,
            'recommendations': self._generate_health_recommendations(resources, health_score),
            'success': True
        }
    
    def _run_cleanup_tasks(self, *args, **kwargs) -> Dict:
        """Ejecutar tareas de limpieza"""
        cleaned_items = 0
        
        try:
            # Limpiar logs antiguos
            logs_dir = Path("logs")
            if logs_dir.exists():
                for log_file in logs_dir.glob("*.log"):
                    if log_file.stat().st_mtime < time.time() - (7 * 24 * 3600):  # 7 días
                        log_file.unlink()
                        cleaned_items += 1
            
            # Limpiar datos antiguos de la base de datos
            with sqlite3.connect(self.db_path) as conn:
                cursor = conn.cursor()
                
                # Eliminar métricas de más de 30 días
                cursor.execute('''
                    DELETE FROM system_metrics 
                    WHERE timestamp < datetime('now', '-30 days')
                ''')
                cleaned_items += cursor.rowcount
                
                # Eliminar ejecuciones de tareas de más de 60 días
                cursor.execute('''
                    DELETE FROM task_executions 
                    WHERE started_at < datetime('now', '-60 days')
                ''')
                cleaned_items += cursor.rowcount
                
                conn.commit()
        
        except Exception as e:
            return {'success': False, 'error': str(e)}
        
        return {
            'cleaned_items': cleaned_items,
            'success': True
        }
    
    def _run_backup_data(self, *args, **kwargs) -> Dict:
        """Ejecutar backup de datos"""
        try:
            backup_dir = Path("backups")
            backup_dir.mkdir(exist_ok=True)
            
            timestamp = datetime.now().strftime('%Y%m%d_%H%M%S')
            backup_file = backup_dir / f"orchestrator_backup_{timestamp}.db"
            
            # Copiar base de datos
            import shutil
            shutil.copy2(self.db_path, backup_file)
            
            # Comprimir si es posible
            try:
                import gzip
                with open(backup_file, 'rb') as f_in:
                    with gzip.open(f"{backup_file}.gz", 'wb') as f_out:
                        f_out.writelines(f_in)
                backup_file.unlink()  # Eliminar original sin comprimir
                backup_file = f"{backup_file}.gz"
            except ImportError:
                pass
            
            file_size = Path(backup_file).stat().st_size / (1024 * 1024)  # MB
            
            return {
                'backup_created': True,
                'backup_file': str(backup_file),
                'size_mb': round(file_size, 2),
                'success': True
            }
            
        except Exception as e:
            return {'success': False, 'error': str(e)}
    
    def _check_database_health(self) -> bool:
        """Verificar salud de la base de datos"""
        try:
            with sqlite3.connect(self.db_path) as conn:
                cursor = conn.cursor()
                cursor.execute("SELECT 1")
                return True
        except:
            return False
    
    def _generate_health_recommendations(self, resources: Dict, health_score: float) -> List[str]:
        """Generar recomendaciones de salud del sistema"""
        recommendations = []
        
        if resources['cpu'] > 80:
            recommendations.append("CPU usage critical - reduce concurrent tasks or optimize workload")
        
        if resources['memory'] > 0.85:
            recommendations.append("Memory usage high - consider system restart or memory optimization")
        
        if resources['disk'] > 0.9:
            recommendations.append("Disk space critical - cleanup required immediately")
        
        if health_score < 0.5:
            recommendations.append("System health degraded - investigate failed components")
        
        if len(self.running_tasks) == 0 and self.task_queue.qsize() > 0:
            recommendations.append("Tasks queued but not processing - check task processor")
        
        return recommendations
    
    async def start(self):
        """Iniciar el orquestador inteligente"""
        self.is_running = True
        self.logger.info("🤖 Iniciando orquestador inteligente...")
        
        # Iniciar procesadores en background
        asyncio.create_task(self.task_processor())
        asyncio.create_task(self.health_monitor())
        
        self.logger.info("✅ Orquestador inteligente iniciado")
    
    async def stop(self):
        """Detener el orquestador"""
        self.is_running = False
        
        # Esperar a que terminen las tareas en ejecución
        if self.running_tasks:
            self.logger.info(f"Esperando {len(self.running_tasks)} tareas en ejecución...")
            await asyncio.sleep(5)  # Tiempo de gracia
        
        self.executor.shutdown(wait=True)
        self.logger.info("🛑 Orquestador detenido")
    
    def get_system_status(self) -> Dict:
        """Obtener estado completo del sistema"""
        return {
            'is_running': self.is_running,
            'active_tasks': len(self.running_tasks),
            'queue_size': self.task_queue.qsize(),
            'registered_tasks': len(self.registered_tasks),
            'max_concurrent_tasks': self.max_concurrent_tasks,
            'system_metrics': self.system_metrics,
            'last_health_check': self.last_health_check.isoformat(),
            'components_status': {
                'fuzzing_engine': self.fuzzing_engine is not None,
                'alert_system': self.alert_system is not None,
                'notification_manager': self.notification_manager is not None,
                'database': self._check_database_health()
            },
            'adaptive_learning_enabled': self.config.get('adaptive_learning', {}).get('enabled', False)
        }
    
    def get_task_history(self, limit: int = 100) -> List[Dict]:
        """Obtener historial de tareas ejecutadas"""
        try:
            with sqlite3.connect(self.db_path) as conn:
                cursor = conn.cursor()
                
                cursor.execute('''
                    SELECT task_name, status, started_at, completed_at, 
                           duration_seconds, error_message
                    FROM task_executions
                    ORDER BY started_at DESC
                    LIMIT ?
                ''', (limit,))
                
                results = cursor.fetchall()
                
                history = []
                for row in results:
                    history.append({
                        'task_name': row[0],
                        'status': row[1],
                        'started_at': row[2],
                        'completed_at': row[3],
                        'duration': row[4],
                        'error': row[5]
                    })
                
                return history
                
        except Exception as e:
            self.logger.error(f"Error obteniendo historial: {e}")
            return []
    
    def get_system_metrics(self) -> Dict:
        """Obtener métricas actuales del sistema"""
        return {
            'current_metrics': self.system_metrics,
            'task_statistics': {
                'running': len(self.running_tasks),
                'queued': self.task_queue.qsize(),
                'completed_today': len([
                    t for t in self.completed_tasks 
                    if t.completed_at and t.completed_at.date() == datetime.now().date()
                ])
            },
            'performance': {
                'avg_task_duration': self._calculate_avg_task_duration(),
                'success_rate': self._calculate_success_rate(),
                'system_health_score': self._calculate_health_score(self.system_metrics)
            }
        }
    
    def _calculate_avg_task_duration(self) -> float:
        """Calcular duración promedio de tareas"""
        completed_with_duration = [
            t for t in self.completed_tasks 
            if t.duration and t.status == TaskStatus.COMPLETED
        ]
        
        if not completed_with_duration:
            return 0.0
        
        total_duration = sum(t.duration for t in completed_with_duration)
        return total_duration / len(completed_with_duration)
    
    def _calculate_success_rate(self) -> float:
        """Calcular tasa de éxito de tareas"""
        if not self.completed_tasks:
            return 1.0
        
        successful = len([t for t in self.completed_tasks if t.status == TaskStatus.COMPLETED])
        return successful / len(self.completed_tasks)