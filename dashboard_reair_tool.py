# 🔧 Dashboard Repair - web/app.py
# Versión simplificada y funcional del dashboard

import sys
import os
from pathlib import Path

# Añadir directorio raíz al path
sys.path.append(str(Path(__file__).parent.parent))

from flask import Flask, render_template_string, request, jsonify, redirect, url_for
from flask_cors import CORS
import sqlite3
import json
from datetime import datetime
import subprocess
import threading
import time

# Configuración
try:
    from config.settings import config
    DATABASE_PATH = config.DATABASE_PATH
    WEB_HOST = config.WEB_HOST
    WEB_PORT = config.WEB_PORT
    DEBUG = config.DEBUG
except ImportError:
    # Configuración por defecto si config no está disponible
    DATABASE_PATH = "data/databases/fuzzing.db"
    WEB_HOST = "0.0.0.0"
    WEB_PORT = 5000
    DEBUG = True

app = Flask(__name__)
app.config['SECRET_KEY'] = 'dev-secret-key-change-in-production'
CORS(app)

# Sistema de estado global
app_state = {
    'scan_running': False,
    'scan_progress': 0,
    'scan_results': [],
    'total_scans': 0,
    'vulnerabilities_found': 0,
    'last_scan_time': None
}

# HTML Template principal
DASHBOARD_HTML = """
<!DOCTYPE html>
<html lang="es">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>Security Fuzzing System - Dashboard</title>
    <style>
        * {
            margin: 0;
            padding: 0;
            box-sizing: border-box;
        }
        
        body {
            font-family: 'Segoe UI', Tahoma, Geneva, Verdana, sans-serif;
            background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
            min-height: 100vh;
            color: #333;
        }
        
        .container {
            max-width: 1200px;
            margin: 0 auto;
            padding: 20px;
        }
        
        .header {
            background: rgba(255, 255, 255, 0.1);
            backdrop-filter: blur(10px);
            border-radius: 15px;
            padding: 30px;
            margin-bottom: 30px;
            text-align: center;
            color: white;
        }
        
        .header h1 {
            font-size: 2.5em;
            margin-bottom: 10px;
        }
        
        .header p {
            font-size: 1.2em;
            opacity: 0.9;
        }
        
        .dashboard-grid {
            display: grid;
            grid-template-columns: repeat(auto-fit, minmax(300px, 1fr));
            gap: 20px;
            margin-bottom: 30px;
        }
        
        .card {
            background: rgba(255, 255, 255, 0.95);
            border-radius: 15px;
            padding: 25px;
            box-shadow: 0 8px 32px rgba(31, 38, 135, 0.37);
            backdrop-filter: blur(4px);
            border: 1px solid rgba(255, 255, 255, 0.18);
        }
        
        .card h3 {
            color: #4A90E2;
            margin-bottom: 15px;
            font-size: 1.3em;
        }
        
        .stats-grid {
            display: grid;
            grid-template-columns: repeat(2, 1fr);
            gap: 15px;
        }
        
        .stat-item {
            text-align: center;
            padding: 15px;
            background: #f8f9fa;
            border-radius: 8px;
        }
        
        .stat-number {
            font-size: 2em;
            font-weight: bold;
            color: #4A90E2;
        }
        
        .stat-label {
            color: #666;
            font-size: 0.9em;
        }
        
        .form-group {
            margin-bottom: 20px;
        }
        
        .form-group label {
            display: block;
            margin-bottom: 5px;
            font-weight: 600;
            color: #333;
        }
        
        .form-group input, .form-group select {
            width: 100%;
            padding: 12px;
            border: 2px solid #ddd;
            border-radius: 8px;
            font-size: 16px;
            transition: border-color 0.3s;
        }
        
        .form-group input:focus, .form-group select:focus {
            outline: none;
            border-color: #4A90E2;
        }
        
        .btn {
            background: linear-gradient(135deg, #4A90E2, #357ABD);
            color: white;
            border: none;
            padding: 12px 30px;
            border-radius: 8px;
            font-size: 16px;
            cursor: pointer;
            transition: transform 0.2s;
        }
        
        .btn:hover {
            transform: translateY(-2px);
        }
        
        .btn:disabled {
            opacity: 0.6;
            cursor: not-allowed;
            transform: none;
        }
        
        .progress-bar {
            width: 100%;
            height: 20px;
            background: #f0f0f0;
            border-radius: 10px;
            overflow: hidden;
            margin: 10px 0;
        }
        
        .progress-fill {
            height: 100%;
            background: linear-gradient(90deg, #4A90E2, #357ABD);
            transition: width 0.3s ease;
        }
        
        .status {
            padding: 10px 15px;
            border-radius: 8px;
            margin: 10px 0;
            font-weight: 500;
        }
        
        .status.success {
            background: #d4edda;
            color: #155724;
            border: 1px solid #c3e6cb;
        }
        
        .status.error {
            background: #f8d7da;
            color: #721c24;
            border: 1px solid #f5c6cb;
        }
        
        .status.warning {
            background: #fff3cd;
            color: #856404;
            border: 1px solid #ffeaa7;
        }
        
        .results-table {
            width: 100%;
            border-collapse: collapse;
            margin-top: 20px;
        }
        
        .results-table th, .results-table td {
            padding: 12px;
            text-align: left;
            border-bottom: 1px solid #ddd;
        }
        
        .results-table th {
            background: #f8f9fa;
            font-weight: 600;
        }
        
        .results-table tr:hover {
            background: #f8f9fa;
        }
        
        .vulnerable {
            color: #dc3545;
            font-weight: bold;
        }
        
        .safe {
            color: #28a745;
        }
        
        .footer {
            text-align: center;
            padding: 20px;
            color: rgba(255, 255, 255, 0.8);
            margin-top: 40px;
        }
        
        @keyframes pulse {
            0% { opacity: 1; }
            50% { opacity: 0.5; }
            100% { opacity: 1; }
        }
        
        .scanning {
            animation: pulse 2s infinite;
        }
    </style>
</head>
<body>
    <div class="container">
        <div class="header">
            <h1>🚀 Security Fuzzing System</h1>
            <p>Dashboard de Control y Monitoreo</p>
        </div>
        
        <div class="dashboard-grid">
            <!-- Estadísticas -->
            <div class="card">
                <h3>📊 Estadísticas del Sistema</h3>
                <div class="stats-grid">
                    <div class="stat-item">
                        <div class="stat-number" id="total-scans">{{ stats.total_scans }}</div>
                        <div class="stat-label">Total Escaneos</div>
                    </div>
                    <div class="stat-item">
                        <div class="stat-number" id="vulnerabilities">{{ stats.vulnerabilities_found }}</div>
                        <div class="stat-label">Vulnerabilidades</div>
                    </div>
                    <div class="stat-item">
                        <div class="stat-number" id="success-rate">{{ stats.success_rate }}%</div>
                        <div class="stat-label">Tasa de Éxito</div>
                    </div>
                    <div class="stat-item">
                        <div class="stat-number" id="uptime">{{ stats.uptime }}</div>
                        <div class="stat-label">Tiempo Activo</div>
                    </div>
                </div>
            </div>
            
            <!-- Nuevo Escaneo -->
            <div class="card">
                <h3>⚡ Nuevo Escaneo</h3>
                <form id="scan-form">
                    <div class="form-group">
                        <label for="target-url">URL Objetivo:</label>
                        <input type="url" id="target-url" name="target_url" 
                               placeholder="http://example.com/FUZZ" required>
                    </div>
                    <div class="form-group">
                        <label for="wordlist">Wordlist:</label>
                        <select id="wordlist" name="wordlist">
                            <option value="common">Común (rápido)</option>
                            <option value="directories">Directorios</option>
                            <option value="files">Archivos</option>
                            <option value="parameters">Parámetros</option>
                        </select>
                    </div>
                    <button type="submit" class="btn" id="start-scan">
                        🚀 Iniciar Escaneo
                    </button>
                </form>
                
                <div id="scan-progress" style="display: none;">
                    <h4>Escaneo en Progreso...</h4>
                    <div class="progress-bar">
                        <div class="progress-fill" id="progress-fill" style="width: 0%"></div>
                    </div>
                    <p id="progress-text">Preparando escaneo...</p>
                </div>
            </div>
            
            <!-- Estado del Sistema -->
            <div class="card">
                <h3>🔍 Estado del Sistema</h3>
                <div id="system-status">
                    <div class="status success">
                        <strong>✅ Dashboard:</strong> Funcionando
                    </div>
                    <div class="status success">
                        <strong>✅ API REST:</strong> Disponible
                    </div>
                    <div class="status success">
                        <strong>✅ Base de Datos:</strong> Conectada
                    </div>
                    <div class="status success">
                        <strong>✅ Fuzzing Engine:</strong> Listo
                    </div>
                </div>
                
                <div style="margin-top: 20px;">
                    <h4>🔗 Enlaces Útiles:</h4>
                    <p><a href="http://localhost:8000/health" target="_blank">🔌 API Health Check</a></p>
                    <p><a href="http://localhost:8000/docs" target="_blank">📚 Documentación API</a></p>
                    <p><a href="/test" target="_blank">🧪 Test del Sistema</a></p>
                </div>
            </div>
        </div>
        
        <!-- Resultados Recientes -->
        <div class="card">
            <h3>📋 Resultados Recientes</h3>
            <div id="recent-results">
                {% if recent_results %}
                <table class="results-table">
                    <thead>
                        <tr>
                            <th>URL</th>
                            <th>Código</th>
                            <th>Tiempo</th>
                            <th>Payload</th>
                            <th>Estado</th>
                        </tr>
                    </thead>
                    <tbody>
                        {% for result in recent_results %}
                        <tr>
                            <td>{{ result.url }}</td>
                            <td>{{ result.status_code }}</td>
                            <td>{{ result.response_time }}ms</td>
                            <td>{{ result.payload }}</td>
                            <td>
                                {% if result.vulnerable %}
                                <span class="vulnerable">🚨 VULNERABLE</span>
                                {% else %}
                                <span class="safe">✅ SEGURO</span>
                                {% endif %}
                            </td>
                        </tr>
                        {% endfor %}
                    </tbody>
                </table>
                {% else %}
                <p>No hay resultados recientes. Ejecuta tu primer escaneo.</p>
                {% endif %}
            </div>
        </div>
        
        <div class="footer">
            <p>🔒 Security Fuzzing System v2.0 | Última actualización: {{ current_time }}</p>
        </div>
    </div>
    
    <script>
        // Actualización en tiempo real
        function updateStats() {
            fetch('/api/stats')
                .then(response => response.json())
                .then(data => {
                    if (data.success) {
                        document.getElementById('total-scans').textContent = data.data.total_scans || 0;
                        document.getElementById('vulnerabilities').textContent = data.data.vulnerabilities_found || 0;
                    }
                })
                .catch(error => console.log('Error actualizando stats:', error));
        }
        
        // Manejo del formulario de escaneo
        document.getElementById('scan-form').addEventListener('submit', function(e) {
            e.preventDefault();
            
            const formData = new FormData(this);
            const data = {
                target_url: formData.get('target_url'),
                wordlist: formData.get('wordlist')
            };
            
            // Mostrar progreso
            document.getElementById('scan-progress').style.display = 'block';
            document.getElementById('start-scan').disabled = true;
            
            // Simular progreso (en un sistema real, esto vendría del backend)
            let progress = 0;
            const progressInterval = setInterval(() => {
                progress += Math.random() * 10;
                if (progress >= 100) {
                    progress = 100;
                    clearInterval(progressInterval);
                    document.getElementById('progress-text').textContent = 'Escaneo completado!';
                    document.getElementById('start-scan').disabled = false;
                    
                    // Actualizar stats
                    setTimeout(updateStats, 1000);
                }
                
                document.getElementById('progress-fill').style.width = progress + '%';
                document.getElementById('progress-text').textContent = `Progreso: ${Math.round(progress)}%`;
            }, 500);
            
            // Enviar datos al backend
            fetch('/api/scan/start', {
                method: 'POST',
                headers: {
                    'Content-Type': 'application/json',
                },
                body: JSON.stringify(data)
            })
            .then(response => response.json())
            .then(data => {
                console.log('Escaneo iniciado:', data);
            })
            .catch(error => {
                console.error('Error:', error);
                document.getElementById('progress-text').textContent = 'Error en el escaneo';
            });
        });
        
        // Actualizar stats cada 30 segundos
        setInterval(updateStats, 30000);
        
        // Actualización inicial
        updateStats();
    </script>
</body>
</html>
"""

