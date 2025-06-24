#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Sistema de Excepciones Customizadas
Manejo centralizado de errores y excepciones del sistema
"""

from typing import Optional, Dict, Any
import traceback
import logging


class SecurityFuzzingException(Exception):
    """Excepción base del sistema de fuzzing"""
    
    def __init__(self, message: str, error_code: Optional[str] = None, 
                 details: Optional[Dict[str, Any]] = None):
        self.message = message
        self.error_code = error_code or self.__class__.__name__
        self.details = details or {}
        super().__init__(self.message)
    
    def to_dict(self) -> Dict[str, Any]:
        """Convertir excepción a diccionario para logging/API"""
        return {
            'error_type': self.__class__.__name__,
            'error_code': self.error_code,
            'message': self.message,
            'details': self.details,
            'traceback': traceback.format_exc()
        }


# =============================================================================
# EXCEPCIONES DE CONFIGURACIÓN
# =============================================================================

class ConfigurationError(SecurityFuzzingException):
    """Error de configuración del sistema"""
    pass


class InvalidConfigurationError(ConfigurationError):
    """Configuración inválida"""
    pass


class MissingConfigurationError(ConfigurationError):
    """Configuración faltante"""
    pass


# =============================================================================
# EXCEPCIONES DE BASE DE DATOS
# =============================================================================

class DatabaseError(SecurityFuzzingException):
    """Error de base de datos"""
    pass


class DatabaseConnectionError(DatabaseError):
    """Error de conexión a base de datos"""
    pass


class DatabaseMigrationError(DatabaseError):
    """Error en migración de base de datos"""
    pass


class DatabaseIntegrityError(DatabaseError):
    """Error de integridad en base de datos"""
    pass


# =============================================================================
# EXCEPCIONES DE FUZZING
# =============================================================================

class FuzzingError(SecurityFuzzingException):
    """Error en proceso de fuzzing"""
    pass


class InvalidTargetError(FuzzingError):
    """Target de fuzzing inválido"""
    pass


class NetworkTimeoutError(FuzzingError):
    """Timeout de red durante fuzzing"""
    pass


class InvalidWordlistError(FuzzingError):
    """Wordlist inválida o corrupta"""
    pass


class TooManyRequestsError(FuzzingError):
    """Demasiadas requests - rate limiting"""
    pass


# =============================================================================
# EXCEPCIONES DE HERRAMIENTAS EXTERNAS
# =============================================================================

class ExternalToolError(SecurityFuzzingException):
    """Error con herramientas externas"""
    pass


class ToolNotFoundError(ExternalToolError):
    """Herramienta externa no encontrada"""
    pass


class ToolExecutionError(ExternalToolError):
    """Error ejecutando herramienta externa"""
    pass


class ToolTimeoutError(ExternalToolError):
    """Timeout ejecutando herramienta externa"""
    pass


class InvalidToolOutputError(ExternalToolError):
    """Output de herramienta externa inválido"""
    pass


# =============================================================================
# EXCEPCIONES DE AUTENTICACIÓN Y AUTORIZACIÓN
# =============================================================================

class AuthenticationError(SecurityFuzzingException):
    """Error de autenticación"""
    pass


class InvalidCredentialsError(AuthenticationError):
    """Credenciales inválidas"""
    pass


class AccountLockedError(AuthenticationError):
    """Cuenta bloqueada"""
    pass


class SessionExpiredError(AuthenticationError):
    """Sesión expirada"""
    pass


class AuthorizationError(SecurityFuzzingException):
    """Error de autorización"""
    pass


class InsufficientPermissionsError(AuthorizationError):
    """Permisos insuficientes"""
    pass


# =============================================================================
# EXCEPCIONES DE API
# =============================================================================

class APIError(SecurityFuzzingException):
    """Error de API"""
    
    def __init__(self, message: str, status_code: int = 500, 
                 error_code: Optional[str] = None, 
                 details: Optional[Dict[str, Any]] = None):
        super().__init__(message, error_code, details)
        self.status_code = status_code


class ValidationError(APIError):
    """Error de validación en API"""
    
    def __init__(self, message: str, field: Optional[str] = None, 
                 details: Optional[Dict[str, Any]] = None):
        super().__init__(message, 400, "VALIDATION_ERROR", details)
        self.field = field


class RateLimitExceededError(APIError):
    """Rate limit excedido"""
    
    def __init__(self, message: str = "Rate limit exceeded", 
                 retry_after: Optional[int] = None):
        super().__init__(message, 429, "RATE_LIMIT_EXCEEDED", 
                        {"retry_after": retry_after})


class ResourceNotFoundError(APIError):
    """Recurso no encontrado"""
    
    def __init__(self, resource_type: str, resource_id: Any):
        message = f"{resource_type} with ID {resource_id} not found"
        super().__init__(message, 404, "RESOURCE_NOT_FOUND", 
                        {"resource_type": resource_type, "resource_id": resource_id})


# =============================================================================
# EXCEPCIONES DE ALERTAS Y NOTIFICACIONES
# =============================================================================

class AlertError(SecurityFuzzingException):
    """Error en sistema de alertas"""
    pass


class NotificationError(SecurityFuzzingException):
    """Error en sistema de notificaciones"""
    pass


class TelegramNotificationError(NotificationError):
    """Error en notificación de Telegram"""
    pass


class EmailNotificationError(NotificationError):
    """Error en notificación de email"""
    pass


# =============================================================================
# EXCEPCIONES DE AUTOMATIZACIÓN
# =============================================================================

class AutomationError(SecurityFuzzingException):
    """Error en sistema de automatización"""
    pass


class SchedulingError(AutomationError):
    """Error en programación de tareas"""
    pass


class TaskExecutionError(AutomationError):
    """Error en ejecución de tarea"""
    pass


class ResourceExhaustionError(AutomationError):
    """Recursos del sistema agotados"""
    pass


# =============================================================================
# EXCEPCIONES DE REPORTES
# =============================================================================

class ReportError(SecurityFuzzingException):
    """Error en generación de reportes"""
    pass


class InvalidReportFormatError(ReportError):
    """Formato de reporte inválido"""
    pass


class ReportGenerationError(ReportError):
    """Error generando reporte"""
    pass


# =============================================================================
# MANEJADOR GLOBAL DE EXCEPCIONES
# =============================================================================

class ExceptionHandler:
    """Manejador centralizado de excepciones"""
    
    def __init__(self):
        self.logger = logging.getLogger(__name__)
    
    def handle_exception(self, exc: Exception, context: Optional[str] = None) -> Dict[str, Any]:
        """Manejar excepción de forma centralizada"""
        
        if isinstance(exc, SecurityFuzzingException):
            # Excepción conocida del sistema
            self._log_known_exception(exc, context)
            return exc.to_dict()
        else:
            # Excepción desconocida
            self._log_unknown_exception(exc, context)
            return self._unknown_exception_to_dict(exc)
    
    def _log_known_exception(self, exc: SecurityFuzzingException, context: Optional[str]):
        """Loggear excepción conocida"""
        log_level = self._get_log_level_for_exception(exc)
        
        message = f"[{exc.error_code}] {exc.message}"
        if context:
            message = f"{context}: {message}"
        
        self.logger.log(log_level, message, extra={
            'error_code': exc.error_code,
            'error_type': exc.__class__.__name__,
            'details': exc.details
        })
    
    def _log_unknown_exception(self, exc: Exception, context: Optional[str]):
        """Loggear excepción desconocida"""
        message = f"Unexpected exception: {str(exc)}"
        if context:
            message = f"{context}: {message}"
        
        self.logger.error(message, exc_info=True)
    
    def _get_log_level_for_exception(self, exc: SecurityFuzzingException) -> int:
        """Obtener nivel de log apropiado para la excepción"""
        
        # Excepciones críticas
        if isinstance(exc, (DatabaseConnectionError, ConfigurationError, 
                          ResourceExhaustionError)):
            return logging.CRITICAL
        
        # Excepciones de error
        elif isinstance(exc, (DatabaseError, FuzzingError, ExternalToolError,
                            AutomationError, ReportError)):
            return logging.ERROR
        
        # Excepciones de warning
        elif isinstance(exc, (AuthenticationError, AuthorizationError, 
                            ValidationError, NotificationError)):
            return logging.WARNING
        
        # Por defecto, info
        else:
            return logging.INFO
    
    def _unknown_exception_to_dict(self, exc: Exception) -> Dict[str, Any]:
        """Convertir excepción desconocida a diccionario"""
        return {
            'error_type': 'UnknownException',
            'error_code': exc.__class__.__name__,
            'message': str(exc),
            'details': {},
            'traceback': traceback.format_exc()
        }


# Instancia global del manejador de excepciones
exception_handler = ExceptionHandler()


# =============================================================================
# DECORADORES PARA MANEJO DE EXCEPCIONES
# =============================================================================

def handle_exceptions(context: Optional[str] = None):
    """Decorador para manejo automático de excepciones"""
    
    def decorator(func):
        def wrapper(*args, **kwargs):
            try:
                return func(*args, **kwargs)
            except Exception as e:
                error_info = exception_handler.handle_exception(e, context)
                
                # Re-raise la excepción para que el llamador pueda manejarla
                raise e
        
        return wrapper
    return decorator


def api_exception_handler(func):
    """Decorador específico para APIs que retorna respuesta JSON"""
    
    def wrapper(*args, **kwargs):
        try:
            return func(*args, **kwargs)
        except APIError as e:
            return {'error': e.to_dict()}, e.status_code
        except SecurityFuzzingException as e:
            return {'error': e.to_dict()}, 500
        except Exception as e:
            error_info = exception_handler.handle_exception(e, f"API: {func.__name__}")
            return {'error': error_info}, 500
    
    return wrapper


# =============================================================================
# UTILIDADES
# =============================================================================

def raise_if_none(value: Any, exception: SecurityFuzzingException):
    """Lanzar excepción si el valor es None"""
    if value is None:
        raise exception


def validate_not_empty(value: str, field_name: str):
    """Validar que un campo no esté vacío"""
    if not value or not value.strip():
        raise ValidationError(f"Field '{field_name}' cannot be empty", field=field_name)


def validate_positive_int(value: int, field_name: str):
    """Validar que un valor sea un entero positivo"""
    if not isinstance(value, int) or value <= 0:
        raise ValidationError(f"Field '{field_name}' must be a positive integer", 
                            field=field_name)


def validate_url(url: str, field_name: str = "url"):
    """Validar que una URL sea válida"""
    import re
    
    url_pattern = re.compile(
        r'^https?://'  # http:// or https://
        r'(?:(?:[A-Z0-9](?:[A-Z0-9-]{0,61}[A-Z0-9])?\.)+[A-Z]{2,6}\.?|'  # domain...
        r'localhost|'  # localhost...
        r'\d{1,3}\.\d{1,3}\.\d{1,3}\.\d{1,3})'  # ...or ip
        r'(?::\d+)?'  # optional port
        r'(?:/?|[/?]\S+)$', re.IGNORECASE)
    
    if not url_pattern.match(url):
        raise ValidationError(f"Invalid URL format: {url}", field=field_name)