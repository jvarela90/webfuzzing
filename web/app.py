#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Dashboard Web Consolidado para Sistema de Fuzzing
Interfaz web completa con analytics avanzado, tiempo real y compatibilidad multiplataforma
"""

import os
import json
import sqlite3
import platform
import pandas as pd
import secrets
import time
import threading
from datetime import datetime, timedelta
from pathlib import Path
from collections import defaultdict

from flask import Flask, render_template_string, request, jsonify, redirect, url_for, flash, session
from flask_socketio import SocketIO, emit
from werkzeug.security import generate_password_hash, check_password_hash

import plotly.graph_objects as go
import plotly.express as px
from plotly.subplots import make_subplots
import plotly.utils

from core.domain_management import domain_bp


# Configurar encoding para Windows
if platform.system() == "Windows":
    import sys
    try:
        sys.stdout.reconfigure(encoding='utf-8')
        sys.stderr.reconfigure(encoding='utf-8')
    except:
        pass

# Configuración de Flask
app = Flask(__name__)
app.secret_key = secrets.token_hex(16)
socketio = SocketIO(app, cors_allowed_origins="*")

# Configuración global
BASE_DIR = Path(__file__).parent.resolve()
DATABASE_FILE = BASE_DIR / "data" / "fuzzing.db"
REPORTS_DIR = BASE_DIR / "reports"

class ConsolidatedDashboardManager:
    """Gestor consolidado para el dashboard web"""
    
    def __init__(self, db_path: str):
        self.db_path = Path(db_path)
        self.cache = {}
        self.cache_timeout = 300  # 5 minutos
        self.last_update = {}
        self.init_database_if_needed()
        
    def init_database_if_needed(self):
        """Inicializar base de datos si no existe"""
        if not self.db_path.exists():
            self.db_path.parent.mkdir(parents=True, exist_ok=True)
            self.create_basic_tables()
            self.insert_sample_data()
    
    def create_basic_tables(self):
        """Crear tablas básicas"""
        try:
            with sqlite3.connect(self.db_path) as conn:
                cursor = conn.cursor()
                
                cursor.execute('''
                    CREATE TABLE IF NOT EXISTS dominios (
                        id INTEGER PRIMARY KEY AUTOINCREMENT,
                        dominio TEXT UNIQUE NOT NULL,
                        protocolo TEXT NOT NULL DEFAULT 'https',
                        puerto INTEGER DEFAULT 443,
                        activo BOOLEAN DEFAULT 1,
                        fecha_agregado DATETIME DEFAULT CURRENT_TIMESTAMP,
                        ultimo_escaneo DATETIME
                    )
                ''')
                
                cursor.execute('''
                    CREATE TABLE IF NOT EXISTS hallazgos (
                        id INTEGER PRIMARY KEY AUTOINCREMENT,
                        dominio_id INTEGER,
                        url_completa TEXT NOT NULL,
                        ruta TEXT NOT NULL,
                        codigo_http INTEGER NOT NULL,
                        es_critico BOOLEAN DEFAULT 0,
                        fecha_descubierto DATETIME DEFAULT CURRENT_TIMESTAMP,
                        contenido_hash TEXT,
                        tamano_respuesta INTEGER DEFAULT 0,
                        herramienta TEXT DEFAULT 'interno',
                        FOREIGN KEY (dominio_id) REFERENCES dominios (id)
                    )
                ''')
                
                cursor.execute('''
                    CREATE TABLE IF NOT EXISTS alertas (
                        id INTEGER PRIMARY KEY AUTOINCREMENT,
                        hallazgo_id INTEGER,
                        tipo_alerta TEXT NOT NULL DEFAULT 'informativa',
                        mensaje TEXT NOT NULL,
                        estado TEXT DEFAULT 'pendiente',
                        analista TEXT,
                        comentarios TEXT,
                        fecha_creada DATETIME DEFAULT CURRENT_TIMESTAMP,
                        fecha_atendida DATETIME,
                        FOREIGN KEY (hallazgo_id) REFERENCES hallazgos (id)
                    )
                ''')
                
                conn.commit()
                print("✅ Tablas creadas exitosamente")
        except Exception as e:
            print(f"❌ Error creando tablas: {e}")
    
    def insert_sample_data(self):
        """Insertar datos de muestra para desarrollo"""
        try:
            with sqlite3.connect(self.db_path) as conn:
                cursor = conn.cursor()
                
                # Insertar dominios de prueba
                sample_domains = [
                    ('httpbin.org', 'https', 443),
                    ('jsonplaceholder.typicode.com', 'https', 443),
                    ('example.com', 'https', 443),
                ]
                
                for domain, protocol, port in sample_domains:
                    cursor.execute('''
                        INSERT OR IGNORE INTO dominios (dominio, protocolo, puerto)
                        VALUES (?, ?, ?)
                    ''', (domain, protocol, port))
                
                # Insertar hallazgos de ejemplo
                sample_findings = [
                    (1, 'https://httpbin.org/status/200', '/status/200', 200, False, 2048),
                    (1, 'https://httpbin.org/json', '/json', 200, False, 1024),
                    (1, 'https://httpbin.org/admin', '/admin', 404, True, 512),
                    (1, 'https://httpbin.org/secret', '/secret', 403, True, 256),
                    (2, 'https://jsonplaceholder.typicode.com/posts', '/posts', 200, False, 8192),
                    (2, 'https://jsonplaceholder.typicode.com/admin', '/admin', 404, True, 512),
                    (3, 'https://example.com/', '/', 200, False, 4096),
                ]
                
                for domain_id, url, path, code, critical, size in sample_findings:
                    cursor.execute('''
                        INSERT OR IGNORE INTO hallazgos 
                        (dominio_id, url_completa, ruta, codigo_http, es_critico, tamano_respuesta, herramienta)
                        VALUES (?, ?, ?, ?, ?, ?, ?)
                    ''', (domain_id, url, path, code, critical, size, 'demo'))
                    
                    if critical:
                        hallazgo_id = cursor.lastrowid
                        cursor.execute('''
                            INSERT OR IGNORE INTO alertas (hallazgo_id, tipo_alerta, mensaje)
                            VALUES (?, ?, ?)
                        ''', (hallazgo_id, 'critica', f'Ruta crítica encontrada: {path}'))
                
                conn.commit()
                print("✅ Datos de muestra insertados")
        except Exception as e:
            print(f"⚠️  Error insertando datos de muestra: {e}")
    
    def get_connection(self):
        return sqlite3.connect(self.db_path)
    
    def get_cached_data(self, key: str, query_func, *args, **kwargs):
        """Sistema de cache para consultas"""
        current_time = time.time()
        
        if (key in self.cache and 
            key in self.last_update and 
            current_time - self.last_update[key] < self.cache_timeout):
            return self.cache[key]
        
        # Ejecutar query y cachear resultado
        result = query_func(*args, **kwargs)
        self.cache[key] = result
        self.last_update[key] = current_time
        
        return result
    
    def get_real_time_stats(self):
        """Obtener estadísticas en tiempo real"""
        try:
            with self.get_connection() as conn:
                stats = {}
                cursor = conn.cursor()
                
                # Total hallazgos
                cursor.execute("SELECT COUNT(*) FROM hallazgos")
                stats['total_findings'] = cursor.fetchone()[0] or 0
                
                # Hallazgos críticos
                cursor.execute("SELECT COUNT(*) FROM hallazgos WHERE es_critico = 1")
                stats['critical_findings'] = cursor.fetchone()[0] or 0
                
                # Alertas pendientes
                cursor.execute("SELECT COUNT(*) FROM alertas WHERE estado = 'pendiente'")
                stats['pending_alerts'] = cursor.fetchone()[0] or 0
                
                # Dominios activos
                cursor.execute("SELECT COUNT(*) FROM dominios WHERE activo = 1")
                stats['active_domains'] = cursor.fetchone()[0] or 0
                
                # Hallazgos últimas 24h
                cursor.execute("""
                    SELECT COUNT(*) FROM hallazgos 
                    WHERE fecha_descubierto > datetime('now', '-1 day')
                """)
                stats['findings_24h'] = cursor.fetchone()[0] or 0
                
                # Hallazgos críticos últimas 24h
                cursor.execute("""
                    SELECT COUNT(*) FROM hallazgos 
                    WHERE es_critico = 1 AND fecha_descubierto > datetime('now', '-1 day')
                """)
                stats['critical_24h'] = cursor.fetchone()[0] or 0
                
                # Tiempo promedio de respuesta a alertas
                cursor.execute("""
                    SELECT AVG((julianday(fecha_atendida) - julianday(fecha_creada)) * 24) 
                    FROM alertas 
                    WHERE fecha_atendida IS NOT NULL
                """)
                avg_response = cursor.fetchone()[0]
                stats['avg_response_hours'] = round(avg_response, 2) if avg_response else 0
                
                return stats
        except Exception as e:
            print(f"Error obteniendo estadísticas: {e}")
            return {
                'total_findings': 0,
                'critical_findings': 0,
                'pending_alerts': 0,
                'active_domains': 0,
                'findings_24h': 0,
                'critical_24h': 0,
                'avg_response_hours': 0
            }
    
    def get_recent_alerts(self, limit=50):
        """Obtener alertas recientes"""
        try:
            with self.get_connection() as conn:
                cursor = conn.cursor()
                cursor.execute('''
                    SELECT a.id, a.tipo_alerta, a.mensaje, a.estado, a.fecha_creada,
                           COALESCE(h.url_completa, 'N/A') as url_completa, 
                           COALESCE(h.codigo_http, 0) as codigo_http, 
                           COALESCE(d.dominio, 'N/A') as dominio,
                           a.analista, a.comentarios, a.fecha_atendida,
                           COALESCE(h.ruta, 'N/A') as ruta, 
                           COALESCE(h.fecha_descubierto, a.fecha_creada) as fecha_descubierto, 
                           COALESCE(h.es_critico, 0) as es_critico
                    FROM alertas a
                    LEFT JOIN hallazgos h ON a.hallazgo_id = h.id
                    LEFT JOIN dominios d ON h.dominio_id = d.id
                    ORDER BY a.fecha_creada DESC
                    LIMIT ?
                ''', (limit,))
                return cursor.fetchall()
        except Exception as e:
            print(f"Error obteniendo alertas: {e}")
            return []
    
    def get_findings_timeline(self, days: int = 30):
        """Obtener timeline de hallazgos"""
        return self.get_cached_data(
            f'timeline_{days}', 
            self._get_findings_timeline_query, 
            days
        )
    
    def _get_findings_timeline_query(self, days: int):
        try:
            with self.get_connection() as conn:
                df = pd.read_sql_query("""
                    SELECT 
                        DATE(fecha_descubierto) as fecha,
                        COUNT(*) as total,
                        COUNT(CASE WHEN es_critico = 1 THEN 1 END) as criticos,
                        COUNT(CASE WHEN codigo_http = 200 THEN 1 END) as exitosos
                    FROM hallazgos 
                    WHERE fecha_descubierto > datetime('now', '-{} days')
                    GROUP BY DATE(fecha_descubierto)
                    ORDER BY fecha
                """.format(days), conn)
                
                return df.to_dict('records')
        except Exception as e:
            print(f"Error obteniendo timeline: {e}")
            return []
    
    def get_domain_analysis(self):
        """Análisis por dominio"""
        return self.get_cached_data('domain_analysis', self._get_domain_analysis_query)
    
    def _get_domain_analysis_query(self):
        try:
            with self.get_connection() as conn:
                df = pd.read_sql_query("""
                    SELECT 
                        d.dominio,
                        COUNT(h.id) as total_hallazgos,
                        COUNT(CASE WHEN h.es_critico = 1 THEN 1 END) as criticos,
                        COUNT(CASE WHEN h.codigo_http = 200 THEN 1 END) as exitosos,
                        MAX(h.fecha_descubierto) as ultimo_hallazgo
                    FROM dominios d
                    LEFT JOIN hallazgos h ON d.id = h.dominio_id
                    WHERE d.activo = 1
                    GROUP BY d.dominio
                    ORDER BY total_hallazgos DESC
                """, conn)
                
                return df.to_dict('records')
        except Exception as e:
            print(f"Error obteniendo análisis de dominios: {e}")
            return []

    def get_alert_details(self, alert_id):
        """Obtener detalles de una alerta específica"""
        try:
            with self.get_connection() as conn:
                cursor = conn.cursor()
                cursor.execute('''
                    SELECT a.*, 
                           COALESCE(h.url_completa, 'N/A') as url_completa, 
                           COALESCE(h.ruta, 'N/A') as ruta, 
                           COALESCE(h.codigo_http, 0) as codigo_http,
                           COALESCE(h.fecha_descubierto, a.fecha_creada) as fecha_descubierto, 
                           COALESCE(d.dominio, 'N/A') as dominio, 
                           COALESCE(h.es_critico, 0) as es_critico,
                           COALESCE(h.tamano_respuesta, 0) as tamano_respuesta, 
                           COALESCE(h.herramienta, 'N/A') as herramienta
                    FROM alertas a
                    LEFT JOIN hallazgos h ON a.hallazgo_id = h.id
                    LEFT JOIN dominios d ON h.dominio_id = d.id
                    WHERE a.id = ?
                ''', (alert_id,))
                return cursor.fetchone()
        except Exception as e:
            print(f"Error obteniendo detalles de alerta: {e}")
            return None
    
    def update_alert_status(self, alert_id, status, analyst, comments=None):
        """Actualizar estado de una alerta"""
        try:
            with self.get_connection() as conn:
                cursor = conn.cursor()
                update_time = datetime.now().isoformat() if status != 'pendiente' else None
                cursor.execute('''
                    UPDATE alertas 
                    SET estado = ?, analista = ?, comentarios = ?, fecha_atendida = ?
                    WHERE id = ?
                ''', (status, analyst, comments, update_time, alert_id))
                conn.commit()
                return True
        except Exception as e:
            print(f"Error actualizando alerta: {e}")
            return False
    
    def get_findings_by_domain(self, domain=None, date_from=None, date_to=None, limit=1000):
        """Obtener hallazgos filtrados"""
        try:
            with self.get_connection() as conn:
                cursor = conn.cursor()
                
                query = '''
                    SELECT h.id, h.url_completa, h.ruta, h.codigo_http, 
                           h.es_critico, h.fecha_descubierto, 
                           COALESCE(d.dominio, 'N/A') as dominio,
                           COALESCE(h.tamano_respuesta, 0) as tamano_respuesta, 
                           COALESCE(h.herramienta, 'interno') as herramienta
                    FROM hallazgos h
                    LEFT JOIN dominios d ON h.dominio_id = d.id
                    WHERE 1=1
                '''
                params = []
                
                if domain:
                    query += " AND (d.dominio LIKE ? OR h.url_completa LIKE ?)"
                    params.extend([f"%{domain}%", f"%{domain}%"])
                
                if date_from:
                    query += " AND h.fecha_descubierto >= ?"
                    params.append(date_from)
                
                if date_to:
                    query += " AND h.fecha_descubierto <= ?"
                    params.append(date_to)
                
                query += " ORDER BY h.fecha_descubierto DESC LIMIT ?"
                params.append(limit)
                
                cursor.execute(query, params)
                return cursor.fetchall()
        except Exception as e:
            print(f"Error obteniendo hallazgos: {e}")
            return []

    def search_findings(self, query: str, filters: dict = None):
        """Búsqueda avanzada de hallazgos"""
        try:
            with self.get_connection() as conn:
                base_query = """
                    SELECT h.*, d.dominio
                    FROM hallazgos h
                    LEFT JOIN dominios d ON h.dominio_id = d.id
                    WHERE 1=1
                """
                
                params = []
                
                # Búsqueda de texto
                if query:
                    base_query += " AND (h.ruta LIKE ? OR h.url_completa LIKE ? OR d.dominio LIKE ?)"
                    search_term = f"%{query}%"
                    params.extend([search_term, search_term, search_term])
                
                # Filtros adicionales
                if filters:
                    if filters.get('domain'):
                        base_query += " AND d.dominio = ?"
                        params.append(filters['domain'])
                    
                    if filters.get('critical_only'):
                        base_query += " AND h.es_critico = 1"
                    
                    if filters.get('status_code'):
                        base_query += " AND h.codigo_http = ?"
                        params.append(filters['status_code'])
                    
                    if filters.get('date_from'):
                        base_query += " AND h.fecha_descubierto >= ?"
                        params.append(filters['date_from'])
                    
                    if filters.get('date_to'):
                        base_query += " AND h.fecha_descubierto <= ?"
                        params.append(filters['date_to'])
                
                base_query += " ORDER BY h.fecha_descubierto DESC LIMIT 1000"
                
                df = pd.read_sql_query(base_query, conn, params=params)
                return df.to_dict('records')
        except Exception as e:
            print(f"Error en búsqueda: {e}")
            return []

# Instancia global del manager
dashboard_manager = ConsolidatedDashboardManager(DATABASE_FILE)

# Funciones para generar gráficos
def create_timeline_chart(data):
    """Crear gráfico de timeline"""
    if not data:
        return go.Figure()
    
    df = pd.DataFrame(data)
    
    fig = make_subplots(
        rows=2, cols=1,
        subplot_titles=('Hallazgos Totales', 'Hallazgos Críticos'),
        vertical_spacing=0.1
    )
    
    # Hallazgos totales
    fig.add_trace(
        go.Scatter(
            x=df['fecha'],
            y=df['total'],
            mode='lines+markers',
            name='Total',
            line=dict(color='#3498db', width=3),
            marker=dict(size=6)
        ),
        row=1, col=1
    )
    
    # Hallazgos críticos
    fig.add_trace(
        go.Scatter(
            x=df['fecha'],
            y=df['criticos'],
            mode='lines+markers',
            name='Críticos',
            line=dict(color='#e74c3c', width=3),
            marker=dict(size=6),
            fill='tonexty',
            fillcolor='rgba(231, 76, 60, 0.1)'
        ),
        row=2, col=1
    )
    
    fig.update_layout(
        title='Timeline de Hallazgos (30 días)',
        height=500,
        showlegend=False,
        plot_bgcolor='rgba(0,0,0,0)',
        paper_bgcolor='rgba(0,0,0,0)'
    )
    
    return fig

def create_domain_chart(data):
    """Crear gráfico de análisis por dominio"""
    if not data:
        return go.Figure()
    
    df = pd.DataFrame(data).head(10)  # Top 10
    
    fig = go.Figure(data=[
        go.Bar(
            x=df['total_hallazgos'],
            y=df['dominio'],
            orientation='h',
            marker=dict(
                color=df['criticos'],
                colorscale='Reds',
                showscale=True,
                colorbar=dict(title="Críticos")
            ),
            text=df['total_hallazgos'],
            textposition='inside'
        )
    ])
    
    fig.update_layout(
        title='Top 10 Dominios por Actividad',
        xaxis_title='Número de Hallazgos',
        yaxis_title='Dominio',
        height=400,
        plot_bgcolor='rgba(0,0,0,0)',
        paper_bgcolor='rgba(0,0,0,0)'
    )
    
    return fig

# Rutas principales de la aplicación

@app.route('/')
def dashboard():
    """Página principal del dashboard"""
    try:
        stats = dashboard_manager.get_real_time_stats()
        recent_alerts = dashboard_manager.get_recent_alerts(20)
        
        return render_template_string(DASHBOARD_TEMPLATE, 
                                    stats=stats, 
                                    alerts=recent_alerts,
                                    enumerate=enumerate)
    except Exception as e:
        flash(f'Error cargando dashboard: {str(e)}', 'error')
        return render_template_string(ERROR_TEMPLATE, error=str(e))

@app.route('/alerts')
def alerts_page():
    """Página de gestión de alertas"""
    try:
        status_filter = request.args.get('status', 'all')
        alerts = dashboard_manager.get_recent_alerts(100)
        
        if status_filter != 'all':
            alerts = [alert for alert in alerts if alert[3] == status_filter]
        
        return render_template_string(ALERTS_TEMPLATE, 
                                    alerts=alerts, 
                                    current_filter=status_filter,
                                    enumerate=enumerate)
    except Exception as e:
        flash(f'Error cargando alertas: {str(e)}', 'error')
        return redirect(url_for('dashboard'))

@app.route('/alert/<int:alert_id>')
def alert_detail(alert_id):
    """Detalles de una alerta específica"""
    try:
        alert = dashboard_manager.get_alert_details(alert_id)
        if not alert:
            flash('Alerta no encontrada', 'error')
            return redirect(url_for('alerts_page'))
        
        return render_template_string(ALERT_DETAIL_TEMPLATE, alert=alert)
    except Exception as e:
        flash(f'Error cargando alerta: {str(e)}', 'error')
        return redirect(url_for('alerts_page'))

@app.route('/update_alert', methods=['POST'])
def update_alert():
    """Actualizar estado de una alerta"""
    try:
        alert_id = request.form.get('alert_id')
        status = request.form.get('status')
        analyst = request.form.get('analyst')
        comments = request.form.get('comments')
        
        if not all([alert_id, status, analyst]):
            flash('Datos incompletos', 'error')
            return redirect(request.referrer or url_for('alerts_page'))
        
        success = dashboard_manager.update_alert_status(alert_id, status, analyst, comments)
        
        if success:
            flash('Alerta actualizada correctamente', 'success')
        else:
            flash('Error actualizando alerta', 'error')
        
        return redirect(url_for('alert_detail', alert_id=alert_id))
        
    except Exception as e:
        flash(f'Error actualizando alerta: {str(e)}', 'error')
        return redirect(request.referrer or url_for('alerts_page'))

@app.route('/findings')
def findings_page():
    """Página de hallazgos"""
    try:
        domain_filter = request.args.get('domain', '')
        date_from = request.args.get('date_from', '')
        date_to = request.args.get('date_to', '')
        
        findings = dashboard_manager.get_findings_by_domain(
            domain_filter if domain_filter else None,
            date_from if date_from else None,
            date_to if date_to else None
        )
        
        return render_template_string(FINDINGS_TEMPLATE,
                                    findings=findings,
                                    domain_filter=domain_filter,
                                    date_from=date_from,
                                    date_to=date_to,
                                    enumerate=enumerate)
    except Exception as e:
        flash(f'Error cargando hallazgos: {str(e)}', 'error')
        return redirect(url_for('dashboard'))

@app.route('/analytics')
def analytics_page():
    """Página de analytics avanzado"""
    return render_template_string(ANALYTICS_TEMPLATE)

# APIs

@app.route('/api/real-time-stats')
def api_real_time_stats():
    """API para estadísticas en tiempo real"""
    try:
        stats = dashboard_manager.get_real_time_stats()
        return jsonify(stats)
    except Exception as e:
        return jsonify({'error': str(e)}), 500

@app.route('/api/timeline/<int:days>')
def api_timeline(days):
    """API para timeline de hallazgos"""
    try:
        data = dashboard_manager.get_findings_timeline(days)
        return jsonify(data)
    except Exception as e:
        return jsonify({'error': str(e)}), 500

@app.route('/api/domain-analysis')
def api_domain_analysis():
    """API para análisis por dominio"""
    try:
        data = dashboard_manager.get_domain_analysis()
        return jsonify(data)
    except Exception as e:
        return jsonify({'error': str(e)}), 500

@app.route('/api/generate-chart/<chart_type>')
def api_generate_chart(chart_type):
    """Generar gráficos dinámicos"""
    try:
        if chart_type == 'timeline':
            data = dashboard_manager.get_findings_timeline(30)
            fig = create_timeline_chart(data)
        elif chart_type == 'domain_analysis':
            data = dashboard_manager.get_domain_analysis()
            fig = create_domain_chart(data)
        else:
            return jsonify({'error': 'Invalid chart type'}), 400
        
        return jsonify(json.loads(plotly.utils.PlotlyJSONEncoder().encode(fig)))
    except Exception as e:
        return jsonify({'error': str(e)}), 500

@app.route('/api/search')
def api_search():
    """API para búsqueda avanzada"""
    try:
        query = request.args.get('q', '')
        filters = {
            'domain': request.args.get('domain'),
            'critical_only': request.args.get('critical') == 'true',
            'status_code': request.args.get('status'),
            'date_from': request.args.get('from'),
            'date_to': request.args.get('to')
        }
        
        # Filtrar valores None
        filters = {k: v for k, v in filters.items() if v is not None}
        
        results = dashboard_manager.search_findings(query, filters)
        return jsonify(results)
    except Exception as e:
        return jsonify({'error': str(e)}), 500

@app.route('/test')
def test_page():
    """Página de pruebas para desarrollo"""
    try:
        stats = dashboard_manager.get_real_time_stats()
        
        return jsonify({
            'status': 'ok',
            'message': 'Sistema funcionando correctamente',
            'stats': stats,
            'platform': platform.system(),
            'python_version': platform.python_version(),
            'database_path': str(DATABASE_FILE),
            'database_exists': DATABASE_FILE.exists()
        })
        
    except Exception as e:
        return jsonify({'status': 'error', 'message': str(e)}), 500

# WebSocket events para actualizaciones en tiempo real

@socketio.on('connect')
def handle_connect():
    """Manejar conexión WebSocket"""
    emit('status', {'msg': 'Conectado al dashboard en tiempo real'})

@socketio.on('request_update')
def handle_request_update():
    """Manejar solicitud de actualización"""
    try:
        stats = dashboard_manager.get_real_time_stats()
        emit('stats_update', stats)
    except Exception as e:
        emit('error', {'msg': str(e)})

# Hilo para actualizaciones automáticas
def background_updates():
    """Enviar actualizaciones en segundo plano"""
    while True:
        try:
            stats = dashboard_manager.get_real_time_stats()
            socketio.emit('stats_update', stats)
            time.sleep(30)  # Actualizar cada 30 segundos
        except Exception as e:
            print(f"Error en actualización automática: {e}")
            time.sleep(60)

# Templates HTML

DASHBOARD_TEMPLATE = '''<!DOCTYPE html>
<html lang="es">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>Dashboard de Seguridad Consolidado</title>
    <link href="https://cdn.jsdelivr.net/npm/bootstrap@5.3.0/dist/css/bootstrap.min.css" rel="stylesheet">
    <link href="https://cdnjs.cloudflare.com/ajax/libs/font-awesome/6.4.0/css/all.min.css" rel="stylesheet">
    <script src="https://cdn.plot.ly/plotly-latest.min.js"></script>
    <script src="https://cdn.socket.io/4.0.0/socket.io.min.js"></script>
    <style>
        :root {
            --primary-color: #667eea;
            --secondary-color: #764ba2;
            --success-color: #00d4aa;
            --warning-color: #f093fb;
            --danger-color: #fc466b;
        }
        
        body {
            background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
            min-height: 100vh;
            font-family: 'Segoe UI', Tahoma, Geneva, Verdana, sans-serif;
        }
        
        .glassmorphism {
            background: rgba(255, 255, 255, 0.25);
            box-shadow: 0 8px 32px 0 rgba(31, 38, 135, 0.37);
            backdrop-filter: blur(4px);
            border-radius: 15px;
            border: 1px solid rgba(255, 255, 255, 0.18);
        }
        
        .metric-card {
            transition: all 0.3s ease;
            cursor: pointer;
        }
        
        .metric-card:hover {
            transform: translateY(-5px);
            box-shadow: 0 15px 40px rgba(0,0,0,0.2);
        }
        
        .metric-number {
            font-size: 2.5rem;
            font-weight: 700;
            margin: 0;
        }
        
        .chart-container {
            background: rgba(255, 255, 255, 0.95);
            border-radius: 15px;
            padding: 20px;
            margin: 20px 0;
            box-shadow: 0 10px 30px rgba(0,0,0,0.1);
        }
        
        .navbar-custom {
            background: rgba(255, 255, 255, 0.1);
            backdrop-filter: blur(10px);
        }
        
        .pulse {
            animation: pulse 2s infinite;
        }
        
        @keyframes pulse {
            0% { transform: scale(1); }
            50% { transform: scale(1.05); }
            100% { transform: scale(1); }
        }
        
        .live-indicator {
            display: inline-block;
            width: 10px;
            height: 10px;
            background: #00ff00;
            border-radius: 50%;
            animation: blink 1s infinite;
        }
        
        @keyframes blink {
            0%, 50% { opacity: 1; }
            51%, 100% { opacity: 0.3; }
        }
        
        .search-container {
            position: relative;
            margin: 20px 0;
        }
        
        .search-results {
            position: absolute;
            top: 100%;
            left: 0;
            right: 0;
            background: white;
            border-radius: 10px;
            box-shadow: 0 10px 30px rgba(0,0,0,0.2);
            max-height: 400px;
            overflow-y: auto;
            z-index: 1000;
            display: none;
        }
    </style>
</head>
<body>
    <!-- Navbar -->
    <nav class="navbar navbar-expand-lg navbar-custom">
        <div class="container-fluid">
            <a class="navbar-brand text-white fw-bold" href="/">
                <i class="fas fa-shield-alt"></i> Panel de Control de URL - DCEA
                <span class="live-indicator ms-2"></span>
                <small class="text-light">ACTIVO</small>
            </a>
            <div class="navbar-nav ms-auto">
                <a class="nav-link text-white" href="/"><i class="fas fa-home"></i> Dashboard</a>
                <a class="nav-link text-white" href="/alerts"><i class="fas fa-bell"></i> Alertas</a>
                <a class="nav-link text-white" href="/findings"><i class="fas fa-search"></i> Hallazgos</a>
                <a class="nav-link text-white" href="/analytics"><i class="fas fa-chart-line"></i> Analytics</a>
                <a class="nav-link text-white" href="/test"><i class="fas fa-flask"></i> Test</a>
            </div>
        </div>
    </nav>

    <div class="container-fluid mt-4">
        <!-- Mensajes flash -->
        {% with messages = get_flashed_messages(with_categories=true) %}
            {% if messages %}
                {% for category, message in messages %}
                    <div class="alert alert-{{ 'danger' if category == 'error' else 'success' }} alert-dismissible fade show">
                        {{ message }}
                        <button type="button" class="btn-close" data-bs-dismiss="alert"></button>
                    </div>
                {% endfor %}
            {% endif %}
        {% endwith %}

        <!-- Búsqueda avanzada -->
        <div class="row mb-4">
            <div class="col-12">
                <div class="search-container">
                    <div class="input-group">
                        <input type="text" class="form-control form-control-lg" 
                               id="searchInput" placeholder="Búsqueda inteligente: dominios, rutas, IPs...">
                        <button class="btn btn-primary" type="button" onclick="performSearch()">
                            <i class="fas fa-search"></i>
                        </button>
                    </div>
                    <div class="search-results" id="searchResults"></div>
                </div>
            </div>
        </div>

        <!-- Métricas en tiempo real -->
        <div class="row mb-4">
            <div class="col-md-2">
                <div class="card metric-card glassmorphism text-white h-100">
                    <div class="card-body text-center">
                        <div class="metric-number" id="totalFindings">{{ stats.total_findings }}</div>
                        <p class="mb-0"><i class="fas fa-search"></i> Total Hallazgos</p>
                        <small class="text-light">Histórico completo</small>
                    </div>
                </div>
            </div>
            <div class="col-md-2">
                <div class="card metric-card glassmorphism text-white h-100">
                    <div class="card-body text-center">
                        <div class="metric-number pulse" id="criticalFindings">{{ stats.critical_findings }}</div>
                        <p class="mb-0"><i class="fas fa-exclamation-triangle"></i> Críticos</p>
                        <small class="text-light">Requieren atención</small>
                    </div>
                </div>
            </div>
            <div class="col-md-2">
                <div class="card metric-card glassmorphism text-white h-100">
                    <div class="card-body text-center">
                        <div class="metric-number" id="pendingAlerts">{{ stats.pending_alerts }}</div>
                        <p class="mb-0"><i class="fas fa-bell"></i> Pendientes</p>
                        <small class="text-light">Sin atender</small>
                    </div>
                </div>
            </div>
            <div class="col-md-2">
                <div class="card metric-card glassmorphism text-white h-100">
                    <div class="card-body text-center">
                        <div class="metric-number" id="activeDomains">{{ stats.active_domains }}</div>
                        <p class="mb-0"><i class="fas fa-globe"></i> Dominios</p>
                        <small class="text-light">Activos</small>
                    </div>
                </div>
            </div>
            <div class="col-md-2">
                <div class="card metric-card glassmorphism text-white h-100">
                    <div class="card-body text-center">
                        <div class="metric-number" id="findings24h">{{ stats.findings_24h }}</div>
                        <p class="mb-0"><i class="fas fa-clock"></i> 24h</p>
                        <small class="text-light">Últimas horas</small>
                    </div>
                </div>
            </div>
            <div class="col-md-2">
                <div class="card metric-card glassmorphism text-white h-100">
                    <div class="card-body text-center">
                        <div class="metric-number" id="responseTime">{{ stats.avg_response_hours }}</div>
                        <p class="mb-0"><i class="fas fa-stopwatch"></i> MTTR</p>
                        <small class="text-light">Horas promedio</small>
                    </div>
                </div>
            </div>
        </div>

        <!-- Gráficos principales -->
        <div class="row">
            <div class="col-lg-8">
                <div class="chart-container">
                    <h5><i class="fas fa-chart-line text-primary"></i> Timeline de Hallazgos</h5>
                    <div id="timelineChart" style="height: 400px;"></div>
                </div>
            </div>
            <div class="col-lg-4">
                <div class="chart-container">
                    <h5><i class="fas fa-server text-info"></i> Análisis por Dominio</h5>
                    <div id="domainChart" style="height: 400px;"></div>
                </div>
            </div>
        </div>

        <!-- Alertas recientes -->
        <div class="row mt-4">
            <div class="col-md-8">
                <div class="chart-container">
                    <div class="d-flex justify-content-between align-items-center mb-3">
                        <h5><i class="fas fa-bell text-danger"></i> Alertas Recientes</h5>
                        <a href="/alerts" class="btn btn-primary btn-sm">Ver Todas</a>
                    </div>
                    
                    {% if alerts %}
                        <div class="table-responsive">
                            <table class="table table-hover">
                                <thead>
                                    <tr>
                                        <th>Tipo</th>
                                        <th>Dominio</th>
                                        <th>Estado</th>
                                        <th>Fecha</th>
                                        <th>Acción</th>
                                    </tr>
                                </thead>
                                <tbody>
                                    {% for alert in alerts[:10] %}
                                    <tr class="{{ 'table-danger' if alert[1] == 'critica' else '' }}">
                                        <td>
                                            <span class="badge bg-{{ 'danger' if alert[1] == 'critica' else 'warning' }}">
                                                {{ alert[1]|upper }}
                                            </span>
                                        </td>
                                        <td>{{ alert[7] or 'N/A' }}</td>
                                        <td>
                                            <span class="badge bg-{{ 'warning' if alert[3] == 'pendiente' else 'info' if alert[3] == 'en-revision' else 'success' }}">
                                                {{ alert[3] }}
                                            </span>
                                        </td>
                                        <td>{{ alert[4][:16] if alert[4] else 'N/A' }}</td>
                                        <td>
                                            <a href="/alert/{{ alert[0] }}" class="btn btn-sm btn-outline-primary">
                                                <i class="fas fa-eye"></i>
                                            </a>
                                        </td>
                                    </tr>
                                    {% endfor %}
                                </tbody>
                            </table>
                        </div>
                    {% else %}
                        <div class="text-center py-4">
                            <i class="fas fa-inbox fa-3x text-muted mb-3"></i>
                            <h5 class="text-muted">No hay alertas</h5>
                            <p class="text-muted">¡Excelente! Todo está funcionando correctamente.</p>
                        </div>
                    {% endif %}
                </div>
            </div>
            
            <div class="col-md-4">
                <div class="chart-container">
                    <h5><i class="fas fa-tools text-success"></i> Acciones Rápidas</h5>
                    <div class="d-grid gap-2">
                        <button class="btn btn-outline-primary" onclick="refreshData()">
                            <i class="fas fa-sync"></i> Actualizar Datos
                        </button>
                        <a href="/findings" class="btn btn-outline-info">
                            <i class="fas fa-search"></i> Ver Hallazgos
                        </a>
                        <a href="/analytics" class="btn btn-outline-success">
                            <i class="fas fa-chart-line"></i> Analytics
                        </a>
                        <a href="/test" class="btn btn-outline-warning">
                            <i class="fas fa-flask"></i> Diagnóstico
                        </a>
                    </div>
                </div>
            </div>
        </div>
    </div>

    <script src="https://cdn.jsdelivr.net/npm/bootstrap@5.3.0/dist/js/bootstrap.bundle.min.js"></script>
    <script>
        // Configurar Socket.IO
        const socket = io();
        
        socket.on('connect', function() {
            console.log('Conectado al servidor en tiempo real');
        });
        
        socket.on('stats_update', function(stats) {
            updateMetrics(stats);
        });
        
        // Actualizar métricas
        function updateMetrics(stats) {
            document.getElementById('totalFindings').textContent = stats.total_findings;
            document.getElementById('criticalFindings').textContent = stats.critical_findings;
            document.getElementById('pendingAlerts').textContent = stats.pending_alerts;
            document.getElementById('activeDomains').textContent = stats.active_domains;
            document.getElementById('findings24h').textContent = stats.findings_24h;
            document.getElementById('responseTime').textContent = stats.avg_response_hours;
        }
        
        // Cargar gráficos
        async function loadCharts() {
            try {
                // Timeline
                const timelineResponse = await fetch('/api/generate-chart/timeline');
                const timelineData = await timelineResponse.json();
                Plotly.newPlot('timelineChart', timelineData.data, timelineData.layout, {responsive: true});
                
                // Análisis por dominio
                const domainResponse = await fetch('/api/generate-chart/domain_analysis');
                const domainData = await domainResponse.json();
                Plotly.newPlot('domainChart', domainData.data, domainData.layout, {responsive: true});
                
            } catch (error) {
                console.error('Error cargando gráficos:', error);
            }
        }
        
        // Búsqueda inteligente
        let searchTimeout;
        document.getElementById('searchInput').addEventListener('input', function() {
            clearTimeout(searchTimeout);
            searchTimeout = setTimeout(() => {
                const query = this.value;
                if (query.length > 2) {
                    performLiveSearch(query);
                } else {
                    document.getElementById('searchResults').style.display = 'none';
                }
            }, 300);
        });
        
        async function performLiveSearch(query) {
            try {
                const response = await fetch(`/api/search?q=${encodeURIComponent(query)}`);
                const results = await response.json();
                displaySearchResults(results);
            } catch (error) {
                console.error('Error en búsqueda:', error);
            }
        }
        
        function displaySearchResults(results) {
            const resultsContainer = document.getElementById('searchResults');
            if (results.length === 0) {
                resultsContainer.style.display = 'none';
                return;
            }
            
            let html = '';
            results.slice(0, 10).forEach(result => {
                const priority = result.es_critico ? 'CRÍTICO' : 'Normal';
                const priorityClass = result.es_critico ? 'danger' : 'secondary';
                
                html += `
                    <div class="p-3 border-bottom">
                        <div class="d-flex justify-content-between">
                            <strong>${result.dominio || 'N/A'}</strong>
                            <span class="badge bg-${priorityClass}">${priority}</span>
                        </div>
                        <div class="text-muted">${result.url_completa}</div>
                        <small class="text-muted">Código: ${result.codigo_http} | ${result.fecha_descubierto}</small>
                    </div>
                `;
            });
            
            resultsContainer.innerHTML = html;
            resultsContainer.style.display = 'block';
        }
        
        function performSearch() {
            const query = document.getElementById('searchInput').value;
            if (query) {
                window.location.href = `/findings?domain=${encodeURIComponent(query)}`;
            }
        }
        
        function refreshData() {
            location.reload();
        }
        
        // Inicializar dashboard
        document.addEventListener('DOMContentLoaded', function() {
            loadCharts();
            
            // Solicitar actualizaciones cada 30 segundos
            setInterval(() => {
                socket.emit('request_update');
            }, 30000);
        });
        
        // Ocultar resultados de búsqueda al hacer click fuera
        document.addEventListener('click', function(e) {
            const searchContainer = document.querySelector('.search-container');
            if (!searchContainer.contains(e.target)) {
                document.getElementById('searchResults').style.display = 'none';
            }
        });
    </script>
</body>
</html>'''

ALERTS_TEMPLATE = '''<!DOCTYPE html>
<html lang="es">
<head>
    <meta charset="UTF-8">
    <title>Gestión de Alertas - Dashboard</title>
    <link href="https://cdn.jsdelivr.net/npm/bootstrap@5.3.0/dist/css/bootstrap.min.css" rel="stylesheet">
    <link href="https://cdnjs.cloudflare.com/ajax/libs/font-awesome/6.4.0/css/all.min.css" rel="stylesheet">
    <style>
        body { 
            background: linear-gradient(135deg, #667eea 0%, #764ba2 100%); 
            min-height: 100vh; 
        }
        .card { 
            border: none; 
            border-radius: 15px; 
            box-shadow: 0 8px 25px rgba(0,0,0,0.1); 
            background: rgba(255, 255, 255, 0.95);
        }
        .alert-critical { 
            background-color: #ffe6e6; 
            border-left: 4px solid #dc3545; 
        }
        .navbar-custom {
            background: rgba(255, 255, 255, 0.1);
            backdrop-filter: blur(10px);
        }
    </style>
</head>
<body>
    <nav class="navbar navbar-expand-lg navbar-custom">
        <div class="container">
            <a class="navbar-brand text-white fw-bold" href="/">
                <i class="fas fa-shield-alt"></i> Panel de Control de URL - DCEA
            </a>
            <div class="navbar-nav ms-auto">
                <a class="nav-link text-white" href="/">Dashboard</a>
                <a class="nav-link text-white active" href="/alerts">Alertas</a>
                <a class="nav-link text-white" href="/findings">Hallazgos</a>
            </div>
        </div>
    </nav>
    
    <div class="container mt-4">
        <div class="d-flex justify-content-between align-items-center mb-4">
            <h2 class="text-white"><i class="fas fa-bell text-warning"></i> Gestión de Alertas</h2>
            <div class="btn-group">
                <a href="/alerts" class="btn btn-outline-light {{ 'active' if current_filter == 'all' else '' }}">Todas</a>
                <a href="/alerts?status=pendiente" class="btn btn-outline-warning {{ 'active' if current_filter == 'pendiente' else '' }}">Pendientes</a>
                <a href="/alerts?status=en-revision" class="btn btn-outline-info {{ 'active' if current_filter == 'en-revision' else '' }}">En Revisión</a>
                <a href="/alerts?status=resuelto" class="btn btn-outline-success {{ 'active' if current_filter == 'resuelto' else '' }}">Resueltas</a>
            </div>
        </div>
        
        <div class="card">
            <div class="card-header bg-primary text-white">
                <h5 class="mb-0">Lista de Alertas <span class="badge bg-light text-dark">{{ alerts|length }}</span></h5>
            </div>
            <div class="card-body">
                {% if alerts %}
                    <div class="table-responsive">
                        <table class="table table-striped table-hover">
                            <thead class="table-dark">
                                <tr>
                                    <th>ID</th>
                                    <th>Tipo</th>
                                    <th>Mensaje</th>
                                    <th>Estado</th>
                                    <th>Dominio</th>
                                    <th>Fecha</th>
                                    <th>Acciones</th>
                                </tr>
                            </thead>
                            <tbody>
                                {% for alert in alerts %}
                                <tr class="{{ 'alert-critical' if alert[1] == 'critica' else '' }}">
                                    <td><strong>#{{ alert[0] }}</strong></td>
                                    <td>
                                        <span class="badge bg-{{ 'danger' if alert[1] == 'critica' else 'warning' }}">
                                            {{ alert[1]|upper }}
                                        </span>
                                    </td>
                                    <td>{{ alert[2][:50] }}{% if alert[2]|length > 50 %}...{% endif %}</td>
                                    <td>
                                        <span class="badge bg-{{ 'warning' if alert[3] == 'pendiente' else 'info' if alert[3] == 'en-revision' else 'success' }}">
                                            {{ alert[3] }}
                                        </span>
                                    </td>
                                    <td>{{ alert[7] or 'N/A' }}</td>
                                    <td>{{ alert[4][:16] if alert[4] else 'N/A' }}</td>
                                    <td>
                                        <a href="/alert/{{ alert[0] }}" class="btn btn-sm btn-primary">
                                            <i class="fas fa-eye"></i> Ver
                                        </a>
                                    </td>
                                </tr>
                                {% endfor %}
                            </tbody>
                        </table>
                    </div>
                {% else %}
                    <div class="text-center py-5">
                        <i class="fas fa-inbox fa-3x text-muted mb-3"></i>
                        <h5 class="text-muted">No hay alertas disponibles</h5>
                        <p class="text-muted">{{ 'No se encontraron alertas con el filtro seleccionado.' if current_filter != 'all' else '¡Excelente! No hay alertas pendientes.' }}</p>
                    </div>
                {% endif %}
            </div>
        </div>
    </div>
    
    <script src="https://cdn.jsdelivr.net/npm/bootstrap@5.3.0/dist/js/bootstrap.bundle.min.js"></script>
</body>
</html>'''

ALERT_DETAIL_TEMPLATE = '''<!DOCTYPE html>
<html lang="es">
<head>
    <meta charset="UTF-8">
    <title>Alerta #{{ alert[0] }} - Dashboard</title>
    <link href="https://cdn.jsdelivr.net/npm/bootstrap@5.3.0/dist/css/bootstrap.min.css" rel="stylesheet">
    <link href="https://cdnjs.cloudflare.com/ajax/libs/font-awesome/6.4.0/css/all.min.css" rel="stylesheet">
    <style>
        body { 
            background: linear-gradient(135deg, #667eea 0%, #764ba2 100%); 
            min-height: 100vh; 
        }
        .card { 
            border: none; 
            border-radius: 15px; 
            box-shadow: 0 8px 25px rgba(0,0,0,0.1); 
            background: rgba(255, 255, 255, 0.95);
        }
        .navbar-custom {
            background: rgba(255, 255, 255, 0.1);
            backdrop-filter: blur(10px);
        }
    </style>
</head>
<body>
    <nav class="navbar navbar-expand-lg navbar-custom">
        <div class="container">
            <a class="navbar-brand text-white fw-bold" href="/">Panel de Control de URL - DCEA</a>
            <div class="navbar-nav ms-auto">
                <a class="nav-link text-white" href="/">Dashboard</a>
                <a class="nav-link text-white" href="/alerts">Alertas</a>
            </div>
        </div>
    </nav>
    
    <div class="container mt-4">
        <div class="d-flex justify-content-between align-items-center mb-4">
            <h2 class="text-white">Alerta #{{ alert[0] }}</h2>
            <a href="/alerts" class="btn btn-outline-light">
                <i class="fas fa-arrow-left"></i> Volver
            </a>
        </div>
        
        <div class="row">
            <div class="col-md-8">
                <div class="card">
                    <div class="card-header bg-info text-white">
                        <h5>Información de la Alerta</h5>
                    </div>
                    <div class="card-body">
                        <div class="row">
                            <div class="col-md-6">
                                <p><strong>ID:</strong> #{{ alert[0] }}</p>
                                <p><strong>Tipo:</strong> 
                                    <span class="badge bg-{{ 'danger' if alert[1] == 'critica' else 'warning' }}">
                                        {{ alert[1]|upper }}
                                    </span>
                                </p>
                                <p><strong>Estado:</strong> 
                                    <span class="badge bg-{{ 'warning' if alert[3] == 'pendiente' else 'info' if alert[3] == 'en-revision' else 'success' }}">
                                        {{ alert[3] }}
                                    </span>
                                </p>
                                <p><strong>Dominio:</strong> {{ alert[14] or 'N/A' }}</p>
                            </div>
                            <div class="col-md-6">
                                <p><strong>Fecha Creación:</strong> {{ alert[4] }}</p>
                                <p><strong>Código HTTP:</strong> {{ alert[11] or 'N/A' }}</p>
                                <p><strong>Ruta:</strong> <code>{{ alert[10] or 'N/A' }}</code></p>
                                <p><strong>Analista:</strong> {{ alert[5] or 'Sin asignar' }}</p>
                            </div>
                        </div>
                        
                        {% if alert[9] and alert[9] != 'N/A' %}
                        <hr>
                        <div class="mb-3">
                            <label><strong>URL Completa:</strong></label>
                            <div class="input-group">
                                <input type="text" class="form-control" value="{{ alert[9] }}" readonly>
                                <a href="{{ alert[9] }}" target="_blank" class="btn btn-outline-primary">
                                    <i class="fas fa-external-link-alt"></i> Abrir
                                </a>
                            </div>
                        </div>
                        {% endif %}
                        
                        <div class="alert alert-{{ 'danger' if alert[1] == 'critica' else 'warning' }}">
                            <strong>Mensaje:</strong> {{ alert[2] }}
                        </div>
                        
                        {% if alert[6] %}
                        <div class="mb-3">
                            <label><strong>Comentarios:</strong></label>
                            <div class="border p-3 bg-light rounded">{{ alert[6] }}</div>
                        </div>
                        {% endif %}
                    </div>
                </div>
            </div>
            
            <div class="col-md-4">
                <div class="card">
                    <div class="card-header bg-success text-white">
                        <h5>Actualizar Estado</h5>
                    </div>
                    <div class="card-body">
                        <form method="POST" action="/update_alert">
                            <input type="hidden" name="alert_id" value="{{ alert[0] }}">
                            
                            <div class="mb-3">
                                <label class="form-label">Estado</label>
                                <select class="form-select" name="status" required>
                                    <option value="pendiente" {{ 'selected' if alert[3] == 'pendiente' else '' }}>Pendiente</option>
                                    <option value="en-revision" {{ 'selected' if alert[3] == 'en-revision' else '' }}>En Revisión</option>
                                    <option value="resuelto" {{ 'selected' if alert[3] == 'resuelto' else '' }}>Resuelto</option>
                                    <option value="falso-positivo" {{ 'selected' if alert[3] == 'falso-positivo' else '' }}>Falso Positivo</option>
                                </select>
                            </div>
                            
                            <div class="mb-3">
                                <label class="form-label">Analista</label>
                                <input type="text" class="form-control" name="analyst" 
                                       value="{{ alert[5] if alert[5] else '' }}" required>
                            </div>
                            
                            <div class="mb-3">
                                <label class="form-label">Comentarios</label>
                                <textarea class="form-control" name="comments" rows="4">{{ alert[6] if alert[6] else '' }}</textarea>
                            </div>
                            
                            <button type="submit" class="btn btn-primary w-100">
                                <i class="fas fa-save"></i> Actualizar Alerta
                            </button>
                        </form>
                    </div>
                </div>
            </div>
        </div>
    </div>
</body>
</html>'''

FINDINGS_TEMPLATE = '''<!DOCTYPE html>
<html lang="es">
<head>
    <meta charset="UTF-8">
    <title>Hallazgos - Dashboard</title>
    <link href="https://cdn.jsdelivr.net/npm/bootstrap@5.3.0/dist/css/bootstrap.min.css" rel="stylesheet">
    <link href="https://cdnjs.cloudflare.com/ajax/libs/font-awesome/6.4.0/css/all.min.css" rel="stylesheet">
    <style>
        body { 
            background: linear-gradient(135deg, #667eea 0%, #764ba2 100%); 
            min-height: 100vh; 
        }
        .card { 
            border: none; 
            border-radius: 15px; 
            box-shadow: 0 8px 25px rgba(0,0,0,0.1); 
            background: rgba(255, 255, 255, 0.95);
        }
        .navbar-custom {
            background: rgba(255, 255, 255, 0.1);
            backdrop-filter: blur(10px);
        }
    </style>
</head>
<body>
    <nav class="navbar navbar-expand-lg navbar-custom">
        <div class="container">
            <a class="navbar-brand text-white fw-bold" href="/">Panel de Control de URL - DCEA</a>
            <div class="navbar-nav ms-auto">
                <a class="nav-link text-white" href="/">Dashboard</a>
                <a class="nav-link text-white" href="/alerts">Alertas</a>
                <a class="nav-link text-white active" href="/findings">Hallazgos</a>
            </div>
        </div>
    </nav>
    
    <div class="container mt-4">
        <h2 class="text-white mb-4"><i class="fas fa-search text-info"></i> Hallazgos de Seguridad</h2>
        
        <!-- Filtros -->
        <div class="card mb-4">
            <div class="card-body">
                <form method="GET" action="/findings">
                    <div class="row g-3">
                        <div class="col-md-4">
                            <label class="form-label">Dominio</label>
                            <input type="text" class="form-control" name="domain" 
                                   value="{{ domain_filter }}" placeholder="ejemplo.com">
                        </div>
                        <div class="col-md-3">
                            <label class="form-label">Desde</label>
                            <input type="date" class="form-control" name="date_from" value="{{ date_from }}">
                        </div>
                        <div class="col-md-3">
                            <label class="form-label">Hasta</label>
                            <input type="date" class="form-control" name="date_to" value="{{ date_to }}">
                        </div>
                        <div class="col-md-2">
                            <label class="form-label">&nbsp;</label>
                            <button type="submit" class="btn btn-primary w-100">
                                <i class="fas fa-filter"></i> Filtrar
                            </button>
                        </div>
                    </div>
                </form>
            </div>
        </div>
        
        <div class="card">
            <div class="card-header bg-info text-white">
                <h5 class="mb-0">Lista de Hallazgos <span class="badge bg-light text-dark">{{ findings|length }}</span></h5>
            </div>
            <div class="card-body">
                {% if findings %}
                    <div class="table-responsive">
                        <table class="table table-striped table-hover">
                            <thead class="table-dark">
                                <tr>
                                    <th>URL</th>
                                    <th>Ruta</th>
                                    <th>Código</th>
                                    <th>Criticidad</th>
                                    <th>Herramienta</th>
                                    <th>Fecha</th>
                                </tr>
                            </thead>
                            <tbody>
                                {% for finding in findings %}
                                <tr class="{{ 'table-danger' if finding[4] else '' }}">
                                    <td>
                                        <a href="{{ finding[1] }}" target="_blank" class="text-decoration-none">
                                            {{ finding[1][:50] }}{% if finding[1]|length > 50 %}...{% endif %}
                                            <i class="fas fa-external-link-alt ms-1"></i>
                                        </a>
                                    </td>
                                    <td><code>{{ finding[2] }}</code></td>
                                    <td>
                                        <span class="badge bg-{{ 'success' if finding[3] == 200 else 'warning' if finding[3] == 403 else 'danger' if finding[3] >= 500 else 'info' }}">
                                            {{ finding[3] }}
                                        </span>
                                    </td>
                                    <td>
                                        {% if finding[4] %}
                                            <span class="badge bg-danger">CRÍTICO</span>
                                        {% else %}
                                            <span class="badge bg-secondary">Normal</span>
                                        {% endif %}
                                    </td>
                                    <td>{{ finding[8] or 'interno' }}</td>
                                    <td>{{ finding[5][:16] if finding[5] else 'N/A' }}</td>
                                </tr>
                                {% endfor %}
                            </tbody>
                        </table>
                    </div>
                {% else %}
                    <div class="text-center py-5">
                        <i class="fas fa-search fa-3x text-muted mb-3"></i>
                        <h5 class="text-muted">No se encontraron hallazgos</h5>
                        <p class="text-muted">Ajusta los filtros o ejecuta un escaneo</p>
                    </div>
                {% endif %}
            </div>
        </div>
    </div>
</body>
</html>'''

ANALYTICS_TEMPLATE = '''<!DOCTYPE html>
<html lang="es">
<head>
    <meta charset="UTF-8">
    <title>Analytics Avanzado</title>
    <link href="https://cdn.jsdelivr.net/npm/bootstrap@5.3.0/dist/css/bootstrap.min.css" rel="stylesheet">
    <link href="https://cdnjs.cloudflare.com/ajax/libs/font-awesome/6.4.0/css/all.min.css" rel="stylesheet">
    <style>
        body { 
            background: linear-gradient(135deg, #667eea 0%, #764ba2 100%); 
            min-height: 100vh; 
        }
        .card { 
            border: none; 
            border-radius: 15px; 
            box-shadow: 0 8px 25px rgba(0,0,0,0.1); 
            background: rgba(255, 255, 255, 0.95);
        }
        .navbar-custom {
            background: rgba(255, 255, 255, 0.1);
            backdrop-filter: blur(10px);
        }
    </style>
</head>
<body>
    <nav class="navbar navbar-expand-lg navbar-custom">
        <div class="container">
            <a class="navbar-brand text-white fw-bold" href="/">Panel de Control de URL - DCEA</a>
            <div class="navbar-nav ms-auto">
                <a class="nav-link text-white" href="/">Dashboard</a>
                <a class="nav-link text-white" href="/alerts">Alertas</a>
                <a class="nav-link text-white" href="/findings">Hallazgos</a>
            </div>
        </div>
    </nav>

    <div class="container mt-4">
        <h1 class="text-white mb-4">🔬 Analytics Avanzado</h1>
        <p class="lead text-white">Análisis profundo de patrones de seguridad y tendencias</p>
        
        <!-- Contenido de analytics -->
        <div class="row">
            <div class="col-12">
                <div class="card">
                    <div class="card-body">
                        <div class="alert alert-info">
                            <h4><i class="fas fa-tools"></i> Analytics en Desarrollo</h4>
                            <p>Esta sección incluirá análisis avanzado con Machine Learning, correlaciones de eventos, y predicción de amenazas.</p>
                            <ul>
                                <li>📊 Análisis de tendencias temporales</li>
                                <li>🔗 Correlación de eventos de seguridad</li>
                                <li>🤖 Detección de anomalías con ML</li>
                                <li>📈 Predicción de amenazas</li>
                                <li>🌐 Análisis de superficie de ataque</li>
                            </ul>
                        </div>
                    </div>
                </div>
            </div>
        </div>
    </div>
</body>
</html>'''

ERROR_TEMPLATE = '''<!DOCTYPE html>
<html>
<head>
    <meta charset="UTF-8">
    <title>Error - Dashboard</title>
    <link href="https://cdn.jsdelivr.net/npm/bootstrap@5.3.0/dist/css/bootstrap.min.css" rel="stylesheet">
    <style>
        body { 
            background: linear-gradient(135deg, #667eea 0%, #764ba2 100%); 
            min-height: 100vh; 
        }
    </style>
</head>
<body>
    <div class="container mt-5">
        <div class="row justify-content-center">
            <div class="col-md-6">
                <div class="alert alert-danger text-center">
                    <h4><i class="fas fa-exclamation-triangle"></i> Error del Sistema</h4>
                    <p>{{ error }}</p>
                    <a href="/" class="btn btn-primary">Volver al Dashboard</a>
                </div>
            </div>
        </div>
    </div>
</body>
</html>'''

if __name__ == '__main__':
    print("🚀 Iniciando Dashboard Consolidado de Seguridad...")
    print("=" * 60)
    print("📊 Características del Dashboard:")
    print("   • Analytics en tiempo real con WebSocket")
    print("   • Gráficos interactivos con Plotly")
    print("   • Búsqueda inteligente de hallazgos")
    print("   • Gestión completa de alertas")
    print("   • UI/UX moderna con glassmorphism")
    print("   • Compatibilidad multiplataforma")
    print("   • Sistema de cache optimizado")
    print("   • API REST completa")
    print("")
    print("🔗 URLs disponibles:")
    print("   • Dashboard principal: http://localhost:5000/")
    print("   • Gestión de alertas: http://localhost:5000/alerts")
    print("   • Hallazgos: http://localhost:5000/findings")
    print("   • Analytics: http://localhost:5000/analytics")
    print("   • API stats: http://localhost:5000/api/real-time-stats")
    print("   • Diagnóstico: http://localhost:5000/test")
    print("")
    print(f"📁 Base de datos: {DATABASE_FILE}")
    print(f"🖥️  Plataforma: {platform.system()} {platform.release()}")
    print("")
    print("Presiona Ctrl+C para detener")
    print("=" * 60)
    
    try:
        # Iniciar hilo de actualizaciones en segundo plano
        update_thread = threading.Thread(target=background_updates, daemon=True)
        update_thread.start()
        
        # Crear directorio de reportes si no existe
        REPORTS_DIR.mkdir(exist_ok=True)
        
        # Ejecutar aplicación
        socketio.run(app, debug=False, host='0.0.0.0', port=5000, use_reloader=False)
        
    except KeyboardInterrupt:
        print("\n✅ Dashboard detenido correctamente")
    except Exception as e:
        print(f"\n❌ Error ejecutando dashboard: {e}")
        print("💡 Verificar dependencias: pip install flask flask-socketio plotly pandas")

app.register_blueprint(domain_bp)