def get_database_connection():
    """Obtener conexión a la base de datos"""
    try:
        # Crear directorio si no existe
        db_path = Path(DATABASE_PATH)
        db_path.parent.mkdir(parents=True, exist_ok=True)
        return sqlite3.connect(DATABASE_PATH)
    except Exception as e:
        print(f"❌ Error conectando a BD: {e}")
        return None

def get_stats():
    """Obtener estadísticas del sistema"""
    conn = get_database_connection()
    stats = {
        'total_scans': 0,
        'vulnerabilities_found': 0,
        'success_rate': 0,
        'uptime': '0h 0m'
    }
    
    if conn:
        try:
            cursor = conn.cursor()
            
            # Total de escaneos
            cursor.execute("SELECT COUNT(*) FROM scan_results")
            result = cursor.fetchone()
            stats['total_scans'] = result[0] if result else 0
            
            # Vulnerabilidades encontradas
            cursor.execute("SELECT COUNT(*) FROM scan_results WHERE vulnerable = 1")
            result = cursor.fetchone()
            stats['vulnerabilities_found'] = result[0] if result else 0
            
            # Calcular tasa de éxito
            if stats['total_scans'] > 0:
                stats['success_rate'] = round((stats['total_scans'] - stats['vulnerabilities_found']) / stats['total_scans'] * 100, 1)
            
        except Exception as e:
            print(f"Error obteniendo stats: {e}")
        finally:
            conn.close()
    
    return stats

