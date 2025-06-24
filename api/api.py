"""
API REST para el Security Fuzzing System
"""
import sys
import os
from pathlib import Path

# Añadir directorio raíz al path
sys.path.append(str(Path(__file__).parent.parent))

from flask import Flask, request, jsonify, send_file
from flask_cors import CORS
from flask_restful import Api, Resource
import sqlite3
import json
from datetime import datetime
from typing import Dict, List, Any
from config.settings import config

app = Flask(__name__)
app.config['SECRET_KEY'] = config.SECRET_KEY
CORS(app)
api = Api(app)

class DatabaseHelper:
    """Helper para operaciones de base de datos"""
    
    @staticmethod
    def get_connection():
        """Obtener conexión a la base de datos"""
        try:
            db_path = config.DATABASE_PATH
            # Crear directorio si no existe
            Path(db_path).parent.mkdir(parents=True, exist_ok=True)
            return sqlite3.connect(db_path)
        except Exception as e:
            print(f"❌ Error conectando a BD: {e}")
            return None
    
    @staticmethod
    def execute_query(query: str, params: tuple = ()) -> List[Dict]:
        """Ejecutar query y retornar resultados"""
        conn = DatabaseHelper.get_connection()
        if not conn:
            return []
        
        try:
            cursor = conn.cursor()
            cursor.execute(query, params)
            
            if query.strip().upper().startswith('SELECT'):
                columns = [description[0] for description in cursor.description]
                rows = cursor.fetchall()
                return [dict(zip(columns, row)) for row in rows]
            else:
                conn.commit()
                return [{"affected_rows": cursor.rowcount}]
        except Exception as e:
            print(f"❌ Error ejecutando query: {e}")
            return []
        finally:
            conn.close()

class HealthCheck(Resource):
    """Endpoint de health check"""
    
    def get(self):
        return {
            "status": "healthy",
            "service": "Security Fuzzing API",
            "version": config.get('system.version', '2.0.0'),
            "timestamp": datetime.now().isoformat()
        }

class ScanResults(Resource):
    """Gestión de resultados de escaneos"""
    
    def get(self):
        """Obtener todos los resultados de escaneos"""
        try:
            query = """
                SELECT id, url, method, status_code, response_time, 
                       content_length, payload, timestamp, vulnerable
                FROM scan_results 
                ORDER BY timestamp DESC 
                LIMIT 100
            """
            results = DatabaseHelper.execute_query(query)
            return {
                "success": True,
                "data": results,
                "count": len(results)
            }
        except Exception as e:
            return {"success": False, "error": str(e)}, 500
    
    def post(self):
        """Crear nuevo resultado de escaneo"""
        try:
            data = request.get_json()
            
            query = """
                INSERT INTO scan_results 
                (url, method, status_code, response_time, content_length, 
                 payload, vulnerable, timestamp)
                VALUES (?, ?, ?, ?, ?, ?, ?, ?)
            """
            
            params = (
                data.get('url'),
                data.get('method', 'GET'),
                data.get('status_code'),
                data.get('response_time'),
                data.get('content_length'),
                data.get('payload'),
                data.get('vulnerable', False),
                datetime.now().isoformat()
            )
            
            result = DatabaseHelper.execute_query(query, params)
            
            return {
                "success": True,
                "message": "Resultado guardado correctamente",
                "data": result
            }
            
        except Exception as e:
            return {"success": False, "error": str(e)}, 500

class ScanStats(Resource):
    """Estadísticas de escaneos"""
    
    def get(self):
        """Obtener estadísticas generales"""
        try:
            stats = {}
            
            # Total de escaneos
            query = "SELECT COUNT(*) as total FROM scan_results"
            result = DatabaseHelper.execute_query(query)
            stats['total_scans'] = result[0]['total'] if result else 0
            
            # Vulnerabilidades encontradas
            query = "SELECT COUNT(*) as vulnerable FROM scan_results WHERE vulnerable = 1"
            result = DatabaseHelper.execute_query(query)
            stats['vulnerabilities_found'] = result[0]['vulnerable'] if result else 0
            
            # Escaneos por código de estado
            query = """
                SELECT status_code, COUNT(*) as count 
                FROM scan_results 
                GROUP BY status_code 
                ORDER BY count DESC
            """
            result = DatabaseHelper.execute_query(query)
            stats['status_codes'] = result
            
            # Últimos escaneos
            query = """
                SELECT url, status_code, vulnerable, timestamp
                FROM scan_results 
                ORDER BY timestamp DESC 
                LIMIT 10
            """
            result = DatabaseHelper.execute_query(query)
            stats['recent_scans'] = result
            
            return {
                "success": True,
                "data": stats
            }
            
        except Exception as e:
            return {"success": False, "error": str(e)}, 500

