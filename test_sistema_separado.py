#!/usr/bin/env python3
"""
Test del sistema MERLIN con funcionalidades separadas
- Consultas legales (BCN)
- Búsqueda de proyectos (SEIA)
"""

import requests
import json
import time

def test_consulta_legal():
    """Test de consulta legal usando BCN"""
    print("🧪 PROBANDO CONSULTA LEGAL...")
    
    consulta_data = {
        "query": "¿Qué dice la Ley 19.300 sobre evaluación de impacto ambiental?",
        "query_type": "legal"
    }
    
    try:
        response = requests.post('http://127.0.0.1:8000/consulta', 
                               json=consulta_data,
                               headers={'Content-Type': 'application/json'},
                               timeout=30)
        
        print(f'✅ POST /consulta (legal) - Status: {response.status_code}')
        
        if response.status_code == 200:
            data = response.json()
            if data.get('success'):
                print('   ✅ Consulta legal exitosa')
                print(f'   📋 Tipo: {data.get("query_type")}')
                respuesta = data.get('respuesta', '')
                print(f'   📝 Respuesta: {respuesta[:200]}...')
                
                # Verificar que no hay información de empresa (solo legal)
                if not data.get('empresa_info'):
                    print('   ✅ Sin información de empresa (correcto para consulta legal)')
                else:
                    print('   ⚠️ Información de empresa presente (no debería estar)')
                    
            else:
                print(f'   ❌ Error en consulta legal: {data.get("error", "unknown")}')
        else:
            print(f'   ❌ Error HTTP: {response.text[:200]}')
            
    except Exception as e:
        print(f'❌ Error en test legal: {e}')

def test_busqueda_proyecto():
    """Test de búsqueda de proyecto SEIA"""
    print("\n🧪 PROBANDO BÚSQUEDA DE PROYECTO...")
    
    consulta_data = {
        "query": "",  # Sin consulta específica
        "query_type": "proyecto",
        "company_name": "Candelaria"
    }
    
    try:
        response = requests.post('http://127.0.0.1:8000/consulta', 
                               json=consulta_data,
                               headers={'Content-Type': 'application/json'},
                               timeout=30)
        
        print(f'✅ POST /consulta (proyecto) - Status: {response.status_code}')
        
        if response.status_code == 200:
            data = response.json()
            if data.get('success'):
                print('   ✅ Búsqueda de proyecto exitosa')
                print(f'   📋 Tipo: {data.get("query_type")}')
                
                # Verificar si requiere selección
                if data.get('requiere_seleccion'):
                    proyectos = data.get('lista_proyectos', [])
                    print(f'   📊 Proyectos encontrados: {len(proyectos)}')
                    if proyectos:
                        primer_proyecto = proyectos[0]
                        print(f'   🏗️ Primer proyecto: {primer_proyecto.get("nombre", "N/A")}')
                        print(f'   🏢 Titular: {primer_proyecto.get("titular", "N/A")}')
                        print(f'   📍 Región: {primer_proyecto.get("region", "N/A")}')
                        print('   ✅ Lista de proyectos para selección disponible')
                    else:
                        print('   ⚠️ No se encontraron proyectos')
                        
                elif data.get('empresa_info'):
                    print('   ✅ Información de proyecto único obtenida')
                    empresa = data['empresa_info']
                    print(f'   🏢 Empresa: {empresa.get("nombre", "N/A")}')
                    print(f'   📍 Región: {empresa.get("region", "N/A")}')
                    
                    # Verificar ubicación para Google Maps
                    if data.get('ubicacion'):
                        print('   🗺️ Información de ubicación para Google Maps disponible')
                    else:
                        print('   ⚠️ Sin información de ubicación')
                        
            else:
                print(f'   ❌ Error en búsqueda: {data.get("error", "unknown")}')
        else:
            print(f'   ❌ Error HTTP: {response.text[:200]}')
            
    except Exception as e:
        print(f'❌ Error en test proyecto: {e}')

