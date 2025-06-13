# run_scraper.py
# Este script se usa para ejecutar manualmente nuestros scrapers y poblar la base de datos.

from config.database import SessionLocal
from scrapers.seia_scraper import sincronizar_proyectos_por_empresa
from config.database import init_db

def poblar_datos_iniciales():
    """
    Función principal para ejecutar los scrapers y llenar la base de datos.
    """
    print("Iniciando proceso de poblado de la base de datos...")
    
    # Obtener una sesión de la base de datos
    db = SessionLocal()

    # Lista de empresas que quieres monitorear
    empresas_a_monitorear = [
        "ACCIONA",
        "ENEL",
        "COLBUN",
        "CODELCO"
        # ... añade aquí todas las empresas que te interesen
    ]

    try:
        for empresa in empresas_a_monitorear:
            print(f"\n--- Procesando empresa: {empresa} ---")
            sincronizar_proyectos_por_empresa(db, empresa)
    finally:
        db.close() # Asegurarse de cerrar la sesión al final

    print("\nProceso de poblado de datos iniciales finalizado.")

if __name__ == "__main__":
    # Opcional: Si quieres crear las tablas desde cero, ejecuta esto primero.
    # print("Inicializando la base de datos (creando tablas si no existen)...")
    # init_db()
    
    poblar_datos_iniciales()
