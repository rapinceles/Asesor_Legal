# scrapers/seia_real.py - Scraper real para SEIA que obtiene información verdadera
import requests
import re
from typing import Dict, Optional, List
import logging
from urllib.parse import urljoin, quote

logger = logging.getLogger(__name__)

class SEIARealScraper:
    """Scraper real para obtener información del SEIA"""
    
    def __init__(self):
        self.base_url = "https://seia.sea.gob.cl"
        self.session = requests.Session()
        self.session.headers.update({
            'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36',
            'Accept': 'text/html,application/xhtml+xml,application/xml;q=0.9,image/webp,*/*;q=0.8',
            'Accept-Language': 'es-ES,es;q=0.8,en-US;q=0.5,en;q=0.3',
            'Accept-Encoding': 'gzip, deflate, br',
            'Connection': 'keep-alive',
            'Upgrade-Insecure-Requests': '1'
        })
    
    def buscar_proyectos(self, nombre_empresa: str) -> Dict:
        """Busca proyectos en el SEIA por nombre de empresa"""
        try:
            from bs4 import BeautifulSoup
        except ImportError:
            return {
                'success': False,
                'error': 'BeautifulSoup no disponible'
            }
        
        try:
            logger.info(f"Buscando proyectos para: {nombre_empresa}")
            
            # URL de búsqueda del SEIA
            search_url = f"{self.base_url}/busqueda/buscarProyectoAction.php"
            
            # Datos del formulario de búsqueda
            search_data = {
                'nombre_empresa_o_titular': nombre_empresa,
                'submit_buscar': 'Buscar'
            }
            
            # Realizar búsqueda
            response = self.session.post(search_url, data=search_data, timeout=30)
            response.raise_for_status()
            
            logger.info(f"Respuesta recibida: {response.status_code}")
            
            # Parsear HTML
            soup = BeautifulSoup(response.content, 'html.parser')
            
            # Debug: guardar HTML para revisar
            # with open('/tmp/seia_response.html', 'w', encoding='utf-8') as f:
            #     f.write(soup.prettify())
            
            # Buscar diferentes posibles selectores para la tabla
            table = None
            possible_selectors = [
                'table.tabla_datos',
                'table[class*="tabla"]',
                'table[class*="datos"]',
                'table[id*="tabla"]',
                'table[id*="resultado"]',
                'div.resultados table',
                'div[class*="resultado"] table'
            ]
            
            for selector in possible_selectors:
                table = soup.select_one(selector)
                if table:
                    logger.info(f"Tabla encontrada con selector: {selector}")
                    break
            
            # Si no se encuentra con selectores específicos, buscar todas las tablas
            if not table:
                tables = soup.find_all('table')
                logger.info(f"Encontradas {len(tables)} tablas en total")
                
                for i, t in enumerate(tables):
                    # Buscar tabla que contenga información de proyectos
                    headers = t.find_all(['th', 'td'])
                    header_text = ' '.join([h.get_text().lower() for h in headers[:10]])
                    
                    if any(keyword in header_text for keyword in ['proyecto', 'expediente', 'titular', 'estado', 'región']):
                        table = t
                        logger.info(f"Tabla de proyectos encontrada en posición {i}")
                        break
            
            if not table:
                # Buscar texto que indique "no se encontraron resultados"
                page_text = soup.get_text().lower()
                if 'no se encontraron' in page_text or 'sin resultados' in page_text:
                    return {
                        'success': False,
                        'error': f'No se encontraron proyectos para la empresa: {nombre_empresa}'
                    }
                else:
                    return {
                        'success': False,
                        'error': 'No se pudo encontrar la tabla de resultados en la página del SEIA'
                    }
            
            # Extraer proyectos de la tabla
            proyectos = self._extraer_proyectos_de_tabla(table)
            
            if not proyectos:
                return {
                    'success': False,
                    'error': f'No se encontraron proyectos para la empresa: {nombre_empresa}'
                }
            
            # Tomar el primer proyecto y obtener detalles
            primer_proyecto = proyectos[0]
            logger.info(f"Proyecto encontrado: {primer_proyecto.get('nombre', 'Sin nombre')}")
            
            # Obtener detalles adicionales si hay link
            if primer_proyecto.get('link_expediente'):
                detalles = self._obtener_detalles_proyecto(primer_proyecto['link_expediente'])
                if detalles:
                    primer_proyecto.update(detalles)
            
            return {
                'success': True,
                'data': primer_proyecto,
                'total_proyectos': len(proyectos)
            }
            
        except requests.exceptions.RequestException as e:
            logger.error(f"Error de conexión: {e}")
            return {
                'success': False,
                'error': f'Error de conexión al SEIA: {str(e)}'
            }
        except Exception as e:
            logger.error(f"Error inesperado: {e}")
            return {
                'success': False,
                'error': f'Error al procesar información del SEIA: {str(e)}'
            }
    
    def _extraer_proyectos_de_tabla(self, table) -> List[Dict]:
        """Extrae proyectos de la tabla de resultados"""
        proyectos = []
        
        try:
            # Buscar tbody o usar la tabla directamente
            tbody = table.find('tbody') or table
            rows = tbody.find_all('tr')
            
            logger.info(f"Encontradas {len(rows)} filas en la tabla")
            
            for i, row in enumerate(rows):
                cols = row.find_all(['td', 'th'])
                
                # Saltar filas de encabezado
                if len(cols) == 0 or all(col.find('th') or 'th' in str(col) for col in cols):
                    continue
                
                if len(cols) >= 10:  # Estructura real del SEIA: 11 columnas
                    proyecto = {}
                    
                    # Extraer información según la estructura real del SEIA:
                    # Col 0: No, Col 1: Nombre, Col 2: Tipo, Col 3: Región, Col 4: Tipología, 
                    # Col 5: Razón de Ingreso, Col 6: Titular, Col 7: Inversión, Col 8: Fecha, Col 9: Estado, Col 10: Mapa
                    
                    for j, col in enumerate(cols):
                        text = col.get_text(strip=True)
                        
                        if j == 0:  # Número de proyecto
                            if text.isdigit():
                                proyecto['numero'] = text
                            else:
                                continue  # Saltar si no es número (probablemente encabezado)
                        
                        elif j == 1:  # Nombre del proyecto
                            proyecto['nombre'] = text
                            # Buscar link del expediente
                            link = col.find('a', href=True)
                            if link:
                                href = link['href']
                                if href.startswith('/'):
                                    proyecto['link_expediente'] = f"{self.base_url}{href}"
                                elif href.startswith('http'):
                                    proyecto['link_expediente'] = href
                                else:
                                    proyecto['link_expediente'] = f"{self.base_url}/{href}"
                        
                        elif j == 2:  # Tipo (DIA/EIA)
                            proyecto['tipo'] = text
                        
                        elif j == 3:  # Región
                            proyecto['region'] = text
                        
                        elif j == 4:  # Tipología
                            proyecto['tipologia'] = text
                        
                        elif j == 5:  # Razón de Ingreso
                            proyecto['razon_ingreso'] = text
                        
                        elif j == 6:  # Titular (empresa)
                            proyecto['titular_nombre'] = text
                        
                        elif j == 7:  # Inversión
                            proyecto['inversion'] = text
                        
                        elif j == 8:  # Fecha de presentación
                            proyecto['fecha_presentacion'] = text
                        
                        elif j == 9:  # Estado
                            proyecto['estado'] = text
                    
                    # Validar que el proyecto tenga información mínima
                    if proyecto.get('nombre') and len(proyecto['nombre']) > 3:
                        # Agregar información básica del titular
                        proyecto['titular'] = {
                            'nombre': proyecto.get('titular_nombre', ''),
                            'nombre_fantasia': proyecto.get('titular_nombre', '')
                        }
                        
                        # Agregar información de ubicación
                        proyecto['ubicacion'] = {
                            'region': proyecto.get('region', ''),
                            'ubicacion_proyecto': proyecto.get('region', '')
                        }
                        
                        proyectos.append(proyecto)
                        logger.info(f"Proyecto extraído: {proyecto['nombre'][:50]}...")
                        
                        if len(proyectos) >= 5:  # Limitar a 5 proyectos
                            break
            
            logger.info(f"Total proyectos extraídos: {len(proyectos)}")
            return proyectos
            
        except Exception as e:
            logger.error(f"Error al extraer proyectos de tabla: {e}")
            return []
    
    def _obtener_detalles_proyecto(self, link_expediente: str) -> Optional[Dict]:
        """Obtiene detalles adicionales del proyecto"""
        try:
            from bs4 import BeautifulSoup
            
            logger.info(f"Obteniendo detalles de: {link_expediente}")
            
            response = self.session.get(link_expediente, timeout=20)
            response.raise_for_status()
            
            soup = BeautifulSoup(response.content, 'html.parser')
            
            detalles = {}
            
            # Buscar información en tablas
            for table in soup.find_all('table'):
                rows = table.find_all('tr')
                for row in rows:
                    cols = row.find_all(['td', 'th'])
                    if len(cols) >= 2:
                        key = cols[0].get_text(strip=True).lower()
                        value = cols[1].get_text(strip=True)
                        
                        if value and len(value) > 1:
                            # Información del titular
                            if 'titular' in key or 'empresa' in key:
                                if not detalles.get('titular'):
                                    detalles['titular'] = {}
                                
                                if 'razón social' in key or 'razon social' in key:
                                    detalles['titular']['razon_social'] = value
                                elif 'nombre' in key:
                                    detalles['titular']['nombre'] = value
                                    detalles['titular']['nombre_fantasia'] = value
                                elif 'rut' in key:
                                    detalles['titular']['rut'] = value
                                elif 'dirección' in key or 'direccion' in key:
                                    detalles['titular']['direccion'] = value
                                elif 'teléfono' in key or 'telefono' in key:
                                    detalles['titular']['telefono'] = value
                                elif 'email' in key or 'correo' in key:
                                    detalles['titular']['email'] = value
                            
                            # Información de ubicación
                            elif 'ubicación' in key or 'ubicacion' in key:
                                if not detalles.get('ubicacion'):
                                    detalles['ubicacion'] = {}
                                detalles['ubicacion']['ubicacion_proyecto'] = value
                            elif 'comuna' in key:
                                if not detalles.get('ubicacion'):
                                    detalles['ubicacion'] = {}
                                detalles['ubicacion']['comuna'] = value
                            elif 'provincia' in key:
                                if not detalles.get('ubicacion'):
                                    detalles['ubicacion'] = {}
                                detalles['ubicacion']['provincia'] = value
                            elif 'coordenadas' in key:
                                if not detalles.get('ubicacion'):
                                    detalles['ubicacion'] = {}
                                detalles['ubicacion']['coordenadas'] = value
            
            # Buscar patrones en el texto completo
            text_content = soup.get_text()
            
            # Buscar RUT si no se encontró
            if not detalles.get('titular', {}).get('rut'):
                rut_match = re.search(r'RUT[:\s]*(\d{1,2}\.?\d{3}\.?\d{3}[-\.]?[\dkK])', text_content, re.IGNORECASE)
                if rut_match:
                    if not detalles.get('titular'):
                        detalles['titular'] = {}
                    detalles['titular']['rut'] = rut_match.group(1)
            
            # Buscar teléfono si no se encontró
            if not detalles.get('titular', {}).get('telefono'):
                phone_match = re.search(r'(?:Tel[éefono]*|Teléfono)[:\s]*([+]?[\d\s\-\(\)]{7,15})', text_content, re.IGNORECASE)
                if phone_match:
                    if not detalles.get('titular'):
                        detalles['titular'] = {}
                    detalles['titular']['telefono'] = phone_match.group(1).strip()
            
            # Buscar email si no se encontró
            if not detalles.get('titular', {}).get('email'):
                email_match = re.search(r'([a-zA-Z0-9._%+-]+@[a-zA-Z0-9.-]+\.[a-zA-Z]{2,})', text_content)
                if email_match:
                    if not detalles.get('titular'):
                        detalles['titular'] = {}
                    detalles['titular']['email'] = email_match.group(1)
            
            logger.info(f"Detalles obtenidos: {len(detalles)} secciones")
            return detalles
            
        except Exception as e:
            logger.warning(f"No se pudieron obtener detalles del proyecto: {e}")
            return {}

# Función principal para usar desde main.py
def obtener_informacion_proyecto_seia_real(nombre_empresa: str) -> Dict:
    """
    Función principal para obtener información real del SEIA
    """
    scraper = SEIARealScraper()
    return scraper.buscar_proyectos(nombre_empresa)

# Test function
def test_scraper_real():
    """Función de test"""
    empresas_test = ['Codelco', 'Antofagasta Minerals', 'BHP Billiton']
    
    for empresa in empresas_test:
        print(f"\n--- Test para: {empresa} ---")
        result = obtener_informacion_proyecto_seia_real(empresa)
        
        if result.get('success'):
            data = result.get('data', {})
            print(f"✅ Éxito")
            print(f"📋 Proyecto: {data.get('nombre', 'N/A')}")
            print(f"📍 Región: {data.get('region', 'N/A')}")
            print(f"📊 Estado: {data.get('estado', 'N/A')}")
            print(f"🏢 Titular: {data.get('titular', {}).get('nombre', 'N/A')}")
        else:
            print(f"❌ Error: {result.get('error', 'Unknown')}")

if __name__ == "__main__":
    test_scraper_real() 