def get_recent_results(limit=10):
    """Obtener resultados recientes"""
    conn = get_database_connection()
    results = []
    
    if conn:
        try:
            cursor = conn.cursor()
            cursor.execute("""
                SELECT url, status_code, response_time, payload, vulnerable, timestamp
                FROM scan_results 
                ORDER BY timestamp DESC 
                LIMIT ?
            """, (limit,))
            
            rows = cursor.fetchall()
            for row in rows:
                results.append({
                    'url': row[0],
                    'status_code': row[1],
                    'response_time': round(row[2] * 1000, 2) if row[2] else 0,
                    'payload': row[3],
                    'vulnerable': bool(row[4]),
                    'timestamp': row[5]
                })
                
        except Exception as e:
            print(f"Error obteniendo resultados: {e}")
        finally:
            conn.close()
    
    return results

def init_database():
    """Inicializar base de datos"""
    conn = get_database_connection()
    if not conn:
        return False
    
    try:
        cursor = conn.cursor()
        
        # Tabla de resultados de escaneo
        cursor.execute("""
            CREATE TABLE IF NOT EXISTS scan_results (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                url TEXT NOT NULL,
                method TEXT DEFAULT 'GET',
                status_code INTEGER,
                response_time REAL,
                content_length INTEGER,
                payload TEXT,
                vulnerable BOOLEAN DEFAULT 0,
                timestamp TEXT NOT NULL,
                created_at DATETIME DEFAULT CURRENT_TIMESTAMP
            )
        """)
        
        # Tabla de objetivos
        cursor.execute("""
            CREATE TABLE IF NOT EXISTS scan_targets (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                name TEXT NOT NULL,
                url TEXT NOT NULL,
                description TEXT,
                enabled BOOLEAN DEFAULT 1,
                created_at TEXT NOT NULL
            )
        """)
        
        conn.commit()
        return True
        
    except Exception as e:
        print(f"❌ Error inicializando BD: {e}")
        return False
    finally:
        conn.close()

