# web/app.py
from flask import Flask, render_template, request, jsonify, redirect, url_for, flash, session
from flask_socketio import SocketIO, emit
from datetime import datetime, timedelta
import json
from typing import Dict, List
from pathlib import Path

from config.database import DatabaseManager
from utils.logger import get_logger
from utils.notifications import NotificationManager

def create_app(config):
    """Crear aplicación Flask"""
    app = Flask(__name__)
    app.config['SECRET_KEY'] = config.get('web.secret_key')
    
    # Inicializar componentes
    db = DatabaseManager(config)
    logger = get_logger(__name__)
    notifications = NotificationManager(config)
    
    # SocketIO para actualizaciones en tiempo real
    socketio = SocketIO(app, cors_allowed_origins="*")
    
    @app.route('/')
    def dashboard():
        """Dashboard principal"""
        try:
            # Estadísticas generales
            stats = {
                'total_domains': len(db.get_active_domains()),
                'recent_findings': len(db.get_recent_findings(24)),
                'critical_findings': len(db.get_critical_findings()),
                'new_alerts': db.execute_query(
                    'SELECT COUNT(*) as count FROM alerts WHERE status = "new"',
                    fetch=True
                )[0]['count']
            }
            
            # Hallazgos recientes
            recent_findings = db.get_recent_findings(24)
            
            # Alertas críticas no resueltas
            critical_alerts = db.execute_query('''
                SELECT * FROM alerts 
                WHERE severity = 'high' AND status != 'resolved'
                ORDER BY created_at DESC
                LIMIT 10
            ''', fetch=True)
            
            # Gráfico de actividad por hora (últimas 24h)
            activity_data = db.execute_query('''
                SELECT 
                    strftime('%H', discovered_at) as hour,
                    COUNT(*) as count
                FROM discovered_paths 
                WHERE discovered_at >= datetime('now', '-24 hours')
                GROUP BY hour
                ORDER BY hour
            ''', fetch=True)
            
            return render_template('dashboard.html', 
                                 stats=stats,
                                 recent_findings=recent_findings,
                                 critical_alerts=critical_alerts,
                                 activity_data=activity_data)
                                 
        except Exception as e:
            logger.error(f"Error en dashboard: {e}")
            flash(f"Error cargando dashboard: {e}", 'error')
            return render_template('error.html', error=str(e))
    
    @app.route('/findings')
    def findings():
        """Página de hallazgos"""
        try:
            # Filtros
            domain_filter = request.args.get('domain', '')
            critical_only = request.args.get('critical', '') == 'true'
            hours = int(request.args.get('hours', 24))
            
            # Consulta base
            query = '''
                SELECT dp.*, d.domain
                FROM discovered_paths dp
                JOIN domains d ON dp.domain_id = d.id
                WHERE dp.discovered_at >= datetime('now', '-{} hours')
            '''.format(hours)
            
            params = []
            
            if domain_filter:
                query += ' AND d.domain LIKE ?'
                params.append(f'%{domain_filter}%')
            
            if critical_only:
                query += ' AND dp.is_critical = TRUE'
            
            query += ' ORDER BY dp.discovered_at DESC LIMIT 500'
            
            findings = db.execute_query(query, tuple(params), fetch=True)
            
            # Obtener dominios únicos para filtro
            domains = db.execute_query(
                'SELECT DISTINCT domain FROM domains ORDER BY domain',
                fetch=True
            )
            
            return render_template('findings.html',
                                 findings=findings,
                                 domains=domains,
                                 filters={
                                     'domain': domain_filter,
                                     'critical': critical_only,
                                     'hours': hours
                                 })
                                 
        except Exception as e:
            logger.error(f"Error en findings: {e}")
            flash(f"Error cargando hallazgos: {e}", 'error')
            return redirect(url_for('dashboard'))
    
    @app.route('/alerts')
    def alerts():
        """Página de alertas"""
        try:
            status_filter = request.args.get('status', 'all')
            
            query = 'SELECT * FROM alerts'
            params = []
            
            if status_filter != 'all':
                query += ' WHERE status = ?'
                params.append(status_filter)
            
            query += ' ORDER BY created_at DESC LIMIT 200'
            
            alerts_list = db.execute_query(query, tuple(params), fetch=True)
            
            return render_template('alerts.html',
                                 alerts=alerts_list,
                                 status_filter=status_filter)
                                 
        except Exception as e:
            logger.error(f"Error en alerts: {e}")
            flash(f"Error cargando alertas: {e}", 'error')
            return redirect(url_for('dashboard'))
    
    @app.route('/alert/<int:alert_id>')
    def alert_detail(alert_id):
        """Detalle de alerta"""
        try:
            alert = db.execute_query(
                'SELECT * FROM alerts WHERE id = ?',
                (alert_id,), fetch=True
            )
            
            if not alert:
                flash('Alerta no encontrada', 'error')
                return redirect(url_for('alerts'))
            
            alert = alert[0]
            
            return render_template('alert_detail.html', alert=alert)
            
        except Exception as e:
            logger.error(f"Error en alert_detail: {e}")
            flash(f"Error cargando alerta: {e}", 'error')
            return redirect(url_for('alerts'))
    
    @app.route('/update_alert/<int:alert_id>', methods=['POST'])
    def update_alert(alert_id):
        """Actualizar estado de alerta"""
        try:
            data = request.get_json()
            status = data.get('status')
            notes = data.get('notes', '')
            
            # Actualizar alerta
            resolved_at = 'CURRENT_TIMESTAMP' if status == 'resolved' else None
            
            db.execute_query('''
                UPDATE alerts 
                SET status = ?, analyst_notes = ?, updated_at = CURRENT_TIMESTAMP,
                    resolved_at = ?
                WHERE id = ?
            ''', (status, notes, resolved_at, alert_id))
            
            # Emitir actualización via WebSocket
            socketio.emit('alert_updated', {
                'alert_id': alert_id,
                'status': status,
                'notes': notes
            })
            
            return jsonify({'success': True, 'message': 'Alerta actualizada'})
            
        except Exception as e:
            logger.error(f"Error actualizando alerta: {e}")
            return jsonify({'success': False, 'error': str(e)})
    
    @app.route('/domains')
    def domains():
        """Página de dominios"""
        try:
            domains_list = db.get_active_domains()
            
            # Agregar estadísticas para cada dominio
            for domain in domains_list:
                domain_stats = db.execute_query('''
                    SELECT 
                        COUNT(*) as total_paths,
                        COUNT(CASE WHEN is_critical = TRUE THEN 1 END) as critical_paths,
                        MAX(discovered_at) as last_scan
                    FROM discovered_paths 
                    WHERE domain_id = ?
                ''', (domain['id'],), fetch=True)
                
                if domain_stats:
                    domain.update(domain_stats[0])
            
            return render_template('domains.html', domains=domains_list)
            
        except Exception as e:
            logger.error(f"Error en domains: {e}")
            flash(f"Error cargando dominios: {e}", 'error')
            return redirect(url_for('dashboard'))
    
    @app.route('/domain/<int:domain_id>')
    def domain_detail(domain_id):
        """Detalle de dominio"""
        try:
            # Obtener información del dominio
            domain = db.execute_query(
                'SELECT * FROM domains WHERE id = ?',
                (domain_id,), fetch=True
            )
            
            if not domain:
                flash('Dominio no encontrado', 'error')
                return redirect(url_for('domains'))
            
            domain = domain[0]
            
            # Obtener hallazgos del dominio
            findings = db.execute_query('''
                SELECT * FROM discovered_paths 
                WHERE domain_id = ?
                ORDER BY discovered_at DESC
                LIMIT 100
            ''', (domain_id,), fetch=True)
            
            # Estadísticas del dominio
            stats = db.execute_query('''
                SELECT 
                    COUNT(*) as total_paths,
                    COUNT(CASE WHEN is_critical = TRUE THEN 1 END) as critical_paths,
                    AVG(response_time) as avg_response_time,
                    MIN(discovered_at) as first_scan,
                    MAX(discovered_at) as last_scan
                FROM discovered_paths 
                WHERE domain_id = ?
            ''', (domain_id,), fetch=True)
            
            return render_template('domain_detail.html',
                                 domain=domain,
                                 findings=findings,
                                 stats=stats[0] if stats else {})
                                 
        except Exception as e:
            logger.error(f"Error en domain_detail: {e}")
            flash(f"Error cargando dominio: {e}", 'error')
            return redirect(url_for('domains'))
    
    @app.route('/api/stats')
    def api_stats():
        """API para estadísticas del dashboard"""
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
            logger.error(f"Error en api_stats: {e}")
            return jsonify({'error': str(e)}), 500
    
    @app.route('/api/recent_findings')
    def api_recent_findings():
        """API para hallazgos recientes"""
        try:
            hours = int(request.args.get('hours', 1))
            findings = db.get_recent_findings(hours)
            
            return jsonify([dict(f) for f in findings])
            
        except Exception as e:
            logger.error(f"Error en api_recent_findings: {e}")
            return jsonify({'error': str(e)}), 500
    
    @app.route('/export/findings')
    def export_findings():
        """Exportar hallazgos a CSV"""
        try:
            import csv
            from io import StringIO
            
            hours = int(request.args.get('hours', 24))
            critical_only = request.args.get('critical', '') == 'true'
            
            # Obtener datos
            query = '''
                SELECT dp.*, d.domain
                FROM discovered_paths dp
                JOIN domains d ON dp.domain_id = d.id
                WHERE dp.discovered_at >= datetime('now', '-{} hours')
            '''.format(hours)
            
            if critical_only:
                query += ' AND dp.is_critical = TRUE'
            
            query += ' ORDER BY dp.discovered_at DESC'
            
            findings = db.execute_query(query, fetch=True)
            
            # Crear CSV
            output = StringIO()
            writer = csv.writer(output)
            
            # Encabezados
            writer.writerow([
                'Dominio', 'URL', 'Ruta', 'Código Estado', 'Tamaño',
                'Tipo Contenido', 'Tiempo Respuesta', 'Es Crítico',
                'Descubierto en', 'Última vez visto'
            ])
            
            # Datos
            for finding in findings:
                writer.writerow([
                    finding['domain'],
                    finding['full_url'],
                    finding['path'],
                    finding['status_code'],
                    finding['content_length'],
                    finding['content_type'],
                    finding['response_time'],
                    'Sí' if finding['is_critical'] else 'No',
                    finding['discovered_at'],
                    finding['last_seen']
                ])
            
            output.seek(0)
            
            from flask import Response
            return Response(
                output.getvalue(),
                mimetype='text/csv',
                headers={
                    'Content-Disposition': f'attachment; filename=hallazgos_{datetime.now().strftime("%Y%m%d_%H%M%S")}.csv'
                }
            )
            
        except Exception as e:
            logger.error(f"Error exportando hallazgos: {e}")
            flash(f"Error exportando hallazgos: {e}", 'error')
            return redirect(url_for('findings'))
    
    # WebSocket events
    @socketio.on('connect')
    def handle_connect():
        """Cliente conectado"""
        logger.info(f"Cliente conectado: {request.sid}")
        emit('connected', {'status': 'connected'})
    
    @socketio.on('disconnect')
    def handle_disconnect():
        """Cliente desconectado"""
        logger.info(f"Cliente desconectado: {request.sid}")
    
    @socketio.on('subscribe_alerts')
    def handle_subscribe_alerts():
        """Suscribirse a alertas"""
        session['subscribed_alerts'] = True
        emit('subscribed', {'type': 'alerts'})
    
    # Función para emitir nuevos hallazgos
    def emit_new_finding(finding):
        """Emitir nuevo hallazgo a clientes conectados"""
        socketio.emit('new_finding', {
            'url': finding['full_url'],
            'path': finding['path'],
            'status_code': finding['status_code'],
            'is_critical': finding['is_critical'],
            'discovered_at': finding['discovered_at']
        })
    
    # Función para emitir nuevas alertas
    def emit_new_alert(alert):
        """Emitir nueva alerta a clientes conectados"""
        socketio.emit('new_alert', {
            'id': alert['id'],
            'type': alert['type'],
            'severity': alert['severity'],
            'title': alert['title'],
            'message': alert['message'],
            'created_at': alert['created_at']
        })
    
    # Agregar funciones de emisión al contexto de la app
    app.emit_new_finding = emit_new_finding
    app.emit_new_alert = emit_new_alert
    app.socketio = socketio
    
    return app
