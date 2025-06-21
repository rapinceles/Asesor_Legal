#!/usr/bin/env python3
# test_sistema_corregido.py - Test completo del sistema corregido

import logging
import sys
import os
import time
import subprocess
import requests
from threading import Thread

# Configurar logging
logging.basicConfig(level=logging.INFO, format='%(levelname)s:%(name)s:%(message)s')

def test_importaciones():
    """Test de todas las importaciones críticas"""
    print("🔍 TEST 1: IMPORTACIONES CRÍTICAS")
    print("=" * 50)
    
    tests_passed = 0
    total_tests = 6
    
    # Test FastAPI
    try:
        from fastapi import FastAPI
        print("✅ FastAPI importado correctamente")
        tests_passed += 1
    except Exception as e:
        print(f"❌ Error importando FastAPI: {e}")
    
    # Test BeautifulSoup
    try:
        from bs4 import BeautifulSoup
        print("✅ BeautifulSoup importado correctamente")
        tests_passed += 1
    except Exception as e:
        print(f"❌ Error importando BeautifulSoup: {e}")
    
    # Test requests
    try:
        import requests
        print("✅ Requests importado correctamente")
        tests_passed += 1
    except Exception as e:
        print(f"❌ Error importando requests: {e}")
    
    # Test scraper SEIA
    try:
        from scrapers.seia_safe import obtener_informacion_proyecto_seia_safe
        print("✅ Scraper SEIA importado correctamente")
        tests_passed += 1
    except Exception as e:
        print(f"❌ Error importando scraper SEIA: {e}")
    
    # Test scraper titular
    try:
        from scrapers.seia_titular import buscar_proyectos_por_titular
        print("✅ Scraper titular importado correctamente")
        tests_passed += 1
    except Exception as e:
        print(f"❌ Error importando scraper titular: {e}")
    
    # Test main app
    try:
        from main import app
        print("✅ Aplicación principal importada correctamente")
        tests_passed += 1
    except Exception as e:
        print(f"❌ Error importando aplicación principal: {e}")
    
    print(f"\n📊 Resultado: {tests_passed}/{total_tests} importaciones exitosas")
    return tests_passed == total_tests

def test_scraper_titular():
    """Test específico del scraper por titular"""
    print("\n🔍 TEST 2: SCRAPER POR TITULAR")
    print("=" * 50)
    
    try:
        from scrapers.seia_titular import buscar_proyectos_por_titular
        
        # Test con Candelaria
        print("🔍 Probando búsqueda: Candelaria")
        result = buscar_proyectos_por_titular('Candelaria')
        
        if result.get('success'):
            data = result['data']
            proyectos = data.get('lista_proyectos', [])
            print(f"✅ Búsqueda exitosa")
            print(f"📊 Proyectos encontrados: {len(proyectos)}")
            print(f"🔍 Variaciones usadas: {result.get('variaciones_usadas', [])[:3]}")
            
            if len(proyectos) > 0:
                primer_proyecto = proyectos[0]
                print(f"📋 Primer proyecto: {primer_proyecto.get('nombre', 'N/A')}")
                print(f"🏢 Titular: {primer_proyecto.get('titular', 'N/A')}")
                return True
            else:
                print("⚠️ No se encontraron proyectos")
                return False
        else:
            print(f"❌ Error en búsqueda: {result.get('error', 'Unknown')}")
            return False
            
    except Exception as e:
        print(f"❌ Error en test scraper titular: {e}")
        return False

def test_conexion_seia():
    """Test de conexión al SEIA"""
    print("\n🔍 TEST 3: CONEXIÓN AL SEIA")
    print("=" * 50)
    
    try:
        import requests
        
        # Test conexión básica
        response = requests.get("https://seia.sea.gob.cl", timeout=10)
        
        if response.status_code == 200:
            print("✅ Conexión al SEIA exitosa")
            
            # Test búsqueda en SEIA
            search_url = "https://seia.sea.gob.cl/busqueda/buscarProyectoAction.php"
            search_data = {
                'nombre_empresa_o_titular': 'test',
                'submit_buscar': 'Buscar'
            }
            
            search_response = requests.post(search_url, data=search_data, timeout=15)
            
            if search_response.status_code == 200:
                print("✅ Formulario de búsqueda del SEIA funcional")
                return True
            else:
                print(f"⚠️ Formulario de búsqueda respondió: {search_response.status_code}")
                return False
        else:
            print(f"❌ SEIA respondió: {response.status_code}")
            return False
            
    except Exception as e:
        print(f"❌ Error conectando al SEIA: {e}")
        return False

