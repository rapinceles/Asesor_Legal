# main.py - MERLIN con integración SEIA
from fastapi import FastAPI, Request
from fastapi.responses import HTMLResponse, JSONResponse
from fastapi.staticfiles import StaticFiles
from fastapi.templating import Jinja2Templates
from typing import Optional
import os

# Importar scraper con fallback
try:
    from scrapers.seia_project_detail_scraper import obtener_informacion_proyecto_seia
    SEIA_DISPONIBLE = True
    print("✅ Scraper SEIA completo disponible")
except ImportError:
    try:
        from scrapers.seia_simple import obtener_informacion_proyecto_seia_simple as obtener_informacion_proyecto_seia
        SEIA_DISPONIBLE = True
        print("✅ Scraper SEIA simplificado disponible")
    except ImportError:
        SEIA_DISPONIBLE = False
        print("⚠️ Scraper SEIA no disponible, funcionando en modo básico")

app = FastAPI(title="MERLIN - Asesor Legal Ambiental Inteligente")

# Configurar carpetas estáticas y plantillas HTML
app.mount("/static", StaticFiles(directory="static"), name="static")
templates = Jinja2Templates(directory="templates")

# Variables de estado del sistema
print("🚀 Iniciando MERLIN - Asesor Legal Ambiental")
print("⚠️  Funcionando en modo simplificado (sin dependencias complejas)")

# Ruta raíz que carga la interfaz visual
@app.get("/", response_class=HTMLResponse)
async def render_form(request: Request):
    return templates.TemplateResponse("index.html", {"request": request})

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
        
        if not query:
            return JSONResponse({
                "success": False,
                "error": "La consulta no puede estar vacía"
            }, status_code=400)
        
        # Procesar según el tipo de consulta
        if query_type == "general":
            # Análisis general
            respuesta = generar_respuesta_legal_general(query)
            referencias = generar_referencias_legales(query)
            
            return JSONResponse({
                "success": True,
                "respuesta": respuesta,
                "referencias": referencias
            })
            
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
                    if seia_result['success']:
                        seia_info = seia_result['data']
                        print(f"Información del SEIA obtenida exitosamente")
                    else:
                        print(f"No se pudo obtener información del SEIA: {seia_result.get('error', 'Error desconocido')}")
                except Exception as e:
                    print(f"Error al consultar SEIA: {e}")
                    seia_info = None
            
            respuesta = generar_respuesta_empresarial(company_name, query, query_type, project_location, seia_info)
            
            response_data = {
                "success": True,
                "respuesta": respuesta,
                "referencias": generar_referencias_ambientales(query)
            }
            
            # Agregar información de empresa desde SEIA si está disponible
            if seia_info:
                empresa_info = construir_info_empresa_seia(seia_info, company_name, query_type)
                response_data["empresa_info"] = empresa_info
                
                # Agregar información de ubicación desde SEIA
                ubicacion_info = construir_info_ubicacion_seia(seia_info, project_location)
                if ubicacion_info:
                    response_data["ubicacion"] = ubicacion_info
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
        return JSONResponse({
            "success": False,
            "error": f"Error al procesar la consulta: {str(e)}"
        }, status_code=500)

def generar_respuesta_legal_general(query: str) -> str:
    """Genera respuestas legales generales basadas en la consulta"""
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
    info_empresa = {
        "nombre": nombre_empresa,
        "tipo": tipo,
        "estado": "Información obtenida del SEIA"
    }
    
    # Extraer información del titular si está disponible
    if 'titular' in seia_info and seia_info['titular']:
        titular = seia_info['titular']
        
        if 'nombre_fantasia' in titular:
            info_empresa['nombre_fantasia'] = titular['nombre_fantasia']
        if 'razon_social' in titular:
            info_empresa['razon_social'] = titular['razon_social']
        if 'rut' in titular:
            info_empresa['rut'] = titular['rut']
        if 'direccion' in titular:
            info_empresa['direccion'] = titular['direccion']
        if 'telefono' in titular:
            info_empresa['telefono'] = titular['telefono']
        if 'email' in titular:
            info_empresa['email'] = titular['email']
    
    # Agregar información adicional del proyecto
    if 'codigo_expediente' in seia_info:
        info_empresa['codigo_expediente'] = seia_info['codigo_expediente']
    if 'estado' in seia_info:
        info_empresa['estado_proyecto'] = seia_info['estado']
    if 'region' in seia_info:
        info_empresa['region'] = seia_info['region']
    if 'link_expediente' in seia_info:
        info_empresa['link_seia'] = seia_info['link_expediente']
    
    return info_empresa

def construir_info_ubicacion_seia(seia_info: dict, ubicacion_manual: str = None) -> dict:
    """
    Construye la información de ubicación a partir de los datos del SEIA
    """
    ubicacion_info = {
        "tipo": "Ubicación desde SEIA",
        "fuente": "Sistema de Evaluación de Impacto Ambiental"
    }
    
    # Priorizar ubicación del SEIA
    if 'ubicacion' in seia_info and seia_info['ubicacion']:
        ubicacion_seia = seia_info['ubicacion']
        
        if 'ubicacion_proyecto' in ubicacion_seia:
            ubicacion_info['direccion'] = ubicacion_seia['ubicacion_proyecto']
        elif 'direccion_proyecto' in ubicacion_seia:
            ubicacion_info['direccion'] = ubicacion_seia['direccion_proyecto']
        
        if 'comuna' in ubicacion_seia:
            ubicacion_info['comuna'] = ubicacion_seia['comuna']
        if 'provincia' in ubicacion_seia:
            ubicacion_info['provincia'] = ubicacion_seia['provincia']
        if 'region' in ubicacion_seia:
            ubicacion_info['region'] = ubicacion_seia['region']
        if 'coordenadas' in ubicacion_seia:
            ubicacion_info['coordenadas'] = ubicacion_seia['coordenadas']
    
    # Si no hay ubicación del SEIA pero hay dirección del titular
    if 'direccion' not in ubicacion_info and 'titular' in seia_info:
        titular = seia_info['titular']
        if 'direccion' in titular:
            ubicacion_info['direccion'] = titular['direccion']
            ubicacion_info['tipo'] = "Dirección Casa Matriz (desde SEIA)"
    
    # Usar ubicación manual como respaldo
    if 'direccion' not in ubicacion_info and ubicacion_manual:
        ubicacion_info['direccion'] = ubicacion_manual
        ubicacion_info['tipo'] = "Ubicación Manual"
        ubicacion_info['fuente'] = "Ingresada por el usuario"
    
    # Solo retornar si hay al menos una dirección
    if 'direccion' in ubicacion_info:
        return ubicacion_info
    
    return None

def generar_referencias_legales(query: str):
    """Genera referencias legales basadas en la consulta"""
    query_lower = query.lower()
    
    if any(word in query_lower for word in ['agua', 'hidrico']):
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
    
    elif any(word in query_lower for word in ['ambiental', 'medio ambiente']):
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
    
    elif any(word in query_lower for word in ['residuo', 'basura']):
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

def generar_referencias_ambientales(query: str):
    """Genera referencias específicas para consultas ambientales"""
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

# Endpoint de prueba para verificar conectividad
@app.get("/test")
async def test_endpoint():
    return {"message": "MERLIN backend funcionando correctamente", "version": "1.0"}

@app.get("/health")
async def health_check():
    return {
        "status": "ok", 
        "message": "Servidor funcionando correctamente",
        "mode": "simplificado",
        "endpoints": ["/", "/consulta", "/test", "/health"]
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