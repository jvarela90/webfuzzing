#!/usr/bin/env python3
"""
Módulo de Gestión de Dominios - URLControl
Permite agregar, editar y eliminar dominios desde el dashboard
"""

from flask import Blueprint, request, jsonify, render_template, redirect, url_for, flash
from sqlalchemy import create_engine, Column, Integer, String, DateTime, Boolean, Text
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy.orm import sessionmaker
from datetime import datetime
import re
import socket
import requests
from urllib.parse import urlparse
import json
import os
from typing import List, Dict, Any, Optional

# Configuración de la base de datos
Base = declarative_base()

class Domain(Base):
    """Modelo de dominio en la base de datos"""
    __tablename__ = 'domains'
    
    id = Column(Integer, primary_key=True)
    domain = Column(String(255), unique=True, nullable=False)
    subdomain = Column(String(255), nullable=True)
    full_url = Column(String(500), nullable=False)
    status = Column(String(20), default='active')  # active, inactive, error
    added_date = Column(DateTime, default=datetime.utcnow)
    last_scan = Column(DateTime, nullable=True)
    scan_enabled = Column(Boolean, default=True)
    custom_paths = Column(Text, nullable=True)  # JSON string of custom paths
    notes = Column(Text, nullable=True)
    
    def to_dict(self):
        """Convertir el dominio a diccionario"""
        return {
            'id': self.id,
            'domain': self.domain,
            'subdomain': self.subdomain,
            'full_url': self.full_url,
            'status': self.status,
            'added_date': self.added_date.isoformat() if self.added_date else None,
            'last_scan': self.last_scan.isoformat() if self.last_scan else None,
            'scan_enabled': self.scan_enabled,
            'custom_paths': json.loads(self.custom_paths) if self.custom_paths else [],
            'notes': self.notes
        }