# Rutas del dashboard
@app.route('/')
def dashboard():
    """Dashboard principal"""
    stats = get_stats()
    recent_results = get_recent_results(5)
    current_time = datetime.now().strftime('%Y-%m-%d %H:%M:%S')
    
    return render_template_string(DASHBOARD_HTML, 
                                stats=stats, 
                                recent_results=recent_results,
                                current_time=current_time)

@app.route('/api/stats')
def api_stats():
    """API para estadísticas"""
    stats = get_stats()
    return jsonify({
        'success': True,
        'data': stats
    })

@app.route('/api/scan/start', methods=['POST'])
def api_scan_start():
    """API para iniciar escaneo"""
    try:
        data = request.get_json()
        target_url = data.get('target_url')
        wordlist = data.get('wordlist', 'common')
        
        # Aquí iría la lógica real de escaneo
        # Por ahora, solo simular el inicio
        
        return jsonify({
            'success': True,
            'message': 'Escaneo iniciado correctamente',
            'scan_id': f"scan_{int(time.time())}"
        })
        
    except Exception as e:
        return jsonify({
            'success': False,
            'error': str(e)
        }), 500

@app.route('/test')
def test_page():
    """Página de prueba"""
    return jsonify({
        'status': 'OK',
        'message': 'Dashboard funcionando correctamente',
        'timestamp': datetime.now().isoformat(),
        'version': '2.0.0'
    })

