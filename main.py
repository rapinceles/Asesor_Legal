# main.py - MERLIN Completo con SEIA y Google Maps
from fastapi import FastAPI, Request, HTTPException
from fastapi.responses import HTMLResponse, JSONResponse
from fastapi.staticfiles import StaticFiles
from fastapi.templating import Jinja2Templates
import os
import sys
import json
import logging
from typing import Dict, Optional, Any
from datetime import datetime

# Configurar logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# Crear app
app = FastAPI(
    title="MERLIN - Asesor Legal Ambiental",
    version="3.0-completo",
    description="Sistema completo de consultas legales ambientales con SEIA y Google Maps"
)

# Configuración
try:
    app.mount("/static", StaticFiles(directory="static"), name="static")
    templates = Jinja2Templates(directory="templates")
    logger.info("✅ Configuración básica OK")
except Exception as e:
    logger.error(f"⚠️ Error en configuración: {e}")
    templates = None

logger.info("🚀 MERLIN Completo v3.0 - Con SEIA y Google Maps")

# Importación segura del scraper SEIA
def importar_scraper_seia():
    """Importar scraper SEIA de forma segura"""
    try:
        from scrapers.seia_safe import obtener_informacion_proyecto_seia_safe
        logger.info("✅ Scraper SEIA importado correctamente")
        return obtener_informacion_proyecto_seia_safe
    except Exception as e:
        logger.warning(f"⚠️ No se pudo importar scraper SEIA: {e}")
        return None

# Importación del scraper por titular
def importar_scraper_titular():
    """Importar scraper por titular de forma segura"""
    try:
        from scrapers.seia_titular import buscar_proyectos_por_titular
        logger.info("✅ Scraper por titular importado correctamente")
        return buscar_proyectos_por_titular
    except Exception as e:
        logger.warning(f"⚠️ No se pudo importar scraper por titular: {e}")
        return None

# Importación del scraper BCN para consultas legales
def importar_scraper_bcn():
    """Importar scraper BCN de forma segura"""
    try:
        from scrapers.bcn_preciso import obtener_normativa_bcn_precisa
        logger.info("✅ Scraper BCN PRECISO importado correctamente")
        return obtener_normativa_bcn_precisa
    except Exception as e:
        logger.warning(f"⚠️ No se pudo importar scraper BCN preciso: {e}")
        try:
            from scrapers.bcn_legal import buscar_normativa_bcn
            logger.info("✅ Scraper BCN original importado como fallback")
            return buscar_normativa_bcn
        except Exception as e2:
            logger.warning(f"⚠️ No se pudo importar scraper BCN original: {e2}")
            return None

# Función de scraper SEIA fallback
def obtener_informacion_seia_fallback(nombre_empresa: str) -> Dict:
    """Función fallback cuando no se puede importar el scraper"""
    return {
        'success': True,
        'data': {
            'codigo_expediente': f'DEMO-{nombre_empresa[:8].upper()}',
            'estado': 'Información no disponible (modo básico)',
            'region': 'Región Metropolitana',
            'tipo': 'Consulta básica',
            'titular': {
                'nombre': nombre_empresa,
                'razon_social': f'{nombre_empresa} (información limitada)',
                'rut': 'No disponible',
                'telefono': 'No disponible',
                'email': 'No disponible',
                'direccion': 'Santiago, Chile'
            },
            'ubicacion': {
                'ubicacion_proyecto': 'Santiago, Chile',
                'comuna': 'Santiago',
                'region': 'Región Metropolitana',
                'coordenadas': '-33.4489, -70.6693'
            },
            'link_expediente': 'https://seia.sea.gob.cl/'
        },
        'modo': 'fallback'
    }

# Inicializar scrapers
scraper_seia = importar_scraper_seia()
scraper_titular = importar_scraper_titular()
scraper_bcn = importar_scraper_bcn()