class DomainManager:
    """Gestor de dominios"""
    
    def __init__(self, database_url: str = None):
        if not database_url:
            database_url = os.getenv('DATABASE_URL', 'sqlite:///urlcontrol.db')
        
        self.engine = create_engine(database_url)
        Base.metadata.create_all(self.engine)
        Session = sessionmaker(bind=self.engine)
        self.session = Session()
    
    def validate_domain(self, domain: str) -> Dict[str, Any]:
        """Validar un dominio y obtener información"""
        result = {
            'valid': False,
            'domain': '',
            'subdomain': '',
            'full_url': '',
            'ip': '',
            'status_code': None,
            'error': ''
        }
        
        try:
            # Limpiar y formatear el dominio
            domain = domain.strip().lower()
            
            # Agregar https:// si no tiene protocolo
            if not domain.startswith(('http://', 'https://')):
                domain = f"https://{domain}"
            
            # Parsear URL
            parsed = urlparse(domain)
            if not parsed.netloc:
                result['error'] = 'Formato de dominio inválido'
                return result
            
            # Extraer dominio principal y subdominio
            parts = parsed.netloc.split('.')
            if len(parts) >= 2:
                if len(parts) > 2:
                    result['subdomain'] = '.'.join(parts[:-2])
                    result['domain'] = '.'.join(parts[-2:])
                else:
                    result['domain'] = parsed.netloc
            else:
                result['error'] = 'Dominio inválido'
                return result
            
            result['full_url'] = domain
            
            # Resolver IP
            try:
                result['ip'] = socket.gethostbyname(parsed.netloc)
            except socket.gaierror:
                result['error'] = 'No se pudo resolver el dominio'
                return result
            
            # Verificar conectividad
            try:
                response = requests.head(domain, timeout=10, allow_redirects=True)
                result['status_code'] = response.status_code
                result['valid'] = True
            except requests.RequestException as e:
                result['error'] = f'Error de conexión: {str(e)}'
                return result
            
        except Exception as e:
            result['error'] = f'Error de validación: {str(e)}'
        
        return result
    
    def add_domain(self, domain_data: Dict[str, Any]) -> Dict[str, Any]:
        """Agregar un nuevo dominio"""
        try:
            # Validar dominio
            validation = self.validate_domain(domain_data['domain'])
            if not validation['valid']:
                return {
                    'success': False,
                    'error': validation['error']
                }
            
            # Verificar si ya existe
            existing = self.session.query(Domain).filter_by(
                full_url=validation['full_url']
            ).first()
            
            if existing:
                return {
                    'success': False,
                    'error': 'El dominio ya existe en la base de datos'
                }
            
            # Crear nuevo dominio
            new_domain = Domain(
                domain=validation['domain'],
                subdomain=validation['subdomain'],
                full_url=validation['full_url'],
                status='active',
                scan_enabled=domain_data.get('scan_enabled', True),
                custom_paths=json.dumps(domain_data.get('custom_paths', [])),
                notes=domain_data.get('notes', '')
            )
            
            self.session.add(new_domain)
            self.session.commit()
            
            return {
                'success': True,
                'domain': new_domain.to_dict(),
                'message': 'Dominio agregado exitosamente'
            }
            
        except Exception as e:
            self.session.rollback()
            return {
                'success': False,
                'error': f'Error al agregar dominio: {str(e)}'
            }
    
    def update_domain(self, domain_id: int, domain_data: Dict[str, Any]) -> Dict[str, Any]:
        """Actualizar un dominio existente"""
        try:
            domain = self.session.query(Domain).filter_by(id=domain_id).first()
            if not domain:
                return {
                    'success': False,
                    'error': 'Dominio no encontrado'
                }
            
            # Actualizar campos
            if 'scan_enabled' in domain_data:
                domain.scan_enabled = domain_data['scan_enabled']
            
            if 'custom_paths' in domain_data:
                domain.custom_paths = json.dumps(domain_data['custom_paths'])
            
            if 'notes' in domain_data:
                domain.notes = domain_data['notes']
            
            if 'status' in domain_data:
                domain.status = domain_data['status']
            
            self.session.commit()
            
            return {
                'success': True,
                'domain': domain.to_dict(),
                'message': 'Dominio actualizado exitosamente'
            }
            
        except Exception as e:
            self.session.rollback()
            return {
                'success': False,
                'error': f'Error al actualizar dominio: {str(e)}'
            }
    
    def delete_domain(self, domain_id: int) -> Dict[str, Any]:
        """Eliminar un dominio"""
        try:
            domain = self.session.query(Domain).filter_by(id=domain_id).first()
            if not domain:
                return {
                    'success': False,
                    'error': 'Dominio no encontrado'
                }
            
            self.session.delete(domain)
            self.session.commit()
            
            return {
                'success': True,
                'message': 'Dominio eliminado exitosamente'
            }
            
        except Exception as e:
            self.session.rollback()
            return {
                'success': False,
                'error': f'Error al eliminar dominio: {str(e)}'
            }
    
    def get_domains(self, status: str = None) -> List[Dict[str, Any]]:
        """Obtener lista de dominios"""
        try:
            query = self.session.query(Domain)
            
            if status:
                query = query.filter_by(status=status)
            
            domains = query.order_by(Domain.added_date.desc()).all()
            return [domain.to_dict() for domain in domains]
            
        except Exception as e:
            print(f"Error al obtener dominios: {str(e)}")
            return []
    
    def get_domain(self, domain_id: int) -> Optional[Dict[str, Any]]:
        """Obtener un dominio específico"""
        try:
            domain = self.session.query(Domain).filter_by(id=domain_id).first()
            return domain.to_dict() if domain else None
            
        except Exception as e:
            print(f"Error al obtener dominio: {str(e)}")
            return None
    
    def bulk_add_domains(self, domains_list: List[str]) -> Dict[str, Any]:
        """Agregar múltiples dominios"""
        results = {
            'success': [],
            'failed': [],
            'total': len(domains_list)
        }
        
        for domain_url in domains_list:
            result = self.add_domain({'domain': domain_url})
            
            if result['success']:
                results['success'].append({
                    'domain': domain_url,
                    'data': result['domain']
                })
            else:
                results['failed'].append({
                    'domain': domain_url,
                    'error': result['error']
                })
        
        return results
    
    def export_domains(self) -> Dict[str, Any]:
        """Exportar dominios a JSON"""
        try:
            domains = self.get_domains()
            export_data = {
                'export_date': datetime.utcnow().isoformat(),
                'total_domains': len(domains),
                'domains': domains
            }
            
            return {
                'success': True,
                'data': export_data
            }
            
        except Exception as e:
            return {
                'success': False,
                'error': f'Error al exportar dominios: {str(e)}'
            }

# Blueprint para las rutas del dashboard
domain_bp = Blueprint('domains', __name__, url_prefix='/domains')
domain_manager = DomainManager()

