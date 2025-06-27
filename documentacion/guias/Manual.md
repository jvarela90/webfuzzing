# WebFuzzing Pro 2.0

Sistema profesional de fuzzing web con alertas inteligentes, automatización completa y dashboard interactivo para análisis de seguridad web.

## 🚀 Características Principales

- **Fuzzing Inteligente**: Escaneo de rutas con diccionarios dinámicos y generación por fuerza bruta
- **Integración Multi-herramienta**: Compatible con ffuf y dirsearch para máxima cobertura
- **Dashboard Web Interactivo**: Interfaz moderna con actualizaciones en tiempo real
- **Sistema de Alertas**: Notificaciones automáticas vía Telegram y email
- **API REST Completa**: Integración con otros sistemas y automatización
- **Programación Automática**: Escaneos programados con horarios personalizables
- **Base de Datos Histórica**: Seguimiento de cambios y análisis temporal
- **Exportación Avanzada**: Reportes en múltiples formatos

## 📋 Requisitos del Sistema

### Mínimos
- **Python**: 3.8 o superior
- **Sistema Operativo**: Windows 11, Linux, macOS
- **RAM**: 4 GB mínimo (8 GB recomendado)
- **Espacio en Disco**: 2 GB libres

### Recomendados para Producción
- **CPU**: 4 núcleos o más
- **RAM**: 8 GB o más
- **Red**: Conexión estable a Internet
- **Almacenamiento**: SSD para mejor rendimiento

## 🛠️ Instalación

### Instalación Automática

```bash
# 1. Clonar el repositorio
git clone https://github.com/jvarela90/urlcontrol.git
cd urlcontrol

# 2. Ejecutar instalador
python scripts/install.py

# 3. Configurar entorno
python scripts/setup_environment.py
```

### Instalación Manual

```bash
# 1. Instalar dependencias
pip install -r requirements.txt

# 2. Instalar herramientas externas
# ffuf (Linux)
sudo apt install ffuf
# ffuf (Windows) - Descargar desde GitHub releases

# dirsearch
pip install dirsearch

# 3. Crear directorios
mkdir -p data/{diccionarios,resultados} logs backups

# 4. Configurar archivos
cp config.json.example config.json
# Editar config.json según necesidades
```

## ⚙️ Configuración

### Archivo de Configuración Principal

Editar `config.json`:

```json
{
  "system": {
    "name": "WebFuzzing Pro",
    "version": "2.0.0",
    "log_level": "INFO"
  },
  "fuzzing": {
    "max_workers": 10,
    "timeout": 5,
    "delay_between_requests": 0.1,
    "critical_paths": [".git", "admin", "config.php", "backup"]
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
      "password": "tu-app-password",
      "recipients": ["admin@empresa.com"]
    }
  }
}
```

### Configuración de Dominios

Editar `data/dominios.csv`:

```csv
# Formato: dominio[:puerto]
miempresa.com:443
app.miempresa.com
intranet.miempresa.com:8080
https://api.miempresa.com
test.miempresa.com:80
```

### Configuración de Telegram

1. Crear bot con @BotFather en Telegram
2. Obtener token del bot
3. Obtener chat_id con @userinfobot
4. Configurar en `config.json`

### Configuración de Email

Para Gmail:
1. Activar verificación en 2 pasos
2. Generar "App Password"
3. Configurar en `config.json`

## 🚀 Uso del Sistema

### Modos de Ejecución

```bash
# Ejecutar sistema completo (recomendado)
python main.py --mode all

# Solo escaneo
python main.py --mode scan

# Solo dashboard web
python main.py --mode web

# Solo API REST
python main.py --mode api
```

### Scripts de Inicio Rápido

**Windows:**
```cmd
start_webfuzzing.bat
```

**Linux/Mac:**
```bash
./start_webfuzzing.sh
```

### Acceso a Interfaces

- **Dashboard Web**: http://localhost:5000
- **API REST**: http://localhost:8000
- **Documentación API**: http://localhost:8000/api/v1/health

## 📊 Dashboard Web

### Funcionalidades Principales

1. **Vista General**
   - Estadísticas en tiempo real
   - Gráficos de actividad
   - Alertas críticas pendientes

2. **Hallazgos**
   - Lista de rutas descubiertas
   - Filtros por dominio, criticidad, fecha
   - Exportación a CSV

