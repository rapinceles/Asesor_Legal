import openai
import json

def generar_analisis(nombre_empresa, datos_seia):
    try:
        if not datos_seia.get("proyectos"):
            return "No se encontraron proyectos para esta empresa en el SEIA."

        proyectos_texto = json.dumps(datos_seia["proyectos"], ensure_ascii=False, indent=2)

        prompt = f"""
Eres un asesor legal y técnico ambiental chileno con experiencia en evaluación ambiental (SEIA), organismos sectoriales y normativa. 
Analiza la siguiente empresa y sus proyectos en el SEIA:

Nombre empresa: {nombre_empresa}

Proyectos:
{proyectos_texto}

Entrega:
1. Normativa aplicable.
2. Organismos evaluadores involucrados.
3. Riesgos técnicos comunes.
4. Recomendaciones para el cumplimiento legal y ambiental.
"""

        response = openai.ChatCompletion.create(
            model="gpt-3.5-turbo",
            messages=[
                {"role": "system", "content": "Eres un asesor legal ambiental experto."},
                {"role": "user", "content": prompt}
            ],
            temperature=0.5
        )

        return response.choices[0].message["content"]

    except Exception as e:
        return f"Error al generar análisis: {str(e)}"
