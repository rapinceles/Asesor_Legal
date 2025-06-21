# scrapers/seia_titular.py - Scraper que busca por titular específico
import requests
import re
from typing import Dict, Optional, List
import logging
from urllib.parse import urljoin

logger = logging.getLogger(__name__)

class SEIATitularScraper:
    """Scraper que busca específicamente por titular en el SEIA"""
    
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
    
    def buscar_por_titular(self, nombre_empresa: str) -> Dict:
        """Busca proyectos por titular específico en el SEIA"""
        try:
            from bs4 import BeautifulSoup
        except ImportError:
            return {
                'success': False,
                'error': 'BeautifulSoup no disponible'
            }
        
        try:
            logger.info(f"🔍 Buscando proyectos por titular: {nombre_empresa}")
            
            # Generar variaciones del nombre para búsqueda más efectiva
            variaciones_titular = self._generar_variaciones_titular(nombre_empresa)
            
            todos_proyectos = []
            
            # Buscar con cada variación
            for variacion in variaciones_titular:
                logger.info(f"📋 Probando búsqueda con: {variacion}")
                proyectos = self._buscar_con_variacion(variacion)
                if proyectos:
                    todos_proyectos.extend(proyectos)
            
            if not todos_proyectos:
                return {
                    'success': False,
                    'error': f'No se encontraron proyectos para el titular: {nombre_empresa}',
                    'variaciones_probadas': variaciones_titular
                }
            
            # Filtrar proyectos únicos y relevantes
            proyectos_filtrados = self._filtrar_proyectos_por_titular(todos_proyectos, nombre_empresa)
            
            if not proyectos_filtrados:
                return {
                    'success': False,
                    'error': f'No se encontraron proyectos relevantes para: {nombre_empresa}',
                    'proyectos_encontrados': len(todos_proyectos),
                    'lista_proyectos': [p.get('nombre', 'Sin nombre') for p in todos_proyectos[:5]]
                }
            
            return {
                'success': True,
                'data': {
                    'titular_buscado': nombre_empresa,
                    'proyectos_encontrados': len(proyectos_filtrados),
                    'lista_proyectos': proyectos_filtrados,
                    'proyecto_principal': proyectos_filtrados[0] if proyectos_filtrados else None
                },
                'variaciones_usadas': variaciones_titular,
                'total_encontrados': len(todos_proyectos)
            }
            
        except Exception as e:
            logger.error(f"❌ Error en búsqueda por titular: {e}")
            return {
                'success': False,
                'error': f'Error al buscar titular en SEIA: {str(e)}'
            }
    
    def _generar_variaciones_titular(self, nombre_empresa: str) -> List[str]:
        """Genera variaciones del nombre del titular para búsqueda más efectiva"""
        variaciones = [nombre_empresa]
        nombre_lower = nombre_empresa.lower()
        
        # Variaciones específicas según el nombre
        if 'candelaria' in nombre_lower:
            variaciones.extend([
                'Candelaria',
                'Minera Candelaria',
                'Compañía Minera Candelaria',
                'Compania Minera Candelaria',
                'Compañía Contractual Minera Candelaria',
                'Compania Contractual Minera Candelaria',
                'Contractual Minera Candelaria'
            ])
        elif 'codelco' in nombre_lower:
            variaciones.extend([
                'Codelco',
                'CODELCO',
                'Corporación Nacional del Cobre',
                'Corporacion Nacional del Cobre',
                'Codelco Chile'
            ])
        elif 'antofagasta' in nombre_lower:
            variaciones.extend([
                'Antofagasta',
                'Antofagasta Minerals',
                'Antofagasta PLC',
                'Minera Antofagasta'
            ])
        elif 'escondida' in nombre_lower:
            variaciones.extend([
                'Escondida',
                'Minera Escondida',
                'Compañía Minera Escondida',
                'BHP Escondida'
            ])
        elif 'bhp' in nombre_lower:
            variaciones.extend([
                'BHP',
                'BHP Billiton',
                'BHP Chile'
            ])
        
        # Eliminar duplicados manteniendo orden
        variaciones_unicas = []
        for v in variaciones:
            if v not in variaciones_unicas:
                variaciones_unicas.append(v)
        
        return variaciones_unicas
    
    def _buscar_con_variacion(self, titular: str) -> List[Dict]:
        """Busca proyectos con una variación específica del titular"""
        try:
            from bs4 import BeautifulSoup
            
            # URL de búsqueda del SEIA
            search_url = f"{self.base_url}/busqueda/buscarProyectoAction.php"
            
            # Datos del formulario - buscar por titular
            search_data = {
                'nombre_empresa_o_titular': titular,
                'submit_buscar': 'Buscar'
            }
            
            # Realizar búsqueda
            response = self.session.post(search_url, data=search_data, timeout=30)
            response.raise_for_status()
            
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
                    logger.info(f"📊 Proyectos encontrados para '{titular}': {proyectos_encontrados}")
            
            if proyectos_encontrados == 0:
                return []
            
            # Buscar la tabla de resultados
            tables = soup.find_all('table')
            data_table = None
            
            for table in tables:
                rows = table.find_all('tr')
                if len(rows) > 1:
                    first_row = rows[0]
                    headers = [th.get_text(strip=True) for th in first_row.find_all(['th', 'td'])]
                    
                    if any(header in headers for header in ['Nombre', 'Tipo', 'Región', 'Titular', 'Estado']):
                        data_table = table
                        break
            
            if not data_table:
                return []
            
            # Extraer proyectos de la tabla
            proyectos = self._extraer_proyectos_de_tabla(data_table, titular)
            return proyectos
            
        except Exception as e:
            logger.warning(f"⚠️ Error al buscar con '{titular}': {e}")
            return []
    
    def _extraer_proyectos_de_tabla(self, table, titular_buscado: str) -> List[Dict]:
        """Extrae proyectos de la tabla de resultados del SEIA"""
        proyectos = []
        
        try:
            rows = table.find_all('tr')
            
            # Analizar header
            header_row = rows[0]
            headers = [th.get_text(strip=True) for th in header_row.find_all(['th', 'td'])]
            
            # Mapear índices de columnas
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
            
            # Procesar filas de datos
            for i, row in enumerate(rows[1:], 1):
                cols = row.find_all(['td', 'th'])
                
                if len(cols) < 5:
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
                    proyecto['titular_buscado'] = titular_buscado
                    proyecto['id_proyecto'] = i
                    proyectos.append(proyecto)
                    
                    if len(proyectos) >= 20:  # Limitar a 20 proyectos por búsqueda
                        break
            
            return proyectos
            
        except Exception as e:
            logger.error(f"❌ Error al extraer proyectos: {e}")
            return []
    
    def _filtrar_proyectos_por_titular(self, proyectos: List[Dict], empresa_buscada: str) -> List[Dict]:
        """Filtra proyectos que realmente pertenezcan al titular buscado"""
        empresa_lower = empresa_buscada.lower()
        proyectos_filtrados = []
        
        # Palabras clave para filtrado más preciso
        palabras_clave = self._generar_palabras_clave(empresa_buscada)
        
        for proyecto in proyectos:
            titular = proyecto.get('titular', '').lower()
            nombre_proyecto = proyecto.get('nombre', '').lower()
            
            # Verificar coincidencias con palabras clave
            coincidencia_encontrada = False
            for palabra in palabras_clave:
                if (palabra in titular or 
                    palabra in nombre_proyecto):
                    proyecto['coincidencia'] = palabra
                    proyecto['score_relevancia'] = self._calcular_score_relevancia(titular, nombre_proyecto, palabra)
                    proyectos_filtrados.append(proyecto)
                    coincidencia_encontrada = True
                    logger.info(f"✅ Coincidencia '{palabra}': {proyecto.get('nombre', 'N/A')} - {titular}")
                    break
            
            if not coincidencia_encontrada:
                logger.debug(f"❌ Sin coincidencia: {proyecto.get('nombre', 'N/A')} - {titular}")
        
        # Ordenar por score de relevancia
        proyectos_filtrados.sort(key=lambda x: x.get('score_relevancia', 0), reverse=True)
        
        return proyectos_filtrados
    
    def _generar_palabras_clave(self, empresa: str) -> List[str]:
        """Genera palabras clave para filtrado más preciso"""
        empresa_lower = empresa.lower()
        palabras = [empresa_lower]
        
        if 'candelaria' in empresa_lower:
            palabras.extend(['candelaria', 'contractual minera candelaria', 'compañía contractual minera candelaria'])
        elif 'codelco' in empresa_lower:
            palabras.extend(['codelco', 'corporación nacional del cobre'])
        elif 'antofagasta' in empresa_lower:
            palabras.extend(['antofagasta', 'antofagasta minerals'])
        elif 'escondida' in empresa_lower:
            palabras.extend(['escondida', 'minera escondida'])
        elif 'bhp' in empresa_lower:
            palabras.extend(['bhp', 'bhp billiton'])
        
        return palabras
    
    def _calcular_score_relevancia(self, titular: str, nombre_proyecto: str, palabra_clave: str) -> float:
        """Calcula un score de relevancia para ordenar resultados"""
        score = 0.0
        
        # Mayor score si la palabra está en el titular
        if palabra_clave in titular:
            score += 10.0
            # Score adicional si es coincidencia exacta
            if titular.strip().lower() == palabra_clave:
                score += 20.0
        
        # Score menor si está en el nombre del proyecto
        if palabra_clave in nombre_proyecto:
            score += 5.0
        
        # Score adicional por longitud de coincidencia
        score += len(palabra_clave) * 0.1
        
        return score
    
    def obtener_detalles_proyecto(self, proyecto: Dict) -> Dict:
        """Obtiene detalles adicionales de un proyecto específico"""
        try:
            link_expediente = proyecto.get('link_expediente')
            if not link_expediente:
                return proyecto
            
            from bs4 import BeautifulSoup
            
            logger.info(f"🔍 Obteniendo detalles de: {proyecto.get('nombre', 'N/A')}")
            
            response = self.session.get(link_expediente, timeout=20)
            response.raise_for_status()
            
            soup = BeautifulSoup(response.content, 'html.parser')
            
            # Buscar información adicional en tablas del expediente
            detalles_adicionales = {}
            
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
                                if 'razón social' in key:
                                    detalles_adicionales['razon_social_completa'] = value
                                elif 'rut' in key:
                                    detalles_adicionales['rut'] = value
                                elif 'dirección' in key:
                                    detalles_adicionales['direccion_titular'] = value
                                elif 'teléfono' in key:
                                    detalles_adicionales['telefono'] = value
                                elif 'email' in key:
                                    detalles_adicionales['email'] = value
                            
                            # Información de ubicación
                            elif 'ubicación' in key or 'comuna' in key or 'provincia' in key:
                                if 'ubicación' in key:
                                    detalles_adicionales['ubicacion_detallada'] = value
                                elif 'comuna' in key:
                                    detalles_adicionales['comuna'] = value
                                elif 'provincia' in key:
                                    detalles_adicionales['provincia'] = value
            
            # Buscar patrones en texto libre
            text_content = soup.get_text()
            
            # Buscar RUT si no se encontró
            if not detalles_adicionales.get('rut'):
                rut_match = re.search(r'RUT[:\s]*(\d{1,2}\.?\d{3}\.?\d{3}[-\.]?[\dkK])', text_content, re.IGNORECASE)
                if rut_match:
                    detalles_adicionales['rut'] = rut_match.group(1)
            
            # Buscar email si no se encontró
            if not detalles_adicionales.get('email'):
                email_match = re.search(r'([a-zA-Z0-9._%+-]+@[a-zA-Z0-9.-]+\.[a-zA-Z]{2,})', text_content)
                if email_match:
                    detalles_adicionales['email'] = email_match.group(1)
            
            # Combinar información
            proyecto_completo = {**proyecto, **detalles_adicionales}
            
            logger.info(f"✅ Detalles obtenidos para: {proyecto.get('nombre', 'N/A')}")
            return proyecto_completo
            
        except Exception as e:
            logger.warning(f"⚠️ No se pudieron obtener detalles adicionales: {e}")
            return proyecto