class ScanTargets(Resource):
    """Gestión de objetivos de escaneo"""
    
    def get(self):
        """Obtener lista de objetivos"""
        try:
            query = """
                SELECT id, name, url, description, enabled, created_at
                FROM scan_targets 
                ORDER BY created_at DESC
            """
            results = DatabaseHelper.execute_query(query)
            return {
                "success": True,
                "data": results
            }
        except Exception as e:
            return {"success": False, "error": str(e)}, 500
    
    def post(self):
        """Agregar nuevo objetivo"""
        try:
            data = request.get_json()
            
            query = """
                INSERT INTO scan_targets (name, url, description, enabled, created_at)
                VALUES (?, ?, ?, ?, ?)
            """
            
            params = (
                data.get('name'),
                data.get('url'),
                data.get('description', ''),
                data.get('enabled', True),
                datetime.now().isoformat()
            )
            
            DatabaseHelper.execute_query(query, params)
            
            return {
                "success": True,
                "message": "Objetivo agregado correctamente"
            }
            
        except Exception as e:
            return {"success": False, "error": str(e)}, 500

class ConfigAPI(Resource):
    """API para gestión de configuración"""
    
    def get(self):
        """Obtener configuración actual"""
        try:
            return {
                "success": True,
                "data": {
                    "system": config.get('system', {}),
                    "network": config.get('network', {}),
                    "tools": config.get('tools', {}),
                    "database_path": config.DATABASE_PATH
                }
            }
        except Exception as e:
            return {"success": False, "error": str(e)}, 500
    
    def put(self):
        """Actualizar configuración"""
        try:
            data = request.get_json()
            
            for key, value in data.items():
                config.set(key, value)
            
            config.save()
            
            return {
                "success": True,
                "message": "Configuración actualizada correctamente"
            }
            
        except Exception as e:
            return {"success": False, "error": str(e)}, 500

class ExportData(Resource):
    """Exportar datos del sistema"""
    
    def get(self):
        """Exportar resultados en JSON"""
        try:
            export_type = request.args.get('type', 'results')
            
            if export_type == 'results':
                query = "SELECT * FROM scan_results ORDER BY timestamp DESC"
            elif export_type == 'targets':
                query = "SELECT * FROM scan_targets ORDER BY created_at DESC"
            else:
                return {"success": False, "error": "Tipo de exportación no válido"}, 400
            
            data = DatabaseHelper.execute_query(query)
            
            # Crear archivo temporal
            export_file = f"export_{export_type}_{datetime.now().strftime('%Y%m%d_%H%M%S')}.json"
            export_path = Path('exports') / export_file
            export_path.parent.mkdir(exist_ok=True)
            
            with open(export_path, 'w', encoding='utf-8') as f:
                json.dump(data, f, indent=2, ensure_ascii=False)
            
            return send_file(export_path, as_attachment=True)
            
        except Exception as e:
            return {"success": False, "error": str(e)}, 500

# Registrar recursos de la API
api.add_resource(HealthCheck, '/health')
api.add_resource(ScanResults, '/api/scan-results')
api.add_resource(ScanStats, '/api/stats')
api.add_resource(ScanTargets, '/api/targets')
api.add_resource(ConfigAPI, '/api/config')
api.add_resource(ExportData, '/api/export')

# Rutas adicionales
@app.route('/')
def index():
    """Endpoint raíz de la API"""
    return jsonify({
        "service": "Security Fuzzing System API",
        "version": config.get('system.version', '2.0.0'),
        "endpoints": [
            "/health",
            "/api/scan-results",
            "/api/stats", 
            "/api/targets",
            "/api/config",
            "/api/export"
        ],
        "documentation": "/docs"
    })

@app.route('/docs')
def docs():
    """Documentación de la API"""
    return jsonify({
        "API Documentation": {
            "GET /health": "Health check del servicio",
            "GET /api/scan-results": "Obtener resultados de escaneos",
            "POST /api/scan-results": "Crear nuevo resultado",
            "GET /api/stats": "Estadísticas del sistema",
            "GET /api/targets": "Lista de objetivos",
            "POST /api/targets": "Agregar objetivo",
            "GET /api/config": "Configuración actual",
            "PUT /api/config": "Actualizar configuración",
            "GET /api/export?type=results": "Exportar datos"
        }
    })

@app.errorhandler(404)
def not_found(error):
    return jsonify({
        "success": False,
        "error": "Endpoint no encontrado",
        "available_endpoints": [
            "/health", "/api/scan-results", "/api/stats",
            "/api/targets", "/api/config", "/api/export"
        ]
    }), 404

@app.errorhandler(500)
def internal_error(error):
    return jsonify({
        "success": False,
        "error": "Error interno del servidor"
    }), 500

def init_database():
    """Inicializar tablas de la base de datos"""
    conn = DatabaseHelper.get_connection()
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
        print("✅ Base de datos inicializada correctamente")
        return True
        
    except Exception as e:
        print(f"❌ Error inicializando BD: {e}")
        return False
    finally:
        conn.close()

if __name__ == '__main__':
    print("🚀 Iniciando Security Fuzzing System API...")
    print("=" * 60)
    
    # Inicializar base de datos
    if init_database():
        print(f"📊 Base de datos: {config.DATABASE_PATH}")
    
    print(f"🌐 API server: http://{config.API_HOST}:{config.API_PORT}")
    print(f"📚 Documentación: http://{config.API_HOST}:{config.API_PORT}/docs")
    print(f"❤️ Health check: http://{config.API_HOST}:{config.API_PORT}/health")
    print("=" * 60)
    print("Presiona Ctrl+C para detener")
    
    app.run(
        host=config.API_HOST,
        port=config.API_PORT,
        debug=config.DEBUG
    )