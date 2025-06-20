# scrapers/seia_simple.py - Versión simplificada del scraper SEIA
import requests
import re
from typing import Dict, Optional

def obtener_informacion_proyecto_seia_simple(nombre_empresa: str) -> Dict:
    """
    Versión simplificada que obtiene información básica del SEIA
    sin dependencias complejas
    """
    try:
        # Importar BeautifulSoup solo cuando se necesite
        try:
            from bs4 import BeautifulSoup
        except ImportError:
            return {
                'success': False,
                'error': 'BeautifulSoup no disponible'
            }
        
        # URL de búsqueda del SEIA
        url_busqueda = "https://seia.sea.gob.cl/busqueda/buscarProyectoAction.php"
        
        # Payload para la búsqueda
        payload = {
            "nombre_empresa_o_titular": nombre_empresa,
            "submit_buscar": "Buscar"
        }
        
        # Headers básicos
        headers = {
            'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36'
        }
        
        # Realizar búsqueda
        response = requests.post(url_busqueda, data=payload, headers=headers, timeout=30)
        response.raise_for_status()
        
        # Parsear HTML
        soup = BeautifulSoup(response.content, 'html.parser')
        
        # Buscar tabla de resultados
        table = soup.find('table', class_='tabla_datos')
        if not table:
            return {
                'success': False,
                'error': f'No se encontraron proyectos para la empresa: {nombre_empresa}'
            }
        
        # Obtener primer proyecto
        tbody = table.find('tbody')
        if not tbody:
            return {
                'success': False,
                'error': 'No se encontraron resultados'
            }
        
        rows = tbody.find_all('tr')
        if not rows:
            return {
                'success': False,
                'error': 'No se encontraron proyectos'
            }
        
        # Extraer información del primer proyecto
        first_row = rows[0]
        cols = first_row.find_all('td')
        
        if len(cols) < 6:
            return {
                'success': False,
                'error': 'Formato de datos inesperado'
            }
        
        # Extraer datos básicos
        proyecto_info = {
            'nombre': cols[0].get_text(strip=True),
            'region': cols[1].get_text(strip=True),
            'tipo': cols[2].get_text(strip=True),
            'fecha_presentacion': cols[3].get_text(strip=True),
            'estado': cols[4].get_text(strip=True),
            'codigo_expediente': cols[5].get_text(strip=True)
        }
        
        # Buscar link del expediente
        link_elem = cols[0].find('a', href=True)
        if link_elem:
            proyecto_info['link_expediente'] = f"https://seia.sea.gob.cl{link_elem['href']}"
        
        # Información básica del titular (empresa)
        titular_info = {
            'nombre': nombre_empresa,
            'nombre_fantasia': nombre_empresa
        }
        
        return {
            'success': True,
            'data': {
                **proyecto_info,
                'titular': titular_info,
                'ubicacion': {
                    'region': proyecto_info['region']
                }
            }
        }
        
    except requests.exceptions.RequestException as e:
        return {
            'success': False,
            'error': f'Error de conexión al SEIA: {str(e)}'
        }
    except Exception as e:
        return {
            'success': False,
            'error': f'Error al procesar información del SEIA: {str(e)}'
        } 