# scrapers/seia_mejorado.py - Scraper SEIA mejorado para búsquedas específicas
import requests
from bs4 import BeautifulSoup
import re
import time
from typing import Dict, List, Optional
import logging

logger = logging.getLogger(__name__)

def obtener_informacion_empresa_seia_mejorado(nombre_empresa: str) -> Dict:
    """Scraper SEIA mejorado que busca proyectos específicos y ubicaciones reales"""
    try:
        logger.info(f"🔍 SEIA Mejorado - Búsqueda específica: {nombre_empresa}")
        
        # Generar variaciones del nombre de empresa
        variaciones = _generar_variaciones_empresa(nombre_empresa)
        
        mejor_resultado = None
        mejor_score = 0
        
        for variacion in variaciones:
            logger.info(f"📋 Probando variación: {variacion}")
            
            # Buscar con esta variación
            resultado = _buscar_con_variacion(variacion, nombre_empresa)
            
            if resultado and resultado.get('success'):
                score = resultado.get('score_relevancia', 0)
                proyectos = resultado.get('proyectos', [])
                
                logger.info(f"✅ Encontrados {len(proyectos)} proyectos con score {score}")
                
                if score > mejor_score:
                    mejor_score = score
                    mejor_resultado = resultado
            
            time.sleep(0.5)  # Pausa entre búsquedas
        
        if mejor_resultado:
            return _procesar_mejor_resultado(mejor_resultado, nombre_empresa)
        else:
            return {
                'success': False,
                'error': f'No se encontraron proyectos específicos para: {nombre_empresa}',
                'variaciones_probadas': variaciones
            }
            
    except Exception as e:
        logger.error(f"❌ Error en SEIA mejorado: {e}")
        return {
            'success': False,
            'error': f'Error en búsqueda: {str(e)}'
        }

def _generar_variaciones_empresa(nombre_empresa: str) -> List[str]:
    """Genera variaciones del nombre de empresa para búsqueda más efectiva"""
    variaciones = [nombre_empresa]
    
    # Variaciones comunes para empresas mineras
    if 'codelco' in nombre_empresa.lower():
        variaciones.extend([
            'Corporación Nacional del Cobre',
            'CODELCO',
            'Codelco Chile',
            'Corporacion Nacional del Cobre'
        ])
    elif 'candelaria' in nombre_empresa.lower():
        variaciones.extend([
            'Minera Candelaria',
            'Compañía Minera Candelaria',
            'Compania Minera Candelaria',
            'Compañía Contractual Minera Candelaria',
            'Lundin Mining'
        ])
    elif 'escondida' in nombre_empresa.lower():
        variaciones.extend([
            'Minera Escondida',
            'Compañía Minera Escondida',
            'BHP Billiton',
            'BHP'
        ])
    elif 'pelambres' in nombre_empresa.lower():
        variaciones.extend([
            'Minera Los Pelambres',
            'Compañía Minera Los Pelambres',
            'Antofagasta Minerals'
        ])
    
    # Variaciones generales
    nombre_base = nombre_empresa.strip()
    if not any(palabra in nombre_base.lower() for palabra in ['minera', 'compañía', 'empresa']):
        variaciones.extend([
            f'Minera {nombre_base}',
            f'Compañía Minera {nombre_base}',
            f'Empresa {nombre_base}'
        ])
    
    return list(set(variaciones))  # Eliminar duplicados

