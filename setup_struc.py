#!/usr/bin/env python3
"""
Script para crear la estructura optimizada del sistema
"""
import os
from pathlib import Path

def create_directory_structure():
    """Crear estructura de directorios optimizada"""
    base_dir = Path("security_fuzzing_system")
    
    directories = [
        # Core system
        "core",
        
        # Modules
        "modules",
        
        # API
        "api",
        "api/routes",
        
        # Web interface
        "web",
        "web/static",
        "web/static/css",
        "web/static/js",
        "web/static/img",
        "web/templates",
        "web/templates/components",
        
        # Automation
        "automation",
        
        # Data directories
        "data",
        "data/config",
        "data/databases",
        "data/wordlists",
        "data/cache",
        
        # Tools
        "tools",
        "tools/ffuf",
        "tools/dirsearch", 
        "tools/nuclei",
        
        # Logs and reports
        "logs",
        "reports",
        "reports/html",
        "reports/json",
        "reports/pdf",
        
        # Development
        "tests",
        "tests/unit",
        "tests/integration",
        "docs",
        "scripts"
    ]
    
    print(f"🏗️  Creando estructura en: {base_dir.absolute()}")
    
    for directory in directories:
        dir_path = base_dir / directory
        dir_path.mkdir(parents=True, exist_ok=True)
        
        # Crear __init__.py para paquetes Python
        if any(python_dir in str(dir_path) for python_dir in ['core', 'modules', 'api', 'web', 'automation']):
            init_file = dir_path / "__init__.py"
            if not init_file.exists():
                init_file.write_text("# -*- coding: utf-8 -*-\n")
        
        print(f"✅ {directory}")
    
    # Crear archivos base
    create_base_files(base_dir)
    
    print(f"\n🎉 Estructura creada exitosamente en: {base_dir.absolute()}")
    return base_dir

def create_base_files(base_dir):
    """Crear archivos base del proyecto"""
    
    # requirements.txt
    requirements = """# Core dependencies
flask>=2.3.0
requests>=2.31.0
sqlite3
pyyaml>=6.0
click>=8.0.0

# Web interface
jinja2>=3.1.0
werkzeug>=2.3.0

# API
flask-restful>=0.3.10
flask-jwt-extended>=4.5.0
flask-cors>=4.0.0
flask-limiter>=3.0.0
marshmallow>=3.19.0

# ML and analytics
scikit-learn>=1.3.0
pandas>=2.0.0
numpy>=1.24.0
plotly>=5.15.0

# Security and crypto
cryptography>=41.0.0
bcrypt>=4.0.0

# Automation and scheduling
schedule>=1.2.0
asyncio

# Notifications
python-telegram-bot>=20.0.0

# Development and testing
pytest>=7.4.0
pytest-cov>=4.1.0
black>=23.0.0
flake8>=6.0.0

# Optional ML dependencies
joblib>=1.3.0
nltk>=3.8.0
"""
    
    (base_dir / "requirements.txt").write_text(requirements)
    
    # .gitignore
    gitignore = """# Python
__pycache__/
*.py[cod]
*$py.class
*.so
.Python
build/
develop-eggs/
dist/
downloads/
eggs/
.eggs/
lib/
lib64/
parts/
sdist/
var/
wheels/
*.egg-info/
.installed.cfg
*.egg

# Virtual environments
venv/
env/
ENV/

# IDE
.vscode/
.idea/
*.swp
*.swo

# System files
.DS_Store
Thumbs.db

# Project specific
data/databases/*.db
data/cache/*
logs/*.log
reports/*
tools/*/
!tools/.gitkeep

# Sensitive configs
config.yaml
data/config/secrets.yaml
*.key
*.pem

# Temporary files
*.tmp
*.temp
temp/
"""
    
    (base_dir / ".gitignore").write_text(gitignore)
    
    # README.md básico
    readme = """# Security Fuzzing System

Sistema profesional de fuzzing web con alertas inteligentes y automatización.

## Instalación Rápida

```bash
python scripts/install.py
```

## Uso

```bash
# Configurar sistema
python scripts/setup_environment.py

# Ejecutar escaneo
python -m core.fuzzing_engine --scan

# Iniciar dashboard
python -m web.app

# Iniciar API
python -m api.app
```

## Documentación

Ver `docs/` para documentación completa.
"""
    
    (base_dir / "README.md").write_text(readme)
    
    print("📄 Archivos base creados")

if __name__ == "__main__":
    create_directory_structure()