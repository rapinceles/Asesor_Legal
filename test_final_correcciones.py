#!/usr/bin/env python3
"""
Test final de las correcciones del sistema MERLIN
"""

import requests
import time

def test_bcn_correcto():
    """Test que BCN devuelve normativas específicas según el término"""
    print("🔍 PROBANDO CORRECCIONES BCN...")
    print("=" * 50)
    
    casos = [
        {'termino': 'suelo', 'debe_contener': 'suelo'},
        {'termino': 'agua', 'debe_contener': 'agua'},
        {'termino': 'energía', 'debe_contener': 'energía'},
        {'termino': 'construcción', 'debe_contener': 'construcción'}
    ]
    
    for caso in casos:
        print(f"\n🧪 Probando: '{caso['termino']}'")
        
        try:
            response = requests.post('http://127.0.0.1:8000/consulta', 
                                   json={
                                       'query_type': 'legal',
                                       'query': caso['termino']
                                   },
                                   timeout=15)
            
            if response.status_code == 200:
                data = response.json()
                if data.get('success'):
                    respuesta = data.get('respuesta', '').lower()
                    
                    # Verificar que contiene el término específico
                    if caso['debe_contener'] in respuesta:
                        print(f"   ✅ CORRECTO: Contiene '{caso['debe_contener']}'")
                    else:
                        print(f"   ❌ ERROR: No contiene '{caso['debe_contener']}'")
                    
                    # Verificar que no es solo genérico
                    if "normativa legal encontrada" in respuesta or caso['debe_contener'] in respuesta:
                        print(f"   ✅ Respuesta específica para '{caso['termino']}'")
                    else:
                        print(f"   ⚠️ Respuesta genérica para '{caso['termino']}'")
                        
                else:
                    print(f"   ❌ Error en consulta")
            else:
                print(f"   ❌ Error HTTP: {response.status_code}")
                
        except Exception as e:
            print(f"   ❌ Excepción: {e}")
        
        time.sleep(0.5)

def test_proyectos_sin_502():
    """Test que proyectos no den error 502"""
    print("\n🏢 PROBANDO CORRECCIONES PROYECTOS...")
    print("=" * 50)
    
    empresas = ['Codelco', 'Candelaria', 'Escondida']
    
    for empresa in empresas:
        print(f"\n🧪 Probando: '{empresa}'")
        
        try:
            response = requests.post('http://127.0.0.1:8000/consulta', 
                                   json={
                                       'query_type': 'proyecto',
                                       'company_name': empresa
                                   },
                                   timeout=15)
            
            print(f"   Status: {response.status_code}")
            
            if response.status_code == 200:
                data = response.json()
                if data.get('success'):
                    print(f"   ✅ CORRECTO: Sin error 502")
                    
                    if data.get('requiere_seleccion'):
                        proyectos = len(data.get('lista_proyectos', []))
                        print(f"   📊 {proyectos} proyectos encontrados")
                    else:
                        print(f"   📄 Información directa obtenida")
                else:
                    print(f"   ⚠️ Respuesta no exitosa")
            elif response.status_code == 502:
                print(f"   ❌ ERROR 502 DETECTADO - CORRECCIÓN FALLIDA")
            else:
                print(f"   ⚠️ Status inesperado: {response.status_code}")
                
        except Exception as e:
            print(f"   ❌ Excepción: {e}")
        
        time.sleep(0.5)

def main():
    """Función principal"""
    print("🚀 TEST FINAL DE CORRECCIONES")
    print("=" * 60)
    
    # Verificar servidor
    try:
        response = requests.get('http://127.0.0.1:8000/health', timeout=5)
        if response.status_code == 200:
            print("✅ Servidor funcionando")
        else:
            print(f"❌ Servidor con problemas: {response.status_code}")
            return
    except Exception as e:
        print(f"❌ No se puede conectar: {e}")
        return
    
    # Ejecutar tests
    test_bcn_correcto()
    test_proyectos_sin_502()
    
    print("\n🎯 RESULTADO FINAL:")
    print("=" * 40)
    print("✅ BCN: Debe mostrar normativas específicas")
    print("✅ Proyectos: No debe dar error 502")
    print("\n📋 PARA VERIFICAR MANUALMENTE:")
    print("1. Abrir: http://127.0.0.1:8000")
    print("2. Probar 'suelo' en consulta legal")
    print("3. Probar 'Codelco' en búsqueda de proyectos")

if __name__ == "__main__":
    main() 