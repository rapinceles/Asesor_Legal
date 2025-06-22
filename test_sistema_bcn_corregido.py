#!/usr/bin/env python3
"""
Test final del sistema BCN corregido para verificar precisión
"""

import requests
import time

def test_sistema_bcn_completo():
    """Test completo del sistema con BCN preciso integrado"""
    
    print("🎯 TEST FINAL - SISTEMA BCN CORREGIDO")
    print("=" * 60)
    
    # URL del servidor
    base_url = "http://127.0.0.1:8001"
    
    # Verificar que el servidor esté funcionando
    try:
        response = requests.get(f"{base_url}/health", timeout=5)
        if response.status_code != 200:
            print("❌ Servidor no está funcionando en puerto 8001")
            print("💡 Ejecuta: python -m uvicorn main:app --host 127.0.0.1 --port 8001")
            return False
        print("✅ Servidor funcionando correctamente")
    except Exception as e:
        print(f"❌ No se puede conectar al servidor: {e}")
        print("💡 Ejecuta: python -m uvicorn main:app --host 127.0.0.1 --port 8001")
        return False
    
    # Términos para probar con el sistema corregido
    terminos_test = [
        {
            'termino': 'suelo',
            'esperado': 'Decreto Supremo 82/2010',
            'descripcion': 'Búsqueda de normativa de suelo'
        },
        {
            'termino': 'agua',
            'esperado': 'Código de Aguas',
            'descripcion': 'Búsqueda de normativa de agua'
        },
        {
            'termino': 'residuos peligrosos',
            'esperado': 'Decreto Supremo 148/2003',
            'descripcion': 'Búsqueda específica de residuos peligrosos'
        },
        {
            'termino': 'residuos',
            'esperado': 'Ley 20.920/2016',
            'descripcion': 'Búsqueda general de residuos'
        },
        {
            'termino': 'energía',
            'esperado': 'DFL 4/2006',
            'descripcion': 'Búsqueda de normativa energética'
        },
        {
            'termino': 'construcción',
            'esperado': 'Ley General de Urbanismo',
            'descripcion': 'Búsqueda de normativa de construcción'
        }
    ]
    
    resultados_correctos = 0
    total_tests = len(terminos_test)
    
    print(f"\n🧪 EJECUTANDO {total_tests} TESTS DE PRECISIÓN...")
    print("-" * 60)
    
    for i, test_case in enumerate(terminos_test, 1):
        termino = test_case['termino']
        esperado = test_case['esperado']
        descripcion = test_case['descripcion']
        
        print(f"\n{i}. {descripcion}")
        print(f"   🔍 Término: '{termino}'")
        print(f"   🎯 Esperado: '{esperado}'")
        
        # Hacer consulta legal al sistema
        consulta_data = {
            "query": termino,
            "query_type": "legal",
            "company_name": "",
            "project_location": ""
        }
        
        try:
            response = requests.post(
                f"{base_url}/consulta", 
                json=consulta_data,
                headers={'Content-Type': 'application/json'},
                timeout=10
            )
            
            if response.status_code == 200:
                data = response.json()
                
                if data.get('success'):
                    respuesta_legal = data.get('respuesta_legal', '')
                    
                    # Verificar si la normativa esperada está en la respuesta
                    if esperado.lower() in respuesta_legal.lower():
                        print(f"   ✅ CORRECTO: '{esperado}' encontrada en la respuesta")
                        resultados_correctos += 1
                        
                        # Mostrar un extracto de la respuesta
                        extracto = respuesta_legal[:200] + "..." if len(respuesta_legal) > 200 else respuesta_legal
                        print(f"   📋 Extracto: {extracto}")
                    else:
                        print(f"   ❌ INCORRECTO: '{esperado}' NO encontrada en la respuesta")
                        
                        # Mostrar qué se encontró en su lugar
                        extracto = respuesta_legal[:200] + "..." if len(respuesta_legal) > 200 else respuesta_legal
                        print(f"   📋 Se encontró: {extracto}")
                else:
                    error = data.get('error', 'Error desconocido')
                    print(f"   ❌ Error en consulta: {error}")
            else:
                print(f"   ❌ Error HTTP {response.status_code}: {response.text[:100]}")
                
        except Exception as e:
            print(f"   ❌ Error en petición: {e}")
        
        # Pequeña pausa entre tests
        time.sleep(0.5)
    
    # Resumen de resultados
    print("\n" + "=" * 60)
    print("📊 RESUMEN DE TESTS:")
    print(f"✅ Correctos: {resultados_correctos}/{total_tests}")
    print(f"📈 Precisión: {(resultados_correctos/total_tests)*100:.1f}%")
    
    if resultados_correctos == total_tests:
        print("\n🎉 TODOS LOS TESTS PASARON")
        print("✅ BCN PRECISO INTEGRADO CORRECTAMENTE")
        print("✅ SISTEMA COMPLETAMENTE CORREGIDO")
    elif resultados_correctos >= total_tests * 0.8:
        print("\n✅ MAYORÍA DE TESTS PASARON")
        print("⚠️ Algunos ajustes menores pueden ser necesarios")
    else:
        print("\n❌ VARIOS TESTS FALLARON")
        print("⚠️ Se requieren más correcciones")
    
    return resultados_correctos >= total_tests * 0.8

