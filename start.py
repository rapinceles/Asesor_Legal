#!/usr/bin/env python3
"""
Script de inicio para MERLIN - Asesor Legal Ambiental
Este script configura el entorno y ejecuta la aplicación
"""

import os
import sys
import subprocess
from pathlib import Path

def check_python_version():
    """Verifica que la versión de Python sea compatible"""
    if sys.version_info < (3, 8):
        print("❌ Error: Se requiere Python 3.8 o superior")
        print(f"   Versión actual: {sys.version}")
        sys.exit(1)
    else:
        print(f"✅ Python {sys.version.split()[0]} - Compatible")

def check_requirements():
    """Verifica que las dependencias estén instaladas"""
    try:
        import fastapi
        import sqlalchemy
        import requests
        import beautifulsoup4
        print("✅ Dependencias principales instaladas")
        return True
    except ImportError as e:
        print(f"❌ Faltan dependencias: {e}")
        print("   Ejecuta: pip install -r requirements.txt")
        return False

def check_database_config():
    """Verifica la configuración de la base de datos"""
    try:
        from config.database import DATABASE_URL, engine
        print("✅ Configuración de base de datos cargada")
        return True
    except Exception as e:
        print(f"❌ Error en configuración de base de datos: {e}")
        return False

def create_tables():
    """Crea las tablas en la base de datos si no existen"""
    try:
        from config.database import engine
        from models.models import Base
        Base.metadata.create_all(bind=engine)
        print("✅ Tablas de base de datos verificadas/creadas")
        return True
    except Exception as e:
        print(f"❌ Error creando tablas: {e}")
        return False

def check_openai_key():
    """Verifica si la API key de OpenAI está configurada"""
    openai_key = os.getenv('OPENAI_API_KEY')
    if not openai_key:
        print("⚠️  Advertencia: OPENAI_API_KEY no configurada")
        print("   El análisis con IA no funcionará sin esta clave")
        return False
    else:
        print("✅ API Key de OpenAI configurada")
        return True

def main():
    """Función principal del script"""
    print("🚀 Iniciando MERLIN - Asesor Legal Ambiental")
    print("=" * 50)
    
    # Verificaciones del sistema
    check_python_version()
    
    if not check_requirements():
        sys.exit(1)
    
    if not check_database_config():
        print("   Verifica tu configuración en config/database.py")
        sys.exit(1)
    
    if not create_tables():
        sys.exit(1)
    
    check_openai_key()
    
    print("\n" + "=" * 50)
    print("✅ Sistema verificado correctamente")
    print("🌐 Iniciando servidor web...")
    print("📍 URL: http://localhost:8000")
    print("⏹️  Para detener: Ctrl+C")
    print("=" * 50)
    
    # Ejecutar la aplicación
    try:
        subprocess.run([
            "uvicorn", 
            "main:app", 
            "--reload", 
            "--host", "0.0.0.0", 
            "--port", "8000"
        ])
    except KeyboardInterrupt:
        print("\n👋 MERLIN detenido correctamente")
    except Exception as e:
        print(f"❌ Error ejecutando la aplicación: {e}")
        sys.exit(1)

if __name__ == "__main__":
    main() 