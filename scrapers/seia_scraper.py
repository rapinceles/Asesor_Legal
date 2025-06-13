# scrapers/seia_scraper.py - VERSIÓN REFACTORIZADA
import requests
from bs4 import BeautifulSoup
import time
from sqlalchemy.orm import Session

# <-- NUEVO: Importamos los modelos ORM que acabamos de crear
from models.seia_models import Empresa, ProyectoSEIA

# <-- Mantenemos las constantes
BUSQUEDA_PROYECTO_URL = "https://seia.sea.gob.cl/busqueda/buscarProyectoAction.php"
BASE_SEIA_URL = "https://seia.sea.gob.cl"

# <-- CAMBIO: La función ahora recibe una sesión de la base de datos como argumento
def sincronizar_proyectos_por_empresa(db: Session, nombre_empresa: str):
    """
    Busca proyectos en el SEIA y los guarda o actualiza en la base de datos.
    Ya no devuelve datos, su efecto es escribir en la DB.
    """
    payload = {"NOMBRE_EMPRESA": nombre_empresa, "submit": "Buscar"}
    headers = {"User-Agent": "Mozilla/5.0"}
    
    print(f"Buscando proyectos para '{nombre_empresa}' para sincronizar con la DB...")

    try:
        response = requests.post(BUSQUEDA_PROYECTO_URL, data=payload, headers=headers, timeout=20)
        response.raise_for_status()
        soup = BeautifulSoup(response.content, 'html.parser')
        
        table = soup.find('table', class_='tabla')
        if not table:
            print(f"No se encontró tabla de resultados para '{nombre_empresa}'.")
            return

        result_rows = table.find_all('tr')[1:] # Saltar encabezado
        print(f"Se encontraron {len(result_rows)} proyectos en la búsqueda.")

        for row in result_rows:
            columns = row.find_all(['td', 'th'])
            if len(columns) < 6:
                continue

            # --- PASO 1: Extraer datos crudos del scraper (lógica que ya tenías) ---
            codigo_expediente = columns[5].get_text(strip=True)
            nombre_proyecto = columns[0].get_text(strip=True)
            link_expediente_raw = columns[0].find('a', href=True)
            link_expediente = (BASE_SEIA_URL + link_expediente_raw['href']) if link_expediente_raw else None

            # <-- CAMBIO: En lugar de devolver un diccionario, ahora interactuamos con la DB -->

            # --- PASO 2: Verificar si el proyecto ya existe en nuestra DB ---
            proyecto_existente = db.query(ProyectoSEIA).filter_by(codigo_expediente=codigo_expediente).first()

            if proyecto_existente:
                # Opcional: Podrías actualizar el estado si ha cambiado, por ahora solo lo saltamos.
                print(f"Proyecto '{codigo_expediente}' ya existe en la DB. Saltando.")
                continue

            # --- PASO 3: Si no existe, crear el objeto y guardarlo ---
            print(f"Nuevo proyecto encontrado: '{codigo_expediente} - {nombre_proyecto}'. Agregando a la DB.")

            # (Opcional) Aquí podrías añadir la lógica para encontrar/crear la empresa titular también.
            # Por ahora, creamos solo el proyecto.
            
            nuevo_proyecto = ProyectoSEIA(
                codigo_expediente=codigo_expediente,
                nombre=nombre_proyecto,
                region=columns[1].get_text(strip=True),
                tipo=columns[2].get_text(strip=True),
                # AÑADIR LÓGICA PARA PARSEAR FECHA SI ES NECESARIO
                # fecha_presentacion=datetime.strptime(columns[3].get_text(strip=True), '%d/%m/%Y').date(),
                estado=columns[4].get_text(strip=True), # Asumiendo que esta es la columna del estado
                link_expediente=link_expediente
            )

            db.add(nuevo_proyecto) # Añade el nuevo proyecto a la sesión

        # --- PASO 4: Confirmar todos los cambios en la base de datos ---
        db.commit() # Guarda todos los proyectos nuevos encontrados en esta ejecución
        print(f"Sincronización para '{nombre_empresa}' completada.")

    except requests.exceptions.RequestException as e:
        print(f"Error de solicitud HTTP en el scraper de SEIA: {e}")
        db.rollback() # Deshace cualquier cambio si hay un error
    except Exception as e:
        print(f"Error general en el scraper de SEIA: {e}")
        db.rollback()

# La función _scrape_expediente_documents no la llamaremos por ahora para simplificar.
# Nuestro primer objetivo es poblar la tabla de proyectos. La dejaremos aquí para usarla en el siguiente paso.
def _scrape_expediente_documents(expediente_url: str) -> list:
    # ... (tu código de esta función se mantiene sin cambios por ahora) ...
    pass
