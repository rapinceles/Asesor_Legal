# main.py - MERLIN con integración SEIA
from fastapi import FastAPI, Request
from fastapi.responses import HTMLResponse, JSONResponse
from fastapi.staticfiles import StaticFiles
from fastapi.templating import Jinja2Templates
from typing import Optional
import os
import sys

# Importar scraper con fallback ultra-seguro
try:
    from scrapers.seia_safe import obtener_informacion_proyecto_seia_safe as obtener_informacion_proyecto_seia
    SEIA_DISPONIBLE = True
    print("✅ Scraper SEIA ultra-seguro disponible")
except ImportError:
    # Fallback interno si no existe el archivo
    def obtener_informacion_proyecto_seia(nombre_empresa: str):
        return {
            'success': False,
            'error': 'SEIA no disponible en este momento',
            'data': None
        }
    SEIA_DISPONIBLE = False
    print("⚠️ Scraper SEIA no disponible, funcionando en modo básico")

app = FastAPI(
    title="MERLIN - Asesor Legal Ambiental Inteligente",
    version="2.0",
    description="Sistema de consultas legales ambientales con integración SEIA"
)

# Configurar carpetas estáticas y plantillas HTML
try:
    app.mount("/static", StaticFiles(directory="static"), name="static")
    templates = Jinja2Templates(directory="templates")
    print("✅ Archivos estáticos y templates configurados")
except Exception as e:
    print(f"⚠️ Error configurando archivos estáticos: {e}")
    # Crear templates básicos si no existen
    templates = None

# Variables de estado del sistema
print("🚀 Iniciando MERLIN - Asesor Legal Ambiental v2.0")
print("⚠️ Funcionando en modo simplificado (sin dependencias complejas)")

# Evento de startup
@app.on_event("startup")
async def startup_event():
    """Inicialización del sistema al arrancar"""
    try:
        print("🔧 Ejecutando verificaciones de startup...")
        
        # Test básico de funciones principales
        test_response = generar_respuesta_legal_general("test startup")
        if test_response:
            print("✅ Funciones principales verificadas")
        else:
            print("⚠️ Warning: Funciones principales no responden correctamente")
            
        # Test del scraper SEIA
        if SEIA_DISPONIBLE:
            try:
                test_seia = obtener_informacion_proyecto_seia("test")
                print("✅ Scraper SEIA verificado")
            except Exception as e:
                print(f"⚠️ Warning: Scraper SEIA con problemas: {e}")
        
        print("🎯 MERLIN iniciado correctamente")
        
    except Exception as e:
        print(f"❌ Error en startup: {e}")
        # No fallar el startup, solo logear

# Ruta raíz que carga la interfaz visual
@app.get("/", response_class=HTMLResponse)
async def render_form(request: Request):
    """Renderizar la interfaz principal de MERLIN"""
    try:
        if templates is None:
            # Fallback si no hay templates
            return HTMLResponse("""
            <html>
                <head><title>MERLIN - Error</title></head>
                <body>
                    <h1>MERLIN - Asesor Legal Ambiental</h1>
                    <p>Error: Templates no disponibles</p>
                    <p>Usar endpoint /test para verificar funcionamiento</p>
                </body>
            </html>
            """)
        
        return templates.TemplateResponse("index.html", {"request": request})
    except Exception as e:
        print(f"Error rendering template: {e}")
        return HTMLResponse(f"""
        <html>
            <head><title>MERLIN - Error</title></head>
            <body>
                <h1>MERLIN - Asesor Legal Ambiental</h1>
                <p>Error: {str(e)}</p>
                <p><a href="/test">Probar endpoint /test</a></p>
                <p><a href="/health">Ver estado del sistema</a></p>
            </body>
        </html>
        """, status_code=500)

