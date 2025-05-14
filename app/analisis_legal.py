import os
import openai

client = openai.OpenAI(api_key=os.getenv("OPENAI_API_KEY"))

def generar_analisis(nombre_empresa, datos_empresa, pregunta_usuario="", tipo_asesor=""):
    try:
        contexto = f"""
Eres un asesor experto en temas {tipo_asesor.lower()} y ambientales. Evalúa la empresa "{nombre_empresa}" considerando estos datos extraídos del SEIA:

{datos_empresa}

Pregunta o análisis solicitado: "{pregunta_usuario}"

Entrega un análisis claro, legalmente fundamentado y con lenguaje técnico apropiado.
"""

        respuesta = client.chat.completions.create(
            model="gpt-4",
            messages=[
                {"role": "system", "content": "Eres un asesor legal ambiental experto en normativa chilena."},
                {"role": "user", "content": contexto}
            ],
            temperature=0.3
        )

        return respuesta.choices[0].message.content.strip()

    except Exception as e:
        return f"Error al generar análisis: {e}"
