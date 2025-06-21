# scrapers/seia_correcto.py - Scraper corregido que funciona con el SEIA real
import requests
import re
from typing import Dict, Optional, List
import logging
from urllib.parse import urljoin
import time

logger = logging.getLogger(__name__)

class SEIACorrectScraper:
    """Scraper corregido para obtener información real del SEIA"""
    
    def __init__(self):
        self.base_url = "https://seia.sea.gob.cl"
        self.session = requests.Session()
        self.session.headers.update({
            'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36',
            'Accept': 'text/html,application/xhtml+xml,application/xml;q=0.9,*/*;q=0.8',
            'Accept-Language': 'es-ES,es;q=0.8',
            'Accept-Encoding': 'gzip, deflate, br',
            'Connection': 'keep-alive',
            'Content-Type': 'application/x-www-form-urlencoded'
        })
    
    def buscar_empresa_en_seia(self, nombre_empresa: str) -> Dict:
        """Busca una empresa específica en el SEIA"""
        try:
            from bs4 import BeautifulSoup
        except ImportError:
            return {
                'success': False,
                'error': 'BeautifulSoup no disponible'
            }
        
        try:
            logger.info(f"🔍 Buscando en SEIA: {nombre_empresa}")
            
            # URL de búsqueda del SEIA
            search_url = f"{self.base_url}/busqueda/buscarProyectoAction.php"
            
            # Datos del formulario - usar el campo correcto para empresa/titular
            search_data = {
                'nombre_empresa_o_titular': nombre_empresa,
                'submit_buscar': 'Buscar'
            }
            
            # Realizar búsqueda
            response = self.session.post(search_url, data=search_data, timeout=30)
            response.raise_for_status()
            
            logger.info(f"✅ Respuesta recibida: {response.status_code}")
            
            # Parsear HTML
            soup = BeautifulSoup(response.content, 'html.parser')
            
            # Verificar si hay resultados
            page_text = soup.get_text()
            
            # Buscar número de proyectos encontrados
            proyectos_encontrados = 0
            if 'Proyectos encontrados:' in page_text:
                match = re.search(r'Proyectos encontrados:\s*(\d+)', page_text)
                if match:
                    proyectos_encontrados = int(match.group(1).replace(',', ''))
                    logger.info(f"📊 Proyectos encontrados: {proyectos_encontrados}")
            
            if proyectos_encontrados == 0:
                return {
                    'success': False,
                    'error': f'No se encontraron proyectos para la empresa: {nombre_empresa}'
                }
            
            # Buscar la tabla de resultados (primera tabla con datos)
            tables = soup.find_all('table')
            data_table = None
            
            for table in tables:
                rows = table.find_all('tr')
                if len(rows) > 1:  # Más de una fila (header + datos)
                    # Verificar si es la tabla de datos
                    first_row = rows[0]
                    headers = [th.get_text(strip=True) for th in first_row.find_all(['th', 'td'])]
                    
                    # Buscar headers característicos del SEIA
                    if any(header in headers for header in ['Nombre', 'Tipo', 'Región', 'Titular', 'Estado']):
                        data_table = table
                        logger.info(f"✅ Tabla de datos encontrada con {len(rows)} filas")
                        break
            
            if not data_table:
                return {
                    'success': False,
                    'error': 'No se pudo encontrar la tabla de resultados'
                }
            
            # Extraer proyectos de la tabla
            proyectos = self._extraer_proyectos_correctos(data_table, nombre_empresa)
            
            if not proyectos:
                return {
                    'success': False,
                    'error': f'No se pudieron extraer datos de proyectos para: {nombre_empresa}'
                }
            
            # Filtrar proyectos que realmente pertenezcan a la empresa buscada
            proyectos_filtrados = self._filtrar_proyectos_por_empresa(proyectos, nombre_empresa)
            
            if not proyectos_filtrados:
                # Si no hay coincidencias exactas, tomar el primer proyecto
                proyecto_seleccionado = proyectos[0]
                logger.warning(f"⚠️ No se encontraron coincidencias exactas, usando primer resultado")
            else:
                proyecto_seleccionado = proyectos_filtrados[0]
                logger.info(f"✅ Proyecto encontrado para {nombre_empresa}")
            
            # Obtener detalles adicionales del proyecto
            if proyecto_seleccionado.get('link_expediente'):
                detalles = self._obtener_detalles_expediente(proyecto_seleccionado['link_expediente'])
                if detalles:
                    proyecto_seleccionado.update(detalles)
            
            return {
                'success': True,
                'data': proyecto_seleccionado,
                'total_encontrados': proyectos_encontrados,
                'proyectos_extraidos': len(proyectos),
                'proyectos_filtrados': len(proyectos_filtrados) if proyectos_filtrados else 0
            }
            
        except requests.exceptions.RequestException as e:
            logger.error(f"❌ Error de conexión: {e}")
            return {
                'success': False,
                'error': f'Error de conexión al SEIA: {str(e)}'
            }
        except Exception as e:
            logger.error(f"❌ Error inesperado: {e}")
            return {
                'success': False,
                'error': f'Error al procesar información del SEIA: {str(e)}'
            }
    
    def _extraer_proyectos_correctos(self, table, empresa_buscada: str) -> List[Dict]:
        """Extrae proyectos de la tabla de resultados del SEIA"""
        proyectos = []
        
        try:
            rows = table.find_all('tr')
            
            # Analizar header para entender estructura
            header_row = rows[0]
            headers = [th.get_text(strip=True) for th in header_row.find_all(['th', 'td'])]
            logger.info(f"📋 Headers encontrados: {headers}")
            
            # Mapear índices de columnas importantes
            col_indices = {}
            for i, header in enumerate(headers):
                header_lower = header.lower()
                if 'nombre' in header_lower:
                    col_indices['nombre'] = i
                elif 'tipo' in header_lower:
                    col_indices['tipo'] = i
                elif 'región' in header_lower or 'region' in header_lower:
                    col_indices['region'] = i
                elif 'titular' in header_lower:
                    col_indices['titular'] = i
                elif 'estado' in header_lower:
                    col_indices['estado'] = i
                elif 'fecha' in header_lower:
                    col_indices['fecha'] = i
                elif 'inversión' in header_lower or 'inversion' in header_lower:
                    col_indices['inversion'] = i
                elif 'tipología' in header_lower or 'tipologia' in header_lower:
                    col_indices['tipologia'] = i
            
            logger.info(f"📊 Mapeo de columnas: {col_indices}")
            
            # Procesar filas de datos (saltar header)
            for i, row in enumerate(rows[1:], 1):
                cols = row.find_all(['td', 'th'])
                
                if len(cols) < 5:  # Saltar filas con pocas columnas
                    continue
                
                proyecto = {}
                
                # Extraer datos según mapeo de columnas
                for campo, indice in col_indices.items():
                    if indice < len(cols):
                        text = cols[indice].get_text(strip=True)
                        proyecto[campo] = text
                        
                        # Buscar links en la columna de nombre
                        if campo == 'nombre':
                            link = cols[indice].find('a', href=True)
                            if link:
                                href = link['href']
                                if href.startswith('/'):
                                    proyecto['link_expediente'] = f"{self.base_url}{href}"
                                elif href.startswith('http'):
                                    proyecto['link_expediente'] = href
                                else:
                                    proyecto['link_expediente'] = f"{self.base_url}/{href}"
                
                # Validar que el proyecto tenga información mínima
                if proyecto.get('nombre') and len(proyecto['nombre']) > 3:
                    # Agregar información estructurada
                    proyecto['titular_info'] = {
                        'nombre': proyecto.get('titular', empresa_buscada),
                        'nombre_fantasia': proyecto.get('titular', empresa_buscada)
                    }
                    
                    proyecto['ubicacion_info'] = {
                        'region': proyecto.get('region', ''),
                        'ubicacion_proyecto': proyecto.get('region', '')
                    }
                    
                    proyectos.append(proyecto)
                    logger.info(f"✅ Proyecto {i}: {proyecto['nombre'][:50]}...")
                    
                    # Limitar a 10 proyectos para eficiencia
                    if len(proyectos) >= 10:
                        break
            
            logger.info(f"📄 Total proyectos extraídos: {len(proyectos)}")
            return proyectos
            
        except Exception as e:
            logger.error(f"❌ Error al extraer proyectos: {e}")
            return []
    
    def _filtrar_proyectos_por_empresa(self, proyectos: List[Dict], empresa_buscada: str) -> List[Dict]:
        """Filtra proyectos que realmente pertenezcan a la empresa buscada"""
        empresa_lower = empresa_buscada.lower()
        proyectos_filtrados = []
        
        # Palabras clave para mejorar filtrado
        palabras_clave = [empresa_lower]
        
        # Agregar variaciones comunes
        if 'candelaria' in empresa_lower:
            palabras_clave.extend(['candelaria', 'minera candelaria', 'compañía minera candelaria'])
        elif 'codelco' in empresa_lower:
            palabras_clave.extend(['codelco', 'corporación nacional del cobre'])
        elif 'antofagasta' in empresa_lower:
            palabras_clave.extend(['antofagasta', 'antofagasta minerals'])
        elif 'escondida' in empresa_lower:
            palabras_clave.extend(['escondida', 'minera escondida'])
        elif 'bhp' in empresa_lower:
            palabras_clave.extend(['bhp', 'bhp billiton'])
        
        for proyecto in proyectos:
            titular = proyecto.get('titular', '').lower()
            nombre_proyecto = proyecto.get('nombre', '').lower()
            
            # Verificar coincidencias con cualquier palabra clave
            encontrado = False
            for palabra in palabras_clave:
                if (palabra in titular or 
                    palabra in nombre_proyecto or
                    titular in palabra):
                    proyectos_filtrados.append(proyecto)
                    logger.info(f"✅ Coincidencia con '{palabra}': {proyecto.get('nombre', 'N/A')} - {proyecto.get('titular', 'N/A')}")
                    encontrado = True
                    break
            
            if not encontrado:
                logger.debug(f"❌ Sin coincidencia: {proyecto.get('nombre', 'N/A')} - {proyecto.get('titular', 'N/A')}")
        
        return proyectos_filtrados
    
    def _obtener_detalles_expediente(self, link_expediente: str) -> Optional[Dict]:
        """Obtiene detalles adicionales del expediente"""
        try:
            from bs4 import BeautifulSoup
            
            logger.info(f"🔍 Obteniendo detalles: {link_expediente}")
            
            response = self.session.get(link_expediente, timeout=20)
            response.raise_for_status()
            
            soup = BeautifulSoup(response.content, 'html.parser')
            detalles = {}
            
            # Buscar información en tablas del expediente
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
                                if not detalles.get('titular_detallado'):
                                    detalles['titular_detallado'] = {}
                                
                                if 'razón social' in key:
                                    detalles['titular_detallado']['razon_social'] = value
                                elif 'rut' in key:
                                    detalles['titular_detallado']['rut'] = value
                                elif 'dirección' in key:
                                    detalles['titular_detallado']['direccion'] = value
                                elif 'teléfono' in key:
                                    detalles['titular_detallado']['telefono'] = value
                                elif 'email' in key:
                                    detalles['titular_detallado']['email'] = value
                            
                            # Información de ubicación
                            elif 'ubicación' in key or 'comuna' in key or 'provincia' in key:
                                if not detalles.get('ubicacion_detallada'):
                                    detalles['ubicacion_detallada'] = {}
                                
                                if 'ubicación' in key:
                                    detalles['ubicacion_detallada']['ubicacion_proyecto'] = value
                                elif 'comuna' in key:
                                    detalles['ubicacion_detallada']['comuna'] = value
                                elif 'provincia' in key:
                                    detalles['ubicacion_detallada']['provincia'] = value
            
            # Buscar patrones en texto libre
            text_content = soup.get_text()
            
            # Buscar RUT
            rut_match = re.search(r'RUT[:\s]*(\d{1,2}\.?\d{3}\.?\d{3}[-\.]?[\dkK])', text_content, re.IGNORECASE)
            if rut_match and not detalles.get('titular_detallado', {}).get('rut'):
                if not detalles.get('titular_detallado'):
                    detalles['titular_detallado'] = {}
                detalles['titular_detallado']['rut'] = rut_match.group(1)
            
            # Buscar email
            email_match = re.search(r'([a-zA-Z0-9._%+-]+@[a-zA-Z0-9.-]+\.[a-zA-Z]{2,})', text_content)
            if email_match and not detalles.get('titular_detallado', {}).get('email'):
                if not detalles.get('titular_detallado'):
                    detalles['titular_detallado'] = {}
                detalles['titular_detallado']['email'] = email_match.group(1)
            
            logger.info(f"✅ Detalles obtenidos: {len(detalles)} secciones")
            return detalles
            
        except Exception as e:
            logger.warning(f"⚠️ No se pudieron obtener detalles: {e}")
            return {}