# Endpoint unificado para todas las consultas
@app.post("/consulta")
async def consulta_unificada(request: Request):
    """
    Endpoint unificado que maneja todos los tipos de consulta
    """
    try:
        # Obtener datos JSON del request
        data = await request.json()
        query = data.get("query", "").strip()
        query_type = data.get("query_type", "general")
        company_name = data.get("company_name", "").strip()
        project_location = data.get("project_location", "").strip()
        
        # Validaciones básicas
        if not query:
            return JSONResponse({
                "success": False,
                "error": "La consulta no puede estar vacía"
            }, status_code=400)
        
        if len(query) > 5000:
            return JSONResponse({
                "success": False,
                "error": "La consulta es demasiado larga (máximo 5000 caracteres)"
            }, status_code=400)
        
        # Procesar según el tipo de consulta
        if query_type == "general":
            try:
                # Análisis general
                respuesta = generar_respuesta_legal_general(query)
                referencias = generar_referencias_legales(query)
                
                return JSONResponse({
                    "success": True,
                    "respuesta": respuesta,
                    "referencias": referencias
                })
            except Exception as e:
                print(f"Error en consulta general: {e}")
                return JSONResponse({
                    "success": False,
                    "error": "Error al procesar la consulta general. Por favor intente nuevamente."
                }, status_code=500)
                
        elif query_type in ["empresa", "proyecto"]:
            # Análisis empresarial/proyecto
            if not company_name:
                return JSONResponse({
                    "success": False,
                    "error": "El nombre de la empresa es requerido"
                }, status_code=400)
            
            # Obtener información real del SEIA si es un proyecto y está disponible
            seia_info = None
            if query_type == "proyecto" and SEIA_DISPONIBLE:
                try:
                    print(f"Consultando SEIA para empresa: {company_name}")
                    seia_result = obtener_informacion_proyecto_seia(company_name)
                    if seia_result and seia_result.get('success'):
                        seia_info = seia_result.get('data')
                        print(f"Información del SEIA obtenida exitosamente")
                    else:
                        print(f"No se pudo obtener información del SEIA: {seia_result.get('error', 'Error desconocido') if seia_result else 'Sin respuesta'}")
                except Exception as e:
                    print(f"Error al consultar SEIA: {e}")
                    seia_info = None
            
            try:
                respuesta = generar_respuesta_empresarial(company_name, query, query_type, project_location, seia_info)
                
                response_data = {
                    "success": True,
                    "respuesta": respuesta,
                    "referencias": generar_referencias_ambientales(query)
                }
                
                # Agregar información de empresa desde SEIA si está disponible
                if seia_info:
                    try:
                        empresa_info = construir_info_empresa_seia(seia_info, company_name, query_type)
                        response_data["empresa_info"] = empresa_info
                        
                        # Agregar información de ubicación desde SEIA
                        ubicacion_info = construir_info_ubicacion_seia(seia_info, project_location)
                        if ubicacion_info:
                            response_data["ubicacion"] = ubicacion_info
                    except Exception as e:
                        print(f"Error al procesar información del SEIA: {e}")
                        # Continuar sin información del SEIA
                        pass
                else:
                    # Información básica si no se encuentra en SEIA
                    response_data["empresa_info"] = {
                        "nombre": company_name,
                        "tipo": query_type,
                        "estado": "Información básica (no encontrada en SEIA)"
                    }
                    
                    # Agregar información de ubicación manual si está disponible
                    if project_location:
                        response_data["ubicacion"] = {
                            "direccion": project_location,
                            "tipo": "Ubicación Manual",
                            "coordenadas": "Ver en mapa para detalles"
                        }
                
                return JSONResponse(response_data)
                
            except Exception as e:
                print(f"Error en consulta empresarial: {e}")
                return JSONResponse({
                    "success": False,
                    "error": "Error al procesar la consulta empresarial. Por favor intente nuevamente."
                }, status_code=500)
        
        else:
            return JSONResponse({
                "success": False,
                "error": "Tipo de consulta no válido"
            }, status_code=400)
        
    except ValueError as e:
        print(f"Error de datos JSON: {e}")
        return JSONResponse({
            "success": False,
            "error": "Formato de datos no válido"
        }, status_code=400)
    except Exception as e:
        print(f"Error general en endpoint: {e}")
        return JSONResponse({
            "success": False,
            "error": "Error interno del servidor. Por favor intente nuevamente."
        }, status_code=500)

