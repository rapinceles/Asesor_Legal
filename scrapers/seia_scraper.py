# scrapers/seia_scraper.py - VERSIÓN FINAL Y COMPLETA
import requests
from bs4 import BeautifulSoup
import time
from sqlalchemy.orm import Session
from models.models import Empresa, ProyectoSEIA
from urllib.parse import urljoin
import datetime

# Constantes del Scraper
BUSQUEDA_PROYECTO_URL = "https://seia.sea.gob.cl/busqueda/buscarProyectoAction.php"
BASE_SEIA_URL = "https://seia.sea.gob.cl"

def sincronizar_proyectos_por_empresa(db: Session, nombre_empresa: str):
    """
    Busca TODOS los proyectos de una empresa en el SEIA, navegando por todas las páginas de resultados
    y evitando duplicados tanto en la sesión actual como en la base de datos.
    """
    headers = {"User-Agent": "Mozilla/5.0"}
    payload = {"nombre_empresa_o_titular": nombre_empresa, "submit_buscar": "Buscar"}
    
    codigos_procesados_en_esta_sesion = set()
    
    print(f"Buscando proyectos para '{nombre_empresa}' en SEIA (Página 1)...")
    
    try:
        response = requests.post(BUSQUEDA_PROYECTO_URL, data=payload, headers=headers, timeout=30)
        response.raise_for_status()
    except requests.exceptions.RequestException as e:
        print(f"Error al realizar la búsqueda inicial en SEIA: {e}")
        return

    current_page_soup = BeautifulSoup(response.content, 'html.parser')
    page_count = 1

    while True: 
        print(f"Procesando página {page_count} de resultados...")
        
        table = current_page_soup.find('table', class_='tabla_datos')
        if not table:
            if page_count == 1:
                print(f"No se encontró tabla de resultados para '{nombre_empresa}'.")
            break

        # Lógica corregida para buscar el <tbody> primero
        tbody = table.find('tbody')
        result_rows = tbody.find_all('tr') if tbody else []
        
        if not result_rows and page_count == 1:
            print("No se encontraron filas de proyectos en esta página.")
        
        for row in result_rows:
            columns = row.find_all('td')
            if len(columns) < 6:
                continue

            codigo_expediente = columns[5].get_text(strip=True)
            if not codigo_expediente:
                continue
            
            if codigo_expediente in codigos_procesados_en_esta_sesion:
                continue

            proyecto_existente = db.query(ProyectoSEIA).filter_by(codigo_expediente=codigo_expediente).first()
            if proyecto_existente:
                print(f"  -> Proyecto {codigo_expediente} ya existe en la DB. Saltando.")
                continue

            link_expediente_raw = columns[0].find('a', href=True)
            link_expediente = urljoin(BASE_SEIA_URL, link_expediente_raw['href']) if link_expediente_raw else None

            try:
                fecha_presentacion_obj = datetime.datetime.strptime(columns[3].get_text(strip=True), '%d/%m/%Y').date()
            except (ValueError, IndexError):
                fecha_presentacion_obj = None

            nuevo_proyecto = ProyectoSEIA(
                codigo_expediente=codigo_expediente,
                nombre=columns[0].get_text(strip=True),
                tipo=columns[2].get_text(strip=True),
                region=columns[1].get_text(strip=True),
                tipologia=columns[2].get_text(strip=True),
                estado=columns[4].get_text(strip=True),
                link_expediente=link_expediente,
                fecha_presentacion=fecha_presentacion_obj
            )
            print(f"  -> Nuevo proyecto encontrado: {codigo_expediente}. Preparando para agregar.")
            db.add(nuevo_proyecto)
            
            codigos_procesados_en_esta_sesion.add(codigo_expediente)

        # Búsqueda robusta para el enlace "Siguiente"
        next_page_link = None
        for link in current_page_soup.find_all('a'):
            if link.get_text(strip=True).lower() == 'siguiente >':
                next_page_link = link
                break
        
        if next_page_link and next_page_link.get('href'):
            next_page_url = urljoin(BASE_SEIA_URL, next_page_link['href'])
            print(f"Enlace 'Siguiente' encontrado. Navegando a la página {page_count + 1}")
            page_count += 1
            time.sleep(2) 
            
            try:
                response = requests.get(next_page_url, headers=headers, timeout=30)
                response.raise_for_status()
                current_page_soup = BeautifulSoup(response.content, 'html.parser')
            except requests.exceptions.RequestException as e:
                print(f"Error al navegar a la siguiente página: {e}")
                break
        else:
            print("No se encontraron más páginas. Finalizando paginación.")
            break

    try:
        print("Guardando todos los nuevos proyectos encontrados en la base de datos...")
        db.commit()
        print(f"Sincronización para '{nombre_empresa}' completada.")
    except Exception as e:
        print(f"Error al guardar en la base de datos: {e}")
        db.rollback()
