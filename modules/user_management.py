#!/usr/bin/env python3
"""
Sistema de Gestión de Usuarios y Configuración
Gestión completa de usuarios, roles, permisos y configuración del sistema
"""

import os
import json
import sqlite3
import yaml
import logging
from datetime import datetime, timedelta
from pathlib import Path
from typing import Dict, List, Optional, Set
from werkzeug.security import generate_password_hash, check_password_hash
from dataclasses import dataclass, asdict
from enum import Enum
import secrets
import smtplib
from email.mime.text import MimeText
from email.mime.multipart import MimeMultipart
import jwt
import qrcode
import io
import base64
from cryptography.fernet import Fernet

class UserRole(Enum):
    """Roles de usuario"""
    ADMIN = "admin"
    ANALYST = "analyst"
    OPERATOR = "operator"
    VIEWER = "viewer"
    AUDITOR = "auditor"

class PermissionLevel(Enum):
    """Niveles de permisos"""
    READ = "read"
    WRITE = "write"
    DELETE = "delete"
    ADMIN = "admin"

@dataclass
class Permission:
    """Definición de permiso"""
    resource: str
    action: str
    level: PermissionLevel
    description: str = ""

@dataclass
class UserProfile:
    """Perfil de usuario"""
    id: int
    username: str
    email: str
    full_name: str
    role: UserRole
    permissions: List[str]
    is_active: bool
    is_verified: bool
    last_login: Optional[datetime]
    created_at: datetime
    updated_at: datetime
    preferences: Dict
    two_factor_enabled: bool = False
    password_expires_at: Optional[datetime] = None
    failed_login_attempts: int = 0
    locked_until: Optional[datetime] = None

