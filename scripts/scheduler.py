# scripts/scheduler.py
import schedule
import time
import threading
from datetime import datetime, timedelta
import subprocess
import sys
from pathlib import Path

# Agregar el directorio raíz al path
sys.path.append(str(Path(__file__).parent.parent))

from config.settings import Config
from core.fuzzing_engine import FuzzingEngine
from utils.logger import get_logger
from utils.notifications import NotificationManager
from config.database import DatabaseManager

class TaskScheduler:
    """Programador de tareas para automatización del sistema"""
    
    def __init__(self, config: Config):
        self.config = config
        self.logger = get_logger(__name__)
        self.notifications = NotificationManager(config)
        self.db = DatabaseManager(config)
        self.fuzzing_engine = FuzzingEngine(config)
        
        # Estado del programador
        self.is_running = False
        self.scheduler_thread = None
        
        # Configurar horarios
        self._setup_schedules()
    
    def _setup_schedules(self):
        """Configurar horarios de ejecución"""
        # Escaneos generales en horarios específicos
        schedule.every().day.at("08:00").do(self._run_general_scan)
        schedule.every().day.at("13:00").do(self._run_general_scan)
        schedule.every().day.at("18:00").do(self._run_general_scan)
        schedule.every().day.at("23:00").do(self._run_general_scan)
        
        # Escaneo profundo semanal
        schedule.every().sunday.at("02:00").do(self._run_deep_scan)
        
        # Reportes sin novedades
        schedule.every().day.at("09:00").do(self._send_status_report)
        schedule.every().day.at("14:00").do(self._send_status_report)
        
        # Tareas de mantenimiento
        schedule.every().day.at("03:00").do(self._cleanup_old_data)
        schedule.every().hour.do(self._check_critical_alerts)
        
        # Backup de base de datos
        schedule.every().day.at("04:00").do(self._backup_database)
        
        self.logger.info("Horarios configurados correctamente")
    
    def _run_general_scan(self):
        """Ejecutar escaneo general"""
        try:
            self.logger.info("Iniciando escaneo general programado")
            
            # Verificar si es horario de trabajo
            current_hour = datetime.now().hour
            working_start = int(self.config.get('schedules.working_hours.start').split(':')[0])
            working_end = int(self.config.get('schedules.working_hours.end').split(':')[0])
            
            is_working_hours = working_start <= current_hour <= working_end
            
            # Ejecutar escaneo
            results = self.fuzzing_engine.run_scan()
            
            # Notificar resultados críticos inmediatamente
            if results['critical_found'] > 0:
                self.notifications.send_scan_report(results, results['results'])
                self.logger.warning(f"Escaneo encontró {results['critical_found']} hallazgos críticos")
            
            # Reporte completo solo en horarios de trabajo
            elif is_working_hours and results['paths_found'] > 0:
                self.notifications.send_scan_report(results, results['results'])
            
            self.logger.info(f"Escaneo general completado: {results['paths_found']} rutas encontradas")
            
        except Exception as e:
            self.logger.error(f"Error en escaneo general: {e}")
            self.notifications.send_email(
                "Error en Escaneo Programado",
                f"Error ejecutando escaneo general: {e}"
            )
    
    def _run_deep_scan(self):
        """Ejecutar escaneo profundo semanal"""
        try:
            self.logger.info("Iniciando escaneo profundo semanal")
            
            # Generar más rutas para escaneo profundo
            original_max_length = self.config.get('fuzzing.max_path_length')
            self.config.set('fuzzing.max_path_length', 15)  # Aumentar longitud
            
            # Ejecutar escaneo con configuración extendida
            results = self.fuzzing_engine.run_scan()
            
            # Restaurar configuración original
            self.config.set('fuzzing.max_path_length', original_max_length)
            
            # Siempre enviar reporte del escaneo profundo
            self.notifications.send_scan_report(results, results['results'])
            
            self.logger.info(f"Escaneo profundo completado: {results['paths_found']} rutas encontradas")
            
        except Exception as e:
            self.logger.error(f"Error en escaneo profundo: {e}")
    
    def _send_status_report(self):
        """Enviar reporte de estado sin novedades"""
        try:
            # Obtener estadísticas recientes
            recent_findings = self.db.get_recent_findings(6)  # Últimas 6 horas
            critical_findings = self.db.get_critical_findings()
            
            # Solo enviar si hay actividad reciente o críticos pendientes
            if recent_findings or critical_findings:
                stats = {
                    'total_domains': len(self.db.get_active_domains()),
                    'paths_found': len(recent_findings),
                    'critical_found': len(critical_findings),
                    'scan_duration': 0,
                    'timestamp': datetime.now().strftime('%Y-%m-%d %H:%M:%S')
                }
                
                self.notifications.send_scan_report(stats, recent_findings)
                self.logger.info("Reporte de estado enviado")
            else:
                self.logger.info("Sin actividad reciente, no se envía reporte")
                
        except Exception as e:
            self.logger.error(f"Error enviando reporte de estado: {e}")
    
    def _check_critical_alerts(self):
        """Verificar alertas críticas cada hora"""
        try:
            # Obtener alertas críticas no resueltas
            critical_alerts = self.db.execute_query('''
                SELECT * FROM alerts 
                WHERE severity = 'high' AND status != 'resolved'
                AND created_at >= datetime('now', '-1 hours')
            ''', fetch=True)
            
            if critical_alerts and len(critical_alerts) > 0:
                self.logger.warning(f"Hay {len(critical_alerts)} alertas críticas sin resolver")
                
                # Enviar recordatorio cada 4 horas
                for alert in critical_alerts:
                    alert_age = datetime.now() - datetime.fromisoformat(alert['created_at'])
                    if alert_age.total_seconds() % (4 * 3600) < 3600:  # Cada 4 horas
                        self.notifications.notify_critical_finding({
                            'url': alert['url'],
                            'path': alert['title'],
                            'status_code': 'ALERT',
                            'discovered_at': alert['created_at']
                        })
                
        except Exception as e:
            self.logger.error(f"Error verificando alertas críticas: {e}")
    
    def _cleanup_old_data(self):
        """Limpiar datos antiguos de la base de datos"""
        try:
            cleanup_days = self.config.get('database.cleanup_after_days', 30)
            
            # Limpiar hallazgos antiguos no críticos
            deleted_paths = self.db.execute_query('''
                DELETE FROM discovered_paths 
                WHERE discovered_at < datetime('now', '-{} days')
                AND is_critical = FALSE
            '''.format(cleanup_days))
            
            # Limpiar alertas resueltas antiguas
            deleted_alerts = self.db.execute_query('''
                DELETE FROM alerts 
                WHERE resolved_at < datetime('now', '-{} days')
                AND status = 'resolved'
            '''.format(cleanup_days))
            
            if deleted_paths or deleted_alerts:
                self.logger.info(f"Limpieza completada: {deleted_paths} rutas, {deleted_alerts} alertas eliminadas")
                
        except Exception as e:
            self.logger.error(f"Error en limpieza de datos: {e}")
    
    def _backup_database(self):
        """Hacer backup de la base de datos"""
        try:
            import shutil
            from datetime import datetime
            
            backup_dir = self.config.base_dir / self.config.get('files.backup_dir')
            backup_dir.mkdir(exist_ok=True)
            
            # Nombre del backup con timestamp
            timestamp = datetime.now().strftime('%Y%m%d_%H%M%S')
            backup_file = backup_dir / f"webfuzzing_backup_{timestamp}.db"
            
            # Copiar base de datos
            db_file = self.config.base_dir / self.config.get('database.name')
            shutil.copy2(str(db_file), str(backup_file))
            
            # Mantener solo los últimos 7 backups
            backups = sorted(backup_dir.glob('webfuzzing_backup_*.db'))
            if len(backups) > 7:
                for old_backup in backups[:-7]:
                    old_backup.unlink()
            
            self.logger.info(f"Backup creado: {backup_file}")
            
        except Exception as e:
            self.logger.error(f"Error creando backup: {e}")
    
    def start(self):
        """Iniciar el programador de tareas"""
        if self.is_running:
            self.logger.warning("El programador ya está ejecutándose")
            return
        
        self.is_running = True
        self.scheduler_thread = threading.Thread(target=self._run_scheduler, daemon=True)
        self.scheduler_thread.start()
        
        self.logger.info("Programador de tareas iniciado")
    
    def stop(self):
        """Detener el programador de tareas"""
        self.is_running = False
        if self.scheduler_thread:
            self.scheduler_thread.join(timeout=10)
        
        self.logger.info("Programador de tareas detenido")
    
    def _run_scheduler(self):
        """Ejecutar el loop principal del programador"""
        while self.is_running:
            try:
                schedule.run_pending()
                time.sleep(60)  # Verificar cada minuto
            except Exception as e:
                self.logger.error(f"Error en el programador: {e}")
                time.sleep(60)
    
    def run_manual_scan(self):
        """Ejecutar escaneo manual"""
        try:
            self.logger.info("Ejecutando escaneo manual")
            results = self.fuzzing_engine.run_scan()
            
            if results['critical_found'] > 0 or results['paths_found'] > 0:
                self.notifications.send_scan_report(results, results['results'])
            
            return results
            
        except Exception as e:
            self.logger.error(f"Error en escaneo manual: {e}")
            raise e
    
    def get_next_scheduled_tasks(self):
        """Obtener próximas tareas programadas"""
        jobs = []
        for job in schedule.jobs:
            jobs.append({
                'job': str(job.job_func.__name__),
                'next_run': job.next_run.isoformat() if job.next_run else None,
                'interval': str(job.interval),
                'unit': job.unit
            })
        return jobs
    
    def start_all_services(self):
        """Iniciar todos los servicios del sistema"""
        self.logger.info("Iniciando todos los servicios del sistema")
        
        # Iniciar programador
        self.start()
        
        # Iniciar aplicación web en un hilo separado
        web_thread = threading.Thread(
            target=self._start_web_app,
            daemon=True
        )
        web_thread.start()
        
        # Iniciar API en un hilo separado
        api_thread = threading.Thread(
            target=self._start_api,
            daemon=True
        )
        api_thread.start()
        
        # Mantener el programa principal ejecutándose
        try:
            while True:
                time.sleep(60)
        except KeyboardInterrupt:
            self.logger.info("Deteniendo sistema...")
            self.stop()
    
    def _start_web_app(self):
        """Iniciar aplicación web"""
        try:
            from web.app import create_app
            app = create_app(self.config)
            
            host = self.config.get('web.host', '127.0.0.1')
            port = self.config.get('web.port', 5000)
            
            self.logger.info(f"Iniciando aplicación web en {host}:{port}")
            app.run(host=host, port=port, debug=False, use_reloader=False)
            
        except Exception as e:
            self.logger.error(f"Error iniciando aplicación web: {e}")
    
    def _start_api(self):
        """Iniciar API REST"""
        try:
            from api.routes import create_api
            api = create_api(self.config)
            
            host = self.config.get('api.host', '127.0.0.1')
            port = self.config.get('api.port', 8000)
            
            self.logger.info(f"Iniciando API REST en {host}:{port}")
            api.run(host=host, port=port, debug=False)
            
        except Exception as e:
            self.logger.error(f"Error iniciando API: {e}")
