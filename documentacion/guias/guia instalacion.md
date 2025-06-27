# 🪟 WebFuzzing Pro - Guía para Windows 11 + VS Code

Esta guía te ayudará a configurar WebFuzzing Pro en Windows 11 usando VS Code para desarrollo y pruebas.

## 📋 Requisitos Previos

### Software Necesario

1. **Python 3.8+** 
   - Descargar desde: https://www.python.org/downloads/windows/
   - ✅ Marcar "Add Python to PATH" durante instalación

2. **Git**
   - Descargar desde: https://git-scm.com/download/win
   - Usar configuración por defecto

3. **Visual Studio Code**
   - Descargar desde: https://code.visualstudio.com/
   - Instalar extensiones recomendadas:
     - Python
     - Python Debugger
     - Pylance
     - Git History

### Verificar Instalaciones

Abrir **PowerShell** o **Command Prompt** y ejecutar:

```cmd
python --version
git --version
code --version
```

Todos deben mostrar sus versiones correspondientes.

## 🚀 Instalación Paso a Paso

### 1. Clonar el Repositorio

```cmd
# Crear carpeta para proyectos
mkdir C:\Proyectos
cd C:\Proyectos

# Clonar repositorio
git clone https://github.com/jvarela90/urlcontrol.git
cd urlcontrol
```

### 2. Configurar Entorno Virtual

```cmd
# Crear entorno virtual
python -m venv venv

# Activar entorno virtual
venv\Scripts\activate

# Verificar activación (debe mostrar (venv) al inicio)
```

### 3. Instalar Dependencias

```cmd
# Actualizar pip
python -m pip install --upgrade pip

# Instalar dependencias del proyecto
pip install -r requirements.txt

# Verificar instalación
pip list
```

### 4. Ejecutar Instalador Automático

```cmd
# Ejecutar script de instalación
python scripts/install.py

# Configurar entorno
python scripts/setup_environment.py
```

### 5. Configurar VS Code

```cmd
# Abrir proyecto en VS Code
code .
```

**En VS Code:**

1. **Seleccionar Intérprete de Python**:
   - `Ctrl+Shift+P` → "Python: Select Interpreter"
   - Elegir: `.\venv\Scripts\python.exe`

2. **Configurar Terminal**:
   - `Ctrl+Shift+P` → "Terminal: Select Default Profile"
   - Elegir: "Command Prompt" o "PowerShell"

3. **Instalar Extensiones**:
   - Python Extension Pack
   - SQLite Viewer (para ver base de datos)
   - REST Client (para probar API)

## ⚙️ Configuración Inicial

### 1. Editar Configuración

Abrir `config.json` en VS Code y modificar:

```json
{
  "system": {
    "log_level": "DEBUG"
  },
  "fuzzing": {
    "max_workers": 5,
    "timeout": 10,
    "delay_between_requests": 0.5
  },
  "web": {
    "host": "127.0.0.1",
    "port": 5000,
    "debug": true
  },
  "tools": {
    "ffuf": {
      "enabled": false
    },
    "dirsearch": {
      "enabled": true
    }
  }
}
```

### 2. Configurar Dominios de Prueba

Editar `data/dominios.csv`:

```csv
# Dominios de prueba - SOLO USAR CON DOMINIOS PROPIOS
httpbin.org
example.com
```

⚠️ **IMPORTANTE**: Solo usar con dominios que te pertenezcan o tengas autorización para probar.

### 3. Configurar Notificaciones (Opcional)

**Para Telegram:**
1. Buscar @BotFather en Telegram
2. Crear bot: `/newbot`
3. Copiar token
4. Buscar @userinfobot para obtener chat_id
5. Configurar en `config.json`

## 🧪 Probar el Sistema

### 1. Ejecutar Pruebas del Sistema