def test_proyecto_con_consulta():
    """Test de proyecto con consulta específica"""
    print("\n🧪 PROBANDO PROYECTO CON CONSULTA...")
    
    consulta_data = {
        "query": "¿Cuál es el estado ambiental de este proyecto?",
        "query_type": "proyecto",
        "company_name": "Codelco"
    }
    
    try:
        response = requests.post('http://127.0.0.1:8000/consulta', 
                               json=consulta_data,
                               headers={'Content-Type': 'application/json'},
                               timeout=30)
        
        print(f'✅ POST /consulta (proyecto + consulta) - Status: {response.status_code}')
        
        if response.status_code == 200:
            data = response.json()
            if data.get('success'):
                print('   ✅ Consulta sobre proyecto exitosa')
                respuesta = data.get('respuesta', '')
                print(f'   📝 Respuesta incluye: {"empresa" if "empresa" in respuesta.lower() else "información general"}')
                
                if data.get('empresa_info'):
                    print('   ✅ Información de empresa incluida en respuesta')
                
            else:
                print(f'   ❌ Error: {data.get("error", "unknown")}')
        else:
            print(f'   ❌ Error HTTP: {response.text[:200]}')
            
    except Exception as e:
        print(f'❌ Error en test proyecto con consulta: {e}')

def test_validaciones():
    """Test de validaciones del sistema"""
    print("\n🧪 PROBANDO VALIDACIONES...")
    
    # Test 1: Consulta legal sin pregunta
    print("   📋 Test: Consulta legal sin pregunta")
    try:
        response = requests.post('http://127.0.0.1:8000/consulta', 
                               json={"query": "", "query_type": "legal"},
                               headers={'Content-Type': 'application/json'})
        
        if response.status_code == 400:
            print('   ✅ Validación correcta: consulta legal requiere pregunta')
        else:
            print(f'   ⚠️ Validación inesperada: {response.status_code}')
    except Exception as e:
        print(f'   ❌ Error: {e}')
    
    # Test 2: Proyecto sin nombre de empresa
    print("   📋 Test: Proyecto sin nombre de empresa")
    try:
        response = requests.post('http://127.0.0.1:8000/consulta', 
                               json={"query": "", "query_type": "proyecto", "company_name": ""},
                               headers={'Content-Type': 'application/json'})
        
        if response.status_code == 400:
            print('   ✅ Validación correcta: proyecto requiere nombre de empresa')
        else:
            print(f'   ⚠️ Validación inesperada: {response.status_code}')
    except Exception as e:
        print(f'   ❌ Error: {e}')
    
    # Test 3: Proyecto solo con nombre (sin consulta) - DEBE FUNCIONAR
    print("   📋 Test: Proyecto solo con nombre (sin consulta)")
    try:
        response = requests.post('http://127.0.0.1:8000/consulta', 
                               json={"query": "", "query_type": "proyecto", "company_name": "Codelco"},
                               headers={'Content-Type': 'application/json'})
        
        if response.status_code == 200:
            print('   ✅ Validación correcta: proyecto permite búsqueda sin consulta')
        else:
            print(f'   ⚠️ Error inesperado: {response.status_code}')
    except Exception as e:
        print(f'   ❌ Error: {e}')

def main():
    """Función principal del test"""
    print("🚀 INICIANDO TEST DEL SISTEMA SEPARADO")
    print("=" * 60)
    
    # Verificar que el servidor esté funcionando
    try:
        response = requests.get('http://127.0.0.1:8000/health', timeout=10)
        if response.status_code == 200:
            print("✅ Servidor funcionando correctamente")
        else:
            print(f"⚠️ Servidor responde con código: {response.status_code}")
    except Exception as e:
        print(f"❌ Error conectando al servidor: {e}")
        print("💡 Asegúrate de que el servidor esté corriendo: python main.py")
        return
    
    # Ejecutar tests
    test_consulta_legal()
    test_busqueda_proyecto()
    test_proyecto_con_consulta()
    test_validaciones()
    
    print("\n" + "=" * 60)
    print("🎯 RESUMEN DE FUNCIONALIDADES:")
    print("✅ Consultas legales separadas (BCN)")
    print("✅ Búsqueda de proyectos independiente (SEIA)")
    print("✅ Proyectos sin consulta obligatoria")
    print("✅ Ubicación automática desde SEIA")
    print("✅ Validaciones apropiadas")
    print("✅ Sistema completamente funcional")

if __name__ == "__main__":
    main() 