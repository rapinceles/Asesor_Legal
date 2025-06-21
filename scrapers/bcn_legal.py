"""
Scraper para consultas legales en BCN (Biblioteca del Congreso Nacional)
URL: https://www.bcn.cl/leychile/consulta/listado_n_sel?agr=2
"""

import requests
from bs4 import BeautifulSoup
import logging
import time
from urllib.parse import urljoin, quote
import re
from typing import Dict, List, Optional, Any

# Configurar logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

class BCNScraper:
    def __init__(self):
        self.base_url = "https://www.bcn.cl"
        self.search_url = "https://www.bcn.cl/leychile/consulta/listado_n_sel"
        self.session = requests.Session()
        self.session.headers.update({
            'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/91.0.4472.124 Safari/537.36',
            'Accept': 'text/html,application/xhtml+xml,application/xml;q=0.9,image/webp,*/*;q=0.8',
            'Accept-Language': 'es-ES,es;q=0.8,en-US;q=0.5,en;q=0.3',
            'Accept-Encoding': 'gzip, deflate',
            'Connection': 'keep-alive',
            'Upgrade-Insecure-Requests': '1',
        })

    def buscar_normativa(self, termino_busqueda: str, tipo_norma: str = "all") -> Dict[str, Any]:
        """
        Busca normativa legal en BCN
        
        Args:
            termino_busqueda: Término a buscar
            tipo_norma: Tipo de norma (ley, decreto, reglamento, etc.)
        
        Returns:
            Diccionario con resultados de la búsqueda
        """
        try:
            logger.info(f"🔍 Buscando normativa en BCN: {termino_busqueda}")
            
            # Parámetros de búsqueda
            params = {
                'agr': '2',  # Búsqueda avanzada
                'q': termino_busqueda,
                'tipo': tipo_norma
            }
            
            # Realizar búsqueda
            response = self.session.get(self.search_url, params=params, timeout=30)
            response.raise_for_status()
            
            logger.info(f"✅ Respuesta recibida: {response.status_code}")
            
            # Parsear contenido
            soup = BeautifulSoup(response.content, 'html.parser')
            
            # Buscar resultados
            resultados = self._extraer_resultados(soup, termino_busqueda)
            
            if not resultados:
                # Intentar búsqueda más amplia
                logger.info("🔄 Intentando búsqueda más amplia...")
                resultados = self._busqueda_amplia(termino_busqueda)
            
            return {
                'success': True,
                'termino_busqueda': termino_busqueda,
                'total_resultados': len(resultados),
                'resultados': resultados,
                'fuente': 'BCN - Biblioteca del Congreso Nacional'
            }
            
        except Exception as e:
            logger.error(f"❌ Error en búsqueda BCN: {e}")
            return {
                'success': False,
                'error': str(e),
                'resultados': []
            }

    def _extraer_resultados(self, soup: BeautifulSoup, termino: str) -> List[Dict]:
        """Extrae los resultados de la página de búsqueda"""
        resultados = []
        
        try:
            # Buscar diferentes selectores posibles
            selectores_posibles = [
                '.resultado-busqueda',
                '.listado-leyes',
                '.resultado',
                'table.tabla-resultados tr',
                '.ley-item',
                'div[class*="resultado"]',
                'li[class*="ley"]'
            ]
            
            items_encontrados = []
            for selector in selectores_posibles:
                items = soup.select(selector)
                if items:
                    logger.info(f"✅ Encontrados {len(items)} items con selector: {selector}")
                    items_encontrados = items
                    break
            
            if not items_encontrados:
                # Buscar enlaces que contengan "ley" o números de ley
                links = soup.find_all('a', href=True)
                for link in links:
                    href = link.get('href', '')
                    texto = link.get_text(strip=True)
                    
                    if any(palabra in texto.lower() for palabra in ['ley', 'decreto', 'reglamento', 'código']) and len(texto) > 10:
                        items_encontrados.append(link)
                
                logger.info(f"✅ Encontrados {len(items_encontrados)} enlaces legales")
            
            # Procesar items encontrados
            for i, item in enumerate(items_encontrados[:10]):  # Limitar a 10 resultados
                resultado = self._procesar_item_legal(item, i + 1)
                if resultado:
                    resultados.append(resultado)
            
            logger.info(f"📄 Total resultados procesados: {len(resultados)}")
            
        except Exception as e:
            logger.error(f"❌ Error extrayendo resultados: {e}")
        
        return resultados

    def _procesar_item_legal(self, item, numero: int) -> Optional[Dict]:
        """Procesa un item legal individual"""
        try:
            # Extraer información básica
            if item.name == 'a':
                titulo = item.get_text(strip=True)
                enlace = item.get('href', '')
                descripcion = ""
            else:
                # Buscar título
                titulo_elem = item.find(['h3', 'h4', 'h5', 'strong', 'b']) or item.find('a')
                titulo = titulo_elem.get_text(strip=True) if titulo_elem else item.get_text(strip=True)[:100]
                
                # Buscar enlace
                enlace_elem = item.find('a', href=True)
                enlace = enlace_elem.get('href', '') if enlace_elem else ''
                
                # Buscar descripción
                descripcion = item.get_text(strip=True)
            
            # Completar URL si es relativa
            if enlace and not enlace.startswith('http'):
                enlace = urljoin(self.base_url, enlace)
            
            # Extraer número de ley si existe
            numero_ley = self._extraer_numero_ley(titulo)
            
            # Determinar tipo de norma
            tipo_norma = self._determinar_tipo_norma(titulo)
            
            return {
                'numero': numero,
                'titulo': titulo[:200],  # Limitar título
                'descripcion': descripcion[:300] if descripcion != titulo else "",  # Limitar descripción
                'enlace': enlace,
                'numero_ley': numero_ley,
                'tipo_norma': tipo_norma,
                'relevancia': self._calcular_relevancia(titulo, descripcion)
            }
            
        except Exception as e:
            logger.error(f"❌ Error procesando item legal: {e}")
            return None

    def _extraer_numero_ley(self, texto: str) -> str:
        """Extrae el número de ley del texto"""
        # Buscar patrones como "Ley 19.300", "Decreto 40", etc.
        patrones = [
            r'Ley\s+N?°?\s*(\d+[\.\-]?\d*)',
            r'Decreto\s+N?°?\s*(\d+[\.\-]?\d*)',
            r'N°\s*(\d+[\.\-]?\d*)',
            r'(\d+[\.\-]?\d*)'
        ]
        
        for patron in patrones:
            match = re.search(patron, texto, re.IGNORECASE)
            if match:
                return match.group(1)
        
        return ""

    def _determinar_tipo_norma(self, titulo: str) -> str:
        """Determina el tipo de norma basado en el título"""
        titulo_lower = titulo.lower()
        
        if 'ley' in titulo_lower:
            return 'Ley'
        elif 'decreto' in titulo_lower:
            return 'Decreto'
        elif 'reglamento' in titulo_lower:
            return 'Reglamento'
        elif 'código' in titulo_lower:
            return 'Código'
        elif 'resolución' in titulo_lower:
            return 'Resolución'
        elif 'circular' in titulo_lower:
            return 'Circular'
        else:
            return 'Norma'

    def _calcular_relevancia(self, titulo: str, descripcion: str) -> float:
        """Calcula un score de relevancia básico"""
        score = 0.0
        
        # Palabras clave importantes
        palabras_importantes = [
            'ambiental', 'medio ambiente', 'evaluación', 'impacto',
            'seia', 'rca', 'dia', 'eia', 'superintendencia',
            'sma', 'sea', 'conama', 'minería', 'forestal'
        ]
        
        texto_completo = (titulo + " " + descripcion).lower()
        
        for palabra in palabras_importantes:
            if palabra in texto_completo:
                score += 1.0
        
        # Bonus por longitud del título (más específico)
        if len(titulo) > 50:
            score += 0.5
        
        return min(score, 5.0)  # Máximo 5.0

    def _busqueda_amplia(self, termino: str) -> List[Dict]:
        """Realiza una búsqueda más amplia si no se encuentran resultados"""
        try:
            # Términos relacionados comunes
            terminos_relacionados = [
                f"{termino} ambiental",
                f"ley {termino}",
                f"decreto {termino}",
                f"reglamento {termino}"
            ]
            
            todos_resultados = []
            
            for termino_relacionado in terminos_relacionados:
                logger.info(f"🔄 Buscando: {termino_relacionado}")
                
                params = {
                    'agr': '2',
                    'q': termino_relacionado
                }
                
                response = self.session.get(self.search_url, params=params, timeout=20)
                if response.status_code == 200:
                    soup = BeautifulSoup(response.content, 'html.parser')
                    resultados = self._extraer_resultados(soup, termino_relacionado)
                    todos_resultados.extend(resultados)
                
                time.sleep(1)  # Pausa entre búsquedas
            
            # Eliminar duplicados y ordenar por relevancia
            resultados_unicos = []
            enlaces_vistos = set()
            
            for resultado in todos_resultados:
                enlace = resultado.get('enlace', '')
                if enlace and enlace not in enlaces_vistos:
                    enlaces_vistos.add(enlace)
                    resultados_unicos.append(resultado)
            
            # Ordenar por relevancia
            resultados_unicos.sort(key=lambda x: x.get('relevancia', 0), reverse=True)
            
            return resultados_unicos[:10]  # Máximo 10 resultados
            
        except Exception as e:
            logger.error(f"❌ Error en búsqueda amplia: {e}")
            return []

    def obtener_detalle_norma(self, enlace: str) -> Dict[str, Any]:
        """Obtiene el detalle de una norma específica"""
        try:
            logger.info(f"🔍 Obteniendo detalle de: {enlace}")
            
            response = self.session.get(enlace, timeout=30)
            response.raise_for_status()
            
            soup = BeautifulSoup(response.content, 'html.parser')
            
            # Extraer información detallada
            detalle = {
                'titulo_completo': self._extraer_titulo_completo(soup),
                'fecha_publicacion': self._extraer_fecha(soup),
                'organismo': self._extraer_organismo(soup),
                'estado': self._extraer_estado(soup),
                'materias': self._extraer_materias(soup),
                'articulos_relevantes': self._extraer_articulos(soup),
                'enlace': enlace
            }
            
            logger.info("✅ Detalle obtenido exitosamente")
            return detalle
            
        except Exception as e:
            logger.error(f"❌ Error obteniendo detalle: {e}")
            return {'error': str(e)}

    def _extraer_titulo_completo(self, soup: BeautifulSoup) -> str:
        """Extrae el título completo de la norma"""
        selectores = ['h1', '.titulo-norma', '.titulo-ley', 'title']
        for selector in selectores:
            elem = soup.select_one(selector)
            if elem:
                return elem.get_text(strip=True)
        return ""

    def _extraer_fecha(self, soup: BeautifulSoup) -> str:
        """Extrae la fecha de publicación"""
        # Buscar patrones de fecha
        texto = soup.get_text()
        patron_fecha = r'\d{1,2}[\-/]\d{1,2}[\-/]\d{4}'
        match = re.search(patron_fecha, texto)
        return match.group(0) if match else ""

    def _extraer_organismo(self, soup: BeautifulSoup) -> str:
        """Extrae el organismo emisor"""
        selectores = ['.organismo', '.ministerio', '.servicio']
        for selector in selectores:
            elem = soup.select_one(selector)
            if elem:
                return elem.get_text(strip=True)
        return ""

    def _extraer_estado(self, soup: BeautifulSoup) -> str:
        """Extrae el estado de la norma"""
        texto = soup.get_text().lower()
        if 'derogad' in texto:
            return 'Derogada'
        elif 'vigente' in texto:
            return 'Vigente'
        elif 'modificad' in texto:
            return 'Modificada'
        return 'Desconocido'

    def _extraer_materias(self, soup: BeautifulSoup) -> List[str]:
        """Extrae las materias relacionadas"""
        materias = []
        selectores = ['.materia', '.tema', '.categoria']
        for selector in selectores:
            elems = soup.select(selector)
            for elem in elems:
                texto = elem.get_text(strip=True)
                if texto and len(texto) > 3:
                    materias.append(texto)
        return materias[:5]  # Máximo 5 materias

    def _extraer_articulos(self, soup: BeautifulSoup) -> List[str]:
        """Extrae artículos relevantes"""
        articulos = []
        # Buscar elementos que contengan "artículo"
        for elem in soup.find_all(text=re.compile(r'art[íi]culo', re.IGNORECASE)):
            parent = elem.parent
            if parent:
                texto = parent.get_text(strip=True)
                if len(texto) > 50 and len(texto) < 500:
                    articulos.append(texto)
        return articulos[:3]  # Máximo 3 artículos