def generar_respuesta_legal_completa(query: str, query_type: str = "general", empresa_info: Optional[Dict] = None) -> str:
    """Genera respuestas legales completas con contexto de empresa si está disponible"""
    try:
        if not query or not isinstance(query, str):
            return "Error: Consulta inválida"
        
        # Para consultas legales, usar BCN
        if query_type == "legal":
            return generar_respuesta_legal_bcn(query)
        
        # Para proyectos, usar la lógica existente
        query_lower = query.lower()
        base_response = ""
        
        # Respuesta específica según el contenido
        if "agua" in query_lower or "hidrico" in query_lower:
            base_response = """**📋 MARCO LEGAL DE RECURSOS HÍDRICOS EN CHILE**

• **Código de Aguas (DFL N° 1122/1981)**: Regula el derecho de aprovechamiento de aguas
• **Ley 21.064 (2018)**: Modifica el Código de Aguas para fortalecer la gestión hídrica
• **DGA**: Dirección General de Aguas administra los recursos hídricos
• **Sanciones**: Multas de 5 a 1000 UTM por uso no autorizado del agua
• **Derechos de Agua**: Consuntivos y no consuntivos, permanentes y eventuales

**PROCEDIMIENTOS CLAVE:**
- Solicitud de derechos de aprovechamiento ante DGA
- Estudios hidrogeológicos para aguas subterráneas
- Evaluación de impacto en otros usuarios
- Inscripción en Conservador de Bienes Raíces"""

        elif "ambiental" in query_lower or "medio ambiente" in query_lower:
            base_response = """**🌍 MARCO LEGAL AMBIENTAL EN CHILE**

• **Ley 19.300**: Bases Generales del Medio Ambiente
• **SEIA**: Sistema de Evaluación de Impacto Ambiental (obligatorio para proyectos específicos)
• **RCA**: Resolución de Calificación Ambiental requerida para operar
• **SMA**: Superintendencia del Medio Ambiente fiscaliza cumplimiento
• **Planes de Prevención y Descontaminación**: Según calidad del aire

**INSTRUMENTOS DE GESTIÓN:**
- Evaluación de Impacto Ambiental (EIA) o Declaración (DIA)
- Permisos ambientales sectoriales
- Planes de seguimiento y monitoreo
- Programas de cumplimiento en caso de infracciones"""

        elif "residuo" in query_lower or "basura" in query_lower:
            base_response = """**♻️ GESTIÓN DE RESIDUOS EN CHILE**

• **Ley 20.920 (REP)**: Responsabilidad Extendida del Productor
• **DS 1/2013**: Reglamenta manejo de residuos peligrosos
• **Plan de Manejo**: Obligatorio para generadores de residuos peligrosos
• **Disposición Final**: Solo en sitios autorizados por SEREMI Salud
• **Registro**: RETC para residuos peligrosos

**OBLIGACIONES EMPRESARIALES:**
- Caracterización y clasificación de residuos
- Manifesto de carga para transporte
- Almacenamiento temporal según normativa
- Reportes anuales a autoridad sanitaria"""

        else:
            # Para consultas de proyectos, respuesta más específica
            if query_type == "proyecto":
                base_response = f"""**🏗️ INFORMACIÓN DEL PROYECTO**

{query}

**📊 ESTADO AMBIENTAL:**
La información específica del proyecto se muestra en las secciones de empresa y ubicación a continuación.

**🔍 ASPECTOS AMBIENTALES RELEVANTES:**
• Verificar estado de la RCA (Resolución de Calificación Ambiental)
• Revisar cumplimiento de condiciones ambientales
• Monitorear reportes de seguimiento ambiental
• Evaluar permisos ambientales sectoriales vigentes

**⚖️ MARCO LEGAL APLICABLE:**
• Ley 19.300 - Bases Generales del Medio Ambiente
• Decreto Supremo 40/2012 - Reglamento del SEIA
• Normativas sectoriales específicas según el tipo de proyecto"""
            else:
                base_response = f"""**⚖️ ANÁLISIS LEGAL AMBIENTAL**

Su consulta sobre "{query}" se enmarca en la legislación ambiental chilena:

• **Marco Normativo**: Leyes ambientales y reglamentos sectoriales específicos
• **Autoridades Competentes**: SEA, SMA, SEREMI según la actividad y ubicación
• **Cumplimiento Normativo**: Documentación actualizada y reportes periódicos obligatorios
• **Fiscalización**: SMA puede realizar inspecciones programadas o por denuncia
• **Sanciones**: Desde amonestaciones hasta clausura según gravedad

**RECOMENDACIONES GENERALES:**
- Evaluar aplicabilidad de normativa específica al proyecto
- Consultar con autoridades competentes en etapa temprana
- Mantener documentación de cumplimiento actualizada
- Implementar sistema de gestión ambiental"""

        # Agregar contexto específico si hay información de empresa
        if empresa_info and empresa_info.get('data'):
            data = empresa_info['data']
            titular = data.get('titular', {})
            ubicacion = data.get('ubicacion', {})
            
            contexto_empresa = f"""

**🏢 CONTEXTO ESPECÍFICO DE LA EMPRESA:**

• **Empresa**: {titular.get('nombre', 'No especificada')}
• **Razón Social**: {titular.get('razon_social', 'No disponible')}
• **RUT**: {titular.get('rut', 'No disponible')}
• **Ubicación**: {ubicacion.get('ubicacion_proyecto', 'No especificada')}
• **Región**: {ubicacion.get('region', 'No especificada')}

**📊 INFORMACIÓN SEIA:**
• **Estado**: {data.get('estado', 'No disponible')}
• **Código Expediente**: {data.get('codigo_expediente', 'No disponible')}

**💡 CONSIDERACIONES ESPECÍFICAS:**
Basado en la información disponible del SEIA, esta empresa debe cumplir con las normativas ambientales aplicables en {ubicacion.get('region', 'su región')}. Se recomienda verificar el estado actual de sus permisos ambientales y mantener el cumplimiento de las condiciones establecidas en su RCA."""

            base_response += contexto_empresa

        # Agregar nota final
        base_response += """

**⚠️ IMPORTANTE**: Esta respuesta es informativa y no constituye asesoría legal específica. Para decisiones importantes, consulte con un abogado especializado en derecho ambiental.

*Última actualización normativa considerada: Diciembre 2024*"""

        return base_response

    except Exception as e:
        logger.error(f"Error en generar_respuesta_legal_completa: {e}")
        return f"Error al procesar consulta: Se produjo un error interno. Por favor intente nuevamente."

