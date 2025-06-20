# main_simple.py - MERLIN Ultra-Simplificado para evitar Error 500
from fastapi import FastAPI, Request
from fastapi.responses import HTMLResponse, JSONResponse
from fastapi.staticfiles import StaticFiles
from fastapi.templating import Jinja2Templates
import os
import sys

# Crear app
app = FastAPI(
    title="MERLIN - Asesor Legal Ambiental",
    version="2.0-simple",
    description="Sistema simplificado de consultas legales ambientales"
)

# Configuración básica
try:
    app.mount("/static", StaticFiles(directory="static"), name="static")
    templates = Jinja2Templates(directory="templates")
    print("✅ Configuración básica OK")
except Exception as e:
    print(f"⚠️ Error en configuración: {e}")
    templates = None

print("🚀 MERLIN Ultra-Simplificado v2.0")

# Función de respuesta legal simplificada
def generar_respuesta_simple(query: str, query_type: str = "general") -> str:
    """Genera respuestas legales simplificadas"""
    try:
        if not query or not isinstance(query, str):
            return "Error: Consulta inválida"
        
        query_lower = query.lower()
        
        if "agua" in query_lower or "hidrico" in query_lower:
            return """**Marco Legal de Recursos Hídricos en Chile:**

• **Código de Aguas (DFL N° 1122/1981)**: Regula el derecho de aprovechamiento de aguas.
• **Ley 21.064**: Modifica el Código de Aguas para fortalecer la gestión hídrica.
• **DGA**: Dirección General de Aguas administra los recursos hídricos.
• **Sanciones**: Multas de 5 a 1000 UTM por uso no autorizado del agua.

**Recomendación**: Consulte con un especialista para casos específicos."""

        elif "ambiental" in query_lower or "medio ambiente" in query_lower:
            return """**Marco Legal Ambiental en Chile:**

• **Ley 19.300**: Bases Generales del Medio Ambiente.
• **SEIA**: Sistema de Evaluación de Impacto Ambiental.
• **RCA**: Resolución de Calificación Ambiental requerida.
• **SMA**: Superintendencia del Medio Ambiente fiscaliza.

**Importante**: Consulte asesoría especializada para proyectos específicos."""

        elif "residuo" in query_lower or "basura" in query_lower:
            return """**Gestión de Residuos en Chile:**

• **Ley 20.920 (REP)**: Responsabilidad Extendida del Productor.
• **DS 1/2013**: Reglamenta residuos peligrosos.
• **Plan de Manejo**: Obligatorio para residuos peligrosos.
• **Disposición Final**: En sitios autorizados únicamente.

**Importante**: Manejo especializado para residuos peligrosos."""

        else:
            return f"""**Análisis Legal General:**

Su consulta sobre "{query}" se enmarca en la legislación ambiental chilena.

• **Marco Normativo**: Leyes ambientales y sectoriales específicas.
• **Autoridad Competente**: SEA, SMA, SEREMI según la actividad.
• **Cumplimiento**: Documentación actualizada y reportes periódicos.
• **Fiscalización**: SMA puede realizar inspecciones.

**Recomendación**: Consulte con abogado especializado para casos específicos.

*Esta respuesta es informativa. Para decisiones importantes, consulte un especialista.*"""

    except Exception as e:
        return f"Error al procesar consulta: {str(e)[:100]}..."

# Endpoint raíz
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
                <body>
                    <h1>MERLIN - Asesor Legal Ambiental</h1>
                    <p>Sistema funcionando en modo simplificado</p>
                    <p><a href="/test">Test del sistema</a></p>
                    <p><a href="/health">Estado del sistema</a></p>
                </body>
            </html>
            """)
    except Exception as e:
        return HTMLResponse(f"<h1>MERLIN</h1><p>Error: {str(e)}</p>", status_code=500)

# Endpoint de consulta ultra-simplificado
@app.post("/consulta")
async def consulta_simple(request: Request):
    """Endpoint de consulta ultra-simplificado"""
    try:
        # Obtener datos
        data = await request.json()
        query = data.get("query", "").strip()
        query_type = data.get("query_type", "general")
        company_name = data.get("company_name", "").strip()
        
        # Validaciones básicas
        if not query:
            return JSONResponse({
                "success": False,
                "error": "La consulta no puede estar vacía"
            }, status_code=400)
        
        if len(query) > 1000:
            return JSONResponse({
                "success": False,
                "error": "Consulta demasiado larga"
            }, status_code=400)
        
        # Generar respuesta
        respuesta = generar_respuesta_simple(query, query_type)
        
        # Respuesta básica
        response_data = {
            "success": True,
            "respuesta": respuesta,
            "referencias": [
                {
                    "title": "Biblioteca del Congreso Nacional",
                    "description": "Leyes chilenas vigentes",
                    "url": "https://www.bcn.cl/leychile/"
                },
                {
                    "title": "Ministerio del Medio Ambiente",
                    "description": "Información oficial ambiental",
                    "url": "https://mma.gob.cl/"
                }
            ]
        }
        
        # Información básica de empresa si se proporciona
        if query_type in ["empresa", "proyecto"] and company_name:
            response_data["empresa_info"] = {
                "nombre": company_name,
                "tipo": query_type,
                "estado": "Información básica (modo simplificado)"
            }
        
        return JSONResponse(response_data)
        
    except ValueError as e:
        return JSONResponse({
            "success": False,
            "error": "Formato de datos inválido"
        }, status_code=400)
    except Exception as e:
        return JSONResponse({
            "success": False,
            "error": f"Error interno: {str(e)[:100]}"
        }, status_code=500)

# Health check simplificado
@app.get("/health")
async def health_check():
    """Health check ultra-simple"""
    return {
        "status": "healthy",
        "message": "MERLIN funcionando",
        "version": "2.0-simple"
    }

# Test endpoint
@app.get("/test")
async def test_endpoint():
    """Test básico"""
    try:
        test_response = generar_respuesta_simple("test")
        return {
            "status": "ok",
            "message": "Sistema funcionando",
            "test_length": len(test_response),
            "version": "2.0-simple"
        }
    except Exception as e:
        return {
            "status": "error",
            "error": str(e)[:100]
        }

if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8000) 