3. **Alertas**
   - Sistema de gestión de incidentes
   - Estados: Nueva, Investigando, Resuelta
   - Comentarios del analista

4. **Dominios**
   - Gestión de objetivos
   - Estadísticas por dominio
   - Histórico de escaneos

### Actualizaciones en Tiempo Real

El dashboard utiliza WebSockets para mostrar:
- Nuevos hallazgos inmediatamente
- Alertas críticas en tiempo real
- Estado de conexión del sistema
- Progreso de escaneos activos

## 🔌 API REST

### Autenticación

Todas las llamadas requieren header `X-API-Key`:

```bash
curl -H "X-API-Key: tu-api-key" http://localhost:8000/api/v1/stats
```

### Endpoints Principales

#### Estadísticas
```bash
GET /api/v1/stats
```

#### Dominios
```bash
GET /api/v1/domains
POST /api/v1/domains
```

#### Hallazgos
```bash
GET /api/v1/findings?hours=24&critical=true
```

#### Alertas
```bash
GET /api/v1/alerts
POST /api/v1/alerts
PUT /api/v1/alerts/{id}
```

#### Escaneo Manual
```bash
POST /api/v1/scan
```

#### Exportación
```bash
GET /api/v1/export/findings?format=csv
```

### Ejemplos de Uso API

```python
import requests

headers = {'X-API-Key': 'tu-api-key'}

# Obtener estadísticas
response = requests.get('http://localhost:8000/api/v1/stats', headers=headers)
stats = response.json()

# Agregar dominio
data = {'domain': 'nuevo.ejemplo.com', 'port': 443}
response = requests.post('http://localhost:8000/api/v1/domains', 
                        json=data, headers=headers)

# Iniciar escaneo manual
response = requests.post('http://localhost:8000/api/v1/scan', 
                        headers=headers)
```

## 📅 Programación Automática

### Horarios Predefinidos

- **08:00, 13:00, 18:00, 23:00**: Escaneos generales
- **02:00 Domingos**: Escaneo profundo semanal
- **09:00, 14:00**: Reportes de estado
- **Cada hora**: Verificación de alertas críticas
- **03:00**: Limpieza de datos antiguos
- **04:00**: Backup de base de datos

### Configuración Personalizada

Modificar en `config.json`:

```json
{
  "schedules": {
    "general_scan": "0 8,13,18,23 * * *",
    "deep_scan": "0 2 * * 0",
    "report_times": ["09:00", "14:00"],
    "working_hours": {
      "start": "08:00",
      "end": "16:00"
    }
  }
}
```

## 🎯 Tipos de Escaneo

### Escaneo General
- Diccionarios base + rutas descubiertas
- Fuzzing con patrones comunes
- Verificación de rutas críticas
- Duración: 15-30 minutos

### Escaneo Profundo
- Generación extendida por fuerza bruta
- Combinaciones hasta 15 caracteres
- Subdominios adicionales
- Duración: 2-4 horas

### Escaneo Dirigido
- Objetivos específicos
- Diccionarios personalizados
- Análisis detallado de respuestas
- Duración: variable

## 🚨 Sistema de Alertas

### Tipos de Alertas

1. **Críticas (Alta Prioridad)**
   - Rutas con información sensible (.git, config.php)
   - Paneles de administración expuestos
   - Backups accesibles

2. **Advertencias (Media Prioridad)**
   - Rutas de desarrollo/test en producción
   - Información de versiones
   - Archivos de log accesibles

3. **Informativas (Baja Prioridad)**
   - Nuevos recursos descubiertos
   - Cambios en estructura de sitios
   - Estadísticas de escaneo

### Gestión de Alertas

**Estados:**
- **Nueva**: Requiere atención inmediata
- **Investigando**: En proceso de análisis
- **Resuelta**: Verificada y corregida

**Acciones:**
- Agregar comentarios del analista
- Cambiar estado y prioridad
- Asignar responsable
- Crear tareas de seguimiento

## 📈 Métricas y Reportes

### Métricas Principales

- **Cobertura**: Dominios y subdominios escaneados
- **Efectividad**: Ratio de rutas encontradas vs probadas
- **Criticidad**: Distribución de hallazgos por nivel de riesgo
- **Tendencias**: Evolución temporal de descubrimientos

### Tipos de Reportes

