# scrapers/seia_project_detail_scraper.py
import requests
from bs4 import BeautifulSoup
import re
import time
from typing import Dict, Optional, List
from urllib.parse import urljoin, urlparse, parse_qs

class SEIAProjectDetailScraper:
    """
    Scraper para obtener detalles específicos de proyectos del SEIA
    incluyendo información completa de la empresa titular
    """
    
    def __init__(self):
        self.base_url = "https://seia.sea.gob.cl"
        self.session = requests.Session()
        self.session.headers.update({
            'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/91.0.4472.124 Safari/537.36'
        })
    
    def buscar_proyectos_por_empresa(self, nombre_empresa: str, limite: int = 10) -> List[Dict]:
        """
        Busca proyectos por nombre de empresa y retorna lista de proyectos básicos
        """
        url_busqueda = f"{self.base_url}/busqueda/buscarProyectoAction.php"
        
        payload = {
            "nombre_empresa_o_titular": nombre_empresa,
            "submit_buscar": "Buscar"
        }
        
        try:
            response = self.session.post(url_busqueda, data=payload, timeout=30)
            response.raise_for_status()
            
            soup = BeautifulSoup(response.content, 'html.parser')
            return self._extraer_proyectos_de_tabla(soup, limite)
            
        except Exception as e:
            print(f"Error al buscar proyectos: {e}")
            return []
    
    def _extraer_proyectos_de_tabla(self, soup: BeautifulSoup, limite: int) -> List[Dict]:
        """
        Extrae proyectos de la tabla de resultados
        """
        proyectos = []
        
        table = soup.find('table', class_='tabla_datos')
        if not table:
            return proyectos
        
        tbody = table.find('tbody')
        if not tbody:
            return proyectos
        
        rows = tbody.find_all('tr')[:limite]
        
        for row in rows:
            cols = row.find_all('td')
            if len(cols) >= 6:
                link_elem = cols[0].find('a', href=True)
                if link_elem:
                    proyecto = {
                        'nombre': cols[0].get_text(strip=True),
                        'region': cols[1].get_text(strip=True),
                        'tipo': cols[2].get_text(strip=True),
                        'fecha_presentacion': cols[3].get_text(strip=True),
                        'estado': cols[4].get_text(strip=True),
                        'codigo_expediente': cols[5].get_text(strip=True),
                        'link_expediente': urljoin(self.base_url, link_elem['href'])
                    }
                    proyectos.append(proyecto)
        
        return proyectos
    
    def obtener_detalles_proyecto(self, link_expediente: str) -> Dict:
        """
        Obtiene los detalles completos de un proyecto específico
        """
        try:
            response = self.session.get(link_expediente, timeout=30)
            response.raise_for_status()
            
            soup = BeautifulSoup(response.content, 'html.parser')
            
            detalles = {
                'informacion_basica': self._extraer_informacion_basica(soup),
                'titular': self._extraer_informacion_titular(soup),
                'ubicacion': self._extraer_ubicacion_proyecto(soup),
                'descripcion': self._extraer_descripcion_proyecto(soup),
                'documentos': self._extraer_documentos(soup)
            }
            
            return detalles
            
        except Exception as e:
            print(f"Error al obtener detalles del proyecto: {e}")
            return {}
    
    def _extraer_informacion_basica(self, soup: BeautifulSoup) -> Dict:
        """
        Extrae información básica del proyecto
        """
        info = {}
        
        # Buscar tabla de información básica
        for table in soup.find_all('table'):
            rows = table.find_all('tr')
            for row in rows:
                cols = row.find_all(['td', 'th'])
                if len(cols) >= 2:
                    key = cols[0].get_text(strip=True).lower()
                    value = cols[1].get_text(strip=True)
                    
                    if 'expediente' in key or 'código' in key:
                        info['codigo_expediente'] = value
                    elif 'nombre' in key and 'proyecto' in key:
                        info['nombre_proyecto'] = value
                    elif 'tipo' in key:
                        info['tipo_proyecto'] = value
                    elif 'estado' in key:
                        info['estado'] = value
                    elif 'región' in key or 'region' in key:
                        info['region'] = value
                    elif 'fecha' in key and 'presentación' in key:
                        info['fecha_presentacion'] = value
        
        return info
    
    def _extraer_informacion_titular(self, soup: BeautifulSoup) -> Dict:
        """
        Extrae información del titular del proyecto
        """
        titular = {}
        
        # Buscar información del titular
        for table in soup.find_all('table'):
            rows = table.find_all('tr')
            for row in rows:
                cols = row.find_all(['td', 'th'])
                if len(cols) >= 2:
                    key = cols[0].get_text(strip=True).lower()
                    value = cols[1].get_text(strip=True)
                    
                    if 'titular' in key or 'empresa' in key:
                        if 'razón social' in key or 'razon social' in key:
                            titular['razon_social'] = value
                        elif 'nombre' in key:
                            titular['nombre_fantasia'] = value
                        else:
                            titular['nombre'] = value
                    elif 'rut' in key and 'titular' in key:
                        titular['rut'] = value
                    elif 'dirección' in key or 'direccion' in key:
                        if 'titular' in key or 'empresa' in key:
                            titular['direccion'] = value
                    elif 'teléfono' in key or 'telefono' in key:
                        if 'titular' in key or 'empresa' in key:
                            titular['telefono'] = value
                    elif 'email' in key or 'correo' in key:
                        if 'titular' in key or 'empresa' in key:
                            titular['email'] = value
        
        # Buscar en texto libre si no se encontró en tablas
        if not titular:
            text_content = soup.get_text()
            
            # Patrones para buscar información
            patterns = {
                'rut': r'RUT[:\s]*(\d{1,2}\.?\d{3}\.?\d{3}[-\.]?[\dkK])',
                'telefono': r'(?:Tel[éefono]*|Teléfono)[:\s]*([+]?[\d\s\-\(\)]{7,15})',
                'email': r'([a-zA-Z0-9._%+-]+@[a-zA-Z0-9.-]+\.[a-zA-Z]{2,})'
            }
            
            for key, pattern in patterns.items():
                matches = re.findall(pattern, text_content, re.IGNORECASE)
                if matches:
                    titular[key] = matches[0]
        
        return titular
    
    def _extraer_ubicacion_proyecto(self, soup: BeautifulSoup) -> Dict:
        """
        Extrae información de ubicación del proyecto
        """
        ubicacion = {}
        
        # Buscar en tablas
        for table in soup.find_all('table'):
            rows = table.find_all('tr')
            for row in rows:
                cols = row.find_all(['td', 'th'])
                if len(cols) >= 2:
                    key = cols[0].get_text(strip=True).lower()
                    value = cols[1].get_text(strip=True)
                    
                    if 'ubicación' in key or 'ubicacion' in key:
                        ubicacion['ubicacion_proyecto'] = value
                    elif 'comuna' in key:
                        ubicacion['comuna'] = value
                    elif 'provincia' in key:
                        ubicacion['provincia'] = value
                    elif 'región' in key or 'region' in key:
                        ubicacion['region'] = value
                    elif 'coordenadas' in key:
                        ubicacion['coordenadas'] = value
                    elif 'dirección' in key and 'proyecto' in key:
                        ubicacion['direccion_proyecto'] = value
        
        return ubicacion
    
    def _extraer_descripcion_proyecto(self, soup: BeautifulSoup) -> str:
        """
        Extrae la descripción del proyecto
        """
        # Buscar descripción del proyecto
        descripcion_keywords = ['descripción', 'descripcion', 'resumen', 'objetivo']
        
        for keyword in descripcion_keywords:
            for table in soup.find_all('table'):
                rows = table.find_all('tr')
                for row in rows:
                    cols = row.find_all(['td', 'th'])
                    if len(cols) >= 2:
                        key = cols[0].get_text(strip=True).lower()
                        if keyword in key:
                            return cols[1].get_text(strip=True)
        
        return ""
    
    def _extraer_documentos(self, soup: BeautifulSoup) -> List[Dict]:
        """
        Extrae links a documentos relacionados
        """
        documentos = []
        
        # Buscar enlaces a documentos
        for link in soup.find_all('a', href=True):
            href = link['href']
            text = link.get_text(strip=True)
            
            if any(ext in href.lower() for ext in ['.pdf', '.doc', '.docx', '.xls', '.xlsx']):
                documentos.append({
                    'nombre': text,
                    'url': urljoin(self.base_url, href)
                })
        
        return documentos
    
    def buscar_proyecto_con_detalles(self, nombre_empresa: str, nombre_proyecto: str = None) -> Optional[Dict]:
        """
        Busca un proyecto específico y obtiene sus detalles completos
        """
        # Buscar proyectos de la empresa
        proyectos = self.buscar_proyectos_por_empresa(nombre_empresa, limite=50)
        
        if not proyectos:
            return None
        
        # Si se especifica un proyecto, buscar el más similar
        if nombre_proyecto:
            proyecto_seleccionado = None
            mejor_coincidencia = 0
            
            for proyecto in proyectos:
                coincidencia = self._calcular_similitud(proyecto['nombre'], nombre_proyecto)
                if coincidencia > mejor_coincidencia:
                    mejor_coincidencia = coincidencia
                    proyecto_seleccionado = proyecto
            
            if mejor_coincidencia < 0.3:  # Umbral mínimo de similitud
                proyecto_seleccionado = proyectos[0]  # Tomar el primero si no hay buena coincidencia
        else:
            # Tomar el proyecto más reciente o el primero
            proyecto_seleccionado = proyectos[0]
        
        if proyecto_seleccionado:
            # Obtener detalles completos
            detalles = self.obtener_detalles_proyecto(proyecto_seleccionado['link_expediente'])
            
            # Combinar información básica con detalles
            resultado = {**proyecto_seleccionado, **detalles}
            
            return resultado
        
        return None
    
    def _calcular_similitud(self, texto1: str, texto2: str) -> float:
        """
        Calcula la similitud entre dos textos (simple)
        """
        texto1 = texto1.lower().strip()
        texto2 = texto2.lower().strip()
        
        if texto1 == texto2:
            return 1.0
        
        if texto2 in texto1 or texto1 in texto2:
            return 0.8
        
        # Similitud basada en palabras comunes
        palabras1 = set(texto1.split())
        palabras2 = set(texto2.split())
        
        interseccion = palabras1.intersection(palabras2)
        union = palabras1.union(palabras2)
        
        if len(union) == 0:
            return 0.0
        
        return len(interseccion) / len(union)

# Función de conveniencia para usar desde el main
def obtener_informacion_proyecto_seia(nombre_empresa: str, nombre_proyecto: str = None) -> Dict:
    """
    Función principal para obtener información completa de un proyecto del SEIA
    """
    scraper = SEIAProjectDetailScraper()
    
    try:
        resultado = scraper.buscar_proyecto_con_detalles(nombre_empresa, nombre_proyecto)
        
        if resultado:
            return {
                'success': True,
                'data': resultado
            }
        else:
            return {
                'success': False,
                'error': f'No se encontraron proyectos para la empresa: {nombre_empresa}'
            }
    except Exception as e:
        return {
            'success': False,
            'error': f'Error al obtener información del SEIA: {str(e)}'
        } 