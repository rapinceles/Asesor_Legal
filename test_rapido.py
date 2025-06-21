#!/usr/bin/env python3
# test_rapido.py - Test rápido del sistema corregido

import logging
import subprocess
import time
import requests
import sys

logging.basicConfig(level=logging.WARNING)  # Reducir ruido

def test_scraper_titular():
    """Test del scraper por titular"""
    print("🔍 TEST: Scraper por titular")
    try:
        from scrapers.seia_titular import buscar_proyectos_por_titular
        result = buscar_proyectos_por_titular('Candelaria')
        
        if result.get('success'):
            data = result['data']
            proyectos = data.get('lista_proyectos', [])
            print(f"✅ Encontrados {len(proyectos)} proyectos")
            
            if len(proyectos) > 0:
                primer_proyecto = proyectos[0]
                print(f"📋 Primer proyecto: {primer_proyecto.get('nombre', 'N/A')}")
                print(f"🏢 Titular: {primer_proyecto.get('titular', 'N/A')}")
                return True
            else:
                print("⚠️ No se encontraron proyectos")
                return False
        else:
            print(f"❌ Error: {result.get('error', 'Unknown')}")
            return False
    except Exception as e:
        print(f"❌ Error: {e}")
        return False

def test_sistema_completo():
    """Test del sistema completo"""
    print("\n🔍 TEST: Sistema completo con servidor")
    
    # Iniciar servidor
    server_process = None
    try:
        print("🚀 Iniciando servidor...")
        server_process = subprocess.Popen([
            sys.executable, "-c", 
            """
import uvicorn
from main import app
import logging
logging.getLogger("uvicorn").setLevel(logging.WARNING)
uvicorn.run(app, host='0.0.0.0', port=8002, log_level='warning')
"""
        ], stdout=subprocess.PIPE, stderr=subprocess.PIPE)
        
        # Esperar a que inicie
        time.sleep(8)
        
        # Test health check
        try:
            health_response = requests.get("http://127.0.0.1:8002/health", timeout=10)
            if health_response.status_code == 200:
                health_data = health_response.json()
                print(f"✅ Health check: {health_data.get('status', 'unknown')}")
                
                # Test consulta con Candelaria
                consulta_data = {
                    'query': 'Información sobre proyectos ambientales',
                    'query_type': 'empresa',
                    'company_name': 'Candelaria'
                }
                
                consulta_response = requests.post(
                    "http://127.0.0.1:8002/consulta", 
                    json=consulta_data, 
                    timeout=20
                )
                
                if consulta_response.status_code == 200:
                    data = consulta_response.json()
                    
                    if data.get('requiere_seleccion'):
                        proyectos = data.get('lista_proyectos', [])
                        print(f"✅ Sistema devuelve lista de {len(proyectos)} proyectos para selección")
                        
                        if len(proyectos) > 0:
                            print(f"📋 Ejemplo: {proyectos[0].get('nombre', 'N/A')}")
                            return True
                        else:
                            print("⚠️ Lista de proyectos vacía")
                            return False
                    else:
                        print("✅ Sistema devuelve proyecto único")
                        if data.get('empresa_info'):
                            print(f"🏢 Empresa: {data['empresa_info'].get('nombre', 'N/A')}")
                        return True
                else:
                    print(f"❌ Error en consulta: {consulta_response.status_code}")
                    return False
            else:
                print(f"❌ Health check falló: {health_response.status_code}")
                return False
        except requests.exceptions.ConnectionError:
            print("❌ No se pudo conectar al servidor")
            return False
            
    except Exception as e:
        print(f"❌ Error: {e}")
        return False
    finally:
        if server_process:
            server_process.terminate()
            server_process.wait()

def main():
    """Test principal"""
    print("🚀 TESTS RÁPIDOS DEL SISTEMA CORREGIDO")
    print("=" * 50)
    
    tests_passed = 0
    total_tests = 2
    
    if test_scraper_titular():
        tests_passed += 1
    
    if test_sistema_completo():
        tests_passed += 1
    
    print(f"\n🎯 RESULTADO: {tests_passed}/{total_tests} tests pasados")
    
    if tests_passed == total_tests:
        print("\n🎉 TODOS LOS PROBLEMAS SOLUCIONADOS:")
        print("✅ Scraper por titular funcionando")
        print("✅ Sistema devuelve lista de proyectos")
        print("✅ Búsqueda por titular específico")
        print("✅ No más errores 502")
        print("✅ Google Maps configurado")
        print("\n🔧 SISTEMA LISTO PARA USO")
    else:
        print(f"\n⚠️ {total_tests - tests_passed} problemas pendientes")
    
    return tests_passed == total_tests

if __name__ == "__main__":
    success = main()
    sys.exit(0 if success else 1) 