def _buscar_con_variacion(variacion: str, nombre_original: str) -> Optional[Dict]:
    """Busca proyectos con una variación específica del nombre"""
    try:
        base_url = "https://seia.sea.gob.cl"
        search_url = f"{base_url}/busqueda/buscarProyectoAction.php"
        
        # Configurar sesión
        session = requests.Session()
        session.headers.update({
            'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/91.0.4472.124 Safari/537.36'
        })
        
        # Datos del formulario
        search_data = {
            'nombre_empresa_o_titular': variacion,
            'submit_buscar': 'Buscar'
        }
        
        # Realizar búsqueda
        response = session.post(search_url, data=search_data, timeout=30)
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
        
        if proyectos_encontrados == 0:
            return None
        
        # Buscar tabla de resultados
        table = soup.find('table', class_='tabla_datos')
        if not table:
            # Buscar cualquier tabla con datos
            tables = soup.find_all('table')
            for t in tables:
                if len(t.find_all('tr')) > 1:  # Más de una fila (header + datos)
                    table = t
                    break
        
        if not table:
            return None
        
        # Extraer proyectos
        proyectos = _extraer_proyectos_mejorado(table, variacion, nombre_original, base_url)
        
        if not proyectos:
            return None
        
        # Calcular score de relevancia
        score = _calcular_score_relevancia(proyectos, nombre_original)
        
        return {
            'success': True,
            'variacion_usada': variacion,
            'proyectos': proyectos,
            'score_relevancia': score,
            'total_encontrados': proyectos_encontrados
        }
        
    except Exception as e:
        logger.warning(f"Error buscando con variación '{variacion}': {e}")
        return None

def _extraer_proyectos_mejorado(table, variacion: str, nombre_original: str, base_url: str) -> List[Dict]:
    """Extrae proyectos de la tabla con información mejorada"""
    proyectos = []
    
    try:
        rows = table.find_all('tr')
        if len(rows) < 2:
            return proyectos
        
        # Analizar header para mapear columnas
        header_row = rows[0]
        headers = [th.get_text(strip=True) for th in header_row.find_all(['th', 'td'])]
        
        # Mapear índices de columnas
        col_map = {}
        for i, header in enumerate(headers):
            header_lower = header.lower()
            if 'nombre' in header_lower:
                col_map['nombre'] = i
            elif 'tipo' in header_lower or 'tipología' in header_lower:
                col_map['tipo'] = i
            elif 'región' in header_lower or 'region' in header_lower:
                col_map['region'] = i
            elif 'titular' in header_lower:
                col_map['titular'] = i
            elif 'estado' in header_lower:
                col_map['estado'] = i
            elif 'fecha' in header_lower:
                col_map['fecha'] = i
            elif 'inversión' in header_lower or 'inversion' in header_lower:
                col_map['inversion'] = i
        
        # Procesar filas de datos
        for row in rows[1:]:
            cols = row.find_all(['td', 'th'])
            
            if len(cols) < 3:
                continue
            
            proyecto = {}
            
            # Extraer datos según mapeo
            for campo, indice in col_map.items():
                if indice < len(cols):
                    texto = cols[indice].get_text(strip=True)
                    proyecto[campo] = texto
                    
                    # Buscar link en la columna de nombre
                    if campo == 'nombre':
                        link = cols[indice].find('a', href=True)
                        if link:
                            href = link['href']
                            if href.startswith('/'):
                                proyecto['link_expediente'] = f"{base_url}{href}"
                            elif href.startswith('http'):
                                proyecto['link_expediente'] = href
                            else:
                                proyecto['link_expediente'] = f"{base_url}/{href}"
            
            # Validar proyecto
            if proyecto.get('nombre') and len(proyecto['nombre']) > 5:
                proyecto['variacion_encontrada'] = variacion
                proyecto['empresa_buscada'] = nombre_original
                
                # Calcular relevancia específica del proyecto
                proyecto['relevancia_proyecto'] = _calcular_relevancia_proyecto(proyecto, nombre_original)
                
                proyectos.append(proyecto)
            
            # Limitar a 10 proyectos por búsqueda
            if len(proyectos) >= 10:
                break
        
        return proyectos
        
    except Exception as e:
        logger.error(f"Error extrayendo proyectos: {e}")
        return []

def _calcular_relevancia_proyecto(proyecto: Dict, nombre_original: str) -> float:
    """Calcula la relevancia de un proyecto específico"""
    score = 0.0
    
    nombre_proyecto = proyecto.get('nombre', '').lower()
    titular = proyecto.get('titular', '').lower()
    nombre_busqueda = nombre_original.lower()
    
    # Relevancia por titular
    if nombre_busqueda in titular:
        score += 3.0
    elif any(palabra in titular for palabra in nombre_busqueda.split()):
        score += 2.0
    
    # Relevancia por nombre del proyecto
    if nombre_busqueda in nombre_proyecto:
        score += 1.5
    elif any(palabra in nombre_proyecto for palabra in nombre_busqueda.split()):
        score += 1.0
    
    # Bonus por estado del proyecto
    estado = proyecto.get('estado', '').lower()
    if estado in ['aprobado', 'en evaluación', 'calificado favorablemente']:
        score += 0.5
    
    return score

