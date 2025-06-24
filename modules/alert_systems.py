#!/usr/bin/env python3
"""
Sistema de Alertas Inteligente con Machine Learning
Detecta anomalías, prioriza alertas y reduce falsos positivos
"""

import os
import json
import sqlite3
import pandas as pd
import numpy as np
from datetime import datetime, timedelta
from pathlib import Path
from typing import List, Dict, Optional, Tuple
import logging
from sklearn.ensemble import IsolationForest, RandomForestClassifier
from sklearn.preprocessing import StandardScaler, LabelEncoder
from sklearn.cluster import DBSCAN
from sklearn.model_selection import train_test_split
from sklearn.metrics import classification_report, confusion_matrix
import joblib
import requests
from collections import defaultdict
import hashlib
import pickle

class IntelligentAlertSystem:
    """Sistema de alertas inteligente con capacidades de ML"""
    
    def __init__(self, db_path: str, models_dir: str = "ml_models"):
        self.db_path = Path(db_path)
        self.models_dir = Path(models_dir)
        self.models_dir.mkdir(exist_ok=True)
        self.logger = logging.getLogger(__name__)
        
        # Configuración de modelos
        self.anomaly_detector = None
        self.priority_classifier = None
        self.false_positive_detector = None
        self.scaler = StandardScaler()
        self.label_encoders = {}
        
        # Configuración de alertas
        self.alert_thresholds = {
            'critical': 0.8,
            'high': 0.6,
            'medium': 0.4,
            'low': 0.2
        }
        
        # Patrones conocidos de falsos positivos
        self.false_positive_patterns = self.load_false_positive_patterns()
        
        # Inicializar modelos si existen
        self.load_models()
    
    def load_false_positive_patterns(self) -> Dict:
        """Cargar patrones conocidos de falsos positivos"""
        return {
            'common_false_positives': [
                'robots.txt', 'favicon.ico', 'sitemap.xml',
                'crossdomain.xml', 'ads.txt', 'humans.txt'
            ],
            'status_code_patterns': {
                '404': 'low_priority',  # Not found generalmente no es crítico
                '405': 'medium_priority',  # Method not allowed puede ser interesante
                '500': 'high_priority'  # Server errors son importantes
            },
            'path_patterns': {
                'test': 'medium_priority',
                'dev': 'medium_priority',
                'admin': 'critical_priority',
                '.git': 'critical_priority',
                'backup': 'high_priority'
            }
        }
    
    def extract_features(self, findings_df: pd.DataFrame) -> pd.DataFrame:
        """Extraer características para machine learning"""
        features_df = findings_df.copy()
        
        # Características temporales
        features_df['fecha_descubierto'] = pd.to_datetime(features_df['fecha_descubierto'])
        features_df['hour'] = features_df['fecha_descubierto'].dt.hour
        features_df['day_of_week'] = features_df['fecha_descubierto'].dt.dayofweek
        features_df['is_weekend'] = features_df['day_of_week'].isin([5, 6]).astype(int)
        
        # Características de la ruta
        features_df['path_length'] = features_df['ruta'].str.len()
        features_df['has_extension'] = features_df['ruta'].str.contains('\.').astype(int)
        features_df['has_admin'] = features_df['ruta'].str.contains('admin', case=False).astype(int)
        features_df['has_api'] = features_df['ruta'].str.contains('api', case=False).astype(int)
        features_df['has_test'] = features_df['ruta'].str.contains('test', case=False).astype(int)
        features_df['has_backup'] = features_df['ruta'].str.contains('backup|bak', case=False).astype(int)
        features_df['has_config'] = features_df['ruta'].str.contains('config', case=False).astype(int)
        features_df['has_git'] = features_df['ruta'].str.contains('\.git', case=False).astype(int)
        
        # Características del dominio
        features_df['domain_length'] = features_df['dominio'].str.len()
        features_df['has_subdomain'] = features_df['dominio'].str.count('\.').apply(lambda x: 1 if x > 1 else 0)
        
        # Características de respuesta HTTP
        features_df['is_success'] = (features_df['codigo_http'] == 200).astype(int)
        features_df['is_redirect'] = features_df['codigo_http'].isin([301, 302, 307]).astype(int)
        features_df['is_client_error'] = (features_df['codigo_http'] // 100 == 4).astype(int)
        features_df['is_server_error'] = (features_df['codigo_http'] // 100 == 5).astype(int)
        
        # Características de tamaño
        if 'tamano_respuesta' in features_df.columns:
            features_df['response_size_kb'] = features_df['tamano_respuesta'] / 1024
            features_df['is_large_response'] = (features_df['tamano_respuesta'] > 100000).astype(int)
        else:
            features_df['response_size_kb'] = 0
            features_df['is_large_response'] = 0
        
        # Frecuencia de la ruta
        path_counts = features_df['ruta'].value_counts()
        features_df['path_frequency'] = features_df['ruta'].map(path_counts)
        features_df['is_rare_path'] = (features_df['path_frequency'] <= 2).astype(int)
        
        return features_df
    
    def calculate_risk_score(self, row: pd.Series) -> float:
        """Calcular puntuación de riesgo para un hallazgo"""
        score = 0.0
        
        # Puntuación base por código HTTP
        if row['codigo_http'] == 200:
            score += 0.7  # Acceso exitoso
        elif row['codigo_http'] in [403, 401]:
            score += 0.5  # Acceso restringido (interesante)
        elif row['codigo_http'] >= 500:
            score += 0.4  # Error del servidor
        
        # Puntuación por patrones de ruta
        ruta_lower = str(row['ruta']).lower()
        
        if any(pattern in ruta_lower for pattern in ['admin', 'panel', 'dashboard']):
            score += 0.8
        elif '.git' in ruta_lower:
            score += 0.9
        elif any(pattern in ruta_lower for pattern in ['backup', 'bak', 'old']):
            score += 0.7
        elif any(pattern in ruta_lower for pattern in ['config', 'conf', 'settings']):
            score += 0.6
        elif any(pattern in ruta_lower for pattern in ['test', 'dev', 'staging']):
            score += 0.3
        
        # Penalización por falsos positivos comunes
        if any(fp in ruta_lower for fp in self.false_positive_patterns['common_false_positives']):
            score *= 0.1
        
        # Bonus por rareza
        if hasattr(row, 'is_rare_path') and row['is_rare_path']:
            score += 0.2
        
        # Bonus por tamaño de respuesta grande
        if hasattr(row, 'is_large_response') and row['is_large_response']:
            score += 0.1
        
        return min(score, 1.0)  # Máximo 1.0
    
    def train_anomaly_detector(self, features_df: pd.DataFrame) -> None:
        """Entrenar detector de anomalías"""
        # Seleccionar características numéricas
        numeric_features = [
            'hour', 'day_of_week', 'path_length', 'domain_length',
            'codigo_http', 'response_size_kb', 'path_frequency'
        ]
        
        # Verificar que las columnas existen
        available_features = [f for f in numeric_features if f in features_df.columns]
        
        if len(available_features) < 3:
            self.logger.warning("Insuficientes características para entrenar detector de anomalías")
            return
        
        X = features_df[available_features].fillna(0)
        
        # Escalar características
        X_scaled = self.scaler.fit_transform(X)
        
        # Entrenar Isolation Forest
        self.anomaly_detector = IsolationForest(
            contamination=0.1,  # 10% de anomalías esperadas
            random_state=42,
            n_estimators=100
        )
        
        self.anomaly_detector.fit(X_scaled)
        
        # Guardar modelo
        self.save_model(self.anomaly_detector, 'anomaly_detector.joblib')
        self.save_model(self.scaler, 'scaler.joblib')
        
        self.logger.info("Detector de anomalías entrenado exitosamente")
    
    def train_priority_classifier(self, features_df: pd.DataFrame) -> None:
        """Entrenar clasificador de prioridad"""
        # Calcular prioridad basada en riesgo
        features_df['risk_score'] = features_df.apply(self.calculate_risk_score, axis=1)
        features_df['priority'] = pd.cut(
            features_df['risk_score'],
            bins=[0, 0.2, 0.4, 0.6, 1.0],
            labels=['low', 'medium', 'high', 'critical']
        )
        
        # Características para clasificación
        feature_columns = [
            'hour', 'day_of_week', 'path_length', 'has_extension',
            'has_admin', 'has_api', 'has_backup', 'has_config',
            'is_success', 'is_redirect', 'is_client_error', 'response_size_kb'
        ]
        
        available_features = [f for f in feature_columns if f in features_df.columns]
        
        if len(available_features) < 5:
            self.logger.warning("Insuficientes características para entrenar clasificador")
            return
        
        X = features_df[available_features].fillna(0)
        y = features_df['priority'].dropna()
        
        # Alinear X e y
        valid_indices = y.index
        X = X.loc[valid_indices]
        
        if len(X) < 10:
            self.logger.warning("Insuficientes datos para entrenar clasificador")
            return
        
        # Dividir datos
        X_train, X_test, y_train, y_test = train_test_split(
            X, y, test_size=0.2, random_state=42, stratify=y
        )
        
        # Entrenar Random Forest
        self.priority_classifier = RandomForestClassifier(
            n_estimators=100,
            random_state=42,
            class_weight='balanced'
        )
        
        self.priority_classifier.fit(X_train, y_train)
        
        # Evaluar modelo
        y_pred = self.priority_classifier.predict(X_test)
        self.logger.info("Clasificador de prioridad entrenado")
        self.logger.info(f"Reporte de clasificación:\n{classification_report(y_test, y_pred)}")
        
        # Guardar modelo
        self.save_model(self.priority_classifier, 'priority_classifier.joblib')
    
    def detect_anomalies(self, features_df: pd.DataFrame) -> np.ndarray:
        """Detectar anomalías en nuevos hallazgos"""
        if self.anomaly_detector is None:
            return np.zeros(len(features_df))
        
        numeric_features = [
            'hour', 'day_of_week', 'path_length', 'domain_length',
            'codigo_http', 'response_size_kb', 'path_frequency'
        ]
        
        available_features = [f for f in numeric_features if f in features_df.columns]
        X = features_df[available_features].fillna(0)
        X_scaled = self.scaler.transform(X)
        
        # -1 para anomalías, 1 para normal
        anomaly_scores = self.anomaly_detector.decision_function(X_scaled)
        predictions = self.anomaly_detector.predict(X_scaled)
        
        return anomaly_scores, predictions
    
    def predict_priority(self, features_df: pd.DataFrame) -> np.ndarray:
        """Predecir prioridad de nuevos hallazgos"""
        if self.priority_classifier is None:
            # Usar scoring manual como fallback
            return features_df.apply(lambda row: self.manual_priority_scoring(row), axis=1)
        
        feature_columns = [
            'hour', 'day_of_week', 'path_length', 'has_extension',
            'has_admin', 'has_api', 'has_backup', 'has_config',
            'is_success', 'is_redirect', 'is_client_error', 'response_size_kb'
        ]
        
        available_features = [f for f in feature_columns if f in features_df.columns]
        X = features_df[available_features].fillna(0)
        
        priorities = self.priority_classifier.predict(X)
        probabilities = self.priority_classifier.predict_proba(X)
        
        return priorities, probabilities
    
    def manual_priority_scoring(self, row: pd.Series) -> str:
        """Scoring manual de prioridad como fallback"""
        risk_score = self.calculate_risk_score(row)
        
        if risk_score >= 0.8:
            return 'critical'
        elif risk_score >= 0.6:
            return 'high'
        elif risk_score >= 0.4:
            return 'medium'
        else:
            return 'low'
    
    def generate_intelligent_alerts(self, findings_df: pd.DataFrame) -> List[Dict]:
        """Generar alertas inteligentes basadas en ML"""
        if findings_df.empty:
            return []
        
        # Extraer características
        features_df = self.extract_features(findings_df)
        
        # Detectar anomalías
        if self.anomaly_detector is not None:
            anomaly_scores, anomaly_predictions = self.detect_anomalies(features_df)
            features_df['anomaly_score'] = anomaly_scores
            features_df['is_anomaly'] = (anomaly_predictions == -1)
        else:
            features_df['anomaly_score'] = 0
            features_df['is_anomaly'] = False
        
        # Predecir prioridad
        if self.priority_classifier is not None:
            priorities, priority_probabilities = self.predict_priority(features_df)
            features_df['predicted_priority'] = priorities
        else:
            features_df['predicted_priority'] = features_df.apply(self.manual_priority_scoring, axis=1)
        
        # Calcular scoring final
        features_df['final_risk_score'] = features_df.apply(self.calculate_final_risk_score, axis=1)
        
        # Generar alertas
        alerts = []
        for _, row in features_df.iterrows():
            alert = self.create_intelligent_alert(row)
            if alert:
                alerts.append(alert)
        
        # Ordenar por prioridad y score
        priority_order = {'critical': 4, 'high': 3, 'medium': 2, 'low': 1}
        alerts.sort(
            key=lambda x: (priority_order.get(x['priority'], 0), x['risk_score']),
            reverse=True
        )
        
        return alerts
    
    def calculate_final_risk_score(self, row: pd.Series) -> float:
        """Calcular score final de riesgo combinando múltiples factores"""
        base_score = self.calculate_risk_score(row)
        
        # Ajustar por anomalía
        if hasattr(row, 'is_anomaly') and row['is_anomaly']:
            base_score += 0.2
        
        # Ajustar por score de anomalía
        if hasattr(row, 'anomaly_score'):
            # Normalizar anomaly_score a [0, 1]
            normalized_anomaly = max(0, min(1, (row['anomaly_score'] + 0.5)))
            base_score += normalized_anomaly * 0.1
        
        return min(base_score, 1.0)
    
    def create_intelligent_alert(self, row: pd.Series) -> Optional[Dict]:
        """Crear alerta inteligente para un hallazgo"""
        # Filtrar falsos positivos obvios
        if self.is_likely_false_positive(row):
            return None
        
        priority = row.get('predicted_priority', 'medium')
        risk_score = row.get('final_risk_score', 0.5)
        
        # Solo crear alertas para prioridad media o superior
        if priority == 'low' and risk_score < 0.3:
            return None
        
        alert = {
            'id': hashlib.md5(f"{row['url_completa']}{row['fecha_descubierto']}".encode()).hexdigest()[:8],
            'timestamp': datetime.now().isoformat(),
            'priority': priority,
            'risk_score': round(risk_score, 3),
            'finding_data': {
                'url': row['url_completa'],
                'path': row['ruta'],
                'domain': row['dominio'],
                'status_code': row['codigo_http'],
                'discovered_at': row['fecha_descubierto']
            },
            'analysis': {
                'is_anomaly': row.get('is_anomaly', False),
                'anomaly_score': round(row.get('anomaly_score', 0), 3),
                'predicted_priority': priority,
                'features': self.extract_alert_features(row)
            },
            'recommendations': self.generate_alert_recommendations(row),
            'metadata': {
                'ml_confidence': self.calculate_ml_confidence(row),
                'false_positive_probability': self.calculate_false_positive_probability(row)
            }
        }
        
        return alert
    
    def is_likely_false_positive(self, row: pd.Series) -> bool:
        """Determinar si un hallazgo es probable falso positivo"""
        ruta_lower = str(row['ruta']).lower()
        
        # Falsos positivos comunes
        if any(fp in ruta_lower for fp in self.false_positive_patterns['common_false_positives']):
            return True
        
        # Códigos 404 en rutas comunes
        if row['codigo_http'] == 404 and any(common in ruta_lower for common in ['favicon', 'robots', 'sitemap']):
            return True
        
        # Rutas muy largas sin sentido
        if len(ruta_lower) > 100 and not any(pattern in ruta_lower for pattern in ['admin', 'api', 'config']):
            return True
        
        return False
    
    def extract_alert_features(self, row: pd.Series) -> Dict:
        """Extraer características relevantes para la alerta"""
        return {
            'has_sensitive_keywords': any(keyword in str(row['ruta']).lower() 
                                        for keyword in ['admin', 'config', 'backup', '.git']),
            'response_type': self.classify_response_type(row['codigo_http']),
            'discovery_time': {
                'hour': pd.to_datetime(row['fecha_descubierto']).hour,
                'is_business_hours': 9 <= pd.to_datetime(row['fecha_descubierto']).hour <= 17
            },
            'path_characteristics': {
                'has_extension': '.' in str(row['ruta']),
                'path_depth': str(row['ruta']).count('/'),
                'estimated_file_type': self.estimate_file_type(row['ruta'])
            }
        }
    
    def classify_response_type(self, status_code: int) -> str:
        """Clasificar tipo de respuesta HTTP"""
        if status_code == 200:
            return 'accessible'
        elif status_code in [301, 302, 307]:
            return 'redirect'
        elif status_code in [401, 403]:
            return 'protected'
        elif status_code == 404:
            return 'not_found'
        elif status_code >= 500:
            return 'server_error'
        else:
            return 'other'
    
    def estimate_file_type(self, path: str) -> str:
        """Estimar tipo de archivo basado en la extensión"""
        path_lower = str(path).lower()
        
        if any(ext in path_lower for ext in ['.php', '.asp', '.jsp']):
            return 'dynamic'
        elif any(ext in path_lower for ext in ['.html', '.htm']):
            return 'static'
        elif any(ext in path_lower for ext in ['.js', '.css']):
            return 'resource'
        elif any(ext in path_lower for ext in ['.pdf', '.doc', '.txt']):
            return 'document'
        elif any(ext in path_lower for ext in ['.zip', '.tar', '.bak']):
            return 'archive'
        elif '.' not in path_lower or path_lower.endswith('/'):
            return 'directory'
        else:
            return 'unknown'
    
    def generate_alert_recommendations(self, row: pd.Series) -> List[str]:
        """Generar recomendaciones específicas para la alerta"""
        recommendations = []
        ruta_lower = str(row['ruta']).lower()
        status_code = row['codigo_http']
        
        # Recomendaciones específicas por patrón
        if '.git' in ruta_lower:
            recommendations.append("🚨 CRÍTICO: Repositorio Git expuesto. Bloquear acceso inmediatamente.")
            recommendations.append("Verificar si contiene información sensible como credenciales.")
        
        elif 'admin' in ruta_lower and status_code == 200:
            recommendations.append("⚠️ Panel administrativo accesible. Verificar autenticación.")
            recommendations.append("Implementar restricciones de IP si es necesario.")
        
        elif any(pattern in ruta_lower for pattern in ['backup', 'bak', 'old']):
            recommendations.append("📁 Archivo/directorio de respaldo encontrado.")
            recommendations.append("Verificar contenido y mover a ubicación segura.")
        
        elif 'config' in ruta_lower:
            recommendations.append("⚙️ Archivo de configuración expuesto.")
            recommendations.append("Revisar si contiene credenciales o información sensible.")
        
        elif status_code == 403:
            recommendations.append("🔒 Recurso protegido detectado. Investigar si debería ser accesible.")
        
        elif status_code >= 500:
            recommendations.append("💥 Error del servidor. Revisar logs para más detalles.")
        
        # Recomendaciones generales
        if not recommendations:
            recommendations.append("📋 Revisar el hallazgo y determinar si requiere acción.")
        
        recommendations.append("📊 Actualizar el estado de la alerta después de la investigación.")
        
        return recommendations
    
    def calculate_ml_confidence(self, row: pd.Series) -> float:
        """Calcular confianza del modelo ML"""
        confidence = 0.5  # Base
        
        # Aumentar confianza si hay múltiples indicadores
        if hasattr(row, 'is_anomaly') and row['is_anomaly']:
            confidence += 0.2
        
        if hasattr(row, 'predicted_priority'):
            priority_confidence = {
                'critical': 0.9,
                'high': 0.8,
                'medium': 0.6,
                'low': 0.4
            }
            confidence = max(confidence, priority_confidence.get(row['predicted_priority'], 0.5))
        
        return min(confidence, 1.0)
    
    def calculate_false_positive_probability(self, row: pd.Series) -> float:
        """Calcular probabilidad de falso positivo"""
        fp_prob = 0.1  # Base baja
        
        ruta_lower = str(row['ruta']).lower()
        
        # Aumentar probabilidad para patrones comunes
        if any(fp in ruta_lower for fp in self.false_positive_patterns['common_false_positives']):
            fp_prob += 0.6
        
        # Disminuir para patrones críticos
        if any(pattern in ruta_lower for pattern in ['admin', '.git', 'config', 'backup']):
            fp_prob = max(0.05, fp_prob - 0.3)
        
        return min(fp_prob, 0.95)
    
    def save_model(self, model, filename: str) -> None:
        """Guardar modelo entrenado"""
        try:
            model_path = self.models_dir / filename
            joblib.dump(model, model_path)
            self.logger.info(f"Modelo guardado: {model_path}")
        except Exception as e:
            self.logger.error(f"Error guardando modelo {filename}: {e}")
    
    def load_models(self) -> None:
        """Cargar modelos entrenados"""
        try:
            # Detector de anomalías
            anomaly_path = self.models_dir / 'anomaly_detector.joblib'
            if anomaly_path.exists():
                self.anomaly_detector = joblib.load(anomaly_path)
                self.logger.info("Detector de anomalías cargado")
            
            # Scaler
            scaler_path = self.models_dir / 'scaler.joblib'
            if scaler_path.exists():
                self.scaler = joblib.load(scaler_path)
                self.logger.info("Scaler cargado")
            
            # Clasificador de prioridad
            classifier_path = self.models_dir / 'priority_classifier.joblib'
            if classifier_path.exists():
                self.priority_classifier = joblib.load(classifier_path)
                self.logger.info("Clasificador de prioridad cargado")
                
        except Exception as e:
            self.logger.error(f"Error cargando modelos: {e}")
    
    def retrain_models(self, days_back: int = 30) -> None:
        """Reentrenar modelos con datos recientes"""
        with sqlite3.connect(self.db_path) as conn:
            # Cargar datos recientes
            query = """
                SELECT h.*, d.dominio 
                FROM hallazgos h
                JOIN dominios d ON h.dominio_id = d.id
                WHERE h.fecha_descubierto >= datetime('now', '-{} days')
            """.format(days_back)
            
            df = pd.read_sql_query(query, conn)
            
            if len(df) < 100:
                self.logger.warning("Insuficientes datos para reentrenamiento")
                return
            
            self.logger.info(f"Reentrenando modelos con {len(df)} registros")
            
            # Extraer características
            features_df = self.extract_features(df)
            
            # Reentrenar modelos
            self.train_anomaly_detector(features_df)
            self.train_priority_classifier(features_df)
            
            self.logger.info("Modelos reentrenados exitosamente")
    
    def get_model_statistics(self) -> Dict:
        """Obtener estadísticas de los modelos"""
        stats = {
            'models_loaded': {
                'anomaly_detector': self.anomaly_detector is not None,
                'priority_classifier': self.priority_classifier is not None
            },
            'last_training': 'Unknown',
            'model_files': []
        }
        
        # Listar archivos de modelos
        for model_file in self.models_dir.glob('*.joblib'):
            stats['model_files'].append({
                'name': model_file.name,
                'size_mb': round(model_file.stat().st_size / (1024*1024), 2),
                'modified': datetime.fromtimestamp(model_file.stat().st_mtime).isoformat()
            })
        
        return stats

# Función principal para testing
def main():
    """Función principal para testing del sistema"""
    import argparse
    
    parser = argparse.ArgumentParser(description='Intelligent Alert System')
    parser.add_argument('--db', required=True, help='Ruta a la base de datos')
    parser.add_argument('--action', choices=['train', 'predict', 'stats'], 
                       default='predict', help='Acción a realizar')
    parser.add_argument('--days', type=int, default=30, help='Días para entrenamiento')
    
    args = parser.parse_args()
    
    # Configurar logging
    logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')
    
    # Crear sistema de alertas
    alert_system = IntelligentAlertSystem(args.db)
    
    if args.action == 'train':
        print("🤖 Entrenando modelos de ML...")
        alert_system.retrain_models(args.days)
        print("✅ Entrenamiento completado")
    
    elif args.action == 'stats':
        stats = alert_system.get_model_statistics()
        print("\n📊 ESTADÍSTICAS DE MODELOS ML:")
        print("=" * 50)
        for key, value in stats.items():
            print(f"{key}: {value}")
    
    elif args.action == 'predict':
        # Cargar hallazgos recientes y generar alertas
        with sqlite3.connect(args.db) as conn:
            df = pd.read_sql_query("""
                SELECT h.*, d.dominio 
                FROM hallazgos h
                JOIN dominios d ON h.dominio_id = d.id
                WHERE h.fecha_descubierto >= datetime('now', '-1 day')
                ORDER BY h.fecha_descubierto DESC
                LIMIT 100
            """, conn)
            
            if not df.empty:
                alerts = alert_system.generate_intelligent_alerts(df)
                
                print(f"\n🚨 ALERTAS INTELIGENTES GENERADAS: {len(alerts)}")
                print("=" * 60)
                
                for alert in alerts[:10]:  # Mostrar top 10
                    print(f"🔹 {alert['priority'].upper()} - Score: {alert['risk_score']}")
                    print(f"   URL: {alert['finding_data']['url']}")
                    print(f"   Recomendación: {alert['recommendations'][0]}")
                    print()
            else:
                print("❌ No hay hallazgos recientes para analizar")

if __name__ == "__main__":
    main()