# Activar entorno virtual
.\venv\Scripts\Activate.ps1

# Instalar dependencias faltantes
pip install loguru colorama tqdm
pip install flask-restful flask-socketio
pip install beautifulsoup4 selenium

# Verificar instalación
python -c "import loguru; print('✅ loguru instalado')"