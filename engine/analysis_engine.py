# engine/analysis_engine.py
# Motor de análisis mejorado para MERLIN

import openai
import os
from typing import List, Optional

# Configurar la API de OpenAI
# openai.api_key = os.getenv("OPENAI_API_KEY")

def realizar_analisis_completo(empresa: str, analisis: str, sector: str, documentos: List[str]):
    """
    Esta función orquesta todo el proceso de análisis:
    1. Determina el tipo de análisis (general o empresarial)
    2. Construye el prompt apropiado
    3. Llama a la API de OpenAI
    4. Devuelve la respuesta final
    """
    
    try:
        client = openai.OpenAI()
        
        if not empresa:
            # Análisis general
            return realizar_analisis_general(client, analisis, documentos)
        else:
            # Análisis empresarial
            return realizar_analisis_empresarial(client, empresa, analisis, documentos)
            
    except Exception as e:
        print(f"Error en el motor de análisis: {e}")
        return generar_respuesta_error(str(e))

def realizar_analisis_general(client, consulta: str, documentos: List[str]):
    """
    Realiza análisis legal general sin contexto empresarial específico
    """
    
    system_prompt = """Eres MERLIN, un asesor legal especializado en derecho chileno. Tu función es:

1. Proporcionar información legal precisa basada en la legislación chilena vigente
2. Explicar conceptos legales de manera clara y comprensible
3. Citar las fuentes legales relevantes (leyes, códigos, reglamentos)
4. Advertir sobre limitaciones y recomendar consulta profesional cuando sea necesario
5. Mantener un tono profesional pero accesible

IMPORTANTE: 
- Siempre indica que tu respuesta es orientativa y no constituye asesoría legal profesional
- Recomienda consultar con un abogado para casos específicos
- Cita las fuentes legales cuando sea posible
- Si no tienes información suficiente, indícalo claramente"""

    texto_docs = "\n\n".join(documentos) if documentos else ""
    
    user_prompt = f"""
Consulta legal: {consulta}

{f"Documentos adjuntos para análisis: {texto_docs}" if texto_docs else ""}

Por favor, proporciona un análisis legal detallado de la consulta planteada, incluyendo:
1. Marco legal aplicable
2. Análisis de la situación
3. Recomendaciones prácticas
4. Fuentes legales citadas
"""

    try:
        response = client.chat.completions.create(
            model="gpt-3.5-turbo",
            messages=[
                {"role": "system", "content": system_prompt},
                {"role": "user", "content": user_prompt}
            ],
            temperature=0.7,
            max_tokens=1500
        )
        return response.choices[0].message.content
    except Exception as e:
        return f"Error al procesar la consulta legal: {str(e)}"

def realizar_analisis_empresarial(client, empresa: str, consulta: str, documentos: List[str]):
    """
    Realiza análisis específico de una empresa en el contexto ambiental
    """
    
    system_prompt = f"""Eres MERLIN, un asesor legal ambiental especializado en el marco regulatorio chileno. Tu función es:

1. Analizar el cumplimiento ambiental de empresas
2. Evaluar riesgos y obligaciones ambientales
3. Proporcionar recomendaciones específicas basadas en normativa chilena
4. Contextualizar la información con el historial de la empresa

Marco legal principal:
- Ley 19.300 (Bases Generales del Medio Ambiente)
- Decreto Supremo N° 40/2012 (Reglamento del SEIA)
- Normativas de la SMA (Superintendencia del Medio Ambiente)
- Resoluciones del SEA (Servicio de Evaluación Ambiental)

Enfoque del análisis para: {empresa}"""

    texto_docs = "\n\n".join(documentos) if documentos else ""
    
    if consulta.strip():
        user_prompt = f"""
Empresa: {empresa}
Consulta específica: {consulta}

{f"Documentos adicionales: {texto_docs}" if texto_docs else ""}

Realiza un análisis ambiental específico para {empresa} considerando:
1. Marco regulatorio aplicable
2. Obligaciones ambientales vigentes
3. Evaluación de riesgos específicos
4. Recomendaciones prácticas
5. Pasos a seguir recomendados

Contextualiza el análisis con la información disponible de la empresa en el SEIA y SNIFA.
"""
    else:
        user_prompt = f"""
Empresa: {empresa}

Realiza un análisis ambiental general para {empresa} que incluya:
1. Evaluación del cumplimiento ambiental
2. Identificación de obligaciones regulatorias
3. Análisis de riesgos ambientales
4. Recomendaciones para mantener el cumplimiento
5. Consideraciones para futuras operaciones

Basa el análisis en la información disponible de registros del SEIA y SNIFA.
"""

    try:
        response = client.chat.completions.create(
            model="gpt-3.5-turbo",
            messages=[
                {"role": "system", "content": system_prompt},
                {"role": "user", "content": user_prompt}
            ],
            temperature=0.7,
            max_tokens=2000
        )
        return response.choices[0].message.content
    except Exception as e:
        return f"Error al procesar el análisis empresarial: {str(e)}"

def generar_respuesta_error(error_msg: str) -> str:
    """
    Genera una respuesta de error amigable para el usuario
    """
    return f"""
    <div style="padding: 20px; background: rgba(255, 71, 87, 0.1); border: 1px solid rgba(255, 71, 87, 0.3); border-radius: 8px;">
        <h3 style="color: #ff4757; margin-bottom: 15px;">⚠️ Error en el Sistema</h3>
        <p>Lo sentimos, ha ocurrido un error al procesar su consulta:</p>
        <p><em>{error_msg}</em></p>
        <p>Por favor, intente nuevamente en unos momentos. Si el problema persiste, 
        contacte al administrador del sistema.</p>
        <p style="margin-top: 15px; font-size: 0.9em; color: #b0b0b0;">
            <strong>Sugerencias:</strong><br>
            • Verifique que su consulta esté bien formulada<br>
            • Asegúrese de que el nombre de la empresa sea correcto<br>
            • Intente con una consulta más específica
        </p>
    </div>
    """