class UserManagementSystem:
    """Sistema completo de gestión de usuarios"""
    
    def __init__(self, db_path: str = "data/users.db", config_path: str = "config/system.yaml"):
        self.db_path = Path(db_path)
        self.config_path = Path(config_path)
        self.logger = logging.getLogger(__name__)
        
        # Configurar encriptación
        self.encryption_key = self._get_or_create_encryption_key()
        self.cipher = Fernet(self.encryption_key)
        
        # Configurar sistema
        self.config = self.load_system_config()
        self.permissions_registry = self._initialize_permissions()
        
        # Inicializar base de datos
        self.init_database()
        
        # Crear usuario admin por defecto
        self.create_default_users()
    
    def _get_or_create_encryption_key(self) -> bytes:
        """Obtener o crear clave de encriptación"""
        key_file = Path("config/encryption.key")
        key_file.parent.mkdir(exist_ok=True)
        
        if key_file.exists():
            with open(key_file, 'rb') as f:
                return f.read()
        else:
            key = Fernet.generate_key()
            with open(key_file, 'wb') as f:
                f.write(key)
            os.chmod(key_file, 0o600)  # Solo lectura para propietario
            return key
    
    def load_system_config(self) -> Dict:
        """Cargar configuración del sistema"""
        default_config = {
            'security': {
                'password_policy': {
                    'min_length': 12,
                    'require_uppercase': True,
                    'require_lowercase': True,
                    'require_numbers': True,
                    'require_symbols': True,
                    'max_age_days': 90,
                    'history_count': 5
                },
                'login_policy': {
                    'max_failed_attempts': 5,
                    'lockout_duration_minutes': 30,
                    'session_timeout_hours': 8,
                    'require_2fa_for_admin': True
                },
                'audit': {
                    'log_all_actions': True,
                    'retain_logs_days': 365,
                    'alert_on_suspicious_activity': True
                }
            },
            'notifications': {
                'email': {
                    'enabled': True,
                    'smtp_server': 'localhost',
                    'smtp_port': 587,
                    'use_tls': True,
                    'from_address': 'security@company.com'
                },
                'welcome_new_users': True,
                'notify_admin_on_new_user': True,
                'password_expiry_warning_days': 7
            },
            'system': {
                'organization_name': 'Security Operations',
                'timezone': 'UTC',
                'default_user_role': 'viewer',
                'auto_logout_inactive_users': True,
                'require_email_verification': True
            }
        }
        
        self.config_path.parent.mkdir(exist_ok=True)
        
        if self.config_path.exists():
            try:
                with open(self.config_path, 'r') as f:
                    loaded_config = yaml.safe_load(f)
                    # Merge con configuración por defecto
                    self._deep_update(default_config, loaded_config)
            except Exception as e:
                self.logger.error(f"Error cargando configuración: {e}")
        else:
            # Guardar configuración por defecto
            with open(self.config_path, 'w') as f:
                yaml.dump(default_config, f, default_flow_style=False, indent=2)
        
        return default_config
    
    def _deep_update(self, base_dict: Dict, update_dict: Dict):
        """Actualización profunda de diccionario"""
        for key, value in update_dict.items():
            if key in base_dict and isinstance(base_dict[key], dict) and isinstance(value, dict):
                self._deep_update(base_dict[key], value)
            else:
                base_dict[key] = value
    
    def _initialize_permissions(self) -> Dict[str, Permission]:
        """Inicializar registro de permisos"""
        permissions = {
            # Gestión de dominios
            'domains:read': Permission('domains', 'read', PermissionLevel.READ, 'Ver dominios'),
            'domains:create': Permission('domains', 'create', PermissionLevel.WRITE, 'Crear dominios'),
            'domains:update': Permission('domains', 'update', PermissionLevel.WRITE, 'Actualizar dominios'),
            'domains:delete': Permission('domains', 'delete', PermissionLevel.DELETE, 'Eliminar dominios'),
            
            # Gestión de escaneos
            'scans:read': Permission('scans', 'read', PermissionLevel.READ, 'Ver escaneos'),
            'scans:execute': Permission('scans', 'execute', PermissionLevel.WRITE, 'Ejecutar escaneos'),
            'scans:cancel': Permission('scans', 'cancel', PermissionLevel.WRITE, 'Cancelar escaneos'),
            'scans:schedule': Permission('scans', 'schedule', PermissionLevel.WRITE, 'Programar escaneos'),
            
            # Gestión de alertas
            'alerts:read': Permission('alerts', 'read', PermissionLevel.READ, 'Ver alertas'),
            'alerts:update': Permission('alerts', 'update', PermissionLevel.WRITE, 'Actualizar alertas'),
            'alerts:assign': Permission('alerts', 'assign', PermissionLevel.WRITE, 'Asignar alertas'),
            'alerts:close': Permission('alerts', 'close', PermissionLevel.WRITE, 'Cerrar alertas'),
            
            # Gestión de reportes
            'reports:read': Permission('reports', 'read', PermissionLevel.READ, 'Ver reportes'),
            'reports:generate': Permission('reports', 'generate', PermissionLevel.WRITE, 'Generar reportes'),
            'reports:export': Permission('reports', 'export', PermissionLevel.WRITE, 'Exportar reportes'),
            
            # Configuración del sistema
            'system:read': Permission('system', 'read', PermissionLevel.READ, 'Ver configuración'),
            'system:configure': Permission('system', 'configure', PermissionLevel.ADMIN, 'Configurar sistema'),
            'system:backup': Permission('system', 'backup', PermissionLevel.ADMIN, 'Respaldar sistema'),
            'system:restore': Permission('system', 'restore', PermissionLevel.ADMIN, 'Restaurar sistema'),
            
            # Gestión de usuarios
            'users:read': Permission('users', 'read', PermissionLevel.READ, 'Ver usuarios'),
            'users:create': Permission('users', 'create', PermissionLevel.ADMIN, 'Crear usuarios'),
            'users:update': Permission('users', 'update', PermissionLevel.ADMIN, 'Actualizar usuarios'),
            'users:delete': Permission('users', 'delete', PermissionLevel.ADMIN, 'Eliminar usuarios'),
            'users:manage_roles': Permission('users', 'manage_roles', PermissionLevel.ADMIN, 'Gestionar roles'),
            
            # Auditoría
            'audit:read': Permission('audit', 'read', PermissionLevel.READ, 'Ver auditoría'),
            'audit:export': Permission('audit', 'export', PermissionLevel.WRITE, 'Exportar auditoría'),
        }
        
        return permissions
    
    def init_database(self):
        """Inicializar base de datos de usuarios"""
        self.db_path.parent.mkdir(exist_ok=True)
        
        with sqlite3.connect(self.db_path) as conn:
            cursor = conn.cursor()
            
            # Tabla de usuarios
            cursor.execute('''
                CREATE TABLE IF NOT EXISTS users (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    username TEXT UNIQUE NOT NULL,
                    email TEXT UNIQUE NOT NULL,
                    password_hash TEXT NOT NULL,
                    full_name TEXT NOT NULL,
                    role TEXT NOT NULL,
                    permissions TEXT,
                    is_active BOOLEAN DEFAULT TRUE,
                    is_verified BOOLEAN DEFAULT FALSE,
                    two_factor_secret TEXT,
                    two_factor_enabled BOOLEAN DEFAULT FALSE,
                    password_expires_at DATETIME,
                    failed_login_attempts INTEGER DEFAULT 0,
                    locked_until DATETIME,
                    last_login DATETIME,
                    created_at DATETIME DEFAULT CURRENT_TIMESTAMP,
                    updated_at DATETIME DEFAULT CURRENT_TIMESTAMP,
                    preferences TEXT DEFAULT '{}'
                )
            ''')
            
            # Tabla de sesiones
            cursor.execute('''
                CREATE TABLE IF NOT EXISTS user_sessions (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    user_id INTEGER NOT NULL,
                    session_token TEXT UNIQUE NOT NULL,
                    ip_address TEXT,
                    user_agent TEXT,
                    created_at DATETIME DEFAULT CURRENT_TIMESTAMP,
                    expires_at DATETIME NOT NULL,
                    is_active BOOLEAN DEFAULT TRUE,
                    FOREIGN KEY (user_id) REFERENCES users (id)
                )
            ''')
            
            # Tabla de auditoría
            cursor.execute('''
                CREATE TABLE IF NOT EXISTS audit_log (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    user_id INTEGER,
                    username TEXT,
                    action TEXT NOT NULL,
                    resource TEXT,
                    resource_id TEXT,
                    ip_address TEXT,
                    user_agent TEXT,
                    success BOOLEAN DEFAULT TRUE,
                    details TEXT,
                    timestamp DATETIME DEFAULT CURRENT_TIMESTAMP,
                    FOREIGN KEY (user_id) REFERENCES users (id)
                )
            ''')
            
            # Tabla de tokens de verificación
            cursor.execute('''
                CREATE TABLE IF NOT EXISTS verification_tokens (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    user_id INTEGER NOT NULL,
                    token TEXT UNIQUE NOT NULL,
                    token_type TEXT NOT NULL,
                    expires_at DATETIME NOT NULL,
                    used_at DATETIME,
                    created_at DATETIME DEFAULT CURRENT_TIMESTAMP,
                    FOREIGN KEY (user_id) REFERENCES users (id)
                )
            ''')
            
            # Tabla de historial de contraseñas
            cursor.execute('''
                CREATE TABLE IF NOT EXISTS password_history (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    user_id INTEGER NOT NULL,
                    password_hash TEXT NOT NULL,
                    created_at DATETIME DEFAULT CURRENT_TIMESTAMP,
                    FOREIGN KEY (user_id) REFERENCES users (id)
                )
            ''')
            
            conn.commit()
    
    def create_default_users(self):
        """Crear usuarios por defecto"""
        # Crear usuario admin si no existe
        if not self.get_user_by_username('admin'):
            admin_password = secrets.token_urlsafe(16)
            
            admin_user = self.create_user(
                username='admin',
                email='admin@security.local',
                password=admin_password,
                full_name='System Administrator',
                role=UserRole.ADMIN,
                is_verified=True
            )
            
            if admin_user:
                self.logger.info(f"Admin user created - Username: admin, Password: {admin_password}")
                
                # Crear token de verificación para cambio de contraseña
                token = self.create_verification_token(admin_user.id, 'password_reset', expires_hours=168)  # 7 días
                self.logger.info(f"Password reset token: {token}")
    
    def create_user(self, username: str, email: str, password: str, full_name: str, 
                   role: UserRole, is_verified: bool = False, 
                   send_welcome_email: bool = True) -> Optional[UserProfile]:
        """Crear nuevo usuario"""
        try:
            # Validar política de contraseña
            if not self.validate_password(password):
                raise ValueError("Password does not meet policy requirements")
            
            # Generar hash de contraseña
            password_hash = generate_password_hash(password)
            
            # Calcular expiración de contraseña
            password_expires_at = None
            max_age_days = self.config['security']['password_policy']['max_age_days']
            if max_age_days > 0:
                password_expires_at = datetime.now() + timedelta(days=max_age_days)
            
            # Obtener permisos por defecto para el rol
            permissions = self.get_role_permissions(role)
            
            with sqlite3.connect(self.db_path) as conn:
                cursor = conn.cursor()
                
                cursor.execute('''
                    INSERT INTO users 
                    (username, email, password_hash, full_name, role, permissions, 
                     is_verified, password_expires_at)
                    VALUES (?, ?, ?, ?, ?, ?, ?, ?)
                ''', (username, email, password_hash, full_name, role.value, 
                     json.dumps(permissions), is_verified, 
                     password_expires_at.isoformat() if password_expires_at else None))
                
                user_id = cursor.lastrowid
                
                # Guardar en historial de contraseñas
                cursor.execute('''
                    INSERT INTO password_history (user_id, password_hash)
                    VALUES (?, ?)
                ''', (user_id, password_hash))
                
                conn.commit()
                
                # Crear token de verificación si es necesario
                if not is_verified and self.config['system']['require_email_verification']:
                    verification_token = self.create_verification_token(user_id, 'email_verification')
                    
                    if send_welcome_email:
                        self.send_welcome_email(email, username, verification_token)
                
                # Log de auditoría
                self.log_audit(
                    user_id=None,
                    username='system',
                    action='user_created',
                    resource='user',
                    resource_id=str(user_id),
                    details=f"User {username} created with role {role.value}"
                )
                
                return self.get_user_by_id(user_id)
                
        except sqlite3.IntegrityError as e:
            if 'username' in str(e):
                raise ValueError("Username already exists")
            elif 'email' in str(e):
                raise ValueError("Email already exists")
            else:
                raise ValueError("User creation failed")
        except Exception as e:
            self.logger.error(f"Error creating user: {e}")
            raise
    
    def validate_password(self, password: str) -> bool:
        """Validar contraseña según política"""
        policy = self.config['security']['password_policy']
        
        if len(password) < policy['min_length']:
            return False
        
        if policy['require_uppercase'] and not any(c.isupper() for c in password):
            return False
        
        if policy['require_lowercase'] and not any(c.islower() for c in password):
            return False
        
        if policy['require_numbers'] and not any(c.isdigit() for c in password):
            return False
        
        if policy['require_symbols'] and not any(c in '!@#$%^&*()_+-=[]{}|;:,.<>?' for c in password):
            return False
        
        return True
    
    def get_role_permissions(self, role: UserRole) -> List[str]:
        """Obtener permisos por defecto para un rol"""
        role_permissions = {
            UserRole.ADMIN: ['*'],  # Todos los permisos
            UserRole.ANALYST: [
                'domains:read', 'domains:create', 'domains:update',
                'scans:read', 'scans:execute', 'scans:schedule',
                'alerts:read', 'alerts:update', 'alerts:assign', 'alerts:close',
                'reports:read', 'reports:generate', 'reports:export',
                'system:read'
            ],
            UserRole.OPERATOR: [
                'domains:read', 'domains:create',
                'scans:read', 'scans:execute',
                'alerts:read', 'alerts:update',
                'reports:read', 'reports:generate'
            ],
            UserRole.VIEWER: [
                'domains:read',
                'scans:read',
                'alerts:read',
                'reports:read'
            ],
            UserRole.AUDITOR: [
                'domains:read',
                'scans:read',
                'alerts:read',
                'reports:read', 'reports:export',
                'audit:read', 'audit:export'
            ]
        }
        
        return role_permissions.get(role, [])
    
    def authenticate_user(self, username: str, password: str, 
                         ip_address: str = None) -> Optional[UserProfile]:
        """Autenticar usuario"""
        user = self.get_user_by_username(username)
        
        if not user:
            self.log_audit(
                username=username,
                action='login_failed',
                resource='auth',
                details='User not found',
                success=False,
                ip_address=ip_address
            )
            return None
        
        # Verificar si la cuenta está bloqueada
        if user.locked_until and user.locked_until > datetime.now():
            self.log_audit(
                user_id=user.id,
                username=username,
                action='login_failed',
                resource='auth',
                details='Account locked',
                success=False,
                ip_address=ip_address
            )
            return None
        
        # Verificar contraseña
        with sqlite3.connect(self.db_path) as conn:
            cursor = conn.cursor()
            cursor.execute('SELECT password_hash FROM users WHERE id = ?', (user.id,))
            stored_hash = cursor.fetchone()[0]
            
            if not check_password_hash(stored_hash, password):
                # Incrementar intentos fallidos
                failed_attempts = user.failed_login_attempts + 1
                max_attempts = self.config['security']['login_policy']['max_failed_attempts']
                
                locked_until = None
                if failed_attempts >= max_attempts:
                    lockout_minutes = self.config['security']['login_policy']['lockout_duration_minutes']
                    locked_until = datetime.now() + timedelta(minutes=lockout_minutes)
                
                cursor.execute('''
                    UPDATE users 
                    SET failed_login_attempts = ?, locked_until = ?
                    WHERE id = ?
                ''', (failed_attempts, locked_until.isoformat() if locked_until else None, user.id))
                
                conn.commit()
                
                self.log_audit(
                    user_id=user.id,
                    username=username,
                    action='login_failed',
                    resource='auth',
                    details=f'Invalid password (attempt {failed_attempts})',
                    success=False,
                    ip_address=ip_address
                )
                
                return None
            
            # Login exitoso - resetear intentos fallidos y actualizar último login
            cursor.execute('''
                UPDATE users 
                SET failed_login_attempts = 0, locked_until = NULL, last_login = CURRENT_TIMESTAMP
                WHERE id = ?
            ''', (user.id,))
            
            conn.commit()
            
            self.log_audit(
                user_id=user.id,
                username=username,
                action='login_success',
                resource='auth',
                details='Successful login',
                ip_address=ip_address
            )
            
            return self.get_user_by_id(user.id)
    
    def get_user_by_id(self, user_id: int) -> Optional[UserProfile]:
        """Obtener usuario por ID"""
        with sqlite3.connect(self.db_path) as conn:
            cursor = conn.cursor()
            cursor.execute('''
                SELECT id, username, email, full_name, role, permissions, 
                       is_active, is_verified, last_login, created_at, updated_at,
                       preferences, two_factor_enabled, password_expires_at,
                       failed_login_attempts, locked_until
                FROM users WHERE id = ?
            ''', (user_id,))
            
            row = cursor.fetchone()
            if not row:
                return None
            
            return UserProfile(
                id=row[0],
                username=row[1],
                email=row[2],
                full_name=row[3],
                role=UserRole(row[4]),
                permissions=json.loads(row[5] or '[]'),
                is_active=bool(row[6]),
                is_verified=bool(row[7]),
                last_login=datetime.fromisoformat(row[8]) if row[8] else None,
                created_at=datetime.fromisoformat(row[9]),
                updated_at=datetime.fromisoformat(row[10]),
                preferences=json.loads(row[11] or '{}'),
                two_factor_enabled=bool(row[12]),
                password_expires_at=datetime.fromisoformat(row[13]) if row[13] else None,
                failed_login_attempts=row[14],
                locked_until=datetime.fromisoformat(row[15]) if row[15] else None
            )
    
    def get_user_by_username(self, username: str) -> Optional[UserProfile]:
        """Obtener usuario por nombre de usuario"""
        with sqlite3.connect(self.db_path) as conn:
            cursor = conn.cursor()
            cursor.execute('SELECT id FROM users WHERE username = ?', (username,))
            row = cursor.fetchone()
            
            if row:
                return self.get_user_by_id(row[0])
            return None
    
    def update_user(self, user_id: int, **kwargs) -> bool:
        """Actualizar usuario"""
        try:
            allowed_fields = [
                'email', 'full_name', 'role', 'permissions', 'is_active', 
                'is_verified', 'preferences', 'two_factor_enabled'
            ]
            
            updates = []
            values = []
            
            for field, value in kwargs.items():
                if field in allowed_fields:
                    if field == 'role' and isinstance(value, UserRole):
                        value = value.value
                    elif field in ['permissions', 'preferences']:
                        value = json.dumps(value)
                    
                    updates.append(f"{field} = ?")
                    values.append(value)
            
            if not updates:
                return False
            
            updates.append("updated_at = CURRENT_TIMESTAMP")
            values.append(user_id)
            
            with sqlite3.connect(self.db_path) as conn:
                cursor = conn.cursor()
                cursor.execute(f'''
                    UPDATE users SET {', '.join(updates)}
                    WHERE id = ?
                ''', values)
                
                conn.commit()
                
                if cursor.rowcount > 0:
                    self.log_audit(
                        user_id=user_id,
                        action='user_updated',
                        resource='user',
                        resource_id=str(user_id),
                        details=f"Updated fields: {', '.join(kwargs.keys())}"
                    )
                    return True
            
            return False
            
        except Exception as e:
            self.logger.error(f"Error updating user: {e}")
            return False
    
    def change_password(self, user_id: int, old_password: str, new_password: str) -> bool:
        """Cambiar contraseña de usuario"""
        try:
            user = self.get_user_by_id(user_id)
            if not user:
                return False
            
            # Verificar contraseña actual
            with sqlite3.connect(self.db_path) as conn:
                cursor = conn.cursor()
                cursor.execute('SELECT password_hash FROM users WHERE id = ?', (user_id,))
                current_hash = cursor.fetchone()[0]
                
                if not check_password_hash(current_hash, old_password):
                    return False
                
                # Validar nueva contraseña
                if not self.validate_password(new_password):
                    raise ValueError("New password does not meet policy requirements")
                
                # Verificar historial de contraseñas
                history_count = self.config['security']['password_policy']['history_count']
                if history_count > 0:
                    cursor.execute('''
                        SELECT password_hash FROM password_history 
                        WHERE user_id = ? 
                        ORDER BY created_at DESC 
                        LIMIT ?
                    ''', (user_id, history_count))
                    
                    for (old_hash,) in cursor.fetchall():
                        if check_password_hash(old_hash, new_password):
                            raise ValueError("Cannot reuse recent passwords")
                
                # Actualizar contraseña
                new_hash = generate_password_hash(new_password)
                
                # Calcular nueva fecha de expiración
                max_age_days = self.config['security']['password_policy']['max_age_days']
                expires_at = None
                if max_age_days > 0:
                    expires_at = datetime.now() + timedelta(days=max_age_days)
                
                cursor.execute('''
                    UPDATE users 
                    SET password_hash = ?, password_expires_at = ?, updated_at = CURRENT_TIMESTAMP
                    WHERE id = ?
                ''', (new_hash, expires_at.isoformat() if expires_at else None, user_id))
                
                # Agregar al historial
                cursor.execute('''
                    INSERT INTO password_history (user_id, password_hash)
                    VALUES (?, ?)
                ''', (user_id, new_hash))
                
                conn.commit()
                
                self.log_audit(
                    user_id=user_id,
                    action='password_changed',
                    resource='user',
                    resource_id=str(user_id),
                    details='Password changed successfully'
                )
                
                return True
                
        except Exception as e:
            self.logger.error(f"Error changing password: {e}")
            return False
    
    def create_verification_token(self, user_id: int, token_type: str, 
                                expires_hours: int = 24) -> str:
        """Crear token de verificación"""
        token = secrets.token_urlsafe(32)
        expires_at = datetime.now() + timedelta(hours=expires_hours)
        
        with sqlite3.connect(self.db_path) as conn:
            cursor = conn.cursor()
            cursor.execute('''
                INSERT INTO verification_tokens (user_id, token, token_type, expires_at)
                VALUES (?, ?, ?, ?)
            ''', (user_id, token, token_type, expires_at.isoformat()))
            
            conn.commit()
        
        return token
    
    def verify_token(self, token: str, token_type: str) -> Optional[int]:
        """Verificar token y retornar user_id si es válido"""
        with sqlite3.connect(self.db_path) as conn:
            cursor = conn.cursor()
            cursor.execute('''
                SELECT user_id FROM verification_tokens
                WHERE token = ? AND token_type = ? 
                AND expires_at > CURRENT_TIMESTAMP AND used_at IS NULL
            ''', (token, token_type))
            
            row = cursor.fetchone()
            if row:
                # Marcar token como usado
                cursor.execute('''
                    UPDATE verification_tokens 
                    SET used_at = CURRENT_TIMESTAMP 
                    WHERE token = ?
                ''', (token,))
                
                conn.commit()
                return row[0]
        
        return None
    
    def setup_two_factor(self, user_id: int) -> Dict:
        """Configurar autenticación de dos factores"""
        try:
            import pyotp
            
            user = self.get_user_by_id(user_id)
            if not user:
                raise ValueError("User not found")
            
            # Generar secreto
            secret = pyotp.random_base32()
            
            # Guardar secreto encriptado
            encrypted_secret = self.cipher.encrypt(secret.encode()).decode()
            
            with sqlite3.connect(self.db_path) as conn:
                cursor = conn.cursor()
                cursor.execute('''
                    UPDATE users SET two_factor_secret = ? WHERE id = ?
                ''', (encrypted_secret, user_id))
                conn.commit()
            
            # Generar QR code
            totp = pyotp.TOTP(secret)
            org_name = self.config['system']['organization_name']
            provisioning_uri = totp.provisioning_uri(
                name=user.email,
                issuer_name=org_name
            )
            
            qr = qrcode.QRCode(version=1, box_size=10, border=5)
            qr.add_data(provisioning_uri)
            qr.make(fit=True)
            
            img = qr.make_image(fill_color="black", back_color="white")
            
            # Convertir a base64
            buffer = io.BytesIO()
            img.save(buffer, format='PNG')
            qr_code_data = base64.b64encode(buffer.getvalue()).decode()
            
            return {
                'secret': secret,
                'qr_code': qr_code_data,
                'provisioning_uri': provisioning_uri
            }
            
        except ImportError:
            raise ValueError("pyotp library required for 2FA")
        except Exception as e:
            self.logger.error(f"Error setting up 2FA: {e}")
            raise
    
    def verify_two_factor(self, user_id: int, token: str) -> bool:
        """Verificar token de dos factores"""
        try:
            import pyotp
            
            with sqlite3.connect(self.db_path) as conn:
                cursor = conn.cursor()
                cursor.execute('''
                    SELECT two_factor_secret FROM users 
                    WHERE id = ? AND two_factor_enabled = TRUE
                ''', (user_id,))
                
                row = cursor.fetchone()
                if not row or not row[0]:
                    return False
                
                # Desencriptar secreto
                encrypted_secret = row[0]
                secret = self.cipher.decrypt(encrypted_secret.encode()).decode()
                
                # Verificar token
                totp = pyotp.TOTP(secret)
                return totp.verify(token, valid_window=1)
                
        except ImportError:
            self.logger.error("pyotp library required for 2FA")
            return False
        except Exception as e:
            self.logger.error(f"Error verifying 2FA: {e}")
            return False
    
    def log_audit(self, action: str, resource: str = None, resource_id: str = None,
                 user_id: int = None, username: str = None, ip_address: str = None,
                 user_agent: str = None, success: bool = True, details: str = None):
        """Registrar evento de auditoría"""
        try:
            with sqlite3.connect(self.db_path) as conn:
                cursor = conn.cursor()
                cursor.execute('''
                    INSERT INTO audit_log 
                    (user_id, username, action, resource, resource_id, 
                     ip_address, user_agent, success, details)
                    VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?)
                ''', (user_id, username, action, resource, resource_id,
                     ip_address, user_agent, success, details))
                
                conn.commit()
        except Exception as e:
            self.logger.error(f"Error logging audit event: {e}")
    
    def get_audit_log(self, limit: int = 100, offset: int = 0, 
                     user_id: int = None, action: str = None,
                     date_from: datetime = None, date_to: datetime = None) -> List[Dict]:
        """Obtener log de auditoría"""
        try:
            with sqlite3.connect(self.db_path) as conn:
                query = """
                    SELECT id, user_id, username, action, resource, resource_id,
                           ip_address, user_agent, success, details, timestamp
                    FROM audit_log
                    WHERE 1=1
                """
                params = []
                
                if user_id:
                    query += " AND user_id = ?"
                    params.append(user_id)
                
                if action:
                    query += " AND action = ?"
                    params.append(action)
                
                if date_from:
                    query += " AND timestamp >= ?"
                    params.append(date_from.isoformat())
                
                if date_to:
                    query += " AND timestamp <= ?"
                    params.append(date_to.isoformat())
                
                query += " ORDER BY timestamp DESC LIMIT ? OFFSET ?"
                params.extend([limit, offset])
                
                cursor = conn.cursor()
                cursor.execute(query, params)
                
                logs = []
                for row in cursor.fetchall():
                    logs.append({
                        'id': row[0],
                        'user_id': row[1],
                        'username': row[2],
                        'action': row[3],
                        'resource': row[4],
                        'resource_id': row[5],
                        'ip_address': row[6],
                        'user_agent': row[7],
                        'success': bool(row[8]),
                        'details': row[9],
                        'timestamp': row[10]
                    })
                
                return logs
                
        except Exception as e:
            self.logger.error(f"Error getting audit log: {e}")
            return []
    
    def send_welcome_email(self, email: str, username: str, verification_token: str = None):
        """Enviar email de bienvenida"""
        if not self.config['notifications']['email']['enabled']:
            return
        
        try:
            org_name = self.config['system']['organization_name']
            
            subject = f"Welcome to {org_name} Security System"
            
            body = f"""
            Welcome to {org_name} Security System!
            
            Username: {username}
            
            """
            
            if verification_token:
                body += f"""
                Please verify your email address by clicking the following link:
                https://security.company.com/verify?token={verification_token}
                
                This link will expire in 24 hours.
                """
            
            body += f"""
            
            Best regards,
            {org_name} Security Team
            """
            
            self._send_email(email, subject, body)
            
        except Exception as e:
            self.logger.error(f"Error sending welcome email: {e}")
    
    def _send_email(self, to_email: str, subject: str, body: str):
        """Enviar email"""
        try:
            email_config = self.config['notifications']['email']
            
            msg = MimeMultipart()
            msg['From'] = email_config['from_address']
            msg['To'] = to_email
            msg['Subject'] = subject
            
            msg.attach(MimeText(body, 'plain'))
            
            with smtplib.SMTP(email_config['smtp_server'], email_config['smtp_port']) as server:
                if email_config['use_tls']:
                    server.starttls()
                
                # Aquí se agregarían credenciales SMTP si son necesarias
                # server.login(username, password)
                
                server.send_message(msg)
                
        except Exception as e:
            self.logger.error(f"Error sending email: {e}")
    
    def list_users(self, limit: int = 100, offset: int = 0, 
                  role: UserRole = None, active_only: bool = True) -> List[UserProfile]:
        """Listar usuarios"""
        try:
            with sqlite3.connect(self.db_path) as conn:
                query = """
                    SELECT id FROM users WHERE 1=1
                """
                params = []
                
                if active_only:
                    query += " AND is_active = TRUE"
                
                if role:
                    query += " AND role = ?"
                    params.append(role.value)
                
                query += " ORDER BY created_at DESC LIMIT ? OFFSET ?"
                params.extend([limit, offset])
                
                cursor = conn.cursor()
                cursor.execute(query, params)
                
                users = []
                for (user_id,) in cursor.fetchall():
                    user = self.get_user_by_id(user_id)
                    if user:
                        users.append(user)
                
                return users
                
        except Exception as e:
            self.logger.error(f"Error listing users: {e}")
            return []
    
    def get_system_stats(self) -> Dict:
        """Obtener estadísticas del sistema"""
        try:
            with sqlite3.connect(self.db_path) as conn:
                cursor = conn.cursor()
                
                # Contar usuarios por rol
                cursor.execute('''
                    SELECT role, COUNT(*) FROM users 
                    WHERE is_active = TRUE 
                    GROUP BY role
                ''')
                users_by_role = dict(cursor.fetchall())
                
                # Usuarios activos últimos 30 días
                cursor.execute('''
                    SELECT COUNT(*) FROM users 
                    WHERE last_login > datetime('now', '-30 days')
                ''')
                active_users_30d = cursor.fetchone()[0]
                
                # Total de eventos de auditoría
                cursor.execute('SELECT COUNT(*) FROM audit_log')
                total_audit_events = cursor.fetchone()[0]
                
                # Intentos fallidos últimas 24h
                cursor.execute('''
                    SELECT COUNT(*) FROM audit_log 
                    WHERE action = 'login_failed' 
                    AND timestamp > datetime('now', '-24 hours')
                ''')
                failed_logins_24h = cursor.fetchone()[0]
                
                return {
                    'users_by_role': users_by_role,
                    'active_users_30d': active_users_30d,
                    'total_audit_events': total_audit_events,
                    'failed_logins_24h': failed_logins_24h,
                    'system_config': {
                        'password_policy_enabled': True,
                        'two_factor_required_admin': self.config['security']['login_policy']['require_2fa_for_admin'],
                        'email_verification_required': self.config['system']['require_email_verification']
                    }
                }
                
        except Exception as e:
            self.logger.error(f"Error getting system stats: {e}")
            return {}