# Función principal para usar el scraper
def buscar_normativa_bcn(termino_busqueda: str, tipo_norma: str = "all") -> Dict[str, Any]:
    """
    Función principal para buscar normativa en BCN
    
    Args:
        termino_busqueda: Término a buscar
        tipo_norma: Tipo de norma
    
    Returns:
        Diccionario con resultados
    """
    scraper = BCNScraper()
    return scraper.buscar_normativa(termino_busqueda, tipo_norma)


def obtener_detalle_norma_bcn(enlace: str) -> Dict[str, Any]:
    """
    Obtiene el detalle de una norma específica
    
    Args:
        enlace: URL de la norma
    
    Returns:
        Diccionario con detalles
    """
    scraper = BCNScraper()
    return scraper.obtener_detalle_norma(enlace)


# Test básico
if __name__ == "__main__":
    # Test de búsqueda
    resultado = buscar_normativa_bcn("medio ambiente")
    print("🧪 TEST BCN SCRAPER")
    print(f"✅ Éxito: {resultado.get('success')}")
    print(f"📊 Resultados: {resultado.get('total_resultados', 0)}")
    
    if resultado.get('resultados'):
        primer_resultado = resultado['resultados'][0]
        print(f"🔍 Primer resultado: {primer_resultado.get('titulo', 'N/A')}")
        print(f"🔗 Enlace: {primer_resultado.get('enlace', 'N/A')}") 