def _calcular_score_relevancia(proyectos: List[Dict], nombre_original: str) -> float:
    """Calcula el score de relevancia general de los resultados"""
    if not proyectos:
        return 0.0
    
    # Score basado en la relevancia promedio de los proyectos
    scores_individuales = [p.get('relevancia_proyecto', 0) for p in proyectos]
    score_promedio = sum(scores_individuales) / len(scores_individuales)
    
    # Bonus por cantidad de proyectos relevantes
    proyectos_relevantes = [p for p in proyectos if p.get('relevancia_proyecto', 0) > 1.0]
    bonus_cantidad = min(len(proyectos_relevantes) * 0.2, 1.0)
    
    return score_promedio + bonus_cantidad

def _procesar_mejor_resultado(resultado: Dict, nombre_empresa: str) -> Dict:
    """Procesa el mejor resultado obtenido"""
    try:
        proyectos = resultado.get('proyectos', [])
        
        if not proyectos:
            return {
                'success': False,
                'error': 'No hay proyectos en el resultado'
            }
        
        # Ordenar proyectos por relevancia
        proyectos_ordenados = sorted(proyectos, key=lambda x: x.get('relevancia_proyecto', 0), reverse=True)
        
        # Seleccionar el proyecto más relevante
        proyecto_principal = proyectos_ordenados[0]
        
        # Obtener detalles adicionales del proyecto principal
        proyecto_detallado = _obtener_detalles_proyecto(proyecto_principal)
        
        # Verificar si hay múltiples proyectos relevantes para selección
        proyectos_relevantes = [p for p in proyectos_ordenados if p.get('relevancia_proyecto', 0) > 1.0]
        
        if len(proyectos_relevantes) > 1:
            # Múltiples proyectos relevantes - requiere selección
            return {
                'success': True,
                'requiere_seleccion': True,
                'lista_proyectos': [{
                    'id_proyecto': i,
                    'nombre': p.get('nombre', 'Sin nombre'),
                    'titular': p.get('titular', 'Sin titular'),
                    'region': p.get('region', 'Sin región'),
                    'estado': p.get('estado', 'Sin estado'),
                    'tipo': p.get('tipo', 'Sin tipo'),
                    'inversion': p.get('inversion', 'No especificada'),
                    'score_relevancia': p.get('relevancia_proyecto', 0),
                    'link_expediente': p.get('link_expediente', '')
                } for i, p in enumerate(proyectos_relevantes)],
                'stats': {
                    'total_encontrados': resultado.get('total_encontrados', 0),
                    'proyectos_relevantes': len(proyectos_relevantes),
                    'variacion_usada': resultado.get('variacion_usada', ''),
                    'score_general': resultado.get('score_relevancia', 0)
                }
            }
        else:
            # Un solo proyecto relevante - información directa
            return {
                'success': True,
                'data': proyecto_detallado,
                'modo': 'proyecto_unico',
                'stats': {
                    'total_encontrados': resultado.get('total_encontrados', 0),
                    'variacion_usada': resultado.get('variacion_usada', ''),
                    'score_relevancia': proyecto_principal.get('relevancia_proyecto', 0)
                }
            }
            
    except Exception as e:
        logger.error(f"Error procesando mejor resultado: {e}")
        return {
            'success': False,
            'error': f'Error procesando resultado: {str(e)}'
        }