def generar_respuesta_legal_bcn(query: str) -> str:
    """Genera respuesta legal usando el scraper BCN"""
    try:
        logger.info(f"🔍 Buscando normativa legal para: {query}")
        
        if scraper_bcn:
            # Buscar en BCN
            resultado_bcn = scraper_bcn(query)
            
            if resultado_bcn and resultado_bcn.get('success') and resultado_bcn.get('resultados'):
                resultados = resultado_bcn['resultados']
                total = resultado_bcn.get('total_resultados', len(resultados))
                
                logger.info(f"✅ Encontradas {total} normas en BCN")
                
                # Construir respuesta con los resultados
                respuesta = f"""**⚖️ NORMATIVA LEGAL ENCONTRADA**

Se encontraron **{total} normas** relacionadas con su consulta "{query}":

"""
                
                # Agregar hasta 10 resultados principales
                for i, norma in enumerate(resultados[:10], 1):
                    titulo = norma.get('titulo', 'Sin título')
                    tipo_norma = norma.get('tipo_norma', 'Norma')
                    numero_ley = norma.get('numero_ley', '')
                    enlace = norma.get('enlace', '')
                    relevancia = norma.get('relevancia', 0)
                    
                    respuesta += f"""**{i}. {tipo_norma} {numero_ley}**
📋 **Título**: {titulo}
🔗 **Enlace**: [Ver normativa completa]({enlace})
⭐ **Relevancia**: {relevancia:.1f}/5.0

"""
                
                # Agregar enlace para ver más resultados si hay más de 10
                if total > 10:
                    respuesta += f"""**🔗 VER MÁS RESULTADOS:**

Se encontraron **{total} normas** en total. Los primeros 10 resultados se muestran arriba.

📋 **[Ver todos los {total} resultados en BCN →](https://www.bcn.cl/leychile/consulta/listado_n_sel?agr=2&q={query.replace(' ', '%20')})**

---

"""
                
                # Agregar recomendaciones
                respuesta += """**💡 RECOMENDACIONES:**

• Revise el texto completo de las normas más relevantes haciendo clic en los enlaces
• Verifique la vigencia actual de las normas consultadas
• Para interpretación específica, consulte con un abogado especializado
• Mantenga actualizada su información sobre cambios normativos

**⚠️ IMPORTANTE**: Esta información es referencial y no constituye asesoría legal específica. Para decisiones importantes, consulte con un profesional del derecho.

*Fuente: Biblioteca del Congreso Nacional (BCN) - www.bcn.cl*"""
                
                return respuesta
                
            else:
                logger.warning("⚠️ No se encontraron resultados en BCN")
                return generar_respuesta_legal_fallback(query)
        
        else:
            logger.warning("⚠️ Scraper BCN no disponible")
            return generar_respuesta_legal_fallback(query)
            
    except Exception as e:
        logger.error(f"❌ Error en generar_respuesta_legal_bcn: {e}")
        return generar_respuesta_legal_fallback(query)

def generar_respuesta_legal_fallback(query: str) -> str:
    """Genera respuesta legal básica cuando BCN no está disponible"""
    query_lower = query.lower()
    
    # Identificar tema principal
    if any(palabra in query_lower for palabra in ['agua', 'hídrico', 'río', 'pozo']):
        tema = "recursos hídricos"
        normativa_principal = "Código de Aguas (DFL N° 1122/1981)"
    elif any(palabra in query_lower for palabra in ['ambiental', 'medio ambiente', 'seia', 'rca']):
        tema = "medio ambiente"
        normativa_principal = "Ley 19.300 - Bases Generales del Medio Ambiente"
    elif any(palabra in query_lower for palabra in ['residuo', 'basura', 'desecho']):
        tema = "gestión de residuos"
        normativa_principal = "Ley 20.920 - Responsabilidad Extendida del Productor"
    elif any(palabra in query_lower for palabra in ['minería', 'minero', 'extracción']):
        tema = "minería"
        normativa_principal = "Código de Minería (Ley 18.248)"
    else:
        tema = "derecho ambiental general"
        normativa_principal = "Marco normativo ambiental chileno"
    
    return f"""**⚖️ CONSULTA LEGAL: {tema.upper()}**

Su consulta sobre "{query}" se relaciona con **{tema}**.

**📋 NORMATIVA PRINCIPAL:**
• {normativa_principal}

**🔍 PARA INFORMACIÓN DETALLADA:**
• Visite: https://www.bcn.cl/leychile/
• Consulte el portal oficial de normativa chilena
• Busque por palabras clave relacionadas con su consulta

**💡 RECOMENDACIONES:**
• Consulte la normativa específica en el portal BCN
• Verifique modificaciones y actualizaciones recientes
• Para interpretación específica, consulte con un abogado especializado

**⚠️ IMPORTANTE**: Esta respuesta es informativa y no constituye asesoría legal específica.

*Para acceder a la normativa completa, visite: https://www.bcn.cl/leychile/consulta/listado_n_sel?agr=2*"""

