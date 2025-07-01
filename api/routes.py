# api/routes.py
from flask import Flask, request, jsonify, abort
from flask_cors import CORS
from datetime import datetime
import json
from functools import wraps
import hashlib
import time

from config.database import DatabaseManager
from core.fuzzing_engine import FuzzingEngine
from utils.logger import get_logger
from utils.notifications import NotificationManager
from scripts.scheduler import TaskScheduler

def create_api(config):
    """Crear API REST"""
    app = Flask(__name__)
    CORS(app)
    
    # Inicializar componentes
    db = DatabaseManager(config)
    logger = get_logger(__name__)
    notifications = NotificationManager(config)
    scheduler = TaskScheduler(config)
    
    api_key = config.get('api.api_key')
    
    def require_api_key(f):
        """Decorador para requerir API key"""
        @wraps(f)
        def decorated_function(*args, **kwargs):
            provided_key = request.headers.get('X-API-Key')
            if not provided_key or provided_key != api_key:
                abort(401)
            return f(*args, **kwargs)
        return decorated_function
    
    @app.route('/api/v1/health', methods=['GET'])
    def health_check():
        """Verificación de salud del API"""
        return jsonify({
            'status': 'healthy',
            'timestamp': datetime.now().isoformat(),
            'version': '1.0.0'
        })
    
    @app.route('/api/v1/stats', methods=['GET'])
    @require_api_key
    def get_stats():
        """Obtener estadísticas del sistema"""
        try:
            stats = {
                'total_domains': len(db.get_active_domains()),
                'recent_findings': len(db.get_recent_findings(24)),
                'critical_findings': len(db.get_critical_findings()),
                'new_alerts': db.execute_query(
                    'SELECT COUNT(*) as count FROM alerts WHERE status = "new"',
                    fetch=True
                )[0]['count'],
                'timestamp': datetime.now().isoformat()
            }
            
            return jsonify(stats)
            
        except Exception as e:
            logger.error(f"Error obteniendo estadísticas: {e}")
            return jsonify({'error': str(e)}), 500
    
    @app.route('/api/v1/domains', methods=['GET'])
    #@require_api_key
    def get_domains():
        """Obtener lista de dominios"""
        try:
            domains = db.get_active_domains()
            return jsonify([dict(d) for d in domains])
            
        except Exception as e:
            logger.error(f"Error obteniendo dominios: {e}")
            return jsonify({'error': str(e)}), 500
    
    @app.route('/api/v1/domains', methods=['POST'])
    #@require_api_key
    def add_domain():
        """Agregar nuevo dominio"""
        try:
            data = request.get_json()
            
            if not data or 'domain' not in data:
                return jsonify({'error': 'Domain is required'}), 400
            
            domain_id = db.add_domain(
                data['domain'],
                data.get('port', 443),
                data.get('protocol', 'https')
            )
            
            return jsonify({
                'message': 'Domain added successfully',
                'domain_id': domain_id
            }), 201
            
        except Exception as e:
            logger.error(f"Error agregando dominio: {e}")
            return jsonify({'error': str(e)}), 500
    
    @app.route('/api/v1/findings', methods=['GET'])
    @require_api_key
    def get_findings():
        """Obtener hallazgos"""
        try:
            hours = int(request.args.get('hours', 24))
            critical_only = request.args.get('critical', '').lower() == 'true'
            domain = request.args.get('domain', '')
            
            # Construir consulta
            query = '''
                SELECT dp.*, d.domain
                FROM discovered_paths dp
                JOIN domains d ON dp.domain_id = d.id
                WHERE dp.discovered_at >= datetime('now', '-{} hours')
            '''.format(hours)
            
            params = []
            
            if domain:
                query += ' AND d.domain LIKE ?'
                params.append(f'%{domain}%')
            
            if critical_only:
                query += ' AND dp.is_critical = TRUE'
            
            query += ' ORDER BY dp.discovered_at DESC LIMIT 1000'
            
            findings = db.execute_query(query, tuple(params), fetch=True)
            
            return jsonify([dict(f) for f in findings])
            
        except Exception as e:
            logger.error(f"Error obteniendo hallazgos: {e}")
            return jsonify({'error': str(e)}), 500
    
    @app.route('/api/v1/alerts', methods=['GET'])
    @require_api_key
    def get_alerts():
        """Obtener alertas"""
        try:
            status = request.args.get('status', 'all')
            
            query = 'SELECT * FROM alerts'
            params = []
            
            if status != 'all':
                query += ' WHERE status = ?'
                params.append(status)
            
            query += ' ORDER BY created_at DESC LIMIT 100'
            
            alerts = db.execute_query(query, tuple(params), fetch=True)
            
            return jsonify([dict(a) for a in alerts])
            
        except Exception as e:
            logger.error(f"Error obteniendo alertas: {e}")
            return jsonify({'error': str(e)}), 500
    
    @app.route('/api/v1/alerts', methods=['POST'])
    @require_api_key
    def create_alert():
        """Crear nueva alerta"""
        try:
            data = request.get_json()
            
            required_fields = ['type', 'severity', 'title', 'message']
            if not all(field in data for field in required_fields):
                return jsonify({'error': 'Missing required fields'}), 400
            
            db.create_alert(
                data['type'],
                data['severity'],
                data['title'],
                data['message'],
                data.get('url')
            )
            
            return jsonify({'message': 'Alert created successfully'}), 201
            
        except Exception as e:
            logger.error(f"Error creando alerta: {e}")
            return jsonify({'error': str(e)}), 500
    
    @app.route('/api/v1/alerts/<int:alert_id>', methods=['PUT'])
    @require_api_key
    def update_alert(alert_id):
        """Actualizar alerta"""
        try:
            data = request.get_json()
            
            if 'status' not in data:
                return jsonify({'error': 'Status is required'}), 400
            
            resolved_at = 'CURRENT_TIMESTAMP' if data['status'] == 'resolved' else None
            
            db.execute_query('''
                UPDATE alerts 
                SET status = ?, analyst_notes = ?, updated_at = CURRENT_TIMESTAMP,
                    resolved_at = ?
                WHERE id = ?
            ''', (data['status'], data.get('notes', ''), resolved_at, alert_id))
            
            return jsonify({'message': 'Alert updated successfully'})
            
        except Exception as e:
            logger.error(f"Error actualizando alerta: {e}")
            return jsonify({'error': str(e)}), 500
    
    @app.route('/api/v1/scan', methods=['POST'])
    @require_api_key
    def start_scan():
        """Iniciar escaneo manual"""
        try:
            data = request.get_json() or {}
            
            # Ejecutar escaneo en hilo separado para no bloquear API
            import threading
            
            def run_scan():
                try:
                    results = scheduler.run_manual_scan()
                    logger.info(f"Escaneo manual completado: {results['paths_found']} rutas encontradas")
                except Exception as e:
                    logger.error(f"Error en escaneo manual: {e}")
            
            scan_thread = threading.Thread(target=run_scan, daemon=True)
            scan_thread.start()
            
            return jsonify({
                'message': 'Scan started successfully',
                'status': 'running',
                'timestamp': datetime.now().isoformat()
            }), 202
            
        except Exception as e:
            logger.error(f"Error iniciando escaneo: {e}")
            return jsonify({'error': str(e)}), 500
    
    @app.route('/api/v1/scheduled-tasks', methods=['GET'])
    @require_api_key
    def get_scheduled_tasks():
        """Obtener tareas programadas"""
        try:
            tasks = scheduler.get_next_scheduled_tasks()
            return jsonify(tasks)
            
        except Exception as e:
            logger.error(f"Error obteniendo tareas programadas: {e}")
            return jsonify({'error': str(e)}), 500
    
    @app.route('/api/v1/export/findings', methods=['GET'])
    @require_api_key
    def export_findings():
        """Exportar hallazgos"""
        try:
            hours = int(request.args.get('hours', 24))
            format_type = request.args.get('format', 'json')
            
            findings = db.get_recent_findings(hours)
            
            if format_type == 'csv':
                import csv
                from io import StringIO
                
                output = StringIO()
                writer = csv.writer(output)
                
                # Encabezados
                writer.writerow([
                    'Domain', 'URL', 'Path', 'Status Code', 'Content Length',
                    'Content Type', 'Response Time', 'Is Critical', 'Discovered At'
                ])
                
                # Datos
                for finding in findings:
                    writer.writerow([
                        finding.get('domain', ''),
                        finding.get('full_url', ''),
                        finding.get('path', ''),
                        finding.get('status_code', ''),
                        finding.get('content_length', ''),
                        finding.get('content_type', ''),
                        finding.get('response_time', ''),
                        'Yes' if finding.get('is_critical') else 'No',
                        finding.get('discovered_at', '')
                    ])
                
                output.seek(0)
                
                from flask import Response
                return Response(
                    output.getvalue(),
                    mimetype='text/csv',
                    headers={
                        'Content-Disposition': f'attachment; filename=findings_{datetime.now().strftime("%Y%m%d_%H%M%S")}.csv'
                    }
                )
            else:
                return jsonify([dict(f) for f in findings])
                
        except Exception as e:
            logger.error(f"Error exportando hallazgos: {e}")
            return jsonify({'error': str(e)}), 500
    
    @app.errorhandler(401)
    def unauthorized(error):
        return jsonify({'error': 'Unauthorized - Invalid API key'}), 401
    
    @app.errorhandler(404)
    def not_found(error):
        return jsonify({'error': 'Not found'}), 404
    
    @app.errorhandler(500)
    def internal_error(error):
        return jsonify({'error': 'Internal server error'}), 500
    
    @app.route('/', methods=['GET'])
    def api_root():
        """Ruta raíz de la API"""
        return jsonify({
            'status': 'WebFuzzing API v1.0',
            'endpoints': {
                'health': '/api/v1/health',
                'stats': '/api/stats',  # Ruta pública para dashboard
                'docs': '/api/v1/docs'
            }
        })

    @app.route('/api/stats', methods=['GET'])
    def get_stats_public():
        """Estadísticas públicas para el dashboard"""
        try:
            stats = {
                'total_domains': len(db.get_active_domains()),
                'recent_findings': len(db.get_recent_findings(24)),
                'critical_findings': len(db.get_critical_findings()),
                'new_alerts': db.execute_query(
                    'SELECT COUNT(*) as count FROM alerts WHERE status = "new"',
                    fetch=True
                )[0]['count'],
                'timestamp': datetime.now().isoformat()
            }
            
            return jsonify(stats)
            
        except Exception as e:
            logger.error(f"Error obteniendo estadísticas públicas: {e}")
            return jsonify({'error': str(e)}), 500

    @app.route('/api/recent_findings', methods=['GET'])
    def get_recent_findings_public():
        """Hallazgos recientes públicos para el dashboard"""
        try:
            hours = int(request.args.get('hours', 24))
            findings = db.get_recent_findings(hours)
            return jsonify([dict(f) for f in findings])
            
        except Exception as e:
            logger.error(f"Error obteniendo hallazgos recientes: {e}")
            return jsonify({'error': str(e)}), 500

#    @app.route('/api/domains', methods=['POST'])
#    def add_domain_public():
#        """Agregar dominio público para el dashboard"""
#        try:
#            data = request.get_json()
#            
#            if not data or 'domain' not in data:
#                return jsonify({'error': 'Domain is required'}), 400
#            
#            domain_id = db.add_domain(
#                data['domain'],
#               data.get('port', 443),
#               data.get('protocol', 'https')
#           )
#            
#           return jsonify({
#                'message': 'Domain added successfully',
#                'domain_id': domain_id
#            }), 201
#            
#        except Exception as e:
#            logger.error(f"Error agregando dominio público: {e}")
#            return jsonify({'error': str(e)}), 500
    
    return app