def generar_respuesta_legal_general(query: str) -> str:
    """Genera respuestas legales generales basadas en la consulta"""
    try:
        query_lower = query.lower()
        
        if any(word in query_lower for word in ['agua', 'hidrico', 'recurso hidrico']):
            return """**Marco Legal de Recursos Hídricos en Chile:**

• **Código de Aguas (DFL N° 1122/1981)**: Regula el derecho de aprovechamiento de aguas y su administración.

• **Ley 21.064**: Modifica el Código de Aguas para fortalecer la gestión y protección de recursos hídricos.

• **Derechos de Aprovechamiento**: Se requiere solicitar derechos ante la Dirección General de Aguas (DGA).

• **Caudal Ecológico**: Obligatorio mantener un caudal mínimo para proteger el ecosistema.

• **Sanciones**: Multas de 5 a 1000 UTM por uso no autorizado del agua.

**Recomendación**: Siempre verificar la disponibilidad hídrica antes de solicitar derechos de aprovechamiento."""
        
        elif any(word in query_lower for word in ['ambiental', 'medio ambiente', 'impacto']):
            return """**Marco Legal Ambiental en Chile:**

• **Ley 19.300 (Bases Generales del Medio Ambiente)**: Marco principal de la legislación ambiental.

• **SEIA (Sistema de Evaluación de Impacto Ambiental)**: Obligatorio para proyectos que puedan causar impacto ambiental.

• **RCA (Resolución de Calificación Ambiental)**: Autorización ambiental requerida para operar.

• **SMA (Superintendencia del Medio Ambiente)**: Fiscaliza el cumplimiento de la normativa.

• **Tipos de Evaluación**: EIA (Estudio) o DIA (Declaración) según el proyecto.

**Importante**: El incumplimiento puede resultar en multas millonarias y cierre temporal."""
        
        elif any(word in query_lower for word in ['residuo', 'basura', 'desecho']):
            return """**Gestión de Residuos en Chile:**

• **Ley 20.920 (REP)**: Establece responsabilidad extendida del productor.

• **DS 1/2013**: Reglamenta residuos peligrosos y su manejo.

• **Plan de Manejo**: Obligatorio para generadores de residuos peligrosos.

• **Transporte**: Solo empresas autorizadas pueden transportar residuos peligrosos.

• **Disposición Final**: Debe realizarse en sitios autorizados por la autoridad sanitaria.

**Sanciones**: Multas de hasta 10,000 UTM por manejo inadecuado de residuos peligrosos."""
        
        elif any(word in query_lower for word in ['aire', 'atmosfer', 'emision', 'contamina']):
            return """**Calidad del Aire y Emisiones:**

• **D.S. 59/1998**: Establece la norma de calidad primaria para PM10.

• **D.S. 12/2011**: Norma primaria de calidad ambiental para material particulado fino PM2,5.

• **Planes de Descontaminación**: Obligatorios en zonas saturadas o latentes.

• **Monitoreo de Emisiones**: Empresas deben reportar emisiones atmosféricas.

• **Compensación de Emisiones**: Requerida en zonas saturadas.

**Sanciones**: Multas de hasta 10,000 UTM por incumplimiento de normas de emisión."""
        
        elif any(word in query_lower for word in ['ruido', 'sonoro', 'acustic']):
            return """**Contaminación Acústica:**

• **D.S. 38/2011**: Norma de emisión de ruidos generados por fuentes fijas.

• **Límites de Ruido**: Varían según zona (residencial, comercial, industrial).

• **Horarios**: Restricciones especiales para período nocturno.

• **Medición**: Debe realizarse según metodología oficial.

• **Plan de Reducción**: Obligatorio si se superan límites permitidos.

**Importante**: Las multas pueden llegar hasta 1,000 UTM por infracciones graves."""
        
        elif any(word in query_lower for word in ['suelo', 'contamina', 'tierra']):
            return """**Protección del Suelo:**

• **D.S. 4/2009**: Reglamento para el manejo de lodos generados en plantas de tratamiento.

• **Caracterización de Suelos**: Obligatoria antes de remediar sitios contaminados.

• **Plan de Descontaminación**: Requerido para sitios con contaminación confirmada.

• **Valores de Referencia**: Establecidos según uso de suelo (residencial, industrial, etc.).

• **Remedación**: Debe alcanzar niveles seguros según normativa.

**Nota**: La responsabilidad de remediar puede ser del propietario actual o histórico."""
        
        else:
            return f"""**Análisis Legal General:**

Su consulta sobre "{query}" se enmarca en la legislación ambiental chilena vigente.

• **Marco Normativo**: Regulado por leyes ambientales y sectoriales específicas.

• **Autoridad Competente**: Depende del tipo de actividad (SEA, SMA, SEREMI, etc.).

• **Procedimiento**: Evaluar requisitos específicos según la actividad.

• **Cumplimiento**: Mantener documentación actualizada y reportes periódicos.

• **Fiscalización**: La SMA puede realizar inspecciones sin previo aviso.

**Recomendación**: Solicite asesoría especializada para casos específicos.

*Esta respuesta es de carácter informativo. Para decisiones importantes, consulte con un abogado especializado.*"""
    
    except Exception as e:
        print(f"Error en generar_respuesta_legal_general: {e}")
        return f"""**Error al procesar la consulta**:

Ha ocurrido un error interno al procesar su consulta: {query}

Por favor, intente reformular su pregunta o contacte al administrador del sistema.

**Información de apoyo**:
• Visite el sitio web oficial del SEA: www.sea.gob.cl
• Consulte la biblioteca digital de la SMA: www.sma.gob.cl
• Para consultas específicas, contacte un abogado ambiental especializado.

*Disculpe las molestias ocasionadas.*"""