```cmd
# En terminal de VS Code (Ctrl+Shift+`)
python scripts/test_system.py
```

### 2. Probar Componentes Individuales

**Base de Datos:**
```cmd
python -c "from config.database import DatabaseManager; from config.settings import Config; db = DatabaseManager(Config()); print('DB OK')"
```

**Motor de Fuzzing:**
```cmd
python -c "from core.fuzzing_engine import FuzzingEngine; from config.settings import Config; engine = FuzzingEngine(Config()); print('Engine OK')"
```

**Aplicación Web:**
```cmd
python main.py --mode web
# Abrir: http://localhost:5000
```

**API REST:**
```cmd
python main.py --mode api
# Probar: http://localhost:8000/api/v1/health
```

## 🐛 Debugging en VS Code

### 1. Configurar Debug

Crear `.vscode/launch.json`:

```json
{
    "version": "0.2.0",
    "configurations": [
        {
            "name": "WebFuzzing - Full System",
            "type": "python",
            "request": "launch",
            "program": "main.py",
            "args": ["--mode", "all"],
            "console": "integratedTerminal",
            "cwd": "${workspaceFolder}"
        },
        {
            "name": "WebFuzzing - Web Only",
            "type": "python",
            "request": "launch",
            "program": "main.py",
            "args": ["--mode", "web"],
            "console": "integratedTerminal",
            "cwd": "${workspaceFolder}"
        },
        {
            "name": "WebFuzzing - Scan Only",
            "type": "python",
            "request": "launch",
            "program": "main.py",
            "args": ["--mode", "scan"],
            "console": "integratedTerminal",
            "cwd": "${workspaceFolder}"
        },
        {
            "name": "Test System",
            "type": "python",
            "request": "launch",
            "program": "scripts/test_system.py",
            "console": "integratedTerminal",
            "cwd": "${workspaceFolder}"
        }
    ]
}
```

### 2. Usar Breakpoints

1. Hacer clic en la línea donde quieres parar
2. `F5` para iniciar debug
3. `F10` para siguiente línea
4. `F11` para entrar en función
5. `F5` para continuar

### 3. Inspeccionar Variables

- **Watch**: Agregar variables a observar
- **Call Stack**: Ver pila de llamadas
- **Variables**: Ver variables locales/globales

## 🔧 Herramientas Adicionales para Windows

### 1. Instalar ffuf (Opcional)

```cmd
# Descargar desde GitHub releases
# https://github.com/ffuf/ffuf/releases
# Descomprimir ffuf.exe en C:\tools\ffuf\
# Agregar C:\tools\ffuf\ al PATH del sistema
```

**Agregar al PATH:**
1. Win + X → System
2. Advanced system settings
3. Environment Variables
4. System Variables → Path → Edit
5. New → `C:\tools\ffuf`

### 2. Configurar Windows Defender

Agregar exclusiones para evitar falsos positivos:

1. **Settings** → **Update & Security** → **Windows Security**
2. **Virus & threat protection** → **Manage settings**
3. **Add or remove exclusions** → **Add an exclusion**
4. **Folder** → Seleccionar carpeta del proyecto

### 3. Configurar Firewall

Si planeas acceder desde otras máquinas:

```cmd
# Ejecutar como Administrador
netsh advfirewall firewall add rule name="WebFuzzing Web" dir=in action=allow protocol=TCP localport=5000
netsh advfirewall firewall add rule name="WebFuzzing API" dir=in action=allow protocol=TCP localport=8000
```

## 🚀 Ejecutar el Sistema

### Modo Desarrollo (Recomendado para Pruebas)

```cmd
# Terminal en VS Code
python main.py --mode web
```

### Modo Producción

```cmd
# Ejecutar todo el sistema
python main.py --mode all