# Función principal para usar desde main.py
def obtener_informacion_empresa_seia_correcto(nombre_empresa: str) -> Dict:
    """
    Función principal para obtener información REAL de una empresa del SEIA
    """
    scraper = SEIACorrectScraper()
    return scraper.buscar_empresa_en_seia(nombre_empresa)

# Test function
def test_scraper_correcto():
    """Función de test con empresas reales"""
    empresas_test = [
        'Candelaria',
        'Codelco', 
        'Antofagasta Minerals',
        'BHP',
        'Escondida'
    ]
    
    for empresa in empresas_test:
        print(f"\n{'='*60}")
        print(f"🔍 PROBANDO: {empresa}")
        print('='*60)
        
        result = obtener_informacion_empresa_seia_correcto(empresa)
        
        if result.get('success'):
            data = result.get('data', {})
            print(f"✅ ÉXITO")
            print(f"📋 Proyecto: {data.get('nombre', 'N/A')}")
            print(f"🏢 Titular: {data.get('titular', 'N/A')}")
            print(f"📍 Región: {data.get('region', 'N/A')}")
            print(f"📊 Estado: {data.get('estado', 'N/A')}")
            print(f"📅 Fecha: {data.get('fecha', 'N/A')}")
            print(f"💰 Inversión: {data.get('inversion', 'N/A')}")
            print(f"🔗 Link: {data.get('link_expediente', 'N/A')}")
            print(f"📊 Stats: {result.get('total_encontrados', 0)} encontrados, {result.get('proyectos_extraidos', 0)} extraídos, {result.get('proyectos_filtrados', 0)} filtrados")
            
            # Información detallada si está disponible
            if data.get('titular_detallado'):
                print(f"🏢 RUT: {data['titular_detallado'].get('rut', 'N/A')}")
                print(f"📧 Email: {data['titular_detallado'].get('email', 'N/A')}")
        else:
            print(f"❌ ERROR: {result.get('error', 'Unknown')}")

if __name__ == "__main__":
    test_scraper_correcto() 