# Función principal para usar desde main.py
def buscar_proyectos_por_titular(nombre_empresa: str) -> Dict:
    """
    Función principal para buscar proyectos por titular específico
    """
    scraper = SEIATitularScraper()
    return scraper.buscar_por_titular(nombre_empresa)

def obtener_proyecto_seleccionado(nombre_empresa: str, id_proyecto: int) -> Dict:
    """
    Obtiene un proyecto específico seleccionado por el usuario
    """
    scraper = SEIATitularScraper()
    
    # Primero buscar todos los proyectos
    resultado_busqueda = scraper.buscar_por_titular(nombre_empresa)
    
    if not resultado_busqueda.get('success'):
        return resultado_busqueda
    
    proyectos = resultado_busqueda['data']['lista_proyectos']
    
    # Buscar el proyecto por ID
    proyecto_seleccionado = None
    for proyecto in proyectos:
        if proyecto.get('id_proyecto') == id_proyecto:
            proyecto_seleccionado = proyecto
            break
    
    if not proyecto_seleccionado:
        return {
            'success': False,
            'error': f'No se encontró el proyecto con ID {id_proyecto}'
        }
    
    # Obtener detalles completos del proyecto
    proyecto_completo = scraper.obtener_detalles_proyecto(proyecto_seleccionado)
    
    return {
        'success': True,
        'data': proyecto_completo
    }

