#!/usr/bin/env python3
# start_server.py - Script de inicio robusto para MERLIN

import os
import sys
import uvicorn
from pathlib import Path

def main():
    """
    Función principal para iniciar el servidor MERLIN
    """
    print("🚀 Iniciando MERLIN - Asesor Legal Ambiental")
    print("=" * 50)
    
    # Verificar que estamos en el directorio correcto
    if not Path("main.py").exists():
        print("❌ Error: No se encuentra main.py en el directorio actual")
        print("   Asegúrate de ejecutar este script desde el directorio raíz del proyecto")
        sys.exit(1)
    
    # Configuración del servidor
    host = os.getenv("HOST", "0.0.0.0")
    port = int(os.getenv("PORT", 8000))
    
    print(f"🌐 Host: {host}")
    print(f"🔌 Puerto: {port}")
    print("=" * 50)
    
    try:
        # Importar y verificar la aplicación
        from main import app
        print("✅ Aplicación MERLIN cargada exitosamente")
        
        # Configuración de uvicorn
        config = uvicorn.Config(
            app=app,
            host=host,
            port=port,
            log_level="info",
            access_log=True,
            reload=False  # Deshabilitado para producción
        )
        
        server = uvicorn.Server(config)
        
        print("🎯 Servidor iniciando...")
        print(f"📱 Acceder en: http://{host}:{port}")
        print("=" * 50)
        
        # Iniciar servidor
        server.run()
        
    except ImportError as e:
        print(f"❌ Error al importar la aplicación: {e}")
        print("   Verifica que todas las dependencias estén instaladas:")
        print("   pip install -r requirements.txt")
        sys.exit(1)
        
    except Exception as e:
        print(f"❌ Error al iniciar el servidor: {e}")
        sys.exit(1)

if __name__ == "__main__":
    main() 