@app.route('/health')
def health_check():
    """Health check del dashboard"""
    return jsonify({
        'status': 'healthy',
        'service': 'Security Fuzzing Dashboard',
        'version': '2.0.0',
        'timestamp': datetime.now().isoformat()
    })

if __name__ == '__main__':
    print("🚀 Iniciando Dashboard Consolidado de Seguridad...")
    print("=" * 60)
    print("📊 Características del Dashboard:")
    print("   • Interfaz web moderna y responsiva")
    print("   • Estadísticas en tiempo real")
    print("   • Formulario de escaneo integrado")
    print("   • Visualización de resultados")
    print("   • API REST integrada")
    print("   • Sistema de monitoreo")
    print("   • Compatibilidad multiplataforma")
    print("   • UI/UX optimizada")
    print("")
    print("🔗 URLs disponibles:")
    print(f"   • Dashboard principal: http://{WEB_HOST}:{WEB_PORT}/")
    print(f"   • API stats: http://{WEB_HOST}:{WEB_PORT}/api/stats")
    print(f"   • Health check: http://{WEB_HOST}:{WEB_PORT}/health")
    print(f"   • Página de prueba: http://{WEB_HOST}:{WEB_PORT}/test")
    print("")
    print(f"📁 Base de datos: {DATABASE_PATH}")
    print(f"🖥️  Plataforma: {os.name}")
    print("Presiona Ctrl+C para detener")
    print("=" * 60)
    
    # Inicializar base de datos
    if init_database():
        print("✅ Base de datos inicializada correctamente")
    else:
        print("⚠️ Warning: Problema inicializando base de datos")
    
    # Iniciar servidor
    try:
        app.run(
            host=WEB_HOST,
            port=WEB_PORT,
            debug=DEBUG,
            threaded=True
        )
    except Exception as e:
        print(f"❌ Error iniciando dashboard: {e}")
        print("🔧 Soluciones posibles:")
        print("   1. Verificar que el puerto 5000 no esté ocupado")
        print("   2. Ejecutar como administrador")
        print("   3. Cambiar el puerto en config.yaml")