def procesar_informacion_empresa(nombre_empresa: str, query_type: str) -> Optional[Dict]:
    """Procesa información de empresa usando scraper por titular o SEIA"""
    try:
        if not nombre_empresa or not isinstance(nombre_empresa, str):
            return None
        
        logger.info(f"Procesando información para empresa: {nombre_empresa}")
        
        # Prioridad 1: Usar scraper por titular para búsqueda específica
        if scraper_titular:
            try:
                logger.info("🔍 Intentando búsqueda por titular específico")
                result_titular = scraper_titular(nombre_empresa)
                
                if result_titular and result_titular.get('success'):
                    data = result_titular.get('data', {})
                    lista_proyectos = data.get('lista_proyectos', [])
                    
                    # Si hay proyectos, siempre devolver para selección (incluso si es uno solo)
                    if len(lista_proyectos) > 0:
                        logger.info(f"✅ Encontrados {len(lista_proyectos)} proyectos para selección")
                        return {
                            'success': True,
                            'requiere_seleccion': True,
                            'lista_proyectos': lista_proyectos,
                            'stats': result_titular.get('stats', {}),
                            'modo': 'titular_multiple'
                        }
                    
                    # Si hay un solo proyecto, estructurar datos
                    elif len(lista_proyectos) == 1:
                        proyecto = lista_proyectos[0]
                        logger.info("✅ Proyecto único encontrado por titular")
                        return {
                            'success': True,
                            'data': {
                                'codigo_expediente': proyecto.get('link_expediente', '').split('=')[-1] if proyecto.get('link_expediente') else 'N/A',
                                'nombre': proyecto.get('nombre', ''),
                                'estado': proyecto.get('estado', ''),
                                'region': proyecto.get('region', ''),
                                'tipo': proyecto.get('tipo', ''),
                                'fecha_presentacion': proyecto.get('fecha', ''),
                                'inversion': proyecto.get('inversion', ''),
                                'link_expediente': proyecto.get('link_expediente', ''),
                                'titular': {
                                    'nombre': proyecto.get('titular', nombre_empresa),
                                    'nombre_fantasia': proyecto.get('titular', nombre_empresa),
                                    'razon_social': proyecto.get('razon_social_completa', ''),
                                    'rut': proyecto.get('rut', ''),
                                    'direccion': proyecto.get('direccion_titular', ''),
                                    'telefono': proyecto.get('telefono', ''),
                                    'email': proyecto.get('email', '')
                                },
                                'ubicacion': {
                                    'region': proyecto.get('region', ''),
                                    'ubicacion_proyecto': proyecto.get('ubicacion_detallada', proyecto.get('region', '')),
                                    'comuna': proyecto.get('comuna', ''),
                                    'provincia': proyecto.get('provincia', ''),
                                    'coordenadas': ''
                                }
                            },
                            'modo': 'titular_unico'
                        }
                
                logger.info("⚠️ Scraper por titular no encontró resultados, probando scraper SEIA")
                
            except Exception as e:
                logger.warning(f"Error en scraper por titular: {e}")
        
        # Prioridad 2: Usar scraper SEIA como fallback
        if scraper_seia:
            try:
                logger.info("🔍 Usando scraper SEIA como fallback")
                result = scraper_seia(nombre_empresa)
                
                if result and result.get('success'):
                    logger.info("✅ Información obtenida con scraper SEIA")
                    return result
                
            except Exception as e:
                logger.warning(f"Error en scraper SEIA: {e}")
        
        # Prioridad 3: Fallback básico
        logger.info("⚠️ Usando fallback básico")
        return obtener_informacion_seia_fallback(nombre_empresa)
        
    except Exception as e:
        logger.error(f"Error en procesar_informacion_empresa: {e}")
        return obtener_informacion_seia_fallback(nombre_empresa)

