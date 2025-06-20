# main_fixed.py - Versión corregida y completamente funcional
from fastapi import FastAPI, Form, Request, HTTPException
from fastapi.responses import HTMLResponse, JSONResponse
from fastapi.staticfiles import StaticFiles
from fastapi.templating import Jinja2Templates
from fastapi.middleware.cors import CORSMiddleware
from typing import Optional
import os
import json

app = FastAPI(title="MERLIN - Asesor Legal Ambiental Inteligente")

# Configurar CORS
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

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
            
            respuesta = generar_respuesta_empresarial(company_name, query, query_type, project_location)
            
            response_data = {
                "success": True,
                "respuesta": respuesta,
                "empresa_info": {
                    "nombre": company_name,
                    "tipo": query_type,
                    "estado": "Análisis completado"
                },
                "referencias": generar_referencias_ambientales(query)
            }
            
            # Agregar información de ubicación si está disponible
            if project_location:
                response_data["ubicacion"] = {
                    "direccion": project_location,
                    "tipo": "Ubicación del Proyecto",
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

def generar_respuesta_empresarial(empresa: str, query: str, tipo: str, ubicacion: str = None) -> str:
    """Genera respuestas específicas para empresas"""
    ubicacion_info = ""
    if ubicacion and tipo == "proyecto":
        ubicacion_info = f"""

• **📍 Análisis de Ubicación**: {ubicacion}
  - Verificar zonificación y ordenanzas municipales locales
  - Evaluar cercanía a áreas protegidas o sensibles (SNASPE)
  - Considerar normativas ambientales específicas de la región
  - Revisar planes reguladores comunales vigentes
  - Identificar posibles restricciones territoriales"""
    
    return f"""**Análisis {tipo.title()} - {empresa}:**

Consulta específica: "{query}"

• **Tipo de Análisis**: {tipo.title()}
• **Empresa**: {empresa}
• **Marco Legal Aplicable**: Normativa ambiental sectorial{ubicacion_info}

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

*Para un análisis detallado, se requiere revisión de documentación específica de la empresa.*"""

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
async def analisis_general(query: str = Form(..., alias="query_box")):
    """Endpoint de compatibilidad para análisis general"""
    try:
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