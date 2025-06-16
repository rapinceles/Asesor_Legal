# main.py - VERSIÓN REFACTORIZADA
from fastapi import FastAPI, Form, UploadFile, File, Request
from fastapi.responses import HTMLResponse
from fastapi.staticfiles import StaticFiles
from fastapi.templating import Jinja2Templates
from typing import List

# <-- NUEVO: Importamos la función central de nuestro nuevo motor de análisis
from engine.analysis_engine import realizar_analisis_completo

app = FastAPI(title="Asesor Legal Ambiental Inteligente")

# Configurar carpetas estáticas y plantillas HTML (esto se mantiene igual)
app.mount("/static", StaticFiles(directory="static"), name="static")
templates = Jinja2Templates(directory="templates")

# Ruta raíz que carga la interfaz visual (esto se mantiene igual)
@app.get("/", response_class=HTMLResponse)
async def render_form(request: Request):
    return templates.TemplateResponse("index.html", {"request": request})


# Ruta para recibir y procesar formulario (AHORA MUCHO MÁS LIMPIA)
@app.post("/analizar_formulario/")
async def analizar_formulario(
    analisis: str = Form(...),
    empresa: str = Form(...),
    sector: str = Form(...),
    documentos: List[UploadFile] = File(default=None)
):
    # --- PASO 1: PROCESAR DOCUMENTOS SUBIDOS (Lógica simplificada aquí) ---
    # <-- CAMBIO: Sacamos la lógica de decodificación compleja para mantener este archivo limpio.
    # La moveremos al motor de análisis en el futuro, por ahora leemos el texto.
    contenidos_docs = []
    if documentos:
        for doc in documentos:
            if doc.filename:
                contenido_bytes = await doc.read()
                # Una decodificación simple por ahora. La robusta estará en el engine.
                contenidos_docs.append(contenido_bytes.decode('utf-8', errors='ignore'))

    # --- PASO 2: DELEGAR TODA LA LÓGICA AL MOTOR DE ANÁLISIS ---
    # <-- ¡CAMBIO PRINCIPAL! Ya no hay if/elif, ni scrapers, ni prompts aquí.
    # Simplemente llamamos a nuestra función centralizada y esperamos el resultado.
    try:
        print(f"Delegando análisis al 'analysis_engine' para el sector: {sector}")
        
        # Llamamos a la función del motor con todos los datos necesarios
        respuesta_final = realizar_analisis_completo(
            empresa=empresa,
            analisis=analisis,
            sector=sector,
            documentos=contenidos_docs
        )
        
        return respuesta_final

    except Exception as e:
        # <-- CAMBIO: Un error general aquí probablemente sea un problema en la llamada
        # al motor de análisis o un error inesperado no controlado.
        print(f"Error inesperado en main.py al llamar al motor de análisis: {e}")
        return f"Ocurrió un error crítico en el orquestador principal de la aplicación: {str(e)}"