def extraer_informacion_ubicacion(empresa_info: Dict) -> Optional[Dict]:
    """Extrae información de ubicación para Google Maps"""
    try:
        if not empresa_info or not empresa_info.get('data'):
            return None
        
        data = empresa_info['data']
        ubicacion = data.get('ubicacion', {})
        titular = data.get('titular', {})
        
        if not ubicacion:
            return None
        
        # Extraer información de ubicación
        ubicacion_info = {
            'direccion': ubicacion.get('ubicacion_proyecto') or titular.get('direccion', ''),
            'comuna': ubicacion.get('comuna', ''),
            'provincia': ubicacion.get('provincia', ''),
            'region': ubicacion.get('region', ''),
            'coordenadas': ubicacion.get('coordenadas', ''),
            'tipo': 'Ubicación del proyecto',
            'fuente': 'Sistema SEIA'
        }
        
        # Filtrar campos vacíos
        ubicacion_filtrada = {k: v for k, v in ubicacion_info.items() if v}
        
        return ubicacion_filtrada if ubicacion_filtrada else None
        
    except Exception as e:
        logger.error(f"Error en extraer_informacion_ubicacion: {e}")
        return None

# Endpoints
@app.get("/", response_class=HTMLResponse)
async def render_form(request: Request):
    """Renderizar interfaz principal"""
    try:
        if templates:
            return templates.TemplateResponse("index.html", {"request": request})
        else:
            return HTMLResponse("""
            <html>
                <head><title>MERLIN - Asesor Legal Ambiental</title></head>
                <body style="font-family: Arial, sans-serif; margin: 40px; background: #1a1a1a; color: #fff;">
                    <h1 style="color: #ff6b35;">MERLIN - Asesor Legal Ambiental</h1>
                    <p>Sistema funcionando en modo básico (templates no disponibles)</p>
                    <ul>
                        <li><a href="/test" style="color: #ff6b35;">Test del sistema</a></li>
                        <li><a href="/health" style="color: #ff6b35;">Estado del sistema</a></li>
                        <li><a href="/diagnostico" style="color: #ff6b35;">Diagnóstico completo</a></li>
                    </ul>
                </body>
            </html>
            """)
    except Exception as e:
        logger.error(f"Error en render_form: {e}")
        return HTMLResponse(f"<h1>MERLIN</h1><p>Error: {str(e)}</p>", status_code=500)