# O usar script batch
start_webfuzzing.bat
```

### Acceso a Interfaces

- **Dashboard**: http://localhost:5000
- **API**: http://localhost:8000/api/v1/health
- **Logs**: Ver en `logs/` o VS Code Output panel

## 📁 Estructura de Desarrollo

```
urlcontrol/
├── .vscode/          # Configuración VS Code
├── config/           # Configuración del sistema
├── core/             # Motor principal
├── web/              # Dashboard web
├── api/              # API REST  
├── utils/            # Utilidades
├── scripts/          # Scripts de administración
├── data/             # Datos y resultados
├── logs/             # Archivos de log
├── venv/             # Entorno virtual
└── main.py           # Punto de entrada
```

## 🔍 Tips para Desarrollo

### 1. Live Reload en VS Code

Instalar extensión **Python Autoreload** para recarga automática.

### 2. Testing

```cmd
# Ejecutar pruebas específicas
python -m pytest tests/ -v

# Con coverage
python -m pytest --cov=. tests/
```

### 3. Linting

```cmd
# Instalar herramientas de código
pip install black flake8 mypy

# Formatear código
black .

# Verificar estilo
flake8 .

# Verificar tipos
mypy .
```

### 4. Git Workflow

```cmd
# Crear branch para nueva feature
git checkout -b feature/nueva-funcionalidad

# Hacer cambios y commit
git add .
git commit -m "Agregar nueva funcionalidad"

# Push y crear PR
git push origin feature/nueva-funcionalidad
```

## 🚨 Troubleshooting

### Problemas Comunes

**Error: "No module named 'flask'"**
```cmd
# Verificar que el entorno virtual está activo
venv\Scripts\activate
pip install flask
```

**Error: "Permission denied"**
```cmd
# Ejecutar PowerShell como Administrador
Set-ExecutionPolicy -ExecutionPolicy RemoteSigned -Scope CurrentUser
```

**Error: Puerto en uso**
```cmd
# Cambiar puerto en config.json o matar proceso
netstat -ano | findstr :5000
taskkill /PID <PID> /F
```

**Error: SQLite locked**
```cmd
# Reiniciar sistema o eliminar archivo .db
del webfuzzing.db
python scripts/test_system.py
```

### Logs de Debug

```cmd
# Ver logs en tiempo real
Get-Content logs/webfuzzing_*.log -Wait -Tail 10

# O en VS Code: Ctrl+Shift+P → "View: Show Output"
```

## 📚 Recursos Adicionales

### Documentación
- [Python en Windows](https://docs.python.org/3/using/windows.html)
- [VS Code Python](https://code.visualstudio.com/docs/python/python-tutorial)
- [Flask Documentation](https://flask.palletsprojects.com/)

### Extensiones VS Code Útiles
- **Python Docstring Generator**: Para documentación
- **GitLens**: Para mejor integración Git
- **Thunder Client**: Cliente REST integrado
- **SQLite**: Para ver base de datos

### Comandos Útiles

```cmd
# Ver procesos Python
tasklist | findstr python

# Ver puertos abiertos
netstat -an | findstr LISTEN

# Limpiar cache Python
python -Bc "import pathlib; [p.unlink() for p in pathlib.Path('.').rglob('*.py[co]')]"

# Reinstalar dependencias
pip freeze > requirements_backup.txt
pip uninstall -r requirements_backup.txt -y
pip install -r requirements.txt
```

## ✅ Checklist de Instalación

- [ ] Python 3.8+ instalado y en PATH
- [ ] Git instalado
- [ ] VS Code con extensiones Python
- [ ] Repositorio clonado
- [ ] Entorno virtual creado y activado
- [ ] Dependencias instaladas
- [ ] Scripts de instalación ejecutados
- [ ] Configuración personalizada
- [ ] Pruebas del sistema ejecutadas ✅
- [ ] Debug configurado en VS Code
- [ ] Sistema funcionando en modo desarrollo

¡Ya tienes WebFuzzing Pro funcionando en tu entorno de desarrollo Windows 11 + VS Code! 🎉

Para preguntas específicas o problemas, revisa la documentación completa o crea un issue en GitHub.