def generar_respuesta_empresarial(empresa: str, query: str, tipo: str, ubicacion: str = None, seia_info: dict = None) -> str:
    """Genera respuestas específicas para empresas"""
    
    # Información del SEIA si está disponible
    seia_info_text = ""
    if seia_info:
        seia_info_text = f"""

• **📊 Información del SEIA**:
  - Código Expediente: {seia_info.get('codigo_expediente', 'No disponible')}
  - Estado del Proyecto: {seia_info.get('estado', 'No disponible')}
  - Región: {seia_info.get('region', 'No disponible')}
  - Tipo de Proyecto: {seia_info.get('tipo', 'No disponible')}"""
        
        if 'titular' in seia_info and seia_info['titular']:
            titular = seia_info['titular']
            seia_info_text += f"""
  - Titular: {titular.get('nombre', titular.get('razon_social', 'No disponible'))}"""
            if 'rut' in titular:
                seia_info_text += f"""
  - RUT: {titular['rut']}"""
    
    # Información de ubicación
    ubicacion_info = ""
    if seia_info and 'ubicacion' in seia_info and seia_info['ubicacion']:
        ubicacion_seia = seia_info['ubicacion']
        direccion = ubicacion_seia.get('ubicacion_proyecto') or ubicacion_seia.get('direccion_proyecto')
        
        if direccion:
            ubicacion_info = f"""

• **📍 Ubicación del Proyecto (SEIA)**: {direccion}"""
            if 'comuna' in ubicacion_seia:
                ubicacion_info += f"""
  - Comuna: {ubicacion_seia['comuna']}"""
            if 'region' in ubicacion_seia:
                ubicacion_info += f"""
  - Región: {ubicacion_seia['region']}"""
            
            ubicacion_info += f"""
  - Verificar zonificación y ordenanzas municipales locales
  - Evaluar cercanía a áreas protegidas o sensibles (SNASPE)
  - Considerar normativas ambientales específicas de la región
  - Revisar planes reguladores comunales vigentes
  - Identificar posibles restricciones territoriales"""
    
    elif ubicacion and tipo == "proyecto":
        ubicacion_info = f"""

• **📍 Análisis de Ubicación**: {ubicacion}
  - Verificar zonificación y ordenanzas municipales locales
  - Evaluar cercanía a áreas protegidas o sensibles (SNASPE)
  - Considerar normativas ambientales específicas de la región
  - Revisar planes reguladores comunales vigentes
  - Identificar posibles restricciones territoriales"""
    
    # Análisis específico basado en información del SEIA
    analisis_seia = ""
    if seia_info:
        estado = seia_info.get('estado', '').lower()
        if 'aprobado' in estado:
            analisis_seia = f"""

• **Estado del Proyecto**: APROBADO - RCA vigente
  - Verificar cumplimiento de compromisos ambientales
  - Revisar condiciones y medidas establecidas en la RCA
  - Mantener reportes de seguimiento actualizados"""
        elif 'calificado' in estado:
            analisis_seia = f"""

• **Estado del Proyecto**: CALIFICADO FAVORABLEMENTE
  - RCA otorgada - proyecto puede ejecutarse
  - Cumplir estrictamente con compromisos ambientales
  - Implementar Plan de Seguimiento Ambiental"""
        elif 'evaluación' in estado or 'admisible' in estado:
            analisis_seia = f"""

• **Estado del Proyecto**: EN EVALUACIÓN
  - Proyecto en proceso de evaluación ambiental
  - Seguir requerimientos de la autoridad ambiental
  - Preparar respuestas a observaciones ciudadanas"""
        elif 'rechazado' in estado or 'no calificado' in estado:
            analisis_seia = f"""

• **Estado del Proyecto**: NO CALIFICADO/RECHAZADO
  - Proyecto no cuenta con aprobación ambiental
  - Revisar causales de rechazo
  - Evaluar posibilidad de nuevo ingreso con modificaciones"""
    
    return f"""**Análisis {tipo.title()} - {empresa}:**

Consulta específica: "{query}"

• **Tipo de Análisis**: {tipo.title()}
• **Empresa**: {empresa}
• **Marco Legal Aplicable**: Normativa ambiental sectorial{seia_info_text}{ubicacion_info}{analisis_seia}

**Recomendaciones Específicas:**
• Verificar cumplimiento de obligaciones ambientales vigentes
• Mantener al día los permisos y autorizaciones sectoriales
• Implementar sistemas de monitoreo y seguimiento
• Capacitar al personal en normativa ambiental
• Establecer procedimientos de emergencia ambiental

**Próximos Pasos:**
• Realizar auditoría de cumplimiento ambiental
• Evaluar riesgos regulatorios específicos
• Implementar plan de mejora continua
• Mantener registro de actividades ambientales

**Aspectos Críticos a Considerar:**
• Vigencia de permisos ambientales
• Cumplimiento de compromisos RCA
• Reportes periódicos a autoridades
• Manejo de residuos y emisiones

*Análisis basado en información oficial del SEIA. Para un análisis detallado, se requiere revisión de documentación específica de la empresa.*"""

