#!/usr/bin/env python3
"""
Test del scraper BCN preciso para verificar precisión en búsquedas
"""

import sys
import os
sys.path.append(os.path.dirname(os.path.abspath(__file__)))

from scrapers.bcn_preciso import obtener_normativa_bcn_precisa

def test_terminos_especificos():
    """Test de términos específicos que deben dar resultados precisos"""
    
    print("🎯 TESTING BCN PRECISO - VERIFICACIÓN DE PRECISIÓN")
    print("=" * 60)
    
    # Términos que deben dar resultados específicos y precisos
    terminos_test = [
        ('suelo', 'Decreto Supremo 82/2010'),
        ('agua', 'Código de Aguas'),
        ('residuos peligrosos', 'Decreto Supremo 148/2003'),
        ('residuos', 'Ley 20.920/2016'),
        ('energía', 'DFL 4/2006'),
        ('minería', 'Código de Minería'),
        ('construcción', 'Ley General de Urbanismo'),
        ('forestal', 'Ley 20.283/2008'),
        ('pesca', 'Ley General de Pesca'),
        ('transporte', 'Ley de Tránsito'),
        ('laboral', 'Código del Trabajo')
    ]
    
    resultados_correctos = 0
    total_tests = len(terminos_test)
    
    for termino, normativa_esperada in terminos_test:
        print(f"\n🔍 PROBANDO: '{termino}'")
        print("-" * 40)
        
        resultado = obtener_normativa_bcn_precisa(termino)
        
        if resultado.get('success'):
            categoria = resultado.get('categoria_encontrada')
            precision = resultado.get('precision')
            total_resultados = resultado.get('total_resultados', 0)
            
            print(f"✅ Éxito: {categoria} ({precision})")
            print(f"📊 Resultados: {total_resultados}")
            
            # Verificar que el primer resultado contiene la normativa esperada
            resultados = resultado.get('resultados', [])
            if resultados:
                primer_resultado = resultados[0]
                titulo = primer_resultado.get('titulo', '')
                
                if normativa_esperada.lower() in titulo.lower():
                    print(f"🎯 CORRECTO: '{normativa_esperada}' encontrada en '{titulo[:80]}...'")
                    resultados_correctos += 1
                else:
                    print(f"⚠️ IMPRECISO: Se esperaba '{normativa_esperada}' pero se encontró '{titulo[:80]}...'")
                
                # Mostrar los primeros 3 resultados
                print("📋 Primeros resultados:")
                for i, r in enumerate(resultados[:3], 1):
                    print(f"  {i}. {r.get('titulo', 'Sin título')[:60]}...")
            else:
                print("❌ No hay resultados")
        else:
            error = resultado.get('error', 'Error desconocido')
            print(f"❌ Error: {error}")
            sugerencias = resultado.get('sugerencias', [])
            if sugerencias:
                print(f"💡 Sugerencias: {', '.join(sugerencias[:5])}")

    print("\n" + "=" * 60)
    print(f"📊 RESUMEN DE PRECISIÓN:")
    print(f"✅ Correctos: {resultados_correctos}/{total_tests}")
    print(f"📈 Precisión: {(resultados_correctos/total_tests)*100:.1f}%")
    
    if resultados_correctos == total_tests:
        print("🎉 TODOS LOS TESTS PASARON - BCN PRECISO FUNCIONANDO PERFECTAMENTE")
    elif resultados_correctos >= total_tests * 0.8:
        print("✅ MAYORÍA DE TESTS PASARON - BCN PRECISO FUNCIONANDO BIEN")
    else:
        print("⚠️ VARIOS TESTS FALLARON - BCN PRECISO NECESITA AJUSTES")
    
    return resultados_correctos == total_tests

