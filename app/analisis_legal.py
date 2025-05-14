import os
import openai

openai.api_key = os.getenv("OPENAI_API_KEY")

def generar_analisis(nombre_empresa, datos_empresa, pregunta_usuario="", tipo_asesor=""):
    try:
        contexto = f"""
Eres un asesor legal ambiental experto en normativa chilena. Analiza la situación de la empresa "{nombre_empresa}".

Tipo de asesor: {tipo_asesor}
Consulta del usuario: {pregunta_usuario}

Datos extraídos del SEIA:
{datos_empresa}

Proporciona un análisis claro, técnico y con recomendaciones legales específicas.
"""
        respuesta = openai.ChatCompletion.create(
            model="gpt-4",
            messages=[
                {"role": "system", "content": "Eres un asesor experto en normativa ambiental, legal y técnica chilena."},
                {"role": "user", "content": contexto}
            ],
            temperature=0.5
        )
        return respuesta.choices[0].message["content"].strip()
    except Exception as e:
        return f"Error al generar análisis: {str(e)}"