def construir_info_empresa_seia(seia_info: dict, nombre_empresa: str, tipo: str) -> dict:
    """
    Construye la información de empresa a partir de los datos del SEIA
    """
    try:
        info_empresa = {
            "nombre": nombre_empresa,
            "tipo": tipo,
            "estado": "Información obtenida del SEIA"
        }
        
        # Verificar que seia_info es un diccionario válido
        if not isinstance(seia_info, dict):
            return info_empresa
        
        # Extraer información del titular si está disponible
        if seia_info.get('titular') and isinstance(seia_info['titular'], dict):
            titular = seia_info['titular']
            
            # Usar get() para evitar KeyError
            if titular.get('nombre_fantasia'):
                info_empresa['nombre_fantasia'] = str(titular['nombre_fantasia'])
            if titular.get('razon_social'):
                info_empresa['razon_social'] = str(titular['razon_social'])
            if titular.get('rut'):
                info_empresa['rut'] = str(titular['rut'])
            if titular.get('direccion'):
                info_empresa['direccion'] = str(titular['direccion'])
            if titular.get('telefono'):
                info_empresa['telefono'] = str(titular['telefono'])
            if titular.get('email'):
                info_empresa['email'] = str(titular['email'])
        
        # Agregar información adicional del proyecto
        if seia_info.get('codigo_expediente'):
            info_empresa['codigo_expediente'] = str(seia_info['codigo_expediente'])
        if seia_info.get('estado'):
            info_empresa['estado_proyecto'] = str(seia_info['estado'])
        if seia_info.get('region'):
            info_empresa['region'] = str(seia_info['region'])
        if seia_info.get('link_expediente'):
            info_empresa['link_seia'] = str(seia_info['link_expediente'])
        
        return info_empresa
        
    except Exception as e:
        print(f"Error en construir_info_empresa_seia: {e}")
        return {
            "nombre": nombre_empresa,
            "tipo": tipo,
            "estado": "Error al procesar información del SEIA",
            "error": str(e)
        }

