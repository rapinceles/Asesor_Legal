# run_scraper.py - VERSIÓN FINAL PARA CREAR TABLAS
from config.database import SessionLocal
from scrapers.seia_scraper import sincronizar_proyectos_por_empresa
# Importamos la función para inicializar la DB
from config.database import init_db
# Importamos el scraper de SNIFA (aunque aún no tenga lógica, para que no dé error)
from scrapers.snifa_scraper import sincronizar_sanciones_por_empresa

def poblar_datos_iniciales():
    """
    Función principal para ejecutar los scrapers y llenar la base de datos.
    """
    print("Iniciando proceso de poblado de la base de datos...")
    
    db = SessionLocal()
    
    empresas_a_monitorear = [
        "ACCIONA",
        "ENEL",
        "COLBUN",
        "CODELCO"
    ]

    try:
        for empresa in empresas_a_monitorear:
            print(f"\n--- Procesando empresa: {empresa} ---")
            sincronizar_proyectos_por_empresa(db, empresa)
            sincronizar_sanciones_por_empresa(db, empresa)
    finally:
        db.close()
    
    print("\nProceso de poblado de datos iniciales finalizado.")

# --- BLOQUE PRINCIPAL MODIFICADO ---
if __name__ == "__main__":
    # 1. Primero, se llama a init_db() para crear las tablas
    print("Inicializando la base de datos (creando tablas si no existen)...")
    init_db()
    
    # 2. Luego, se inicia el proceso de scraping
    print("Tablas creadas/verificadas. Iniciando poblado de datos...")
    poblar_datos_iniciales()