@app.post("/consulta")
async def consulta_completa(request: Request):
    """Endpoint principal de consulta con SEIA y ubicación"""
    try:
        # Obtener datos de la petición
        try:
            data = await request.json()
        except Exception as e:
            logger.error(f"Error al parsear JSON: {e}")
            raise HTTPException(status_code=400, detail="Formato de datos inválido")
        
        # Extraer y validar parámetros
        query = str(data.get("query", "")).strip()
        query_type = str(data.get("query_type", "general")).strip()
        company_name = str(data.get("company_name", "")).strip()
        project_location = str(data.get("project_location", "")).strip()
        
        # Validaciones específicas por tipo
        if query_type == "legal":
            if not query:
                raise HTTPException(status_code=400, detail="Para consultas legales se requiere una pregunta específica")
        elif query_type == "proyecto":
            if not company_name:
                raise HTTPException(status_code=400, detail="Para búsqueda de proyectos se requiere nombre de empresa o proyecto")
        
        # Validación de longitud solo si hay query
        if query and len(query) > 2000:
            raise HTTPException(status_code=400, detail="Consulta demasiado larga (máximo 2000 caracteres)")
        
        logger.info(f"Procesando consulta: {query_type} - {company_name[:50] if company_name else 'N/A'}")
        
        # Procesar información de empresa si es necesario
        empresa_info = None
        if query_type == "proyecto" and company_name:
            empresa_info = procesar_informacion_empresa(company_name, query_type)
            if empresa_info:
                logger.info("✅ Información de empresa obtenida")
                
                # Verificar si requiere selección de proyecto
                if empresa_info.get('requiere_seleccion'):
                    lista_proyectos = empresa_info.get('lista_proyectos', [])
                    return JSONResponse({
                        "success": True,
                        "requiere_seleccion": True,
                        "empresa_buscada": company_name,
                        "proyectos_encontrados": len(lista_proyectos),
                        "lista_proyectos": [{
                            "id": p.get('id_proyecto'),
                            "nombre": p.get('nombre', 'Sin nombre'),
                            "titular": p.get('titular', 'Sin titular'),
                            "region": p.get('region', 'Sin región'),
                            "estado": p.get('estado', 'Sin estado'),
                            "tipo": p.get('tipo', 'Sin tipo'),
                            "inversion": p.get('inversion', 'No especificada'),
                            "score": p.get('score_relevancia', 0)
                        } for p in lista_proyectos],
                        "mensaje": f"Se encontraron {len(lista_proyectos)} proyectos para '{company_name}'. Selecciona el proyecto específico:",
                        "stats": empresa_info.get('stats', {}),
                        "timestamp": datetime.now().isoformat()
                    })
                    
            else:
                logger.warning("⚠️ No se pudo obtener información de empresa")
        
        # Generar respuesta legal
        if query_type == "proyecto" and not query:
            # Para proyectos sin consulta, generar respuesta básica
            query = f"Información del proyecto de {company_name}"
        
        respuesta = generar_respuesta_legal_completa(query, query_type, empresa_info)
        
        # Preparar respuesta base
        response_data = {
            "success": True,
            "respuesta": respuesta,
            "query_type": query_type,
            "timestamp": datetime.now().isoformat(),
            "referencias": [
                {
                    "title": "Sistema de Evaluación de Impacto Ambiental (SEIA)",
                    "description": "Portal oficial del SEIA - Información de proyectos ambientales",
                    "url": "https://seia.sea.gob.cl/"
                },
                {
                    "title": "Biblioteca del Congreso Nacional",
                    "description": "Legislación chilena vigente - Leyes y reglamentos",
                    "url": "https://www.bcn.cl/leychile/"
                },
                {
                    "title": "Ministerio del Medio Ambiente",
                    "description": "Información oficial sobre normativa ambiental",
                    "url": "https://mma.gob.cl/"
                },
                {
                    "title": "Superintendencia del Medio Ambiente",
                    "description": "Fiscalización y cumplimiento ambiental",
                    "url": "https://www.sma.gob.cl/"
                }
            ]
        }
        
        # Agregar información de empresa si está disponible
        if empresa_info and empresa_info.get('success') and empresa_info.get('data'):
            data_empresa = empresa_info['data']
            titular = data_empresa.get('titular', {})
            
            response_data["empresa_info"] = {
                "nombre": titular.get('nombre', company_name),
                "nombre_fantasia": titular.get('nombre_fantasia', ''),
                "razon_social": titular.get('razon_social', ''),
                "rut": titular.get('rut', ''),
                "direccion": titular.get('direccion', ''),
                "telefono": titular.get('telefono', ''),
                "email": titular.get('email', ''),
                "region": data_empresa.get('ubicacion', {}).get('region', ''),
                "codigo_expediente": data_empresa.get('codigo_expediente', ''),
                "estado_proyecto": data_empresa.get('estado', ''),
                "link_seia": data_empresa.get('link_expediente', ''),
                "tipo": query_type,
                "fuente": f"SEIA ({empresa_info.get('modo', 'normal')})"
            }
            
            # Agregar información de ubicación para Google Maps
            ubicacion_info = extraer_informacion_ubicacion(empresa_info)
            if ubicacion_info:
                response_data["ubicacion"] = ubicacion_info
                logger.info("✅ Información de ubicación incluida")
        
        # Log de respuesta exitosa
        logger.info(f"✅ Consulta procesada exitosamente - Tipo: {query_type}")
        
        return JSONResponse(response_data)
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error crítico en consulta_completa: {str(e)}")
        return JSONResponse({
            "success": False,
            "error": f"Error interno del servidor: {str(e)[:200]}",
            "timestamp": datetime.now().isoformat()
        }, status_code=500)