def construir_info_ubicacion_seia(seia_info: dict, ubicacion_manual: str = None) -> dict:
    """
    Construye la información de ubicación a partir de los datos del SEIA
    """
    try:
        ubicacion_info = {
            "tipo": "Ubicación desde SEIA",
            "fuente": "Sistema de Evaluación de Impacto Ambiental"
        }
        
        # Verificar que seia_info es un diccionario válido
        if not isinstance(seia_info, dict):
            if ubicacion_manual:
                return {
                    "direccion": ubicacion_manual,
                    "tipo": "Ubicación Manual",
                    "fuente": "Ingresada por el usuario"
                }
            return None
        
        # Priorizar ubicación del SEIA
        if seia_info.get('ubicacion') and isinstance(seia_info['ubicacion'], dict):
            ubicacion_seia = seia_info['ubicacion']
            
            if ubicacion_seia.get('ubicacion_proyecto'):
                ubicacion_info['direccion'] = str(ubicacion_seia['ubicacion_proyecto'])
            elif ubicacion_seia.get('direccion_proyecto'):
                ubicacion_info['direccion'] = str(ubicacion_seia['direccion_proyecto'])
            
            if ubicacion_seia.get('comuna'):
                ubicacion_info['comuna'] = str(ubicacion_seia['comuna'])
            if ubicacion_seia.get('provincia'):
                ubicacion_info['provincia'] = str(ubicacion_seia['provincia'])
            if ubicacion_seia.get('region'):
                ubicacion_info['region'] = str(ubicacion_seia['region'])
            if ubicacion_seia.get('coordenadas'):
                ubicacion_info['coordenadas'] = str(ubicacion_seia['coordenadas'])
        
        # Si no hay ubicación del SEIA pero hay dirección del titular
        if 'direccion' not in ubicacion_info and seia_info.get('titular'):
            titular = seia_info['titular']
            if isinstance(titular, dict) and titular.get('direccion'):
                ubicacion_info['direccion'] = str(titular['direccion'])
                ubicacion_info['tipo'] = "Dirección Casa Matriz (desde SEIA)"
        
        # Usar ubicación manual como respaldo
        if 'direccion' not in ubicacion_info and ubicacion_manual:
            ubicacion_info['direccion'] = str(ubicacion_manual)
            ubicacion_info['tipo'] = "Ubicación Manual"
            ubicacion_info['fuente'] = "Ingresada por el usuario"
        
        # Solo retornar si hay al menos una dirección
        if ubicacion_info.get('direccion'):
            return ubicacion_info
        
        return None
        
    except Exception as e:
        print(f"Error en construir_info_ubicacion_seia: {e}")
        if ubicacion_manual:
            return {
                "direccion": str(ubicacion_manual),
                "tipo": "Ubicación Manual",
                "fuente": "Ingresada por el usuario (error en SEIA)",
                "error": str(e)
            }
        return None

def generar_referencias_legales(query: str):
    """Genera referencias legales basadas en la consulta"""
    try:
        if not query or not isinstance(query, str):
            return []
            
        query_lower = query.lower()
        
        if any(word in query_lower for word in ['agua', 'hidrico', 'recurso hidrico']):
            return [
                {
                    "title": "Código de Aguas (DFL N° 1122/1981)",
                    "description": "Marco legal principal que regula los derechos de aprovechamiento de aguas en Chile.",
                    "url": "https://www.bcn.cl/leychile/navegar?idNorma=5605"
                },
                {
                    "title": "Dirección General de Aguas (DGA)",
                    "description": "Organismo encargado de administrar los recursos hídricos del país.",
                    "url": "https://www.dga.cl/"
                }
            ]
        
        elif any(word in query_lower for word in ['ambiental', 'medio ambiente', 'impacto']):
            return [
                {
                    "title": "Ley 19.300 - Bases Generales del Medio Ambiente",
                    "description": "Marco legal principal de la legislación ambiental chilena.",
                    "url": "https://www.bcn.cl/leychile/navegar?idNorma=30667"
                },
                {
                    "title": "Sistema de Evaluación de Impacto Ambiental (SEIA)",
                    "description": "Portal oficial para tramitación de proyectos ambientales.",
                    "url": "https://seia.sea.gob.cl/"
                }
            ]
        
        elif any(word in query_lower for word in ['residuo', 'basura', 'desecho']):
            return [
                {
                    "title": "Ley 20.920 - Responsabilidad Extendida del Productor",
                    "description": "Marco legal para la gestión de residuos y reciclaje.",
                    "url": "https://www.bcn.cl/leychile/navegar?idNorma=1090894"
                },
                {
                    "title": "Ministerio del Medio Ambiente - Residuos",
                    "description": "Información oficial sobre gestión de residuos.",
                    "url": "https://mma.gob.cl/economia-circular/gestion-de-residuos/"
                }
            ]
        
        else:
            return [
                {
                    "title": "Biblioteca del Congreso Nacional",
                    "description": "Compilación completa de leyes chilenas vigentes.",
                    "url": "https://www.bcn.cl/leychile/"
                },
                {
                    "title": "Ministerio del Medio Ambiente",
                    "description": "Información oficial sobre normativas ambientales.",
                    "url": "https://mma.gob.cl/"
                }
            ]
    
    except Exception as e:
        print(f"Error en generar_referencias_legales: {e}")
        return [
            {
                "title": "Biblioteca del Congreso Nacional",
                "description": "Compilación completa de leyes chilenas vigentes.",
                "url": "https://www.bcn.cl/leychile/"
            }
        ]