@domain_bp.route('/')
def domains_list():
    """Página principal de gestión de dominios"""
    domains = domain_manager.get_domains()
    return render_template('domains/list.html', domains=domains)

@domain_bp.route('/add', methods=['GET', 'POST'])
def add_domain():
    """Agregar nuevo dominio"""
    if request.method == 'POST':
        domain_data = {
            'domain': request.form.get('domain'),
            'scan_enabled': request.form.get('scan_enabled') == 'on',
            'custom_paths': request.form.get('custom_paths', '').split('\n') if request.form.get('custom_paths') else [],
            'notes': request.form.get('notes', '')
        }
        
        result = domain_manager.add_domain(domain_data)
        
        if result['success']:
            flash('Dominio agregado exitosamente', 'success')
            return redirect(url_for('domains.domains_list'))
        else:
            flash(f'Error: {result["error"]}', 'error')
    
    return render_template('domains/add.html')

@domain_bp.route('/api/add', methods=['POST'])
def api_add_domain():
    """API para agregar dominio via AJAX"""
    data = request.get_json()
    
    if not data or 'domain' not in data:
        return jsonify({'success': False, 'error': 'Dominio requerido'}), 400
    
    result = domain_manager.add_domain(data)
    
    if result['success']:
        return jsonify(result), 201
    else:
        return jsonify(result), 400

@domain_bp.route('/api/validate', methods=['POST'])
def api_validate_domain():
    """API para validar dominio"""
    data = request.get_json()
    
    if not data or 'domain' not in data:
        return jsonify({'success': False, 'error': 'Dominio requerido'}), 400
    
    validation = domain_manager.validate_domain(data['domain'])
    return jsonify(validation)

@domain_bp.route('/api/bulk', methods=['POST'])
def api_bulk_add():
    """API para agregar múltiples dominios"""
    data = request.get_json()
    
    if not data or 'domains' not in data:
        return jsonify({'success': False, 'error': 'Lista de dominios requerida'}), 400
    
    results = domain_manager.bulk_add_domains(data['domains'])
    return jsonify(results)

@domain_bp.route('/api/<int:domain_id>', methods=['PUT'])
def api_update_domain(domain_id):
    """API para actualizar dominio"""
    data = request.get_json()
    result = domain_manager.update_domain(domain_id, data)
    
    if result['success']:
        return jsonify(result)
    else:
        return jsonify(result), 400

@domain_bp.route('/api/<int:domain_id>', methods=['DELETE'])
def api_delete_domain(domain_id):
    """API para eliminar dominio"""
    result = domain_manager.delete_domain(domain_id)
    
    if result['success']:
        return jsonify(result)
    else:
        return jsonify(result), 400

@domain_bp.route('/api/list')
def api_list_domains():
    """API para listar dominios"""
    status = request.args.get('status')
    domains = domain_manager.get_domains(status)
    return jsonify({'domains': domains})

@domain_bp.route('/api/export')
def api_export_domains():
    """API para exportar dominios"""
    result = domain_manager.export_domains()
    
    if result['success']:
        return jsonify(result['data'])
    else:
        return jsonify(result), 500

@domain_bp.route('/edit/<int:domain_id>', methods=['GET', 'POST'])
def edit_domain(domain_id):
    """Editar dominio existente"""
    domain = domain_manager.get_domain(domain_id)
    
    if not domain:
        flash('Dominio no encontrado', 'error')
        return redirect(url_for('domains.domains_list'))
    
    if request.method == 'POST':
        domain_data = {
            'scan_enabled': request.form.get('scan_enabled') == 'on',
            'custom_paths': request.form.get('custom_paths', '').split('\n') if request.form.get('custom_paths') else [],
            'notes': request.form.get('notes', ''),
            'status': request.form.get('status', 'active')
        }
        
        result = domain_manager.update_domain(domain_id, domain_data)
        
        if result['success']:
            flash('Dominio actualizado exitosamente', 'success')
            return redirect(url_for('domains.domains_list'))
        else:
            flash(f'Error: {result["error"]}', 'error')
    
    return render_template('domains/edit.html', domain=domain)

@domain_bp.route('/delete/<int:domain_id>')
def delete_domain(domain_id):
    """Eliminar dominio"""
    result = domain_manager.delete_domain(domain_id)
    
    if result['success']:
        flash('Dominio eliminado exitosamente', 'success')
    else:
        flash(f'Error: {result["error"]}', 'error')
    
    return redirect(url_for('domains.domains_list'))