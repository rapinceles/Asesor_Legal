import os
from openai import OpenAI

client = OpenAI(api_key=os.getenv("OPENAI_API_KEY"))

def generar_analisis(nombre, datos):
    prompt = f"""
    Analiza la empresa {nombre} en el contexto del SEIA.
    Tiene proyectos como: {datos['proyectos']} en la región {datos['region']} (sector {datos['sector']}).
    Identifica normas legales aplicables (ambientales, civiles, penales, administrativas, económicas, etc.).
    Detecta vacíos legales y propón cómo abordarlos con medidas técnicas y legales.
    """
    try:
        response = client.chat.completions.create(
            model="gpt-3.5-turbo",
            messages=[
                {"role": "system", "content": "Eres un asesor legal y ambiental experto en minería."},
                {"role": "user", "content": prompt}
            ],
            temperature=0.7
        )
        return response.choices[0].message.content
    except Exception as e:
        return f"Error al generar análisis: {str(e)}"