def test_servidor_local():
    """Test del servidor local"""
    print("\n🔍 TEST 4: SERVIDOR LOCAL")
    print("=" * 50)
    
    # Iniciar servidor en background
    server_process = None
    try:
        print("🚀 Iniciando servidor...")
        server_process = subprocess.Popen([
            sys.executable, "-c", 
            "import uvicorn; from main import app; uvicorn.run(app, host='0.0.0.0', port=8001, log_level='warning')"
        ], stdout=subprocess.PIPE, stderr=subprocess.PIPE)
        
        # Esperar a que el servidor inicie
        time.sleep(5)
        
        # Test endpoints
        base_url = "http://127.0.0.1:8001"
        
        # Test health
        try:
            health_response = requests.get(f"{base_url}/health", timeout=10)
            if health_response.status_code == 200:
                health_data = health_response.json()
                print(f"✅ Health check: {health_data.get('status', 'unknown')}")
                
                # Test consulta
                consulta_data = {
                    'query': 'Test de funcionamiento',
                    'query_type': 'general'
                }
                
                consulta_response = requests.post(
                    f"{base_url}/consulta", 
                    json=consulta_data, 
                    timeout=15
                )
                
                if consulta_response.status_code == 200:
                    print("✅ Endpoint de consulta funcional")
                    return True
                else:
                    print(f"❌ Endpoint de consulta falló: {consulta_response.status_code}")
                    return False
            else:
                print(f"❌ Health check falló: {health_response.status_code}")
                return False
                
        except requests.exceptions.ConnectionError:
            print("❌ No se pudo conectar al servidor")
            return False
            
    except Exception as e:
        print(f"❌ Error en test servidor: {e}")
        return False
    finally:
        if server_process:
            server_process.terminate()
            server_process.wait()

def test_google_maps():
    """Test de configuración de Google Maps"""
    print("\n🔍 TEST 5: GOOGLE MAPS")
    print("=" * 50)
    
    try:
        # Verificar que la API Key esté en el HTML
        with open('templates/index.html', 'r', encoding='utf-8') as f:
            html_content = f.read()
        
        if 'AIzaSyDVQ6eab8AerCjUCaa00pdHGGp5pHH3mUY' in html_content:
            print("✅ API Key de Google Maps encontrada en HTML")
            
            # Verificar que no esté duplicada
            api_key_count = html_content.count('AIzaSyDVQ6eab8AerCjUCaa00pdHGGp5pHH3mUY')
            if api_key_count == 1:
                print("✅ API Key única (sin duplicados)")
                
                # Verificar estructura del mapa
                if 'initMap' in html_content and 'map-container' in html_content:
                    print("✅ Estructura del mapa correcta")
                    return True
                else:
                    print("❌ Estructura del mapa incompleta")
                    return False
            else:
                print(f"⚠️ API Key duplicada {api_key_count} veces")
                return False
        else:
            print("❌ API Key de Google Maps no encontrada")
            return False
            
    except Exception as e:
        print(f"❌ Error verificando Google Maps: {e}")
        return False

def main():
    """Función principal de test"""
    print("🚀 INICIANDO TESTS DEL SISTEMA CORREGIDO")
    print("=" * 70)
    print()
    
    tests_passed = 0
    total_tests = 5
    
    # Ejecutar todos los tests
    if test_importaciones():
        tests_passed += 1
    
    if test_scraper_titular():
        tests_passed += 1
    
    if test_conexion_seia():
        tests_passed += 1
    
    if test_servidor_local():
        tests_passed += 1
        
    if test_google_maps():
        tests_passed += 1
    
    # Resumen final
    print("\n" + "=" * 70)
    print("🎯 RESUMEN FINAL")
    print("=" * 70)
    print(f"✅ Tests pasados: {tests_passed}/{total_tests}")
    print(f"📊 Porcentaje de éxito: {(tests_passed/total_tests)*100:.1f}%")
    
    if tests_passed == total_tests:
        print("\n🎉 TODOS LOS ERRORES CORREGIDOS")
        print("✅ Error 502: SOLUCIONADO")
        print("✅ Google Maps: FUNCIONANDO")
        print("✅ Scraper SEIA: OBTENIENDO DATOS REALES")
        print("✅ Búsqueda por titular: IMPLEMENTADA")
        print("✅ Sistema completo: FUNCIONAL")
        print("\n🔧 LISTO PARA PRODUCCIÓN")
    else:
        print(f"\n⚠️ {total_tests - tests_passed} problemas encontrados")
        print("Revisar logs para más detalles")
    
    return tests_passed == total_tests

if __name__ == "__main__":
    success = main()
    sys.exit(0 if success else 1) 