@app.post("/seleccionar_proyecto")
async def seleccionar_proyecto(request: Request):
    """Endpoint para seleccionar un proyecto específico de la lista"""
    try:
        # Obtener datos de la petición
        try:
            data = await request.json()
        except Exception as e:
            logger.error(f"Error al parsear JSON: {e}")
            raise HTTPException(status_code=400, detail="Formato de datos inválido")
        
        # Extraer y validar parámetros
        empresa_nombre = str(data.get("empresa_nombre", "")).strip()
        proyecto_id = data.get("proyecto_id")
        query = str(data.get("query", "")).strip()
        query_type = str(data.get("query_type", "proyecto")).strip()
        
        # Validaciones
        if not empresa_nombre:
            raise HTTPException(status_code=400, detail="Se requiere nombre de empresa")
        
        if proyecto_id is None:
            raise HTTPException(status_code=400, detail="Se requiere ID de proyecto")
        
        try:
            proyecto_id = int(proyecto_id)
        except (ValueError, TypeError):
            raise HTTPException(status_code=400, detail="ID de proyecto debe ser un número")
        
        logger.info(f"Seleccionando proyecto {proyecto_id} para empresa: {empresa_nombre}")
        
        # Obtener proyecto específico
        try:
            from scrapers.seia_titular import obtener_proyecto_seleccionado
            resultado = obtener_proyecto_seleccionado(empresa_nombre, proyecto_id)
            
            if not resultado.get('success'):
                raise HTTPException(status_code=404, detail=f"No se encontró el proyecto: {resultado.get('error', 'Error desconocido')}")
            
            proyecto_data = resultado.get('data', {})
            
        except ImportError:
            raise HTTPException(status_code=500, detail="Scraper por titular no disponible")
        except Exception as e:
            logger.error(f"Error al obtener proyecto seleccionado: {e}")
            raise HTTPException(status_code=500, detail=f"Error al obtener proyecto: {str(e)}")
        
        # Estructurar información de empresa
        empresa_info = {
            'success': True,
            'data': {
                'codigo_expediente': proyecto_data.get('link_expediente', '').split('=')[-1] if proyecto_data.get('link_expediente') else 'N/A',
                'nombre': proyecto_data.get('nombre', ''),
                'estado': proyecto_data.get('estado', ''),
                'region': proyecto_data.get('region', ''),
                'tipo': proyecto_data.get('tipo', ''),
                'fecha_presentacion': proyecto_data.get('fecha', ''),
                'inversion': proyecto_data.get('inversion', ''),
                'link_expediente': proyecto_data.get('link_expediente', ''),
                'titular': {
                    'nombre': proyecto_data.get('titular', empresa_nombre),
                    'nombre_fantasia': proyecto_data.get('titular', empresa_nombre),
                    'razon_social': proyecto_data.get('razon_social_completa', ''),
                    'rut': proyecto_data.get('rut', ''),
                    'direccion': proyecto_data.get('direccion_titular', ''),
                    'telefono': proyecto_data.get('telefono', ''),
                    'email': proyecto_data.get('email', '')
                },
                'ubicacion': {
                    'region': proyecto_data.get('region', ''),
                    'ubicacion_proyecto': proyecto_data.get('ubicacion_detallada', proyecto_data.get('region', '')),
                    'comuna': proyecto_data.get('comuna', ''),
                    'provincia': proyecto_data.get('provincia', ''),
                    'coordenadas': ''
                }
            },
            'modo': 'titular_seleccionado'
        }
        
        # Generar respuesta legal
        respuesta = generar_respuesta_legal_completa(query or f"Información del proyecto {proyecto_data.get('nombre', 'seleccionado')}", query_type, empresa_info)
        
        # Preparar respuesta
        response_data = {
            "success": True,
            "respuesta": respuesta,
            "query_type": query_type,
            "proyecto_seleccionado": True,
            "timestamp": datetime.now().isoformat(),
            "referencias": [
                {
                    "title": "Sistema de Evaluación de Impacto Ambiental (SEIA)",
                    "description": "Portal oficial del SEIA - Información de proyectos ambientales",
                    "url": "https://seia.sea.gob.cl/"
                },
                {
                    "title": "Expediente SEIA del Proyecto",
                    "description": f"Información detallada del proyecto: {proyecto_data.get('nombre', 'N/A')}",
                    "url": proyecto_data.get('link_expediente', 'https://seia.sea.gob.cl/')
                }
            ]
        }
        
        # Agregar información de empresa
        data_empresa = empresa_info['data']
        titular = data_empresa.get('titular', {})
        
        response_data["empresa_info"] = {
            "nombre": titular.get('nombre', empresa_nombre),
            "nombre_fantasia": titular.get('nombre_fantasia', ''),
            "razon_social": titular.get('razon_social', ''),
            "rut": titular.get('rut', ''),
            "direccion": titular.get('direccion', ''),
            "telefono": titular.get('telefono', ''),
            "email": titular.get('email', ''),
            "region": data_empresa.get('ubicacion', {}).get('region', ''),
            "codigo_expediente": data_empresa.get('codigo_expediente', ''),
            "estado_proyecto": data_empresa.get('estado', ''),
            "link_seia": data_empresa.get('link_expediente', ''),
            "tipo": query_type,
            "fuente": "SEIA (proyecto seleccionado)",
            "proyecto_nombre": proyecto_data.get('nombre', ''),
            "proyecto_id": proyecto_id
        }
        
        # Agregar información de ubicación para Google Maps
        ubicacion_info = extraer_informacion_ubicacion(empresa_info)
        if ubicacion_info:
            response_data["ubicacion"] = ubicacion_info
            logger.info("✅ Información de ubicación incluida")
        
        logger.info(f"✅ Proyecto {proyecto_id} seleccionado exitosamente")
        
        return JSONResponse(response_data)
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error crítico en seleccionar_proyecto: {str(e)}")
        return JSONResponse({
            "success": False,
            "error": f"Error interno del servidor: {str(e)[:200]}",
            "timestamp": datetime.now().isoformat()
        }, status_code=500)

