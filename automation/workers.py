#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Workers Especializados para Tareas de Automatización
Contiene workers especializados para diferentes tipos de tareas del sistema de fuzzing
"""

import asyncio
import logging
import time
import json
import threading
import multiprocessing
from abc import ABC, abstractmethod
from datetime import datetime, timedelta
from pathlib import Path
from typing import Dict, List, Optional, Any, Callable, Union
from dataclasses import dataclass, field
from enum import Enum
import subprocess
import tempfile
import shutil
import concurrent.futures

class WorkerType(Enum):
    """Tipos de workers"""
    FUZZING = "fuzzing"
    ALERT = "alert"
    REPORT = "report"
    ANALYSIS = "analysis"
    CLEANUP = "cleanup"
    NOTIFICATION = "notification"
    INTEGRATION = "integration"

class WorkerStatus(Enum):
    """Estados de workers"""
    IDLE = "idle"
    BUSY = "busy"
    ERROR = "error"
    OFFLINE = "offline"

@dataclass
class WorkerMetrics:
    """Métricas de rendimiento de worker"""
    tasks_completed: int = 0
    tasks_failed: int = 0
    total_execution_time: float = 0.0
    average_execution_time: float = 0.0
    last_task_time: Optional[datetime] = None
    errors_last_hour: int = 0
    success_rate: float = 1.0
    
    def update_task_completion(self, execution_time: float, success: bool):
        """Actualizar métricas tras completar una tarea"""
        if success:
            self.tasks_completed += 1
        else:
            self.tasks_failed += 1
        
        self.total_execution_time += execution_time
        total_tasks = self.tasks_completed + self.tasks_failed
        
        if total_tasks > 0:
            self.average_execution_time = self.total_execution_time / total_tasks
            self.success_rate = self.tasks_completed / total_tasks
        
        self.last_task_time = datetime.now()

class BaseWorker(ABC):
    """Clase base para todos los workers"""
    
    def __init__(self, worker_id: str, worker_type: WorkerType):
        """
        Inicializar worker base
        
        Args:
            worker_id: Identificador único del worker
            worker_type: Tipo de worker
        """
        self.worker_id = worker_id
        self.worker_type = worker_type
        self.logger = logging.getLogger(f"{__name__}.{worker_id}")
        
        # Estado del worker
        self.status = WorkerStatus.IDLE
        self.current_task = None
        self.start_time = datetime.now()
        self.last_heartbeat = datetime.now()
        
        # Métricas
        self.metrics = WorkerMetrics()
        
        # Configuración
        self.max_retries = 3
        self.timeout = 3600  # 1 hora por defecto
        
        # Control de estado
        self.is_running = False
        self._lock = threading.Lock()
        
        self.logger.info(f"Worker {worker_id} ({worker_type.value}) inicializado")
    
    @abstractmethod
    async def execute_task(self, task_data: Dict[str, Any]) -> Dict[str, Any]:
        """
        Ejecutar tarea específica del worker
        
        Args:
            task_data: Datos de la tarea a ejecutar
            
        Returns:
            Dict con resultado de la ejecución
        """
        pass
    
    async def process_task(self, task_data: Dict[str, Any]) -> Dict[str, Any]:
        """
        Procesar tarea con manejo de errores y métricas
        
        Args:
            task_data: Datos de la tarea
            
        Returns:
            Dict con resultado de la ejecución
        """
        start_time = time.time()
        result = {
            'worker_id': self.worker_id,
            'worker_type': self.worker_type.value,
            'task_id': task_data.get('task_id', 'unknown'),
            'started_at': datetime.now().isoformat(),
            'success': False,
            'result': None,
            'error': None,
            'execution_time': 0.0
        }
        
        with self._lock:
            self.status = WorkerStatus.BUSY
            self.current_task = task_data
        
        try:
            self.logger.info(f"Ejecutando tarea: {task_data.get('task_name', 'unknown')}")
            
            # Ejecutar tarea específica del worker
            task_result = await asyncio.wait_for(
                self.execute_task(task_data),
                timeout=task_data.get('timeout', self.timeout)
            )
            
            result['result'] = task_result
            result['success'] = True
            
            self.logger.info(f"Tarea completada exitosamente en {time.time() - start_time:.2f}s")
            
        except asyncio.TimeoutError:
            error_msg = f"Timeout after {task_data.get('timeout', self.timeout)} seconds"
            result['error'] = error_msg
            self.logger.error(error_msg)
            
        except Exception as e:
            error_msg = f"Error ejecutando tarea: {str(e)}"
            result['error'] = error_msg
            self.logger.error(error_msg, exc_info=True)
            
        finally:
            execution_time = time.time() - start_time
            result['execution_time'] = execution_time
            result['completed_at'] = datetime.now().isoformat()
            
            # Actualizar métricas
            self.metrics.update_task_completion(execution_time, result['success'])
            
            with self._lock:
                self.status = WorkerStatus.IDLE
                self.current_task = None
                self.last_heartbeat = datetime.now()
        
        return result
    
    def get_status(self) -> Dict[str, Any]:
        """Obtener estado actual del worker"""
        return {
            'worker_id': self.worker_id,
            'worker_type': self.worker_type.value,
            'status': self.status.value,
            'current_task': self.current_task.get('task_name') if self.current_task else None,
            'uptime_seconds': (datetime.now() - self.start_time).total_seconds(),
            'last_heartbeat': self.last_heartbeat.isoformat(),
            'metrics': {
                'tasks_completed': self.metrics.tasks_completed,
                'tasks_failed': self.metrics.tasks_failed,
                'success_rate': self.metrics.success_rate,
                'average_execution_time': self.metrics.average_execution_time,
                'last_task_time': self.metrics.last_task_time.isoformat() if self.metrics.last_task_time else None
            }
        }

class FuzzingWorker(BaseWorker):
    """Worker especializado para tareas de fuzzing"""
    
    def __init__(self, fuzzing_engine, worker_id: str = "fuzzing_worker"):
        """
        Inicializar worker de fuzzing
        
        Args:
            fuzzing_engine: Motor de fuzzing a utilizar
            worker_id: ID del worker
        """
        super().__init__(worker_id, WorkerType.FUZZING)
        self.fuzzing_engine = fuzzing_engine
        self.timeout = 7200  # 2 horas para fuzzing completo
        
        # Configuración específica de fuzzing
        self.scan_types = {
            'full': self._run_full_scan,
            'quick': self._run_quick_scan,
            'deep': self._run_deep_scan,
            'targeted': self._run_targeted_scan,
            'subdomain': self._run_subdomain_scan
        }
    
    async def execute_task(self, task_data: Dict[str, Any]) -> Dict[str, Any]:
        """Ejecutar tarea de fuzzing"""
        if not self.fuzzing_engine:
            raise Exception("Fuzzing engine no disponible")
        
        scan_type = task_data.get('scan_type', 'quick')
        domains = task_data.get('domains', [])
        wordlist = task_data.get('wordlist', [])
        
        if scan_type not in self.scan_types:
            raise ValueError(f"Tipo de escaneo no soportado: {scan_type}")
        
        # Ejecutar escaneo específico
        scan_function = self.scan_types[scan_type]
        result = await scan_function(domains, wordlist, task_data)
        
        return result
    
    async def _run_full_scan(self, domains: List[str], wordlist: List[str], task_data: Dict) -> Dict:
        """Ejecutar escaneo completo"""
        start_time = time.time()
        
        # Usar fuzzing engine para escaneo completo
        if hasattr(self.fuzzing_engine, 'run_comprehensive_scan'):
            findings = self.fuzzing_engine.run_comprehensive_scan()
        else:
            findings = self.fuzzing_engine.run_scan()
        
        execution_time = time.time() - start_time
        critical_findings = [f for f in findings if f.get('is_critical', False)]
        
        return {
            'scan_type': 'full',
            'total_findings': len(findings),
            'critical_findings': len(critical_findings),
            'domains_scanned': len(domains) if domains else 'all_configured',
            'execution_time': execution_time,
            'findings_sample': findings[:10],  # Muestra de hallazgos
            'timestamp': datetime.now().isoformat()
        }
    
    async def _run_quick_scan(self, domains: List[str], wordlist: List[str], task_data: Dict) -> Dict:
        """Ejecutar escaneo rápido"""
        start_time = time.time()
        
        # Escaneo rápido con wordlist limitada
        quick_wordlist = wordlist[:100] if wordlist else self._get_quick_wordlist()
        target_domains = domains[:3] if domains else self._get_sample_domains()
        
        all_findings = []
        for domain in target_domains:
            if hasattr(self.fuzzing_engine, 'fuzz_domain'):
                findings = self.fuzzing_engine.fuzz_domain(domain, quick_wordlist)
                all_findings.extend(findings)
        
        execution_time = time.time() - start_time
        
        return {
            'scan_type': 'quick',
            'total_findings': len(all_findings),
            'critical_findings': len([f for f in all_findings if f.get('is_critical', False)]),
            'domains_scanned': len(target_domains),
            'paths_tested': len(quick_wordlist),
            'execution_time': execution_time,
            'timestamp': datetime.now().isoformat()
        }
    
    async def _run_deep_scan(self, domains: List[str], wordlist: List[str], task_data: Dict) -> Dict:
        """Ejecutar escaneo profundo"""
        start_time = time.time()
        
        # Escaneo profundo con múltiples técnicas
        extended_wordlist = self._generate_extended_wordlist(wordlist)
        
        # Simular escaneo profundo (en implementación real usaría herramientas externas)
        await asyncio.sleep(30)  # Simular trabajo intensivo
        
        execution_time = time.time() - start_time
        
        return {
            'scan_type': 'deep',
            'total_findings': 45,  # Simulado
            'critical_findings': 8,
            'domains_scanned': len(domains),
            'advanced_techniques_used': ['brute_force', 'recursive_scan', 'parameter_fuzzing'],
            'execution_time': execution_time,
            'timestamp': datetime.now().isoformat()
        }
    
    async def _run_targeted_scan(self, domains: List[str], wordlist: List[str], task_data: Dict) -> Dict:
        """Ejecutar escaneo dirigido a vulnerabilidades específicas"""
        target_vulns = task_data.get('target_vulnerabilities', ['sqli', 'xss', 'rfi'])
        
        start_time = time.time()
        
        # Escaneo dirigido por tipo de vulnerabilidad
        findings_by_vuln = {}
        for vuln_type in target_vulns:
            findings_by_vuln[vuln_type] = await self._scan_for_vulnerability(domains, vuln_type)
        
        execution_time = time.time() - start_time
        total_findings = sum(len(findings) for findings in findings_by_vuln.values())
        
        return {
            'scan_type': 'targeted',
            'target_vulnerabilities': target_vulns,
            'findings_by_vulnerability': findings_by_vuln,
            'total_findings': total_findings,
            'execution_time': execution_time,
            'timestamp': datetime.now().isoformat()
        }
    
    async def _run_subdomain_scan(self, domains: List[str], wordlist: List[str], task_data: Dict) -> Dict:
        """Ejecutar descubrimiento de subdominios"""
        start_time = time.time()
        
        discovered_subdomains = []
        for domain in domains:
            subdomains = await self._discover_subdomains(domain)
            discovered_subdomains.extend(subdomains)
        
        execution_time = time.time() - start_time
        
        return {
            'scan_type': 'subdomain',
            'parent_domains': domains,
            'discovered_subdomains': discovered_subdomains,
            'total_subdomains': len(discovered_subdomains),
            'execution_time': execution_time,
            'timestamp': datetime.now().isoformat()
        }
    
    def _get_quick_wordlist(self) -> List[str]:
        """Obtener wordlist rápida por defecto"""
        return [
            'admin', 'login', 'panel', 'test', 'api', 'backup',
            'config.php', 'robots.txt', 'sitemap.xml', '.git',
            'wp-admin', 'phpmyadmin', 'database', 'private'
        ]
    
    def _get_sample_domains(self) -> List[str]:
        """Obtener dominios de muestra si no se especifican"""
        if hasattr(self.fuzzing_engine, 'load_domains'):
            domains = self.fuzzing_engine.load_domains()
            return domains[:3] if domains else ['httpbin.org']
        return ['httpbin.org']
    
    def _generate_extended_wordlist(self, base_wordlist: List[str]) -> List[str]:
        """Generar wordlist extendida para escaneo profundo"""
        extended = base_wordlist.copy() if base_wordlist else []
        
        # Agregar variaciones comunes
        extensions = ['.php', '.html', '.asp', '.jsp', '.txt', '.bak', '.old']
        for word in base_wordlist[:50]:  # Limitar para evitar explosión
            for ext in extensions:
                extended.append(word + ext)
        
        return extended
    
    async def _scan_for_vulnerability(self, domains: List[str], vuln_type: str) -> List[Dict]:
        """Escanear vulnerabilidad específica"""
        await asyncio.sleep(5)  # Simular escaneo
        
        # Simulación de hallazgos por tipo de vulnerabilidad
        vuln_findings = {
            'sqli': [{'url': f'{domains[0]}/search?q=test', 'type': 'sql_injection', 'severity': 'high'}],
            'xss': [{'url': f'{domains[0]}/comment', 'type': 'xss', 'severity': 'medium'}],
            'rfi': [{'url': f'{domains[0]}/include.php', 'type': 'file_inclusion', 'severity': 'high'}]
        }
        
        return vuln_findings.get(vuln_type, [])
    
    async def _discover_subdomains(self, domain: str) -> List[str]:
        """Descubrir subdominios de un dominio"""
        await asyncio.sleep(3)  # Simular descubrimiento
        
        # Simulación de subdominios descubiertos
        common_subdomains = ['www', 'mail', 'ftp', 'admin', 'test', 'dev', 'api', 'staging']
        discovered = [f'{sub}.{domain}' for sub in common_subdomains[:3]]  # Simular algunos encontrados
        
        return discovered

class AlertWorker(BaseWorker):
    """Worker especializado para procesamiento de alertas"""
    
    def __init__(self, alert_system, worker_id: str = "alert_worker"):
        """
        Inicializar worker de alertas
        
        Args:
            alert_system: Sistema de alertas inteligente
            worker_id: ID del worker
        """
        super().__init__(worker_id, WorkerType.ALERT)
        self.alert_system = alert_system
        self.timeout = 300  # 5 minutos para procesamiento de alertas
        
        # Tipos de procesamiento de alertas
        self.alert_processors = {
            'generate': self._generate_alerts,
            'analyze': self._analyze_alerts,
            'classify': self._classify_alerts,
            'correlate': self._correlate_alerts,
            'prioritize': self._prioritize_alerts
        }
    
    async def execute_task(self, task_data: Dict[str, Any]) -> Dict[str, Any]:
        """Ejecutar tarea de procesamiento de alertas"""
        if not self.alert_system:
            raise Exception("Alert system no disponible")
        
        alert_action = task_data.get('action', 'generate')
        findings = task_data.get('findings', [])
        
        if alert_action not in self.alert_processors:
            raise ValueError(f"Acción de alerta no soportada: {alert_action}")
        
        # Ejecutar procesamiento específico
        processor = self.alert_processors[alert_action]
        result = await processor(findings, task_data)
        
        return result
    
    async def _generate_alerts(self, findings: List[Dict], task_data: Dict) -> Dict:
        """Generar alertas inteligentes"""
        start_time = time.time()
        
        generated_alerts = []
        critical_findings = [f for f in findings if f.get('is_critical', False)]
        
        if hasattr(self.alert_system, 'generate_intelligent_alerts'):
            alerts = self.alert_system.generate_intelligent_alerts(critical_findings)
            generated_alerts.extend(alerts)
        
        # Generar alertas adicionales basadas en patrones
        pattern_alerts = await self._generate_pattern_alerts(findings)
        generated_alerts.extend(pattern_alerts)
        
        execution_time = time.time() - start_time
        
        return {
            'action': 'generate',
            'total_findings_processed': len(findings),
            'alerts_generated': len(generated_alerts),
            'critical_alerts': len([a for a in generated_alerts if a.get('severity') == 'critical']),
            'execution_time': execution_time,
            'alerts_sample': generated_alerts[:5]
        }
    
    async def _analyze_alerts(self, findings: List[Dict], task_data: Dict) -> Dict:
        """Analizar alertas existentes"""
        start_time = time.time()
        
        # Análisis de tendencias y patrones
        analysis_result = {
            'trending_attack_vectors': await self._identify_trending_attacks(findings),
            'geographical_patterns': await self._analyze_geo_patterns(findings),
            'temporal_patterns': await self._analyze_temporal_patterns(findings),
            'severity_distribution': self._calculate_severity_distribution(findings)
        }
        
        execution_time = time.time() - start_time
        
        return {
            'action': 'analyze',
            'analysis_result': analysis_result,
            'execution_time': execution_time,
            'timestamp': datetime.now().isoformat()
        }
    
    async def _classify_alerts(self, findings: List[Dict], task_data: Dict) -> Dict:
        """Clasificar alertas automáticamente"""
        start_time = time.time()
        
        classified_alerts = {
            'critical': [],
            'high': [],
            'medium': [],
            'low': [],
            'false_positive': []
        }
        
        for finding in findings:
            classification = await self._classify_single_alert(finding)
            classified_alerts[classification].append(finding)
        
        execution_time = time.time() - start_time
        
        return {
            'action': 'classify',
            'classification_results': {k: len(v) for k, v in classified_alerts.items()},
            'execution_time': execution_time,
            'total_classified': len(findings)
        }
    
    async def _correlate_alerts(self, findings: List[Dict], task_data: Dict) -> Dict:
        """Correlacionar alertas para detectar campañas de ataque"""
        start_time = time.time()
        
        correlations = await self._find_alert_correlations(findings)
        attack_campaigns = await self._identify_attack_campaigns(correlations)
        
        execution_time = time.time() - start_time
        
        return {
            'action': 'correlate',
            'correlations_found': len(correlations),
            'attack_campaigns': len(attack_campaigns),
            'execution_time': execution_time,
            'campaigns_sample': attack_campaigns[:3]
        }
    
    async def _prioritize_alerts(self, findings: List[Dict], task_data: Dict) -> Dict:
        """Priorizar alertas basado en contexto y riesgo"""
        start_time = time.time()
        
        prioritized_alerts = []
        for finding in findings:
            priority_score = await self._calculate_priority_score(finding)
            prioritized_alerts.append({
                'finding': finding,
                'priority_score': priority_score,
                'priority_level': self._score_to_priority_level(priority_score)
            })
        
        # Ordenar por prioridad
        prioritized_alerts.sort(key=lambda x: x['priority_score'], reverse=True)
        
        execution_time = time.time() - start_time
        
        return {
            'action': 'prioritize',
            'prioritized_alerts': prioritized_alerts[:10],  # Top 10
            'total_processed': len(findings),
            'execution_time': execution_time
        }
    
    async def _generate_pattern_alerts(self, findings: List[Dict]) -> List[Dict]:
        """Generar alertas basadas en patrones detectados"""
        pattern_alerts = []
        
        # Detectar patrones de ataque
        if len(findings) > 10:  # Muchos hallazgos en poco tiempo
            pattern_alerts.append({
                'type': 'mass_scanning',
                'severity': 'high',
                'message': f'Posible escaneo masivo detectado: {len(findings)} hallazgos',
                'evidence': findings[:5]
            })
        
        # Detectar intentos de acceso a rutas administrativas
        admin_attempts = [f for f in findings if any(admin_path in f.get('path', '') 
                         for admin_path in ['admin', 'login', 'panel'])]
        
        if len(admin_attempts) > 3:
            pattern_alerts.append({
                'type': 'admin_access_attempt',
                'severity': 'critical',
                'message': f'Múltiples intentos de acceso administrativo: {len(admin_attempts)}',
                'evidence': admin_attempts
            })
        
        return pattern_alerts
    
    async def _identify_trending_attacks(self, findings: List[Dict]) -> List[str]:
        """Identificar vectores de ataque en tendencia"""
        await asyncio.sleep(1)  # Simular análisis
        return ['sql_injection', 'directory_traversal', 'xss']
    
    async def _analyze_geo_patterns(self, findings: List[Dict]) -> Dict:
        """Analizar patrones geográficos"""
        await asyncio.sleep(1)
        return {'top_countries': ['US', 'CN', 'RU'], 'suspicious_regions': ['CN', 'RU']}
    
    async def _analyze_temporal_patterns(self, findings: List[Dict]) -> Dict:
        """Analizar patrones temporales"""
        await asyncio.sleep(1)
        return {'peak_hours': [2, 3, 14, 15], 'attack_frequency': 'increasing'}
    
    def _calculate_severity_distribution(self, findings: List[Dict]) -> Dict:
        """Calcular distribución de severidad"""
        distribution = {'critical': 0, 'high': 0, 'medium': 0, 'low': 0}
        
        for finding in findings:
            severity = finding.get('severity', 'low')
            distribution[severity] = distribution.get(severity, 0) + 1
        
        return distribution
    
    async def _classify_single_alert(self, finding: Dict) -> str:
        """Clasificar una alerta individual"""
        # Clasificación simple basada en características
        if finding.get('is_critical', False):
            return 'critical'
        
        status_code = finding.get('status_code', 0)
        path = finding.get('path', '')
        
        if status_code == 200 and any(admin in path.lower() for admin in ['admin', 'login']):
            return 'high'
        elif status_code in [403, 401]:
            return 'medium'
        else:
            return 'low'
    
    async def _find_alert_correlations(self, findings: List[Dict]) -> List[Dict]:
        """Encontrar correlaciones entre alertas"""
        await asyncio.sleep(2)  # Simular análisis complejo
        
        # Simulación de correlaciones encontradas
        return [
            {'type': 'same_ip', 'count': 5, 'ip': '192.168.1.100'},
            {'type': 'attack_pattern', 'pattern': 'sql_injection_scan', 'count': 3}
        ]
    
    async def _identify_attack_campaigns(self, correlations: List[Dict]) -> List[Dict]:
        """Identificar campañas de ataque coordinadas"""
        campaigns = []
        
        for correlation in correlations:
            if correlation['count'] > 3:
                campaigns.append({
                    'campaign_type': correlation['type'],
                    'severity': 'high' if correlation['count'] > 5 else 'medium',
                    'indicators': correlation,
                    'recommended_action': 'immediate_investigation'
                })
        
        return campaigns
    
    async def _calculate_priority_score(self, finding: Dict) -> float:
        """Calcular score de prioridad para un hallazgo"""
        score = 0.0
        
        # Factores de prioridad
        if finding.get('is_critical', False):
            score += 50
        
        status_code = finding.get('status_code', 0)
        if status_code == 200:
            score += 30
        elif status_code in [403, 401]:
            score += 20
        
        # Análisis de ruta
        path = finding.get('path', '').lower()
        high_value_paths = ['admin', 'login', 'config', 'backup', 'database']
        for hvp in high_value_paths:
            if hvp in path:
                score += 25
                break
        
        # Factor temporal (hallazgos recientes tienen mayor prioridad)
        timestamp = finding.get('timestamp')
        if timestamp:
            # Lógica simplificada de temporalidad
            score += 10
        
        return min(score, 100.0)  # Máximo 100
    
    def _score_to_priority_level(self, score: float) -> str:
        """Convertir score numérico a nivel de prioridad"""
        if score >= 80:
            return 'critical'
        elif score >= 60:
            return 'high'
        elif score >= 40:
            return 'medium'
        else:
            return 'low'

class ReportWorker(BaseWorker):
    """Worker especializado para generación de reportes"""
    
    def __init__(self, notification_manager=None, worker_id: str = "report_worker"):
        """
        Inicializar worker de reportes
        
        Args:
            notification_manager: Gestor de notificaciones
            worker_id: ID del worker
        """
        super().__init__(worker_id, WorkerType.REPORT)
        self.notification_manager = notification_manager
        self.timeout = 600  # 10 minutos para generación de reportes
        
        # Tipos de reportes
        self.report_generators = {
            'security_summary': self._generate_security_summary,
            'vulnerability_report': self._generate_vulnerability_report,
            'trend_analysis': self._generate_trend_analysis,
            'compliance_report': self._generate_compliance_report,
            'executive_summary': self._generate_executive_summary
        }
        
        # Configuración de reportes
        self.reports_dir = Path("reports")
        self.reports_dir.mkdir(exist_ok=True)
    
    async def execute_task(self, task_data: Dict[str, Any]) -> Dict[str, Any]:
        """Ejecutar tarea de generación de reportes"""
        report_type = task_data.get('report_type', 'security_summary')
        data = task_data.get('data', {})
        
        if report_type not in self.report_generators:
            raise ValueError(f"Tipo de reporte no soportado: {report_type}")
        
        # Generar reporte específico
        generator = self.report_generators[report_type]
        result = await generator(data, task_data)
        
        return result
    
    async def _generate_security_summary(self, data: Dict, task_data: Dict) -> Dict:
        """Generar resumen de seguridad"""
        start_time = time.time()
        
        # Recopilar datos de seguridad
        summary_data = await self._collect_security_data(data)
        
        # Generar reporte HTML
        report_html = self._create_html_report(summary_data, 'Security Summary')
        
        # Guardar reporte
        timestamp = datetime.now().strftime('%Y%m%d_%H%M%S')
        report_file = self.reports_dir / f"security_summary_{timestamp}.html"
        
        with open(report_file, 'w', encoding='utf-8') as f:
            f.write(report_html)
        
        execution_time = time.time() - start_time
        
        return {
            'report_type': 'security_summary',
            'report_file': str(report_file),
            'file_size_mb': report_file.stat().st_size / (1024 * 1024),
            'execution_time': execution_time,
            'summary_stats': summary_data.get('stats', {}),
            'timestamp': datetime.now().isoformat()
        }
    
    async def _generate_vulnerability_report(self, data: Dict, task_data: Dict) -> Dict:
        """Generar reporte de vulnerabilidades"""
        start_time = time.time()
        
        vulnerabilities = data.get('vulnerabilities', [])
        
        # Analizar vulnerabilidades
        vuln_analysis = {
            'total_vulnerabilities': len(vulnerabilities),
            'critical_count': len([v for v in vulnerabilities if v.get('severity') == 'critical']),
            'high_count': len([v for v in vulnerabilities if v.get('severity') == 'high']),
            'medium_count': len([v for v in vulnerabilities if v.get('severity') == 'medium']),
            'low_count': len([v for v in vulnerabilities if v.get('severity') == 'low']),
            'top_vulnerability_types': self._get_top_vuln_types(vulnerabilities)
        }
        
        # Generar reporte JSON detallado
        report_data = {
            'generated_at': datetime.now().isoformat(),
            'analysis': vuln_analysis,
            'vulnerabilities': vulnerabilities,
            'recommendations': self._generate_vuln_recommendations(vuln_analysis)
        }
        
        # Guardar reporte
        timestamp = datetime.now().strftime('%Y%m%d_%H%M%S')
        report_file = self.reports_dir / f"vulnerability_report_{timestamp}.json"
        
        with open(report_file, 'w', encoding='utf-8') as f:
            json.dump(report_data, f, indent=2, ensure_ascii=False)
        
        execution_time = time.time() - start_time
        
        return {
            'report_type': 'vulnerability_report',
            'report_file': str(report_file),
            'vulnerabilities_analyzed': len(vulnerabilities),
            'critical_vulnerabilities': vuln_analysis['critical_count'],
            'execution_time': execution_time,
            'timestamp': datetime.now().isoformat()
        }
    
    async def _generate_trend_analysis(self, data: Dict, task_data: Dict) -> Dict:
        """Generar análisis de tendencias"""
        start_time = time.time()
        
        # Análisis de tendencias temporales
        trend_data = await self._analyze_security_trends(data)
        
        # Crear gráficos y visualizaciones (simulado)
        visualizations = await self._create_trend_visualizations(trend_data)
        
        execution_time = time.time() - start_time
        
        return {
            'report_type': 'trend_analysis',
            'trend_data': trend_data,
            'visualizations_created': len(visualizations),
            'execution_time': execution_time,
            'key_trends': trend_data.get('key_trends', []),
            'timestamp': datetime.now().isoformat()
        }
    
    async def _generate_compliance_report(self, data: Dict, task_data: Dict) -> Dict:
        """Generar reporte de cumplimiento"""
        start_time = time.time()
        
        compliance_framework = task_data.get('framework', 'ISO27001')
        
        # Evaluación de cumplimiento
        compliance_results = await self._evaluate_compliance(data, compliance_framework)
        
        execution_time = time.time() - start_time
        
        return {
            'report_type': 'compliance_report',
            'framework': compliance_framework,
            'compliance_score': compliance_results.get('overall_score', 0),
            'passed_controls': compliance_results.get('passed', 0),
            'failed_controls': compliance_results.get('failed', 0),
            'execution_time': execution_time,
            'timestamp': datetime.now().isoformat()
        }
    
    async def _generate_executive_summary(self, data: Dict, task_data: Dict) -> Dict:
        """Generar resumen ejecutivo"""
        start_time = time.time()
        
        # Crear resumen de alto nivel
        executive_data = {
            'security_posture': await self._assess_security_posture(data),
            'risk_assessment': await self._perform_risk_assessment(data),
            'key_metrics': await self._calculate_key_metrics(data),
            'recommendations': await self._generate_executive_recommendations(data)
        }
        
        # Generar PDF ejecutivo (simulado)
        report_file = await self._create_executive_pdf(executive_data)
        
        execution_time = time.time() - start_time
        
        return {
            'report_type': 'executive_summary',
            'report_file': str(report_file),
            'security_posture': executive_data['security_posture'],
            'risk_level': executive_data['risk_assessment']['level'],
            'execution_time': execution_time,
            'timestamp': datetime.now().isoformat()
        }
    
    async def _collect_security_data(self, data: Dict) -> Dict:
        """Recopilar datos de seguridad para reportes"""
        return {
            'stats': {
                'total_scans': data.get('total_scans', 0),
                'vulnerabilities_found': data.get('vulnerabilities_found', 0),
                'critical_issues': data.get('critical_issues', 0),
                'scan_coverage': data.get('scan_coverage', '100%')
            },
            'recent_activities': data.get('recent_activities', []),
            'threat_landscape': data.get('threat_landscape', {})
        }
    
    def _create_html_report(self, data: Dict, title: str) -> str:
        """Crear reporte HTML básico"""
        html_template = f"""
        <!DOCTYPE html>
        <html>
        <head>
            <title>{title}</title>
            <style>
                body {{ font-family: Arial, sans-serif; margin: 40px; }}
                .header {{ background: #2c3e50; color: white; padding: 20px; }}
                .metric {{ background: #ecf0f1; padding: 15px; margin: 10px 0; }}
                .critical {{ background: #e74c3c; color: white; }}
            </style>
        </head>
        <body>
            <div class="header">
                <h1>{title}</h1>
                <p>Generado: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}</p>
            </div>
            
            <div class="content">
                <h2>Métricas de Seguridad</h2>
                {self._format_metrics_html(data.get('stats', {}))}
                
                <h2>Actividades Recientes</h2>
                {self._format_activities_html(data.get('recent_activities', []))}
            </div>
        </body>
        </html>
        """
        return html_template
    
    def _format_metrics_html(self, stats: Dict) -> str:
        """Formatear métricas como HTML"""
        html = ""
        for key, value in stats.items():
            css_class = "metric critical" if "critical" in key.lower() else "metric"
            html += f'<div class="{css_class}"><strong>{key}:</strong> {value}</div>'
        return html
    
    def _format_activities_html(self, activities: List) -> str:
        """Formatear actividades como HTML"""
        if not activities:
            return "<p>No hay actividades recientes</p>"
        
        html = "<ul>"
        for activity in activities[:10]:  # Últimas 10
            html += f"<li>{activity}</li>"
        html += "</ul>"
        return html
    
    def _get_top_vuln_types(self, vulnerabilities: List[Dict]) -> List[Dict]:
        """Obtener tipos de vulnerabilidades más comunes"""
        vuln_types = {}
        for vuln in vulnerabilities:
            vuln_type = vuln.get('type', 'unknown')
            vuln_types[vuln_type] = vuln_types.get(vuln_type, 0) + 1
        
        # Ordenar por frecuencia
        sorted_types = sorted(vuln_types.items(), key=lambda x: x[1], reverse=True)
        return [{'type': t[0], 'count': t[1]} for t in sorted_types[:5]]
    
    def _generate_vuln_recommendations(self, analysis: Dict) -> List[str]:
        """Generar recomendaciones basadas en análisis de vulnerabilidades"""
        recommendations = []
        
        if analysis['critical_count'] > 0:
            recommendations.append(f"URGENT: Address {analysis['critical_count']} critical vulnerabilities immediately")
        
        if analysis['high_count'] > 5:
            recommendations.append(f"High priority: {analysis['high_count']} high-severity issues require attention")
        
        if analysis['total_vulnerabilities'] > 20:
            recommendations.append("Consider implementing automated vulnerability management")
        
        return recommendations
    
    async def _analyze_security_trends(self, data: Dict) -> Dict:
        """Analizar tendencias de seguridad"""
        await asyncio.sleep(2)  # Simular análisis
        
        return {
            'key_trends': [
                'Increasing SQL injection attempts',
                'Rise in admin panel brute force attacks',
                'New subdomain discovery patterns'
            ],
            'trend_direction': 'increasing_threats',
            'risk_evolution': 'moderate_increase'
        }
    
    async def _create_trend_visualizations(self, trend_data: Dict) -> List[str]:
        """Crear visualizaciones de tendencias"""
        await asyncio.sleep(1)
        return ['timeline_chart.png', 'threat_heatmap.png', 'risk_evolution.png']
    
    async def _evaluate_compliance(self, data: Dict, framework: str) -> Dict:
        """Evaluar cumplimiento normativo"""
        await asyncio.sleep(3)  # Simular evaluación
        
        return {
            'overall_score': 85,
            'passed': 42,
            'failed': 8,
            'framework': framework,
            'assessment_date': datetime.now().isoformat()
        }
    
    async def _assess_security_posture(self, data: Dict) -> str:
        """Evaluar postura de seguridad general"""
        await asyncio.sleep(1)
        
        # Lógica simplificada de evaluación
        critical_issues = data.get('critical_issues', 0)
        
        if critical_issues == 0:
            return 'Strong'
        elif critical_issues <= 3:
            return 'Moderate'
        else:
            return 'Weak'
    
    async def _perform_risk_assessment(self, data: Dict) -> Dict:
        """Realizar evaluación de riesgos"""
        await asyncio.sleep(1)
        
        return {
            'level': 'Medium',
            'factors': ['Unpatched vulnerabilities', 'Exposed admin panels'],
            'mitigation_priority': 'High'
        }
    
    async def _calculate_key_metrics(self, data: Dict) -> Dict:
        """Calcular métricas clave"""
        return {
            'mean_time_to_detection': '2.5 hours',
            'mean_time_to_response': '4.2 hours',
            'vulnerability_density': '0.3 per 1000 LOC',
            'security_coverage': '94%'
        }
    
    async def _generate_executive_recommendations(self, data: Dict) -> List[str]:
        """Generar recomendaciones ejecutivas"""
        return [
            'Increase security scanning frequency',
            'Implement automated patch management',
            'Enhance incident response capabilities',
            'Consider additional security training'
        ]
    
    async def _create_executive_pdf(self, data: Dict) -> Path:
        """Crear PDF ejecutivo (simulado)"""
        await asyncio.sleep(2)
        
        timestamp = datetime.now().strftime('%Y%m%d_%H%M%S')
        pdf_file = self.reports_dir / f"executive_summary_{timestamp}.pdf"
        
        # Simular creación de PDF
        with open(pdf_file, 'w') as f:
            f.write("PDF content placeholder")
        
        return pdf_file

class WorkerManager:
    """Gestor de workers para el sistema de automatización"""
    
    def __init__(self, orchestrator=None, max_workers: int = 5):
        """
        Inicializar gestor de workers
        
        Args:
            orchestrator: Referencia al orquestador
            max_workers: Número máximo de workers concurrentes
        """
        self.orchestrator = orchestrator
        self.max_workers = max_workers
        self.logger = logging.getLogger(__name__)
        
        # Workers registrados
        self.workers = {}
        self.worker_pool = {}
        
        # Estado del gestor
        self.is_running = False
        self.task_queue = asyncio.Queue()
        
        # Métricas
        self.total_tasks_processed = 0
        self.failed_tasks = 0
        
        self.logger.info(f"WorkerManager inicializado con {max_workers} workers máximo")
    
    def register_worker(self, worker_type: str, worker: BaseWorker):
        """Registrar nuevo worker"""
        self.workers[worker_type] = worker
        self.logger.info(f"Worker {worker_type} registrado: {worker.worker_id}")
    
    async def assign_task(self, worker_type: str, task_data: Dict[str, Any]) -> str:
        """
        Asignar tarea a worker específico
        
        Args:
            worker_type: Tipo de worker requerido
            task_data: Datos de la tarea
            
        Returns:
            str: ID de la tarea asignada
        """
        if worker_type not in self.workers:
            raise ValueError(f"Worker type {worker_type} not registered")
        
        worker = self.workers[worker_type]
        
        # Verificar que el worker esté disponible
        if worker.status != WorkerStatus.IDLE:
            # En un sistema real, aquí podríamos poner en cola o crear pool de workers
            self.logger.warning(f"Worker {worker_type} está ocupado")
        
        # Asignar tarea
        task_id = f"task_{worker_type}_{int(time.time())}"
        task_data['task_id'] = task_id
        
        # Procesar tarea
        result = await worker.process_task(task_data)
        
        # Actualizar métricas
        self.total_tasks_processed += 1
        if not result['success']:
            self.failed_tasks += 1
        
        return task_id
    
    async def start(self):
        """Iniciar gestor de workers"""
        self.is_running = True
        self.logger.info("🔧 WorkerManager iniciado")
    
    async def stop(self):
        """Detener gestor de workers"""
        self.is_running = False
        
        # Detener todos los workers
        for worker in self.workers.values():
            if hasattr(worker, 'stop'):
                await worker.stop()
        
        self.logger.info("🛑 WorkerManager detenido")
    
    def get_status(self) -> Dict[str, Any]:
        """Obtener estado del gestor de workers"""
        worker_statuses = {}
        for worker_type, worker in self.workers.items():
            worker_statuses[worker_type] = worker.get_status()
        
        return {
            'is_running': self.is_running,
            'registered_workers': len(self.workers),
            'total_tasks_processed': self.total_tasks_processed,
            'failed_tasks': self.failed_tasks,
            'success_rate': (self.total_tasks_processed - self.failed_tasks) / max(self.total_tasks_processed, 1),
            'worker_statuses': worker_statuses
        }