def test_terminos_problematicos():
    """Test de términos que anteriormente causaban confusión"""
    
    print("\n🔧 TESTING TÉRMINOS PROBLEMÁTICOS")
    print("=" * 60)
    
    # Términos que anteriormente daban resultados incorrectos
    terminos_problematicos = [
        ('suelo', 'NO debe devolver residuos'),
        ('agua', 'NO debe devolver energía'),
        ('residuos', 'NO debe devolver residuos peligrosos específicamente'),
        ('energía', 'NO debe devolver agua'),
        ('construcción', 'NO debe devolver minería')
    ]
    
    for termino, expectativa in terminos_problematicos:
        print(f"\n🔍 PROBANDO: '{termino}' - {expectativa}")
        print("-" * 50)
        
        resultado = obtener_normativa_bcn_precisa(termino)
        
        if resultado.get('success'):
            categoria = resultado.get('categoria_encontrada')
            resultados = resultado.get('resultados', [])
            
            print(f"✅ Categoría encontrada: {categoria}")
            
            # Verificar que los resultados sean específicos del término
            if resultados:
                primer_titulo = resultados[0].get('titulo', '').lower()
                
                # Verificaciones específicas
                if termino == 'suelo' and 'residuo' in primer_titulo:
                    print("❌ ERROR: 'suelo' devolvió normativa de residuos")
                elif termino == 'agua' and ('energía' in primer_titulo or 'eléctrico' in primer_titulo):
                    print("❌ ERROR: 'agua' devolvió normativa de energía")
                elif termino == 'residuos' and 'peligroso' in primer_titulo:
                    print("⚠️ ADVERTENCIA: 'residuos' devolvió residuos peligrosos específicamente")
                elif termino == 'energía' and 'agua' in primer_titulo:
                    print("❌ ERROR: 'energía' devolvió normativa de agua")
                elif termino == 'construcción' and 'minería' in primer_titulo:
                    print("❌ ERROR: 'construcción' devolvió normativa de minería")
                else:
                    print(f"✅ CORRECTO: Resultado específico para '{termino}'")
                
                print(f"📋 Primer resultado: {resultados[0].get('titulo', '')[:80]}...")
        else:
            print(f"❌ No se encontraron resultados para '{termino}'")

def test_terminos_invalidos():
    """Test de términos que no deben dar resultados"""
    
    print("\n🚫 TESTING TÉRMINOS INVÁLIDOS")
    print("=" * 60)
    
    terminos_invalidos = [
        'xyz123',
        'término inexistente',
        'abcdefgh',
        'palabra inventada',
        'normativa falsa'
    ]
    
    for termino in terminos_invalidos:
        print(f"\n🔍 PROBANDO: '{termino}'")
        resultado = obtener_normativa_bcn_precisa(termino)
        
        if resultado.get('success'):
            print(f"⚠️ INESPERADO: Se encontraron resultados para término inválido")
            resultados = resultado.get('resultados', [])
            if resultados:
                print(f"📋 Resultado: {resultados[0].get('titulo', '')[:60]}...")
        else:
            print(f"✅ CORRECTO: No se encontraron resultados (como se esperaba)")
            sugerencias = resultado.get('sugerencias', [])
            if sugerencias:
                print(f"💡 Sugerencias ofrecidas: {', '.join(sugerencias[:3])}")

if __name__ == "__main__":
    print("🚀 INICIANDO TESTS DEL SCRAPER BCN PRECISO")
    print("=" * 60)
    
    try:
        # Test principal de precisión
        precision_ok = test_terminos_especificos()
        
        # Test de términos problemáticos
        test_terminos_problematicos()
        
        # Test de términos inválidos
        test_terminos_invalidos()
        
        print("\n" + "=" * 60)
        print("🏁 TESTS COMPLETADOS")
        
        if precision_ok:
            print("🎉 BCN PRECISO ESTÁ FUNCIONANDO CORRECTAMENTE")
            print("✅ Listo para integración en el sistema principal")
        else:
            print("⚠️ BCN PRECISO NECESITA AJUSTES ANTES DE LA INTEGRACIÓN")
            
    except Exception as e:
        print(f"❌ ERROR EN TESTS: {e}")
        import traceback
        traceback.print_exc() 