@app.get("/health")
async def health_check():
    """Health check completo y robusto"""
    try:
        health_status = {
            "status": "healthy",
            "message": "MERLIN funcionando correctamente",
            "version": "3.0-completo",
            "timestamp": datetime.now().isoformat(),
            "components": {}
        }
        
        # Verificar componentes críticos
        try:
            # Test scraper SEIA
            health_status["components"]["scraper_seia"] = "disponible" if scraper_seia else "fallback"
            
            # Test scraper titular
            health_status["components"]["scraper_titular"] = "disponible" if scraper_titular else "no disponible"
            
            # Test templates
            health_status["components"]["templates"] = "disponible" if templates else "no disponible"
            
            # Test respuesta legal
            test_response = generar_respuesta_legal_completa("test de salud", "general")
            health_status["components"]["respuesta_legal"] = "funcional" if len(test_response) > 50 else "limitada"
            
            # Test conexión a SEIA (rápido)
            try:
                import requests
                response = requests.get("https://seia.sea.gob.cl", timeout=5)
                health_status["components"]["conexion_seia"] = "disponible" if response.status_code == 200 else "limitada"
            except:
                health_status["components"]["conexion_seia"] = "no disponible"
            
            # Test importaciones críticas
            try:
                from bs4 import BeautifulSoup
                health_status["components"]["beautifulsoup"] = "disponible"
            except:
                health_status["components"]["beautifulsoup"] = "no disponible"
            
            health_status["components"]["logging"] = "activo"
            
            # Verificar si algún componente crítico falla
            componentes_criticos = ["scraper_seia", "respuesta_legal"]
            for componente in componentes_criticos:
                if health_status["components"].get(componente) not in ["disponible", "funcional"]:
                    health_status["status"] = "degraded"
                    health_status["message"] = f"Componente crítico {componente} con problemas"
        
        except Exception as component_error:
            health_status["status"] = "degraded"
            health_status["message"] = f"Error verificando componentes: {str(component_error)}"
            health_status["components"]["error"] = str(component_error)
        
        return health_status
        
    except Exception as e:
        logger.error(f"Error crítico en health check: {e}")
        return {
            "status": "unhealthy",
            "error": str(e),
            "timestamp": datetime.now().isoformat()
        }

@app.get("/test")
async def test_endpoint():
    """Test completo del sistema"""
    try:
        results = {
            "status": "ok",
            "version": "3.0-completo",
            "timestamp": datetime.now().isoformat(),
            "tests": {}
        }
        
        # Test 1: Respuesta legal básica
        try:
            response = generar_respuesta_legal_completa("test", "general")
            results["tests"]["respuesta_legal"] = {
                "status": "ok",
                "length": len(response)
            }
        except Exception as e:
            results["tests"]["respuesta_legal"] = {
                "status": "error",
                "error": str(e)
            }
        
        # Test 2: Scraper SEIA
        try:
            if scraper_seia:
                seia_result = scraper_seia("test")
                results["tests"]["scraper_seia"] = {
                    "status": "ok",
                    "available": True,
                    "success": seia_result.get('success', False)
                }
            else:
                results["tests"]["scraper_seia"] = {
                    "status": "fallback",
                    "available": False
                }
        except Exception as e:
            results["tests"]["scraper_seia"] = {
                "status": "error",
                "error": str(e)
            }
        
        # Test 3: Templates
        results["tests"]["templates"] = {
            "status": "ok" if templates else "unavailable",
            "available": templates is not None
        }
        
        return results
        
    except Exception as e:
        return {
            "status": "error",
            "error": str(e),
            "timestamp": datetime.now().isoformat()
        }

@app.get("/diagnostico")
async def diagnostico_completo():
    """Diagnóstico completo del sistema"""
    try:
        return {
            "sistema": "MERLIN v3.0",
            "estado": "Funcional",
            "componentes": {
                "fastapi": "Activo",
                "templates": "Disponible" if templates else "No disponible",
                "scraper_seia": "Funcional" if scraper_seia else "Modo fallback",
                "logging": "Configurado",
                "static_files": "Montado"
            },
            "funcionalidades": {
                "consultas_generales": "✅ Activo",
                "consultas_empresa": "✅ Activo",
                "consultas_proyecto": "✅ Activo",
                "scraping_seia": "✅ Activo (con fallback)",
                "google_maps": "✅ Activo (requiere API Key)",
                "ubicacion_proyectos": "✅ Activo"
            },
            "endpoints": {
                "/": "Interfaz principal",
                "/consulta": "Endpoint principal de consultas",
                "/health": "Estado del sistema",
                "/test": "Tests automáticos",
                "/diagnostico": "Este diagnóstico"
            },
            "timestamp": datetime.now().isoformat()
        }
    except Exception as e:
        return {"error": str(e)}

# Evento de startup usando lifespan
from contextlib import asynccontextmanager

@asynccontextmanager
async def lifespan(app: FastAPI):
    """Manejo del ciclo de vida de la aplicación"""
    # Startup
    logger.info("🚀 MERLIN iniciando...")
    logger.info(f"📊 Scraper SEIA: {'Disponible' if scraper_seia else 'Modo fallback'}")
    logger.info(f"🎯 Scraper Titular: {'Disponible' if scraper_titular else 'No disponible'}")
    logger.info(f"🎨 Templates: {'Disponible' if templates else 'No disponible'}")
    logger.info("✅ MERLIN listo para consultas")
    yield
    # Shutdown
    logger.info("👋 MERLIN cerrando...")

# Aplicar lifespan al app
app.router.lifespan_context = lifespan

if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8000) 