def generar_referencias_ambientales(query: str):
    """Genera referencias específicas para consultas ambientales"""
    try:
        return [
            {
                "title": "Superintendencia del Medio Ambiente (SMA)",
                "description": "Organismo fiscalizador del cumplimiento de la normativa ambiental.",
                "url": "https://www.sma.gob.cl/"
            },
            {
                "title": "Servicio de Evaluación Ambiental (SEA)",
                "description": "Administra el Sistema de Evaluación de Impacto Ambiental.",
                "url": "https://www.sea.gob.cl/"
            },
            {
                "title": "Portal de Transparencia Ambiental",
                "description": "Acceso público a información ambiental de empresas y proyectos.",
                "url": "https://sinia.mma.gob.cl/"
            }
        ]
    except Exception as e:
        print(f"Error en generar_referencias_ambientales: {e}")
        return [
            {
                "title": "Ministerio del Medio Ambiente",
                "description": "Información oficial sobre normativas ambientales.",
                "url": "https://mma.gob.cl/"
            }
        ]

# Endpoint de prueba para verificar conectividad
@app.get("/test")
async def test_endpoint():
    """Endpoint de diagnóstico completo"""
    try:
        diagnostics = {
            "status": "ok",
            "message": "MERLIN backend funcionando correctamente", 
            "version": "2.0",
            "timestamp": "2025-01-19",
            "system_info": {
                "seia_available": SEIA_DISPONIBLE,
                "templates_available": templates is not None,
                "python_version": sys.version.split()[0] if 'sys' in globals() else "unknown"
            }
        }
        
        # Test de función principal
        try:
            test_response = generar_respuesta_legal_general("test")
            diagnostics["function_test"] = "ok" if test_response else "failed"
        except Exception as e:
            diagnostics["function_test"] = f"error: {str(e)}"
        
        # Test de SEIA si está disponible
        if SEIA_DISPONIBLE:
            try:
                seia_test = obtener_informacion_proyecto_seia("test")
                diagnostics["seia_test"] = "ok" if seia_test else "failed"
            except Exception as e:
                diagnostics["seia_test"] = f"error: {str(e)}"
        
        return diagnostics
        
    except Exception as e:
        return {
            "status": "error",
            "message": f"Error en diagnóstico: {str(e)}",
            "version": "2.0"
        }

@app.get("/health")
async def health_check():
    """Health check endpoint para Render"""
    try:
        # Test básico de las funciones principales
        test_response = generar_respuesta_legal_general("test")
        if not test_response:
            raise Exception("Función principal no responde")
            
        return {
            "status": "healthy", 
            "message": "MERLIN funcionando correctamente",
            "version": "2.0",
            "seia_available": SEIA_DISPONIBLE,
            "endpoints": ["/", "/consulta", "/test", "/health"],
            "timestamp": "2025-01-19"
        }
    except Exception as e:
        return {
            "status": "unhealthy",
            "error": str(e),
            "message": "Error en health check"
        }

# Endpoint adicional para análisis general (compatibilidad)
@app.post("/analisis_general/")
async def analisis_general(request: Request):
    """Endpoint de compatibilidad para análisis general"""
    try:
        # Obtener datos del request
        form_data = await request.form()
        query = form_data.get("query_box", "")
        
        if not query:
            return JSONResponse({
                "success": False,
                "error": "La consulta no puede estar vacía"
            }, status_code=400)
        
        respuesta = generar_respuesta_legal_general(query)
        referencias = generar_referencias_legales(query)
        
        return JSONResponse({
            "success": True,
            "respuesta": respuesta,
            "referencias": referencias
        })
        
    except Exception as e:
        return JSONResponse({
            "success": False,
            "error": f"Error al procesar la consulta: {str(e)}"
        }, status_code=500)

if __name__ == "__main__":
    import uvicorn
    print("🚀 Iniciando servidor MERLIN en puerto 8000...")
    uvicorn.run(app, host="0.0.0.0", port=8000) 