1. **Ejecutivo**: Resumen de alto nivel
2. **Técnico**: Detalles de implementación
3. **Comparativo**: Análisis temporal
4. **Por Dominio**: Enfoque específico

### Exportación

- **CSV**: Para análisis en Excel/sheets
- **JSON**: Para integración con otras herramientas
- **PDF**: Para documentación formal

## 🔧 Integración con Herramientas

### ffuf
- Fuzzing de alta velocidad
- Configuración automática
- Procesamiento de resultados JSON

### dirsearch
- Análisis complementario
- Diccionarios integrados
- Detección de tecnologías

### Herramientas Personalizadas
- API extensible
- Plugins personalizados
- Scripts de post-procesamiento

## 🛡️ Seguridad y Buenas Prácticas

### Configuración Segura

1. **Cambiar claves por defecto**
   ```bash
   python scripts/setup_environment.py
   ```

2. **Configurar firewall**
   - Permitir solo IPs autorizadas
   - Usar HTTPS en producción

3. **Logs de auditoría**
   - Revisar logs regularmente
   - Monitorear accesos API

### Consideraciones Éticas

- **Solo escanear dominios propios**
- **Respetar robots.txt cuando aplique**
- **No sobrecargar servidores objetivo**
- **Documentar todos los escaneos**

### Límites de Velocidad

```json
{
  "fuzzing": {
    "max_workers": 5,
    "delay_between_requests": 0.5,
    "timeout": 10
  }
}
```

## 🐛 Troubleshooting

### Problemas Comunes

#### Error: "No se pueden cargar dominios"
```bash
# Verificar formato del archivo
cat data/dominios.csv
# Debe tener formato: dominio:puerto
```

#### Error: "ffuf no encontrado"
```bash
# Linux
sudo apt install ffuf
# Windows
# Descargar desde GitHub y agregar al PATH
```

#### Error: "Timeout en requests"
```bash
# Aumentar timeout en config.json
"timeout": 15
```

#### Error: "Base de datos bloqueada"
```bash
# Reiniciar sistema
python main.py --mode all
```

### Logs de Debug

```bash
# Activar debug en config.json
"log_level": "DEBUG"

# Ver logs
tail -f logs/webfuzzing_20241225.log
```

### Verificar Instalación

```bash
# Verificar componentes
python -c "import requests, flask, schedule; print('OK')"

# Verificar herramientas externas
ffuf -h
dirsearch -h
```

## 🔄 Mantenimiento

### Tareas Regulares

1. **Semanal**
   - Revisar logs de errores
   - Actualizar diccionarios
   - Verificar espacio en disco

2. **Mensual**
   - Backup completo del sistema
   - Revisar configuración de alertas
   - Actualizar dependencias

3. **Trimestral**
   - Auditoría de seguridad
   - Optimización de base de datos
   - Revisión de métricas

### Comandos de Mantenimiento

```bash
# Limpiar logs antiguos
find logs/ -name "*.log" -mtime +30 -delete

# Backup manual
cp webfuzzing.db backups/backup_$(date +%Y%m%d).db

# Verificar salud del sistema
python -c "from config.database import DatabaseManager; print('DB OK')"
```

## 📞 Soporte y Contribución

### Reportar Problemas

1. **Crear issue en GitHub** con:
   - Descripción detallada del problema
   - Logs relevantes
   - Configuración (sin claves sensibles)
   - Pasos para reproducer

2. **Información del sistema**:
   ```bash
   python --version
   pip list | grep -E "(flask|requests|schedule)"
   ```

### Contribuir al Proyecto

1. Fork del repositorio
2. Crear branch para nueva funcionalidad
3. Desarrollar con tests
4. Crear pull request

### Roadmap

- [ ] Integración con Shodan/Censys
- [ ] Dashboard móvil responsive
- [ ] Machine Learning para detección de patrones
- [ ] Integración con SIEM
- [ ] Plugin system extensible
- [ ] Análisis de contenido avanzado

## 📄 Licencia

MIT License - Ver archivo LICENSE para detalles completos.

## 🙏 Agradecimientos

- Comunidad de seguridad informática
- Desarrolladores de ffuf y dirsearch
- Contribuidores del proyecto

---

**WebFuzzing Pro 2.0** - Sistema profesional para análisis de seguridad web automatizado.

Para más información, visita: https://github.com/jvarela90/urlcontrol