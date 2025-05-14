from openai import OpenAI
import os

client = OpenAI(api_key=os.getenv("OPENAI_API_KEY"))

def generar_analisis(nombre_empresa, datos, pregunta=""):
    proyectos = datos.get("proyectos", [])
    if not proyectos:
        return "No se encontraron proyectos para esta empresa en el SEIA."

    descripcion = f"Empresa: {nombre_empresa}\n\n"
    for p in proyectos:
        for k, v in p.items():
            descripcion += f"{k.capitalize()}: {v}\n"
        descripcion += "\n"

    prompt = f"""Eres un asesor legal ambiental en Chile. Analiza la siguiente información del SEIA sobre la empresa "{nombre_empresa}" y responde a la consulta: {pregunta}

    Información:
    {descripcion}

    Análisis:
    """

    try:
        response = client.chat.completions.create(
            model="gpt-4",
            messages=[
                {"role": "system", "content": "Eres un experto en normativa ambiental chilena."},
                {"role": "user", "content": prompt}
            ]
        )
        return response.choices[0].message.content
    except Exception as e:
        return f"Error al generar análisis: {e}"