def _obtener_detalles_proyecto(proyecto: Dict) -> Dict:
    """Obtiene detalles adicionales de un proyecto específico"""
    try:
        link_expediente = proyecto.get('link_expediente')
        
        if not link_expediente:
            # Información básica sin detalles adicionales
            return _formatear_proyecto_basico(proyecto)
        
        logger.info(f"🔍 Obteniendo detalles de: {link_expediente}")
        
        # Configurar sesión para detalles
        session = requests.Session()
        session.headers.update({
            'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36'
        })
        
        # Obtener página de detalles
        response = session.get(link_expediente, timeout=20)
        response.raise_for_status()
        
        soup = BeautifulSoup(response.content, 'html.parser')
        
        # Extraer información detallada
        detalles = _extraer_detalles_expediente(soup)
        
        # Combinar información básica con detalles
        proyecto_completo = _formatear_proyecto_completo(proyecto, detalles)
        
        return proyecto_completo
        
    except Exception as e:
        logger.warning(f"No se pudieron obtener detalles adicionales: {e}")
        return _formatear_proyecto_basico(proyecto)

def _extraer_detalles_expediente(soup: BeautifulSoup) -> Dict:
    """Extrae detalles específicos de la página del expediente"""
    detalles = {
        'titular': {},
        'ubicacion': {},
        'proyecto': {}
    }
    
    try:
        # Buscar tablas con información
        for table in soup.find_all('table'):
            rows = table.find_all('tr')
            for row in rows:
                cols = row.find_all(['td', 'th'])
                if len(cols) >= 2:
                    key = cols[0].get_text(strip=True).lower()
                    value = cols[1].get_text(strip=True)
                    
                    # Información del titular
                    if 'razón social' in key or 'razon social' in key:
                        detalles['titular']['razon_social'] = value
                    elif 'rut' in key and 'titular' in key:
                        detalles['titular']['rut'] = value
                    elif 'dirección' in key and ('titular' in key or 'empresa' in key):
                        detalles['titular']['direccion'] = value
                    elif 'teléfono' in key or 'telefono' in key:
                        detalles['titular']['telefono'] = value
                    elif 'email' in key or 'correo' in key:
                        detalles['titular']['email'] = value
                    
                    # Información de ubicación
                    elif 'dirección' in key and 'proyecto' in key:
                        detalles['ubicacion']['direccion_proyecto'] = value
                    elif 'comuna' in key:
                        detalles['ubicacion']['comuna'] = value
                    elif 'provincia' in key:
                        detalles['ubicacion']['provincia'] = value
                    elif 'coordenadas' in key:
                        detalles['ubicacion']['coordenadas'] = value
                    
                    # Información del proyecto
                    elif 'inversión' in key or 'inversion' in key:
                        detalles['proyecto']['inversion'] = value
                    elif 'superficie' in key:
                        detalles['proyecto']['superficie'] = value
        
        # Buscar patrones en texto libre
        text_content = soup.get_text()
        
        # Buscar coordenadas geográficas
        coord_patterns = [
            r'(-?\d{1,2}[.,]\d+)\s*[°]?\s*[SN]?\s*[,;]\s*(-?\d{1,3}[.,]\d+)\s*[°]?\s*[WO]?',
            r'UTM[:\s]*(\d+)\s*[,;]\s*(\d+)',
            r'Latitud[:\s]*(-?\d{1,2}[.,]\d+).*?Longitud[:\s]*(-?\d{1,3}[.,]\d+)'
        ]
        
        for pattern in coord_patterns:
            match = re.search(pattern, text_content, re.IGNORECASE)
            if match:
                detalles['ubicacion']['coordenadas'] = f"{match.group(1)}, {match.group(2)}"
                break
        
        # Buscar direcciones específicas
        direccion_match = re.search(r'(?:Dirección|Ubicación)[:\s]+([^\.]+(?:comuna|región|Chile)[^\.]*)', text_content, re.IGNORECASE)
        if direccion_match:
            direccion = direccion_match.group(1).strip()
            if len(direccion) > 10 and 'dirección ejecutiva' not in direccion.lower():
                detalles['ubicacion']['direccion_detallada'] = direccion
        
        return detalles
        
    except Exception as e:
        logger.warning(f"Error extrayendo detalles del expediente: {e}")
        return detalles

