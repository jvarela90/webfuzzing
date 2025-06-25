
# ==========================================
# fix_environment.ps1 - Arreglar entorno virtual corrupto
# ==========================================

Write-Host "🔧 Arreglando entorno virtual corrupto..." -ForegroundColor Yellow
Write-Host "=" * 50

# Desactivar entorno virtual actual si está activo
if ($env:VIRTUAL_ENV) {
    Write-Host "Desactivando entorno virtual actual..." -ForegroundColor Cyan
    deactivate
}

# Eliminar entorno virtual corrupto
if (Test-Path "venv") {
    Write-Host "Eliminando entorno virtual corrupto..." -ForegroundColor Red
    Remove-Item -Recurse -Force venv
}

# Crear nuevo entorno virtual
Write-Host "Creando nuevo entorno virtual..." -ForegroundColor Green
python -m venv venv

# Activar entorno virtual
Write-Host "Activando entorno virtual..." -ForegroundColor Green
& .\venv\Scripts\Activate.ps1

# Actualizar pip
Write-Host "Actualizando pip..." -ForegroundColor Cyan
python -m pip install --upgrade pip

# Instalar dependencias esenciales
Write-Host "Instalando dependencias esenciales..." -ForegroundColor Cyan
python -m pip install flask requests aiohttp pyyaml sqlalchemy
python -m pip install flask-cors flask-socketio flask-restful beautifulsoup4
python -m pip install pandas plotly jinja2 cryptography

Write-Host "✅ Entorno virtual arreglado correctamente!" -ForegroundColor Green