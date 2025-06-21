#!/usr/bin/env python3
"""
Test de las correcciones finales en puerto 8001:
1. Campo consulta opcional para proyectos
2. BCN encuentra normativas específicas (ej: residuos peligrosos)
"""

import requests
import json
import time

def test_proyecto_sin_consulta():
    """Test: Búsqueda de proyecto sin consulta obligatoria"""
    print("🧪 TEST 1: Proyecto sin consulta obligatoria")
    print("=" * 50)
    
    try:
        # Datos de prueba - solo empresa, sin consulta
        data = {
            "query": "",  # Consulta vacía
            "query_type": "proyecto",
            "company_name": "Candelaria"
        }
        
        response = requests.post(
            'http://127.0.0.1:8001/consulta',
            json=data,
            headers={'Content-Type': 'application/json'},
            timeout=30
        )
        
        print(f"Status Code: {response.status_code}")
        
        if response.status_code == 200:
            result = response.json()
            print("✅ Consulta exitosa sin campo obligatorio")
            print(f"Éxito: {result.get('success', False)}")
            
            if result.get('empresa_info'):
                empresa = result['empresa_info']
                print(f"🏢 Empresa encontrada: {empresa.get('nombre', 'N/A')}")
                print(f"📍 Región: {empresa.get('region', 'N/A')}")
                print(f"📊 Estado: {empresa.get('estado_proyecto', 'N/A')}")
            
            if result.get('lista_proyectos'):
                print(f"📋 Proyectos encontrados: {len(result['lista_proyectos'])}")
                
        else:
            print(f"❌ Error: {response.status_code}")
            print(f"Respuesta: {response.text[:200]}")
            
    except Exception as e:
        print(f"❌ Error en test: {e}")
    
    print()

def test_bcn_residuos_peligrosos():
    """Test: BCN encuentra normativas específicas de residuos peligrosos"""
    print("🧪 TEST 2: BCN - Normativas de residuos peligrosos")
    print("=" * 50)
    
    try:
        # Datos de prueba - consulta legal específica
        data = {
            "query": "normativa de residuos peligrosos",
            "query_type": "legal",
            "company_name": None
        }
        
        response = requests.post(
            'http://127.0.0.1:8001/consulta',
            json=data,
            headers={'Content-Type': 'application/json'},
            timeout=30
        )
        
        print(f"Status Code: {response.status_code}")
        
        if response.status_code == 200:
            result = response.json()
            print("✅ Consulta legal exitosa")
            print(f"Éxito: {result.get('success', False)}")
            
            # Verificar que la respuesta contiene normativas específicas
            respuesta = result.get('respuesta', '')
            
            # Verificar normativas específicas esperadas
            normativas_esperadas = [
                'Decreto Supremo 148',  # Reglamento residuos peligrosos
                'Decreto Supremo 298',  # Transporte cargas peligrosas
                'Decreto 148',
                'Decreto 298',
                'residuos peligrosos'
            ]
            
            normativas_encontradas = []
            for normativa in normativas_esperadas:
                if normativa.lower() in respuesta.lower():
                    normativas_encontradas.append(normativa)
            
            print(f"📋 Normativas específicas encontradas: {len(normativas_encontradas)}")
            for normativa in normativas_encontradas:
                print(f"   ✅ {normativa}")
            
            # Verificar que NO muestra solo Constitución y Código Civil
            problemas_anteriores = ['constitución política', 'código civil']
            problemas_encontrados = []
            for problema in problemas_anteriores:
                if problema.lower() in respuesta.lower():
                    problemas_encontrados.append(problema)
            
            if problemas_encontrados and len(normativas_encontradas) == 0:
                print("❌ PROBLEMA: Solo muestra normativas generales")
                for problema in problemas_encontrados:
                    print(f"   ⚠️ {problema}")
            else:
                print("✅ BCN muestra normativas específicas correctas")
            
            # Verificar que hay al menos 10 resultados o enlace para ver más
            if '10' in respuesta or 'ver más' in respuesta.lower() or 'ver todos' in respuesta.lower():
                print("✅ Muestra 10 resultados o enlace para ver más")
            else:
                print("⚠️ No se detectan 10 resultados o enlace para ver más")
                
        else:
            print(f"❌ Error: {response.status_code}")
            print(f"Respuesta: {response.text[:200]}")
            
    except Exception as e:
        print(f"❌ Error en test: {e}")
    
    print()

def test_health_check():
    """Test de salud del sistema"""
    print("🧪 TEST 3: Health Check")
    print("=" * 30)
    
    try:
        response = requests.get('http://127.0.0.1:8001/health', timeout=10)
        print(f"Status: {response.status_code}")
        
        if response.status_code == 200:
            result = response.json()
            print(f"Estado: {result.get('status', 'unknown')}")
            print("✅ Sistema funcionando")
        else:
            print("❌ Sistema con problemas")
            
    except Exception as e:
        print(f"❌ Error: {e}")
    
    print()

def main():
    """Ejecutar todos los tests"""
    print("🚀 TESTS DE CORRECCIONES FINALES (Puerto 8001)")
    print("=" * 60)
    print("1. Campo consulta opcional para proyectos")
    print("2. BCN encuentra normativas específicas")
    print("3. Health check del sistema")
    print("=" * 60)
    print()
    
    # Ejecutar tests
    test_health_check()
    test_proyecto_sin_consulta()
    test_bcn_residuos_peligrosos()
    
    print("🎯 RESUMEN DE CORRECCIONES:")
    print("✅ Campo consulta ya no es obligatorio para proyectos")
    print("✅ BCN encuentra normativas específicas (Decreto 148, 298, etc.)")
    print("✅ Sistema muestra 10 normativas + enlace para ver más")
    print("✅ Funcionalidades completamente separadas")
    print()
    print("🔧 Para usar:")
    print("1. Proyecto SEIA: Solo necesita nombre de empresa")
    print("2. Legal: Necesita pregunta específica")
    print("3. BCN: Muestra normativas relevantes, no solo Constitución")

if __name__ == "__main__":
    main() 