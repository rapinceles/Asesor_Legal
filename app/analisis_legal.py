import os
import openai

openai.api_key = os.getenv("OPENAI_API_KEY")

def generar_analisis(nombre, datos):
    prompt = f"""
    Analiza la empresa {nombre} en el contexto del SEIA.
    Tiene proyectos como: {datos['proyectos']} en la región {datos['region']} (sector {datos['sector']}).
    Identifica normas legales aplicables (ambientales, civiles, penales, administrativas, económicas, etc.).
    Detecta vacíos legales y propón cómo abordarlos con medidas técnicas y legales.
    """
    response = openai.ChatCompletion.create(
        model="gpt-4",
        messages=[{"role": "user", "content": prompt}],
        temperature=0.7
    )
    return response.choices[0]["message"]["content"]