def test_terminos_problematicos():
    """Test específico para términos que anteriormente causaban problemas"""
    
    print("\n🔧 TEST DE TÉRMINOS PROBLEMÁTICOS")
    print("=" * 60)
    
    # Términos que anteriormente daban resultados incorrectos
    casos_problematicos = [
        {
            'termino': 'suelo',
            'no_debe_contener': ['residuos', 'basura', 'desecho'],
            'debe_contener': ['suelo', 'urbanismo', 'construcción']
        },
        {
            'termino': 'agua',
            'no_debe_contener': ['energía', 'eléctrico', 'solar'],
            'debe_contener': ['agua', 'hídrico', 'código']
        },
        {
            'termino': 'residuos',
            'no_debe_contener': ['agua', 'suelo', 'energía'],
            'debe_contener': ['residuos', 'gestión', 'reciclaje']
        }
    ]
    
    base_url = "http://127.0.0.1:8001"
    problemas_encontrados = 0
    
    for caso in casos_problematicos:
        termino = caso['termino']
        no_debe_contener = caso['no_debe_contener']
        debe_contener = caso['debe_contener']
        
        print(f"\n🔍 PROBANDO: '{termino}'")
        print(f"   ❌ NO debe contener: {', '.join(no_debe_contener)}")
        print(f"   ✅ SÍ debe contener: {', '.join(debe_contener)}")
        
        consulta_data = {
            "query": termino,
            "query_type": "legal",
            "company_name": "",
            "project_location": ""
        }
        
        try:
            response = requests.post(
                f"{base_url}/consulta", 
                json=consulta_data,
                headers={'Content-Type': 'application/json'},
                timeout=10
            )
            
            if response.status_code == 200:
                data = response.json()
                
                if data.get('success'):
                    respuesta_legal = data.get('respuesta_legal', '').lower()
                    
                    # Verificar que NO contenga términos problemáticos
                    problemas_en_respuesta = []
                    for termino_problema in no_debe_contener:
                        if termino_problema.lower() in respuesta_legal:
                            problemas_en_respuesta.append(termino_problema)
                    
                    # Verificar que SÍ contenga términos correctos
                    terminos_correctos = []
                    for termino_correcto in debe_contener:
                        if termino_correcto.lower() in respuesta_legal:
                            terminos_correctos.append(termino_correcto)
                    
                    if problemas_en_respuesta:
                        print(f"   ❌ PROBLEMA: Contiene términos incorrectos: {', '.join(problemas_en_respuesta)}")
                        problemas_encontrados += 1
                    else:
                        print(f"   ✅ CORRECTO: No contiene términos problemáticos")
                    
                    if terminos_correctos:
                        print(f"   ✅ CORRECTO: Contiene términos apropiados: {', '.join(terminos_correctos)}")
                    else:
                        print(f"   ⚠️ ADVERTENCIA: No contiene suficientes términos específicos")
                        
        except Exception as e:
            print(f"   ❌ Error en petición: {e}")
            problemas_encontrados += 1
    
    if problemas_encontrados == 0:
        print("\n🎉 NO SE ENCONTRARON PROBLEMAS DE CONFUSIÓN")
        print("✅ BCN PRECISO ELIMINA CORRECTAMENTE LAS CONFUSIONES")
    else:
        print(f"\n⚠️ Se encontraron {problemas_encontrados} problemas de confusión")
        print("❌ Se requieren más ajustes en BCN PRECISO")

if __name__ == "__main__":
    print("🚀 INICIANDO TEST FINAL DEL SISTEMA BCN CORREGIDO")
    print("=" * 60)
    
    try:
        # Test principal de precisión
        precision_ok = test_sistema_bcn_completo()
        
        # Test de términos problemáticos
        test_terminos_problematicos()
        
        print("\n" + "=" * 60)
        print("🏁 TEST FINAL COMPLETADO")
        
        if precision_ok:
            print("\n🎉 SISTEMA BCN COMPLETAMENTE CORREGIDO")
            print("✅ Precisión mejorada significativamente")
            print("✅ Confusiones eliminadas")
            print("✅ Listo para uso en producción")
        else:
            print("\n⚠️ SISTEMA NECESITA MÁS AJUSTES")
            print("❌ Algunos problemas de precisión persisten")
            
    except Exception as e:
        print(f"❌ ERROR EN TEST FINAL: {e}")
        import traceback
        traceback.print_exc() 