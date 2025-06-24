# 🤖 Sistema de Automatización y Orquestación Inteligente v2.0

Sistema completo de fuzzing automatizado con inteligencia artificial, orquestación avanzada y dashboard web en tiempo real.

## 📋 Tabla de Contenidos

- [Características Principales](#-características-principales)
- [Arquitectura del Sistema](#-arquitectura-del-sistema)
- [Instalación y Configuración](#-instalación-y-configuración)
- [Uso del Sistema](#-uso-del-sistema)
- [Configuración Avanzada](#-configuración-avanzada)
- [API y Integración](#-api-y-integración)
- [Monitoreo y Métricas](#-monitoreo-y-métricas)
- [Solución de Problemas](#-solución-de-problemas)
- [Contribución](#-contribución)

## 🚀 Características Principales

### 🔍 Motor de Fuzzing Consolidado
- **Fuzzing multiplataforma** compatible con Windows, Linux y macOS
- **Detección inteligente de vulnerabilidades** con análisis crítico automático
- **Generación adaptativa de wordlists** con aprendizaje automático
- **Integración con herramientas externas** (ffuf, dirsearch, gobuster)
- **Cache inteligente** para optimización de rendimiento

### 🎭 Orquestación Inteligente
- **Programación adaptativa** con ML que aprende patrones óptimos
- **Auto-escalado dinámico** basado en carga del sistema
- **Gestión de dependencias** entre tareas
- **Recuperación automática** ante fallos
- **Monitoreo continuo de salud del sistema**

### 📊 Dashboard Web Avanzado
- **Interfaz moderna** con glassmorphism y efectos visuales
- **Tiempo real** con WebSocket para actualizaciones live
- **Gráficos interactivos** con Plotly
- **Búsqueda inteligente** con autocompletado
- **Gestión completa de alertas** con workflow de analistas

### 🤖 Sistema de Alertas con IA
- **Clasificación automática** de severidad con ML
- **Correlación de eventos** para detectar campañas de ataque
- **Reducción de falsos positivos** con análisis contextual
- **Priorización inteligente** basada en riesgo

### 📈 Automatización Completa
- **Programación de tareas** con patrones cron avanzados
- **Workers especializados** para diferentes tipos de tareas
- **Integración con herramientas** de seguridad externas
- **Generación automática de reportes** en múltiples formatos

## 🏗️ Arquitectura del Sistema

```
├── main.py                    # Script principal del sistema
├── automation_config.yaml    # Configuración principal
│
├── automation/              # Sistema de automatización
│   ├── __init__.py          # Inicialización del módulo
│   ├── scheduler.py         # Programador de tareas
│   ├── orchestrator.py      # Orquestador inteligente
│   └── workers.py           # Workers especializados
│
├── fuzzing_engine.py        # Motor de fuzzing consolidado
├── app.py                   # Dashboard web consolidado
│
├── data/                    # Datos del sistema
│   ├── dominios.csv         # Dominios a escanear
│   ├── diccionario.txt      # Diccionario de rutas
│   ├── descubiertos.txt     # Rutas descubiertas
│   └── fuzzing.db           # Base de datos principal
│
├── logs/                    # Logs del sistema
├── reports/                 # Reportes generados
├── backups/                 # Backups automáticos
└── templates/               # Plantillas de reportes
```

## 🛠️ Instalación y Configuración

### Requisitos del Sistema

- **Python 3.8+**
- **Sistema operativo**: Windows 10+, Linux, macOS
- **RAM**: Mínimo 4GB, recomendado 8GB+
- **Disco**: Mínimo 2GB de espacio libre
- **Red**: Acceso a Internet para actualizaciones

### Instalación

1. **Clonar o descargar el sistema**:
```bash
# Si está en un repositorio
git clone <repository-url>
cd sistema-fuzzing

# O simplemente tener todos los archivos en un directorio
```

2. **Instalar dependencias**:
```bash
pip install -r requirements.txt

# O instalar manualmente:
pip install requests flask flask-socketio plotly pandas pyyaml psutil pathlib
```

3. **Configurar entorno inicial**:
```bash
python main.py --setup
```

### Configuración Básica

1. **Editar dominios a escanear**:
```bash
# Editar data/dominios.csv
nano data/dominios.csv
```

Ejemplo de contenido:
```csv
# Solo agregar dominios propios o con autorización
https://miempresa.com
https://app.miempresa.com
api.miempresa.com:8080
```

2. **Configurar notificaciones** (opcional):
```bash
# Variables de entorno para Telegram
export TELEGRAM_BOT_TOKEN="tu_bot_token"
export TELEGRAM_CHAT_ID_SECURITY="tu_chat_id"
```

3. **Validar configuración**:
```bash
python main.py --config
```

## 🖥️ Uso del Sistema

### Comandos Principales

```bash
# Configurar entorno inicial
python main.py --setup

# Verificar configuración
python main.py --config

# Iniciar sistema completo (interactivo)
python main.py --start

# Ejecutar como daemon (segundo plano)
python main.py --daemon

# Ver estado del sistema
python main.py --status

# Ejecutar tarea específica
python main.py --task full_scan
python main.py --task quick_scan
python main.py --task vulnerability_scan
```

### Dashboard Web

Una vez iniciado el sistema, el dashboard estará disponible en:
- **URL**: http://localhost:5000
- **Características**:
  - Vista en tiempo real de hallazgos
  - Gestión de alertas con workflow
  - Gráficos interactivos
  - Búsqueda avanzada
  - Métricas del sistema

### Tipos de Escaneo

| Tipo | Duración | Descripción | Uso |
|------|----------|-------------|-----|
| `quick_scan` | 5-15 min | Escaneo rápido con wordlist básica | Verificaciones frecuentes |
| `full_scan` | 1-2 horas | Escaneo completo con todas las rutas | Auditorías programadas |
| `vulnerability_scan` | 2-3 horas | Escaneo dirigido a vulnerabilidades | Evaluaciones de seguridad |
| `subdomain_discovery` | 30-60 min | Descubrimiento de subdominios | Reconocimiento |

### Programación Automática

El sistema ejecuta automáticamente:

- **Escaneos rápidos**: Cada 30 minutos
- **Escaneos completos**: 8 AM, 1 PM, 6 PM, 11 PM
- **Escaneos de vulnerabilidades**: Domingos 2 AM
- **Reportes diarios**: 9 AM
- **Limpieza del sistema**: 1 AM diario
- **Backups**: Domingos medianoche

## ⚙️ Configuración Avanzada

### Archivo de Configuración Principal

El archivo `automation_config.yaml` controla todos los aspectos del sistema:

```yaml
# Configuración del orquestador
orchestrator:
  max_concurrent_tasks: 8
  auto_scaling: true
  resource_limits:
    cpu_threshold: 0.8
    memory_threshold: 0.85

# Programación de tareas
scheduler:
  schedules:
    full_scan:
      pattern: "0 8,13,18,23 * * *"
      enabled: true
      priority: "high"
```

### Workers Especializados

- **FuzzingWorker**: Ejecuta escaneos de fuzzing
- **AlertWorker**: Procesa y analiza alertas
- **ReportWorker**: Genera reportes automáticos

### Aprendizaje Automático

```yaml
adaptive_learning:
  enabled: true
  learning_period_days: 7
  optimization_targets:
    - "response_time"
    - "resource_usage" 
    - "success_rate"
```

### Integración con Herramientas Externas

```yaml
integrations:
  fuzzing_tools:
    ffuf:
      enabled: true
      binary_path: "/usr/local/bin/ffuf"
    dirsearch:
      enabled: true
      binary_path: "/opt/dirsearch/dirsearch.py"
```

## 📡 API y Integración

### API REST del Dashboard

```bash
# Estadísticas en tiempo real
GET /api/real-time-stats

# Timeline de hallazgos
GET /api/timeline/30

# Análisis por dominio
GET /api/domain-analysis

# Búsqueda avanzada
GET /api/search?q=admin&critical=true
```

### Integración con CI/CD

```yaml
# Ejemplo para GitHub Actions
- name: Security Scan
  run: |
    python main.py --task quick_scan
    python main.py --status
```

### Webhooks

```yaml
notifications:
  webhook:
    enabled: true
    url: "https://hooks.slack.com/services/..."
    notification_levels: ["critical"]
```

## 📊 Monitoreo y Métricas

### Métricas del Sistema

- **CPU, Memoria, Disco**: Uso en tiempo real
- **Tareas**: Ejecutadas, fallidas, en cola
- **Rendimiento**: Tiempo de respuesta, throughput
- **Salud**: Score general del sistema

### Alertas Automáticas

- **Recursos críticos**: >90% uso de memoria/disco
- **Fallos de tareas**: >10% tasa de fallo
- **Hallazgos críticos**: Detección automática
- **Anomalías**: Comportamiento inusual

### Reportes Automáticos

- **Resumen diario**: Estadísticas del día
- **Reporte semanal**: Tendencias y análisis
- **Resumen ejecutivo**: Reporte mensual de alto nivel
- **Alertas críticas**: Notificación inmediata

## 🔧 Solución de Problemas

### Problemas Comunes

**Error: "Fuzzing engine no disponible"**
```bash
# Verificar configuración
python main.py --config

# Reinstalar dependencias
pip install --upgrade -r requirements.txt
```

**Error: "Base de datos bloqueada"**
```bash
# Reiniciar sistema
python main.py --setup
```

**Dashboard no accesible**
```bash
# Verificar puerto 5000
netstat -an | grep 5000

# Usar puerto alternativo
export FLASK_PORT=8080
```

### Logs y Debugging

```bash
# Ver logs en tiempo real
tail -f logs/automation_system_*.log

# Aumentar nivel de logging
export LOG_LEVEL=DEBUG
python main.py --start
```

### Restaurar desde Backup

```bash
# Los backups se crean automáticamente en backups/
cp backups/orchestrator_backup_*.db data/orchestrator.db
```

## 🧪 Desarrollo y Testing

### Modo de Desarrollo

```bash
# Modo debug con logs verbosos
python main.py --start --log-level DEBUG

# Modo dry-run (sin ejecutar acciones reales)
python main.py --task full_scan --dry-run
```

### Testing

```bash
# Ejecutar pruebas del motor de fuzzing
python fuzzing_engine.py --test

# Ejecutar pruebas del dashboard
python app.py --test

# Verificar todos los componentes
python main.py --status
```

## 🔒 Consideraciones de Seguridad

### ⚠️ IMPORTANTE: Uso Ético

- **Solo escanee dominios propios** o con autorización explícita
- **El fuzzing no autorizado puede ser ilegal** en muchas jurisdicciones
- **Respete los términos de servicio** de los sitios web
- **Use con responsabilidad** en entornos de producción

### Configuración Segura

```yaml
security:
  access_control:
    enabled: true
    require_authentication: true
  encryption:
    encrypt_sensitive_data: true
  audit_logging:
    enabled: true
```

### Variables de Entorno Sensibles

```bash
# Nunca hardcodear tokens en archivos
export TELEGRAM_BOT_TOKEN="..."
export API_KEYS="..."
export DATABASE_PASSWORD="..."
```

## 📈 Roadmap y Futuras Mejoras

### Versión 2.1 (Próxima)
- [ ] Interfaz web mejorada con React
- [ ] Integración con más herramientas de seguridad
- [ ] API GraphQL
- [ ] Clusters distribuidos

### Versión 2.2 (Futura)
- [ ] Machine Learning avanzado
- [ ] Integración con SIEM
- [ ] Análisis de tráfico en tiempo real
- [ ] Mobile app para notificaciones

## 🤝 Contribución

### Cómo Contribuir

1. **Fork** del proyecto
2. **Crear** rama para nueva característica
3. **Implementar** mejoras con tests
4. **Enviar** pull request

### Estructura de Commits

```
feat: nueva característica de fuzzing
fix: corregir error en dashboard
docs: actualizar documentación
test: agregar tests para workers
```

### Guías de Desarrollo

- **Código**: Seguir PEP 8 para Python
- **Tests**: Cobertura mínima 80%
- **Documentación**: Actualizar README y docstrings
- **Seguridad**: Revisar vulnerabilidades antes de merge

## 📄 Licencia y Soporte

### Licencia
Este proyecto está bajo licencia MIT. Ver `LICENSE` para más detalles.

### Soporte
- **Issues**: Reportar bugs en GitHub Issues
- **Documentación**: Wiki del proyecto
- **Comunidad**: Discord/Slack para discusiones

### Contacto
- **Email**: security-team@company.com
- **Documentación**: https://docs.security-automation.com
- **Status**: https://status.security-automation.com

---

## 🎯 Ejemplo de Uso Rápido

```bash
# 1. Configurar entorno
python main.py --setup

# 2. Editar dominios (SOLO PROPIOS)
nano data/dominios.csv

# 3. Iniciar sistema
python main.py --start

# 4. Abrir dashboard
# http://localhost:5000

# 5. Ejecutar escaneo manual
python main.py --task quick_scan

# 6. Ver resultados
python main.py --status
```

**¡El sistema estará ejecutándose y escaneando automáticamente según la programación configurada!**

---

*Sistema desarrollado para profesionales de ciberseguridad. Usar responsablemente.* 🛡️