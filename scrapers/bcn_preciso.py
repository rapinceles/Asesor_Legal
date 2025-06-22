# scrapers/bcn_preciso.py
import logging
from typing import Dict

logger = logging.getLogger(__name__)

def obtener_normativa_bcn_precisa(termino_busqueda: str) -> Dict:
    """BCN ultra-preciso - mapea términos específicos a normativas exactas"""
    try:
        logger.info(f"🎯 BCN PRECISO - Búsqueda: '{termino_busqueda}'")
        
        termino_lower = termino_busqueda.lower().strip()
        
        # Mapeo ultra-específico de términos
        mapeo_exacto = {
            # SUELO
            'suelo': 'suelo',
            'suelos': 'suelo',
            'uso de suelo': 'suelo',
            'uso del suelo': 'suelo',
            'terreno': 'suelo',
            
            # AGUA
            'agua': 'agua',
            'aguas': 'agua',
            'hídrico': 'agua',
            'hidrico': 'agua',
            'recursos hídricos': 'agua',
            'recursos hidricos': 'agua',
            
            # RESIDUOS PELIGROSOS (específico)
            'residuos peligrosos': 'residuos peligrosos',
            'residuo peligroso': 'residuos peligrosos',
            'sustancias peligrosas': 'residuos peligrosos',
            'sustancia peligrosa': 'residuos peligrosos',
            
            # RESIDUOS GENERALES
            'residuos': 'residuos',
            'residuo': 'residuos',
            'basura': 'residuos',
            'desechos': 'residuos',
            'reciclaje': 'residuos',
            
            # ENERGÍA
            'energía': 'energia',
            'energia': 'energia',
            'eléctrico': 'energia',
            'electrico': 'energia',
            'renovable': 'energia',
            'solar': 'energia',
            'eólico': 'energia',
            'eolico': 'energia',
            
            # MINERÍA
            'minería': 'mineria',
            'mineria': 'mineria',
            'minero': 'mineria',
            'extracción': 'mineria',
            'yacimiento': 'mineria',
            'cobre': 'mineria',
            'oro': 'mineria',
            
            # CONSTRUCCIÓN
            'construcción': 'construccion',
            'construccion': 'construccion',
            'edificación': 'construccion',
            'edificacion': 'construccion',
            'urbanismo': 'construccion',
            'vivienda': 'construccion',
            'edificio': 'construccion',
            
            # FORESTAL
            'forestal': 'forestal',
            'bosque': 'forestal',
            'bosques': 'forestal',
            'árbol': 'forestal',
            'arboles': 'forestal',
            'madera': 'forestal',
            
            # PESCA
            'pesca': 'pesca',
            'pesquero': 'pesca',
            'acuicultura': 'pesca',
            'marítimo': 'pesca',
            'maritimo': 'pesca',
            'mar': 'pesca',
            
            # TRANSPORTE
            'transporte': 'transporte',
            'tránsito': 'transporte',
            'transito': 'transporte',
            'vehículo': 'transporte',
            'vehiculo': 'transporte',
            'carretera': 'transporte',
            
            # LABORAL
            'laboral': 'laboral',
            'trabajo': 'laboral',
            'trabajador': 'laboral',
            'empleo': 'laboral',
            'empleado': 'laboral'
        }
        
        # Base de datos ultra-específica
        normativas_precisas = {
            'suelo': [
                {
                    'titulo': 'Decreto Supremo 82/2010 - Reglamento de Suelos, Aguas y Humedales',
                    'numero': '82/2010',
                    'tipo': 'Decreto Supremo',
                    'descripcion': 'Regula específicamente la protección de suelos',
                    'relevancia': 10.0
                },
                {
                    'titulo': 'DFL 458/1975 - Ley General de Urbanismo y Construcciones',
                    'numero': '458/1975',
                    'tipo': 'DFL',
                    'descripcion': 'Regula el uso del suelo urbano',
                    'relevancia': 9.5
                }
            ],
            'agua': [
                {
                    'titulo': 'DFL 1122/1981 - Código de Aguas',
                    'numero': '1122/1981',
                    'tipo': 'DFL',
                    'descripcion': 'Marco legal fundamental para el uso de aguas',
                    'relevancia': 10.0
                },
                {
                    'titulo': 'Ley 21.064/2018 - Introduce modificaciones al marco normativo que rige las aguas',
                    'numero': '21.064/2018',
                    'tipo': 'Ley',
                    'descripcion': 'Reforma al Código de Aguas',
                    'relevancia': 9.5
                }
            ],
            'residuos peligrosos': [
                {
                    'titulo': 'Decreto Supremo 148/2003 - Reglamento Sanitario sobre Manejo de Residuos Peligrosos',
                    'numero': '148/2003',
                    'tipo': 'Decreto Supremo',
                    'descripcion': 'Marco regulatorio específico para residuos peligrosos',
                    'relevancia': 10.0
                }
            ],
            'residuos': [
                {
                    'titulo': 'Ley 20.920/2016 - Marco para la Gestión de Residuos y Fomento al Reciclaje',
                    'numero': '20.920/2016',
                    'tipo': 'Ley',
                    'descripcion': 'Ley REP - Responsabilidad Extendida del Productor',
                    'relevancia': 10.0
                }
            ],
            'energia': [
                {
                    'titulo': 'DFL 4/2006 - Ley General de Servicios Eléctricos',
                    'numero': '4/2006',
                    'tipo': 'DFL',
                    'descripcion': 'Marco legal del sector eléctrico',
                    'relevancia': 10.0
                }
            ],
            'mineria': [
                {
                    'titulo': 'Ley 18.248/1983 - Código de Minería',
                    'numero': '18.248/1983',
                    'tipo': 'Ley',
                    'descripcion': 'Marco legal fundamental de la minería',
                    'relevancia': 10.0
                }
            ],
            'construccion': [
                {
                    'titulo': 'DFL 458/1975 - Ley General de Urbanismo y Construcciones',
                    'numero': '458/1975',
                    'tipo': 'DFL',
                    'descripcion': 'Marco legal específico de construcción',
                    'relevancia': 10.0
                }
            ],
            'forestal': [
                {
                    'titulo': 'Ley 20.283/2008 - Sobre Recuperación del Bosque Nativo y Fomento Forestal',
                    'numero': '20.283/2008',
                    'tipo': 'Ley',
                    'descripcion': 'Protección específica del bosque nativo',
                    'relevancia': 10.0
                }
            ],
            'pesca': [
                {
                    'titulo': 'Ley 18.892/1989 - Ley General de Pesca y Acuicultura',
                    'numero': '18.892/1989',
                    'tipo': 'Ley',
                    'descripcion': 'Marco legal específico de pesca y acuicultura',
                    'relevancia': 10.0
                }
            ],
            'transporte': [
                {
                    'titulo': 'Ley 18.290/1984 - Ley de Tránsito',
                    'numero': '18.290/1984',
                    'tipo': 'Ley',
                    'descripcion': 'Marco legal específico del tránsito',
                    'relevancia': 10.0
                }
            ],
            'laboral': [
                {
                    'titulo': 'DFL 1/2003 - Código del Trabajo',
                    'numero': '1/2003',
                    'tipo': 'DFL',
                    'descripcion': 'Marco legal específico del trabajo',
                    'relevancia': 10.0
                }
            ]
        }
        
        # BÚSQUEDA EXACTA
        categoria_encontrada = mapeo_exacto.get(termino_lower)
        
        if categoria_encontrada and categoria_encontrada in normativas_precisas:
            logger.info(f"✅ Categoría EXACTA encontrada: '{categoria_encontrada}' para término '{termino_busqueda}'")
            
            normativas = normativas_precisas[categoria_encontrada]
            
            resultados = []
            for i, normativa in enumerate(normativas, 1):
                resultado = {
                    'numero': i,
                    'titulo': normativa['titulo'],
                    'descripcion': normativa['descripcion'],
                    'enlace': f"https://www.bcn.cl/leychile/navegar?idNorma={normativa['numero']}",
                    'numero_ley': normativa['numero'],
                    'tipo_norma': normativa['tipo'],
                    'relevancia': normativa['relevancia'],
                    'categoria_encontrada': categoria_encontrada,
                    'precision': 'exacta'
                }
                resultados.append(resultado)
            
            return {
                'success': True,
                'termino_busqueda': termino_busqueda,
                'categoria_encontrada': categoria_encontrada,
                'total_resultados': len(resultados),
                'resultados': resultados,
                'precision': 'exacta',
                'fuente': 'BCN Preciso - Mapeo exacto'
            }
        
        # NO ENCONTRADO
        logger.warning(f"⚠️ NO se encontraron normativas específicas para: '{termino_busqueda}'")
        
        return {
            'success': False,
            'termino_busqueda': termino_busqueda,
            'error': f'No se encontraron normativas específicas para: {termino_busqueda}',
            'sugerencias': [
                'suelo', 'agua', 'residuos peligrosos', 'residuos', 'energía', 
                'minería', 'construcción', 'forestal', 'pesca', 'transporte', 'laboral'
            ],
            'total_resultados': 0,
            'resultados': [],
            'precision': 'ninguna',
            'fuente': 'BCN Preciso - Sin resultados'
        }
        
    except Exception as e:
        logger.error(f"❌ Error en BCN Preciso: {e}")
        return {
            'success': False,
            'error': str(e),
            'resultados': []
        }
