# scrapers/seia_safe.py - Scraper SEIA ultra-seguro para evitar errores
from typing import Dict, Optional
import logging

# Configurar logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

def obtener_informacion_proyecto_seia_safe(nombre_empresa: str) -> Dict:
    """
    Función ultra-segura para obtener información del SEIA.
    No falla nunca, siempre retorna un diccionario válido.
    """
    try:
        logger.info(f"Consultando SEIA para: {nombre_empresa}")
        
        # Validar entrada
        if not nombre_empresa or not isinstance(nombre_empresa, str):
            return {
                'success': False,
                'error': 'Nombre de empresa no válido',
                'data': None
            }
        
        # Intentar diferentes métodos de scraping
        # Método 1: Scraper real (nuevo)
        try:
            from scrapers.seia_real import obtener_informacion_proyecto_seia_real
            result = obtener_informacion_proyecto_seia_real(nombre_empresa)
            if result and result.get('success'):
                logger.info("✅ Información obtenida con scraper real")
                return result
        except Exception as e:
            logger.warning(f"Scraper real falló: {e}")
        
        # Método 2: Scraper completo
        try:
            from scrapers.seia_project_detail_scraper import obtener_informacion_proyecto_seia
            result = obtener_informacion_proyecto_seia(nombre_empresa)
            if result and result.get('success'):
                logger.info("Información obtenida con scraper completo")
                return result
        except Exception as e:
            logger.warning(f"Scraper completo falló: {e}")
        
        # Método 3: Scraper simple
        try:
            from scrapers.seia_simple import obtener_informacion_proyecto_seia_simple
            result = obtener_informacion_proyecto_seia_simple(nombre_empresa)
            if result and result.get('success'):
                logger.info("Información obtenida con scraper simple")
                return result
        except Exception as e:
            logger.warning(f"Scraper simple falló: {e}")
        
        # Método 4: Búsqueda directa básica
        logger.info("Intentando búsqueda directa básica")
        try:
            import requests
            from bs4 import BeautifulSoup
            
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
            
            # Realizar búsqueda con timeout corto
            response = requests.post(url_busqueda, data=payload, headers=headers, timeout=15)
            response.raise_for_status()
            
            # Parsear HTML
            soup = BeautifulSoup(response.content, 'html.parser')
            
            # Buscar tabla de resultados
            table = soup.find('table', class_='tabla_datos')
            if table:
                tbody = table.find('tbody')
                if tbody:
                    rows = tbody.find_all('tr')
                    if rows:
                        # Extraer información del primer proyecto
                        first_row = rows[0]
                        cols = first_row.find_all('td')
                        
                        if len(cols) >= 6:
                            # Buscar link del expediente
                            link_elem = cols[0].find('a', href=True)
                            link_expediente = f"https://seia.sea.gob.cl{link_elem['href']}" if link_elem else 'https://seia.sea.gob.cl/'
                            
                            proyecto_info = {
                                'nombre': cols[0].get_text(strip=True),
                                'region': cols[1].get_text(strip=True),
                                'tipo': cols[2].get_text(strip=True),
                                'fecha_presentacion': cols[3].get_text(strip=True),
                                'estado': cols[4].get_text(strip=True),
                                'codigo_expediente': cols[5].get_text(strip=True),
                                'link_expediente': link_expediente
                            }
                            
                            # Obtener más información del proyecto si es posible
                            titular_info = {'nombre': nombre_empresa, 'nombre_fantasia': nombre_empresa}
                            ubicacion_info = {'region': proyecto_info['region']}
                            
                            # Intentar obtener más detalles del expediente
                            try:
                                detail_response = requests.get(link_expediente, headers=headers, timeout=10)
                                detail_response.raise_for_status()
                                detail_soup = BeautifulSoup(detail_response.content, 'html.parser')
                                
                                # Buscar información adicional en el detalle
                                for table in detail_soup.find_all('table'):
                                    rows = table.find_all('tr')
                                    for row in rows:
                                        cols = row.find_all(['td', 'th'])
                                        if len(cols) >= 2:
                                            key = cols[0].get_text(strip=True).lower()
                                            value = cols[1].get_text(strip=True)
                                            
                                            # Información del titular
                                            if 'razón social' in key or 'razon social' in key:
                                                titular_info['razon_social'] = value
                                            elif 'rut' in key and 'titular' in key:
                                                titular_info['rut'] = value
                                            elif 'dirección' in key or 'direccion' in key:
                                                if 'titular' in key or 'empresa' in key:
                                                    titular_info['direccion'] = value
                                                elif 'proyecto' in key:
                                                    ubicacion_info['ubicacion_proyecto'] = value
                                            elif 'teléfono' in key or 'telefono' in key:
                                                titular_info['telefono'] = value
                                            elif 'email' in key or 'correo' in key:
                                                titular_info['email'] = value
                                            elif 'comuna' in key:
                                                ubicacion_info['comuna'] = value
                                            elif 'provincia' in key:
                                                ubicacion_info['provincia'] = value
                                            elif 'coordenadas' in key:
                                                ubicacion_info['coordenadas'] = value
                                
                                # Buscar patrones en texto libre
                                text_content = detail_soup.get_text()
                                
                                # Buscar RUT
                                rut_match = re.search(r'RUT[:\s]*(\d{1,2}\.?\d{3}\.?\d{3}[-\.]?[\dkK])', text_content, re.IGNORECASE)
                                if rut_match and 'rut' not in titular_info:
                                    titular_info['rut'] = rut_match.group(1)
                                
                                # Buscar teléfono
                                phone_match = re.search(r'(?:Tel[éefono]*|Teléfono)[:\s]*([+]?[\d\s\-\(\)]{7,15})', text_content, re.IGNORECASE)
                                if phone_match and 'telefono' not in titular_info:
                                    titular_info['telefono'] = phone_match.group(1)
                                
                                # Buscar email
                                email_match = re.search(r'([a-zA-Z0-9._%+-]+@[a-zA-Z0-9.-]+\.[a-zA-Z]{2,})', text_content)
                                if email_match and 'email' not in titular_info:
                                    titular_info['email'] = email_match.group(1)
                                
                            except Exception as e:
                                logger.warning(f"No se pudo obtener detalle del expediente: {e}")
                            
                            logger.info("✅ Información real obtenida del SEIA")
                            return {
                                'success': True,
                                'data': {
                                    **proyecto_info,
                                    'titular': titular_info,
                                    'ubicacion': ubicacion_info
                                },
                                'modo': 'real_seia'
                            }
            
            # Si no se encontraron resultados
            logger.warning("No se encontraron proyectos en SEIA")
            return {
                'success': False,
                'error': f'No se encontraron proyectos para la empresa: {nombre_empresa} en el SEIA',
                'data': None
            }
            
        except Exception as e:
            logger.error(f"Error en búsqueda directa: {e}")
        
        # Método 5: Respuesta de error final
        logger.error("Todos los métodos fallaron")
        return {
            'success': False,
            'error': f'No se pudo obtener información del SEIA para: {nombre_empresa}',
            'data': None
        }
        
    except Exception as e:
        logger.error(f"Error crítico en SEIA safe: {e}")
        return {
            'success': False,
            'error': f'Error interno: {str(e)}',
            'data': None
        }

def test_seia_safe():
    """Función de test para verificar el funcionamiento"""
    empresas_test = [
        "Codelco",
        "Empresa Test",
        "Minera Los Pelambres",
        "",
        None,
        123
    ]
    
    for empresa in empresas_test:
        print(f"\n--- Test para: {empresa} ---")
        result = obtener_informacion_proyecto_seia_safe(empresa)
        print(f"Success: {result.get('success', False)}")
        if result.get('success'):
            print(f"Datos: {result.get('data', {}).get('titular', {}).get('nombre', 'N/A')}")
        else:
            print(f"Error: {result.get('error', 'N/A')}")

if __name__ == "__main__":
    test_seia_safe() 