# Función principal para testing
def main():
    """Función principal para testing del sistema"""
    import argparse
    
    parser = argparse.ArgumentParser(description='User Management System')
    parser.add_argument('--action', choices=['create', 'list', 'stats', 'audit'], 
                       default='stats', help='Acción a realizar')
    parser.add_argument('--username', help='Nombre de usuario')
    parser.add_argument('--email', help='Email del usuario')
    parser.add_argument('--role', choices=['admin', 'analyst', 'operator', 'viewer', 'auditor'],
                       default='viewer', help='Rol del usuario')
    
    args = parser.parse_args()
    
    # Configurar logging
    logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')
    
    # Crear sistema de gestión
    user_system = UserManagementSystem()
    
    if args.action == 'create':
        if not args.username or not args.email:
            print("❌ Username y email requeridos para crear usuario")
            return
        
        password = secrets.token_urlsafe(12)
        role = UserRole(args.role)
        
        try:
            user = user_system.create_user(
                username=args.username,
                email=args.email,
                password=password,
                full_name=args.username.title(),
                role=role,
                is_verified=True
            )
            
            if user:
                print(f"✅ Usuario creado exitosamente:")
                print(f"   Username: {user.username}")
                print(f"   Email: {user.email}")
                print(f"   Password: {password}")
                print(f"   Role: {user.role.value}")
            
        except Exception as e:
            print(f"❌ Error creando usuario: {e}")
    
    elif args.action == 'list':
        users = user_system.list_users()
        
        print(f"\n👥 USUARIOS DEL SISTEMA ({len(users)}):")
        print("=" * 80)
        for user in users:
            status = "🟢 Activo" if user.is_active else "🔴 Inactivo"
            verified = "✅ Verificado" if user.is_verified else "❌ No verificado"
            last_login = user.last_login.strftime('%d/%m/%Y %H:%M') if user.last_login else "Nunca"
            
            print(f"ID: {user.id:3d} | {user.username:15s} | {user.role.value:10s} | {status} | {verified} | Último: {last_login}")
    
    elif args.action == 'stats':
        stats = user_system.get_system_stats()
        
        print("\n📊 ESTADÍSTICAS DEL SISTEMA:")
        print("=" * 50)
        print(f"Usuarios por rol:")
        for role, count in stats.get('users_by_role', {}).items():
            print(f"   {role:10s}: {count:3d}")
        
        print(f"\nActividad:")
        print(f"   Usuarios activos (30d): {stats.get('active_users_30d', 0)}")
        print(f"   Eventos de auditoría: {stats.get('total_audit_events', 0)}")
        print(f"   Login fallidos (24h): {stats.get('failed_logins_24h', 0)}")
        
        print(f"\nConfiguración:")
        config = stats.get('system_config', {})
        print(f"   Política de contraseña: {'✅' if config.get('password_policy_enabled') else '❌'}")
        print(f"   2FA para admin: {'✅' if config.get('two_factor_required_admin') else '❌'}")
        print(f"   Verificación email: {'✅' if config.get('email_verification_required') else '❌'}")
    
    elif args.action == 'audit':
        logs = user_system.get_audit_log(limit=20)
        
        print(f"\n📋 LOG DE AUDITORÍA (últimos 20 eventos):")
        print("=" * 100)
        for log in logs:
            timestamp = log['timestamp'][:19].replace('T', ' ')
            username = log['username'] or 'N/A'
            action = log['action']
            resource = log['resource'] or ''
            status = "✅" if log['success'] else "❌"
            
            print(f"{timestamp} | {username:12s} | {action:20s} | {resource:10s} | {status}")

if __name__ == "__main__":
    main()