# engine/analysis_engine.py
# Este será el nuevo cerebro de nuestra aplicación.

import openai

def realizar_analisis_completo(empresa: str, analisis: str, sector: str, documentos: list):
    """
    Esta función orquesta todo el proceso de análisis:
    1. Consulta la base de datos local para obtener datos de SEIA, SNIFA y BCN.
    2. Procesa los documentos adjuntos.
    3. Construye un prompt detallado para la IA.
    4. Llama a la API de OpenAI.
    5. Devuelve la respuesta final.
    """
    # --- PASO 1: Consultar la Base de Datos (Lógica a implementar en los siguientes pasos) ---
    # Por ahora, simularemos la obtención de datos.
    # En el futuro, aquí llamaremos a funciones que hagan:
    # db.query(Proyectos_SEIA).filter_by(empresa=empresa)...
    # db.query(Sanciones_SNIFA).filter_by(empresa=empresa)...
    datos_db_seia = f"Búsqueda en SEIA para '{empresa}' realizada en la base de datos local. (Lógica pendiente)\n"
    datos_db_snifa = f"Búsqueda en SNIFA para '{empresa}' realizada en la base de datos local. (Lógica pendiente)\n"
    datos_db_bcn = f"Búsqueda en BCN para la consulta '{analisis}' realizada en la base de datos local. (Lógica pendiente)\n"

    datos_externos_formateados = ""
    if sector.lower() == "ambiental":
        datos_externos_formateados = datos_db_seia + datos_db_snifa # El análisis ambiental incluye SEIA y SNIFA
    elif sector.lower() == "legal":
        datos_externos_formateados = datos_db_bcn
    # ...y así para otros sectores.

    # --- PASO 2: Procesar documentos (esta lógica la pasaremos aquí más adelante) ---
    texto_docs = "\n\n".join(documentos) if documentos else "Sin documentos adjuntos."

    # --- PASO 3: Construir el prompt (la lógica que ya tenías) ---
    # (Esta lógica se moverá aquí desde main.py)
    client = openai.OpenAI()
    system_prompt_content = f"""Eres un asesor experto en normativa, regulaciones y análisis en Chile. Tu rol es: **{sector.capitalize()}**.""" # ... (el resto de tu prompt del sistema)
    prompt_user_content = f"""
Información para el análisis:
Empresa: {empresa}
Tipo de asesor solicitado: {sector}
Consulta específica: {analisis}
--- Datos Externos Obtenidos de nuestra Base de Datos ({sector}) ---
{datos_externos_formateados}
---------------------------------------
--- Contenido de Documentos Adjuntos ---
{texto_docs}
------------------------------------
Por favor, realiza el análisis solicitado.
"""
    # --- PASO 4: Llamar a la IA (la misma lógica que ya tenías) ---
    try:
        response = client.chat.completions.create(
            model="gpt-3.5-turbo",
            messages=[
                {"role": "system", "content": system_prompt_content},
                {"role": "user", "content": prompt_user_content}
            ],
            temperature=0.7
        )
        return response.choices[0].message.content
    except Exception as e:
        print(f"Error en el motor de análisis llamando a OpenAI: {e}")
        return f"Error al generar el análisis en el motor interno: {e}"
