import os
from openai import OpenAI

client = OpenAI(api_key=os.getenv("OPENAI_API_KEY"))

def generar_analisis(nombre_empresa, datos_empresa, pregunta_usuario="", tipo_asesor=""):
    try:
        contexto = f"""
Eres un asesor legal ambiental experto en normativa chilena. Analiza la situación de la empresa "{nombre_empresa}".

Tipo de asesor: {tipo_asesor}
Consulta específica: {pregunta_usuario}

Datos del SEIA:
{datos_empresa}

Proporciona un análisis técnico, claro y con recomendaciones legales aplicables.
"""

        respuesta = client.chat.completions.create(
            model="gpt-4-1106-preview",  # Usa el modelo correcto según tu cuenta
            messages=[
                {"role": "system", "content": "Eres un asesor legal ambiental experto en normativa chilena."},
                {"role": "user", "content": contexto}
            ],
            temperature=0.5
        )

        return respuesta.choices[0].message.content.strip()

    except Exception as e:
        return f"Error al generar análisis: {str(e)}"
