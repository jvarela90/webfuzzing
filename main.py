# main.py - Punto de entrada principal
import argparse
import sys
import os
from pathlib import Path

# Agregar el directorio raíz al path
sys.path.append(str(Path(__file__).parent))

from config.settings import Config
from core.fuzzing_engine import FuzzingEngine
from web.app import create_app
from api.routes import create_api
from utils.logger import setup_logger
from scripts.scheduler import TaskScheduler

def main():
    """Punto de entrada principal del sistema"""
    parser = argparse.ArgumentParser(description='Sistema de Web Fuzzing Profesional')
    parser.add_argument('--mode', choices=['scan', 'web', 'api', 'all'], 
                       default='all', help='Modo de ejecución')
    parser.add_argument('--config', help='Archivo de configuración personalizado')
    parser.add_argument('--domains', help='Archivo CSV con dominios')
    parser.add_argument('--output', help='Directorio de salida')
    
    args = parser.parse_args()
    
    # Configurar logger
    logger = setup_logger()
    
    try:
        # Cargar configuración
        config = Config(args.config) if args.config else Config()
        
        # Ejecutar modo seleccionado
        if args.mode == 'scan':
            logger.info("Iniciando modo de escaneo")
            engine = FuzzingEngine(config)
            engine.run_scan(args.domains, args.output)
            
        elif args.mode == 'web':
            logger.info("Iniciando dashboard web")
            app = create_app(config)
            app.run(host='0.0.0.0', port=5000, debug=True)
            
        elif args.mode == 'api':
            logger.info("Iniciando API REST")
            api = create_api(config)
            api.run(host='0.0.0.0', port=8000)
            
        elif args.mode == 'all':
            logger.info("Iniciando sistema completo")
            scheduler = TaskScheduler(config)
            scheduler.start_all_services()
            
    except Exception as e:
        logger.error(f"Error fatal: {e}")
        sys.exit(1)

if __name__ == "__main__":
    main()