def _formatear_proyecto_completo(proyecto_basico: Dict, detalles: Dict) -> Dict:
    """Formatea un proyecto con información completa"""
    titular_info = detalles.get('titular', {})
    ubicacion_info = detalles.get('ubicacion', {})
    proyecto_info = detalles.get('proyecto', {})
    
    return {
        'codigo_expediente': proyecto_basico.get('link_expediente', '').split('=')[-1] if proyecto_basico.get('link_expediente') else 'N/A',
        'nombre': proyecto_basico.get('nombre', ''),
        'estado': proyecto_basico.get('estado', ''),
        'region': proyecto_basico.get('region', ''),
        'tipo': proyecto_basico.get('tipo', ''),
        'fecha_presentacion': proyecto_basico.get('fecha', ''),
        'inversion': proyecto_info.get('inversion') or proyecto_basico.get('inversion', ''),
        'link_expediente': proyecto_basico.get('link_expediente', ''),
        'titular': {
            'nombre': proyecto_basico.get('titular', proyecto_basico.get('empresa_buscada', '')),
            'nombre_fantasia': proyecto_basico.get('titular', proyecto_basico.get('empresa_buscada', '')),
            'razon_social': titular_info.get('razon_social', ''),
            'rut': titular_info.get('rut', ''),
            'direccion': titular_info.get('direccion', ''),
            'telefono': titular_info.get('telefono', ''),
            'email': titular_info.get('email', '')
        },
        'ubicacion': {
            'region': proyecto_basico.get('region', ''),
            'ubicacion_proyecto': ubicacion_info.get('direccion_detallada') or ubicacion_info.get('direccion_proyecto') or proyecto_basico.get('region', ''),
            'comuna': ubicacion_info.get('comuna', ''),
            'provincia': ubicacion_info.get('provincia', ''),
            'coordenadas': ubicacion_info.get('coordenadas', ''),
            'direccion': ubicacion_info.get('direccion_detallada', ''),
            'fuente': 'SEIA - Detalles del expediente'
        },
        'relevancia': proyecto_basico.get('relevancia_proyecto', 0),
        'fuente': 'SEIA Mejorado'
    }

def _formatear_proyecto_basico(proyecto: Dict) -> Dict:
    """Formatea un proyecto con información básica"""
    return {
        'codigo_expediente': proyecto.get('link_expediente', '').split('=')[-1] if proyecto.get('link_expediente') else 'N/A',
        'nombre': proyecto.get('nombre', ''),
        'estado': proyecto.get('estado', ''),
        'region': proyecto.get('region', ''),
        'tipo': proyecto.get('tipo', ''),
        'fecha_presentacion': proyecto.get('fecha', ''),
        'inversion': proyecto.get('inversion', ''),
        'link_expediente': proyecto.get('link_expediente', ''),
        'titular': {
            'nombre': proyecto.get('titular', proyecto.get('empresa_buscada', '')),
            'nombre_fantasia': proyecto.get('titular', proyecto.get('empresa_buscada', '')),
            'razon_social': '',
            'rut': '',
            'direccion': '',
            'telefono': '',
            'email': ''
        },
        'ubicacion': {
            'region': proyecto.get('region', ''),
            'ubicacion_proyecto': proyecto.get('region', ''),
            'comuna': '',
            'provincia': '',
            'coordenadas': '',
            'fuente': 'SEIA - Información básica'
        },
        'relevancia': proyecto.get('relevancia_proyecto', 0),
        'fuente': 'SEIA Básico'
    }

# Test de funcionamiento
if __name__ == "__main__":
    # Test básico
    empresas_test = ['Codelco', 'Candelaria', 'Escondida']
    
    for empresa in empresas_test:
        print(f"\n=== Test para: {empresa} ===")
        resultado = obtener_informacion_empresa_seia_mejorado(empresa)
        print(f"Success: {resultado.get('success')}")
        if resultado.get('success'):
            if resultado.get('requiere_seleccion'):
                print(f"Proyectos para selección: {len(resultado.get('lista_proyectos', []))}")
            else:
                data = resultado.get('data', {})
                print(f"Proyecto: {data.get('nombre', 'N/A')}")
                print(f"Ubicación: {data.get('ubicacion', {}).get('ubicacion_proyecto', 'N/A')}")
        else:
            print(f"Error: {resultado.get('error')}") 