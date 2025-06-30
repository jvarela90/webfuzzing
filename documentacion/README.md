# README.md
# 🔍 WebFuzzing Pro 2.0

**Sistema profesional de fuzzing web con alertas inteligentes y automatización completa**

[![Python Version](https://img.shields.io/badge/python-3.8+-blue.svg)](https://python.org)
[![License](https://img.shields.io/badge/license-MIT-green.svg)](LICENSE)
[![Platform](https://img.shields.io/badge/platform-Windows%20%7C%20Linux%20%7C%20macOS-lightgrey.svg)]()

WebFuzzing Pro es una plataforma avanzada de descubrimiento y análisis de rutas web que combina fuzzing inteligente, automatización completa y un sistema de alertas en tiempo real para profesionales de ciberseguridad.

## ✨ Características Principales

### 🎯 Fuzzing Inteligente
- **Diccionarios Dinámicos**: Gestión automática de wordlists con aprendizaje adaptativo
- **Generación por Fuerza Bruta**: Combinaciones alfabéticas hasta 12 caracteres con patrones inteligentes
- **Integración Multi-herramienta**: Compatible con ffuf y dirsearch para máxima cobertura
- **Descobrimiento de Subdominios**: Escaneo automático con Certificate Transparency y DNS

### 🚨 Sistema de Alertas Avanzado
- **Detección de Rutas Críticas**: Identificación automática de .git, admin, config.php, backups
- **Notificaciones Multi-canal**: Telegram y email con personalización de horarios
- **Dashboard en Tiempo Real**: Actualizaciones WebSocket con estado de conexión
- **Gestión de Incidentes**: Estados (nueva, investigando, resuelta) con notas del analista

### 🤖 Automatización Completa
- **Programación Avanzada**: Escaneos en horarios específicos (08:00, 13:00, 18:00, 23:00)
- **Escaneos Profundos**: Análisis semanal extendido con mayor cobertura
- **Mantenimiento Automático**: Limpieza de datos, backups y optimización
- **Reportes Programados**: Sin novedades a las 09:00 y 14:00

### 📊 Dashboard Interactivo
- **Visualización en Tiempo Real**: Gráficos de actividad y estadísticas actualizadas
- **Filtros Avanzados**: Por dominio, criticidad, fecha y estado
- **Exportación Múltiple**: CSV, JSON y reportes personalizados
- **Gestión de Dominios**: CRUD completo con estadísticas por objetivo

### 🔌 API REST Completa
- **Endpoints Completos**: Estadísticas, dominios, hallazgos, alertas, escaneos
- **Autenticación Segura**: API Keys configurables con rate limiting
- **Documentación Automática**: Endpoints auto-documentados
- **Integración Fácil**: Compatible con herramientas CI/CD y SIEM

## 🚀 Instalación Rápida

### Prerrequisitos
- **Python 3.8+** instalado y configurado
- **Git** para clonado del repositorio
- **Windows 11** / Linux / macOS

### Instalación en Windows 11 + VS Code

```cmd
# 1. Clonar repositorio
git clone https://github.com/jvarela90/webfuzzing.git
cd urlcontrol

# 2. Crear entorno virtual
python -m venv venv
venv\Scripts\activate

# 3. Ejecutar instalador automático
python scripts/install.py

# 4. Configurar entorno
python scripts/setup_environment.py

# 5. Probar sistema
python scripts/test_system.py
```

### Inicio Rápido

```cmd
# Ejecutar sistema completo
python main.py --mode all

# Solo dashboard web
python main.py --mode web

# Solo escaneo manual
python main.py --mode scan
```

**Acceso:**
- 🌐 **Dashboard**: http://localhost:5000
- 🔗 **API**: http://localhost:8000/api/v1/health

## 📁 Estructura del Proyecto

```
urlcontrol/
├── 📁 config/              # Configuración del sistema
│   ├── settings.py         # Configuración centralizada
│   └── database.py         # Gestión de SQLite
├── 📁 core/                # Motor principal
│   ├── fuzzing_engine.py   # Motor de fuzzing
│   ├── dictionary_manager.py # Gestión inteligente de diccionarios
│   └── subdomain_scanner.py # Descubrimiento de subdominios
├── 📁 web/                 # Dashboard web
│   ├── app.py              # Aplicación Flask
│   ├── templates/          # Templates HTML
│   └── static/             # CSS/JS/assets
├── 📁 api/                 # API REST
│   └── routes.py           # Endpoints de la API
├── 📁 integrations/        # Integraciones externas
│   ├── ffuf_integration.py # Integración con ffuf
│   ├── dirsearch_integration.py # Integración con dirsearch
│   └── telegram_bot.py     # Bot de Telegram
├── 📁 utils/               # Utilidades del sistema
│   ├── logger.py           # Sistema de logging
│   ├── notifications.py    # Gestión de notificaciones
│   └── file_manager.py     # Gestión de archivos
├── 📁 scripts/             # Scripts de administración
│   ├── install.py          # Instalador automático
│   ├── setup_environment.py # Configuración del entorno
│   ├── scheduler.py        # Programador de tareas
│   └── test_system.py      # Suite de pruebas
├── 📁 data/                # Datos del sistema
│   ├── dominios.csv        # Lista de dominios objetivo
│   ├── diccionarios/       # Wordlists para fuzzing
│   └── resultados/         # Resultados de escaneos
└── main.py                 # Punto de entrada principal
```

## ⚙️ Configuración

### Archivo Principal (config.json)

```json
{
  "fuzzing": {
    "max_workers": 10,
    "timeout": 5,
    "critical_paths": [".git", "admin", "config.php", "backup"],
    "max_path_length": 12
  },
  "notifications": {
    "telegram": {
      "enabled": true,
      "bot_token": "TU_BOT_TOKEN",
      "chat_id": "TU_CHAT_ID"
    },
    "email": {
      "enabled": true,
      "smtp_server": "smtp.gmail.com",
      "username": "tu-email@gmail.com",
      "recipients": ["admin@empresa.com"]
    }
  },
  "schedules": {
    "general_scan": "0 8,13,18,23 * * *",
    "deep_scan": "0 2 * * 0"
  }
}
```

### Configuración de Dominios (data/dominios.csv)

```csv
# Formato: dominio[:puerto]
miempresa.com
app.miempresa.com:8080
api.miempresa.com:443
intranet.miempresa.com
```

## 🎯 Casos de Uso

### Para Equipos de Seguridad
- **Auditorías Continuas**: Monitoreo 24/7 de superficie de ataque
- **Compliance**: Cumplimiento de normativas con reportes automáticos
- **Gestión de Vulnerabilidades**: Priorización basada en criticidad
- **Inteligencia de Amenazas**: Descubrimiento proactivo de exposiciones

### Para DevSecOps
- **Integración CI/CD**: API REST para pipelines automatizados
- **Shift-Left Security**: Detección temprana en desarrollo
- **Monitoreo de Producción**: Alertas ante cambios no autorizados
- **Métricas de Seguridad**: KPIs y tendencias históricas

### Para Consultores
- **Evaluaciones de Seguridad**: Herramienta completa para pentesting
- **Reportes Profesionales**: Documentación automática con exportación
- **Multi-cliente**: Gestión de múltiples organizaciones
- **Evidencia Forense**: Trazabilidad completa de descubrimientos

## 📈 Métricas y Reportes

### Dashboard Principal
- **Estadísticas en Tiempo Real**: Dominios, hallazgos, alertas críticas
- **Gráficos Interactivos**: Actividad por hora, tendencias semanales
- **Estado del Sistema**: Conexión, escaneos activos, próximas tareas

### Tipos de Reportes
1. **Ejecutivo**: Resumen de alto nivel con métricas clave
2. **Técnico**: Detalles completos con URLs y códigos de respuesta
3. **Comparativo**: Análisis temporal de cambios
4. **Por Dominio**: Enfoque específico en objetivos individuales

### Exportación
- **CSV**: Compatible con Excel y Google Sheets
- **JSON**: Para integración con herramientas de análisis
- **Reportes HTML**: Documentación profesional con gráficos

## 🔧 Integración con Herramientas

### Fuzzing Externo
- **ffuf**: Integración nativa para fuzzing de alta velocidad
- **dirsearch**: Análisis complementario con detección de tecnologías
- **Configuración Automática**: Setup sin intervención manual

### Notificaciones
- **Telegram**: Bot personalizado con comandos interactivos
- **Email/SMTP**: Compatible con Gmail, Outlook, servidores corporativos
- **Webhooks**: Integración con Slack, Discord, Microsoft Teams

### APIs Externas
- **Certificate Transparency**: Descubrimiento de subdominios automático
- **Shodan/Censys**: Enriquecimiento de datos (futuro)
- **SIEM Integration**: Conectores para Splunk, ELK, QRadar (roadmap)

## 🛡️ Seguridad y Buenas Prácticas

### Configuración Segura
- **Claves Secretas**: Generación automática de API keys y secrets
- **Encriptación**: Datos sensibles protegidos en base de datos
- **Auditoría**: Logs completos de todas las operaciones
- **Rate Limiting**: Protección contra abuso de API

### Consideraciones Éticas
⚠️ **IMPORTANTE**: Este sistema debe usarse únicamente en:
- Dominios de tu propiedad
- Sistemas con autorización explícita por escrito
- Entornos de testing autorizados
- Cumplimiento con leyes locales e internacionales

### Límites Responsables
- **Throttling Configurable**: Control de velocidad para evitar DoS
- **Timeouts Inteligentes**: Prevención de bloqueos de recursos
- **Logging Ético**: Sin almacenamiento de datos sensibles
- **Respeto a robots.txt**: Configuración opcional de cumplimiento

## 🔄 Roadmap y Desarrollo Futuro

### v2.1 (Q2 2024)
- [ ] **Machine Learning**: Detección de patrones con IA
- [ ] **Dashboard Móvil**: Aplicación responsive para dispositivos móviles
- [ ] **Plugin System**: Arquitectura extensible para módulos personalizados

### v2.2 (Q3 2024)
- [ ] **Integración Shodan**: Enriquecimiento automático de datos
- [ ] **Análisis de Contenido**: Detección de tecnologías y frameworks
- [ ] **Multi-tenancy**: Soporte para múltiples organizaciones

### v2.3 (Q4 2024)
- [ ] **Docker Support**: Containerización completa
- [ ] **Kubernetes**: Orquestación y escalabilidad
- [ ] **Cloud Deployment**: Templates para AWS, Azure, GCP

## 🤝 Contribución

### Cómo Contribuir
1. **Fork** del repositorio
2. **Crear branch** para nueva funcionalidad (`git checkout -b feature/nueva-funcionalidad`)
3. **Desarrollar** con tests incluidos
4. **Commit** con mensajes descriptivos (`git commit -m 'Agregar nueva funcionalidad'`)
5. **Push** al branch (`git push origin feature/nueva-funcionalidad`)
6. **Crear Pull Request** con descripción detallada

### Tipos de Contribuciones Bienvenidas
- 🐛 **Bug fixes** y correcciones
- ✨ **Nuevas funcionalidades** y mejoras
- 📚 **Documentación** y tutoriales
- 🧪 **Tests** y casos de prueba
- 🌐 **Traducciones** a otros idiomas
- 🎨 **Mejoras de UI/UX**

### Desarrollo Local
```bash
# Setup para desarrollo
git clone https://github.com/jvarela90/urlcontrol.git
cd urlcontrol
python -m venv venv
source venv/bin/activate  # Linux/Mac
# venv\Scripts\activate   # Windows
pip install -r requirements-dev.txt
python scripts/test_system.py
```

## 📞 Soporte y Comunidad

### Obtener Ayuda
- 📖 **Documentación**: [Wiki del proyecto](https://github.com/jvarela90/urlcontrol/wiki)
- 💬 **Discusiones**: [GitHub Discussions](https://github.com/jvarela90/urlcontrol/discussions)
- 🐛 **Issues**: [Reportar problemas](https://github.com/jvarela90/urlcontrol/issues)
- 📧 **Email**: Para consultas privadas o de seguridad

### Información del Sistema para Soporte
```bash
# Generar reporte de diagnóstico
python scripts/test_system.py > diagnostico.txt
python --version >> diagnostico.txt
pip list >> diagnostico.txt
```

## 📄 Licencia

Este proyecto está licenciado bajo la **MIT License** - ver el archivo [LICENSE](LICENSE) para detalles completos.

### Resumen de la Licencia
- ✅ **Uso comercial** permitido
- ✅ **Modificación** permitida
- ✅ **Distribución** permitida
- ✅ **Uso privado** permitido
- ❌ **Sin garantía** ni responsabilidad
- ℹ️ **Incluir licencia** en redistribuciones

## 🙏 Agradecimientos

- **Comunidad de Ciberseguridad** por feedback y testing
- **Desarrolladores de ffuf** ([@joohoi](https://github.com/joohoi)) por la herramienta base
- **Proyecto dirsearch** ([@maurosoria](https://github.com/maurosoria)) por la integración
- **SecLists** ([@danielmiessler](https://github.com/danielmiessler)) por los diccionarios
- **Todos los contribuidores** que hacen posible este proyecto

## 📊 Estadísticas del Proyecto

![GitHub stars](https://img.shields.io/github/stars/jvarela90/urlcontrol?style=social)
![GitHub forks](https://img.shields.io/github/forks/jvarela90/urlcontrol?style=social)
![GitHub issues](https://img.shields.io/github/issues/jvarela90/urlcontrol)
![GitHub pull requests](https://img.shields.io/github/issues-pr/jvarela90/urlcontrol)
![GitHub last commit](https://img.shields.io/github/last-commit/jvarela90/urlcontrol)

---

<div align="center">

**WebFuzzing Pro 2.0** - *Descubrimiento inteligente para seguridad web profesional*

[🌟 Dar Star](https://github.com/jvarela90/urlcontrol) • [🐛 Reportar Bug](https://github.com/jvarela90/urlcontrol/issues) • [💡 Solicitar Feature](https://github.com/jvarela90/urlcontrol/issues) • [📖 Documentación](https://github.com/jvarela90/urlcontrol/wiki)

</div>