# Test function
def test_titular_scraper():
    """Función de test específica para titulares"""
    empresas_test = [
        'Candelaria',
        'Compañía Contractual Minera Candelaria',
        'Codelco',
        'Antofagasta Minerals'
    ]
    
    for empresa in empresas_test:
        print(f"\n{'='*80}")
        print(f"🔍 BUSCANDO PROYECTOS PARA TITULAR: {empresa}")
        print('='*80)
        
        result = buscar_proyectos_por_titular(empresa)
        
        if result.get('success'):
            data = result.get('data', {})
            print(f"✅ ÉXITO")
            print(f"📊 Proyectos encontrados: {data.get('proyectos_encontrados', 0)}")
            print(f"🔍 Variaciones usadas: {result.get('variaciones_usadas', [])}")
            
            proyectos = data.get('lista_proyectos', [])
            print(f"\n📋 LISTA DE PROYECTOS:")
            for i, proyecto in enumerate(proyectos[:5], 1):
                print(f"{i}. {proyecto.get('nombre', 'N/A')}")
                print(f"   Titular: {proyecto.get('titular', 'N/A')}")
                print(f"   Región: {proyecto.get('region', 'N/A')}")
                print(f"   Estado: {proyecto.get('estado', 'N/A')}")
                print(f"   Score: {proyecto.get('score_relevancia', 0):.1f}")
                print()
        else:
            print(f"❌ ERROR: {result.get('error', 'Unknown')}")
            if result.get('lista_proyectos'):
                print(f"📋 Proyectos encontrados (no relevantes): {result['lista_proyectos']}")

if __name__ == "__main__":
    test_titular_scraper() 