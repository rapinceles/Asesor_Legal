# Configuración de Google Maps para MERLIN

## 📍 Implementación de Ubicación de Proyectos

Se ha agregado la funcionalidad de Google Maps para mostrar la ubicación de los proyectos buscados en el sistema MERLIN.

## 🔧 Configuración Requerida

### 1. Obtener API Key de Google Maps

1. Ve a [Google Cloud Console](https://console.cloud.google.com/)
2. Crea un nuevo proyecto o selecciona uno existente
3. Habilita las siguientes APIs:
   - Maps JavaScript API
   - Geocoding API
   - Places API
4. Ve a "Credentials" y crea una nueva API Key
5. Configura las restricciones de la API Key (recomendado por seguridad)

### 2. Configurar la API Key en el HTML

Reemplaza `YOUR_API_KEY` en el archivo `templates/index.html` en la línea:

```html
<script async defer src="https://maps.googleapis.com/maps/api/js?key=YOUR_API_KEY&libraries=places&callback=initMap"></script>
```

Por ejemplo:
```html
<script async defer src="https://maps.googleapis.com/maps/api/js?key=AIzaSyBOti4mM-6x9WDnZIjIeyEU21OpBXqWBgw&libraries=places&callback=initMap"></script>
```

### 3. Restricciones de Seguridad (Recomendado)

Para producción, configura restricciones en tu API Key:

**Restricciones de HTTP referrer:**
- `https://tu-dominio.com/*`
- `https://www.tu-dominio.com/*`
- `http://localhost:8000/*` (para desarrollo)

**Restricciones de API:**
- Maps JavaScript API
- Geocoding API
- Places API

## 🌟 Funcionalidades Implementadas

### 1. Campo de Ubicación
- Se muestra automáticamente cuando se selecciona "Proyecto" como tipo de consulta
- Permite ingresar direcciones o coordenadas
- Ejemplo: "Santiago, Chile" o "-33.4489, -70.6693"

### 2. Mapa Interactivo
- Mapa con estilo oscuro personalizado acorde al tema de MERLIN
- Marcador personalizado con colores del tema
- Centrado por defecto en Santiago, Chile
- Zoom automático al encontrar una ubicación

### 3. Búsqueda de Ubicación
- Geocodificación de direcciones a coordenadas
- Actualización automática del marcador
- Ventana de información con detalles de la ubicación
- Formato de dirección mejorado

### 4. Modo Sin Conexión
- Mensaje informativo cuando Google Maps no está disponible
- Funcionalidad de respaldo que mantiene la interfaz
- Instrucciones claras para el usuario

## 🎨 Características de Diseño

- **Estilo Oscuro**: Mapa con tema oscuro que combina con MERLIN
- **Marcador Personalizado**: Ícono naranja a juego con el tema
- **Responsive**: Se adapta a dispositivos móviles
- **Integración Fluida**: Se integra naturalmente en el flujo de trabajo

## 🔍 Uso

1. Selecciona "Proyecto" como tipo de consulta
2. Ingresa el nombre de la empresa
3. En el campo "Ubicación del proyecto", escribe:
   - Una dirección: "Las Condes, Santiago, Chile"
   - Coordenadas: "-33.4489, -70.6693"
   - Un lugar conocido: "Aeropuerto de Santiago"
4. Haz clic en "🗺️ Mostrar en Mapa"
5. El mapa se centrará en la ubicación encontrada

## 💡 Casos de Uso en MERLIN

Esta funcionalidad es especialmente útil para:
- **Evaluación de impacto ambiental** por ubicación geográfica
- **Análisis de zonificación** y regulaciones locales
- **Identificación de áreas protegidas** cercanas al proyecto
- **Evaluación de riesgos ambientales** por zona geográfica
- **Cumplimiento de normativas** específicas por región

## 🛠️ Personalización Adicional

### Cambiar Ubicación por Defecto
En el archivo `templates/index.html`, modifica las coordenadas:
```javascript
const defaultLocation = { lat: -33.4489, lng: -70.6693 }; // Santiago, Chile
```

### Personalizar Estilo del Mapa
Modifica el array `styles` en la función `initMap()` para cambiar la apariencia del mapa.

### Agregar Más Información
Puedes expandir la ventana de información (`infoWindow`) para incluir más detalles sobre la ubicación del proyecto.

## 📝 Notas Importantes

- La API Key es necesaria para el funcionamiento completo
- Se recomienda configurar límites de uso para evitar costos excesivos
- La funcionalidad funciona sin API Key pero con capacidades limitadas
- Los estilos del mapa están optimizados para el tema oscuro de MERLIN

## 🔒 Seguridad

- **Nunca** expongas tu API Key en repositorios públicos
- Usa variables de entorno para producción
- Configura restricciones apropiadas en Google Cloud Console
- Monitorea el uso regularmente 