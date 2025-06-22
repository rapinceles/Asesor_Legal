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
        # Método 1: Scraper MEJORADO (NUEVO - búsqueda específica y ubicaciones reales)
        try:
            from scrapers.seia_mejorado import obtener_informacion_empresa_seia_mejorado
            result = obtener_informacion_empresa_seia_mejorado(nombre_empresa)
            if result and result.get('success'):
                logger.info("✅ Información obtenida con scraper MEJORADO")
                return result
        except Exception as e:
            logger.warning(f"Scraper mejorado falló: {e}")
        
        # Método 2: Scraper por titular (búsqueda específica por titular)
        try:
            from scrapers.seia_titular import buscar_proyectos_por_titular
            result = buscar_proyectos_por_titular(nombre_empresa)
            if result and result.get('success'):
                logger.info("✅ Información obtenida con scraper POR TITULAR")
                # Adaptar formato para compatibilidad con el sistema
                if result.get('data'):
                    data = result['data']
                    proyecto_principal = data.get('proyecto_principal', {})
                    lista_proyectos = data.get('lista_proyectos', [])
                    
                    # Estructurar datos del proyecto principal para compatibilidad
                    formatted_data = {
                        'codigo_expediente': proyecto_principal.get('link_expediente', '').split('=')[-1] if proyecto_principal.get('link_expediente') else 'N/A',
                        'nombre': proyecto_principal.get('nombre', ''),
                        'estado': proyecto_principal.get('estado', ''),
                        'region': proyecto_principal.get('region', ''),
                        'tipo': proyecto_principal.get('tipo', ''),
                        'fecha_presentacion': proyecto_principal.get('fecha', ''),
                        'inversion': proyecto_principal.get('inversion', ''),
                        'link_expediente': proyecto_principal.get('link_expediente', ''),
                        'titular': {
                            'nombre': proyecto_principal.get('titular', nombre_empresa),
                            'nombre_fantasia': proyecto_principal.get('titular', nombre_empresa),
                            'razon_social': proyecto_principal.get('razon_social_completa', ''),
                            'rut': proyecto_principal.get('rut', ''),
                            'direccion': proyecto_principal.get('direccion_titular', ''),
                            'telefono': proyecto_principal.get('telefono', ''),
                            'email': proyecto_principal.get('email', '')
                        },
                        'ubicacion': {
                            'region': proyecto_principal.get('region', ''),
                            'ubicacion_proyecto': proyecto_principal.get('ubicacion_detallada', proyecto_principal.get('region', '')),
                            'comuna': proyecto_principal.get('comuna', ''),
                            'provincia': proyecto_principal.get('provincia', ''),
                            'coordenadas': ''
                        }
                    }
                    
                    return {
                        'success': True,
                        'data': formatted_data,
                        'modo': 'titular',
                        'lista_proyectos': lista_proyectos,  # Lista completa para selección
                        'stats': {
                            'titular_buscado': data.get('titular_buscado', nombre_empresa),
                            'proyectos_encontrados': data.get('proyectos_encontrados', 0),
                            'total_encontrados': result.get('total_encontrados', 0),
                            'variaciones_usadas': result.get('variaciones_usadas', [])
                        }
                    }
                return result
        except Exception as e:
            logger.warning(f"Scraper por titular falló: {e}")
        
        # Método 3: Scraper corregido (anterior)
        try:
            from scrapers.seia_correcto import obtener_informacion_empresa_seia_correcto
            result = obtener_informacion_empresa_seia_correcto(nombre_empresa)
            if result and result.get('success'):
                logger.info("✅ Información obtenida con scraper CORREGIDO")
                # Adaptar formato para compatibilidad
                if result.get('data'):
                    data = result['data']
                    # Estructurar datos para compatibilidad con el sistema
                    formatted_data = {
                        'codigo_expediente': data.get('link_expediente', '').split('=')[-1] if data.get('link_expediente') else 'N/A',
                        'nombre': data.get('nombre', ''),
                        'estado': data.get('estado', ''),
                        'region': data.get('region', ''),
                        'tipo': data.get('tipo', ''),
                        'fecha_presentacion': data.get('fecha', ''),
                        'inversion': data.get('inversion', ''),
                        'link_expediente': data.get('link_expediente', ''),
                        'titular': {
                            'nombre': data.get('titular', nombre_empresa),
                            'nombre_fantasia': data.get('titular', nombre_empresa),
                            'razon_social': data.get('titular_detallado', {}).get('razon_social', ''),
                            'rut': data.get('titular_detallado', {}).get('rut', ''),
                            'direccion': data.get('titular_detallado', {}).get('direccion', ''),
                            'telefono': data.get('titular_detallado', {}).get('telefono', ''),
                            'email': data.get('titular_detallado', {}).get('email', '')
                        },
                        'ubicacion': {
                            'region': data.get('region', ''),
                            'ubicacion_proyecto': data.get('ubicacion_detallada', {}).get('ubicacion_proyecto', data.get('region', '')),
                            'comuna': data.get('ubicacion_detallada', {}).get('comuna', ''),
                            'provincia': data.get('ubicacion_detallada', {}).get('provincia', ''),
                            'coordenadas': ''
                        }
                    }
                    return {
                        'success': True,
                        'data': formatted_data,
                        'modo': 'correcto',
                        'stats': {
                            'total_encontrados': result.get('total_encontrados', 0),
                            'proyectos_extraidos': result.get('proyectos_extraidos', 0),
                            'proyectos_filtrados': result.get('proyectos_filtrados', 0)
                        }
                    }
                return result
        except Exception as e:
            logger.warning(f"Scraper corregido falló: {e}")
        
        # Método 4: Scraper real (anterior)
        try:
            from scrapers.seia_real import obtener_informacion_proyecto_seia_real
            result = obtener_informacion_proyecto_seia_real(nombre_empresa)
            if result and result.get('success'):
                logger.info("✅ Información obtenida con scraper real")
                return result
        except Exception as e:
            logger.warning(f"Scraper real falló: {e}")
        
        # Método 5: Scraper completo
        try:
            from scrapers.seia_project_detail_scraper import obtener_informacion_proyecto_seia
            result = obtener_informacion_proyecto_seia(nombre_empresa)
            if result and result.get('success'):
                logger.info("Información obtenida con scraper completo")
                return result
        except Exception as e:
            logger.warning(f"Scraper completo falló: {e}")
        
        # Método 6: Scraper simple
        try:
            from scrapers.seia_simple import obtener_informacion_proyecto_seia_simple
            result = obtener_informacion_proyecto_seia_simple(nombre_empresa)
            if result and result.get('success'):
                logger.info("Información obtenida con scraper simple")
                return result
        except Exception as e:
            logger.warning(f"Scraper simple falló: {e}")
        
        # Método 7: Búsqueda directa básica
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
        
        # Método 8: Respuesta de error final
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