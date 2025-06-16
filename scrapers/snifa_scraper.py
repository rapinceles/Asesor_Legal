# scrapers/snifa_scraper.py - VERSIÓN FINAL Y FUNCIONAL
import requests
from bs4 import BeautifulSoup
from sqlalchemy.orm import Session
from models.models import SancionSNIFA
from urllib.parse import urljoin
import time

# URL a la que se envían los datos del formulario
SNIFA_SEARCH_URL = "https://snifa.sma.gob.cl/RegistroPublico/Resultado"
# URL base para construir enlaces completos a los expedientes
SNIFA_BASE_URL = "https://snifa.sma.gob.cl"

def sincronizar_sanciones_por_empresa(db: Session, nombre_empresa: str):
    """
    Busca expedientes de sanción en SNIFA y los guarda en la base de datos.
    """
    # Construimos el payload con los nombres de campo correctos que descubrimos
    payload = {
        'txtPalabraClave': nombre_empresa,
        'sltCategoria': '',
        'txtNumero': ''
    }
    headers = {"User-Agent": "Mozilla/5.0"}

    print(f"Buscando sanciones para '{nombre_empresa}' en SNIFA...")
    
    try:
        response = requests.post(SNIFA_SEARCH_URL, data=payload, headers=headers, timeout=20)
        response.raise_for_status()
        soup = BeautifulSoup(response.text, 'html.parser')

        # Buscamos la tabla de resultados. Basado en la web, no tiene un id o clase fácil,
        # así que buscaremos la primera tabla dentro del div de resultados principal.
        results_div = soup.find('div', id='resultados')
        if not results_div:
            print(f"No se encontró el contenedor de resultados para '{nombre_empresa}'.")
            return
        
        table = results_div.find('table')
        if not table:
            print(f"No se encontró la tabla de resultados para '{nombre_empresa}'.")
            return

        rows = table.find_all('tr')[1:] # Saltar la fila de encabezado
        print(f"Se encontraron {len(rows)} expedientes en la búsqueda de SNIFA.")

        for row in rows:
            columns = row.find_all('td')
            if len(columns) < 7: # Debe tener al menos 7 columnas
                continue

            expediente_num = columns[0].get_text(strip=True)
            if not expediente_num:
                continue
            
            sancion_existente = db.query(SancionSNIFA).filter_by(expediente=expediente_num).first()
            if sancion_existente:
                continue

            link_expediente_raw = columns[6].find('a', href=True) # El enlace está en la última columna
            link_expediente = urljoin(SNIFA_BASE_URL, link_expediente_raw['href']) if link_expediente_raw else None

            nueva_sancion = SancionSNIFA(
                expediente=expediente_num,
                unidad_fiscalizable=columns[1].get_text(strip=True),
                nombre_infractor=columns[2].get_text(strip=True),
                categoria=columns[3].get_text(strip=True),
                region=columns[4].get_text(strip=True),
                estado='Pagado' if 'pagado.png' in str(columns[5]) else 'Pendiente', # Lógica para determinar el estado
                link_expediente=link_expediente
            )
            
            print(f"  -> Nueva sanción encontrada: Expediente {expediente_num}. Preparando para agregar.")
            db.add(nueva_sancion)
            
        db.commit()
        time.sleep(2)

    except requests.exceptions.RequestException as e:
        print(f"Error de solicitud HTTP en el scraper de SNIFA: {e}")
        db.rollback()
    except Exception as e:
        print(f"Error general en el scraper de SNIFA: {e}")
        db.rollback()
