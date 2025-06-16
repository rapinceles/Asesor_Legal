# MERLIN - Asesor Legal Ambiental Inteligente

MERLIN es un sistema inteligente de asesoría legal ambiental que integra datos del SEIA (Sistema de Evaluación de Impacto Ambiental) y SNIFA (Sistema Nacional de Información de Fiscalización Ambiental) para proporcionar análisis legales especializados.

## Características Principales

- 🤖 **Análisis con IA**: Utiliza OpenAI GPT para análisis legales inteligentes
- 🏢 **Análisis Empresarial**: Búsqueda y análisis específico de empresas
- 📊 **Datos Oficiales**: Integración con SEIA y SNIFA
- 🗺️ **Geolocalización**: Mapas interactivos de proyectos
- 📋 **Análisis General**: Consultas legales generales
- 🔍 **Referencias Legales**: Enlaces a fuentes oficiales

## Instalación

### Prerrequisitos

- Python 3.8+
- PostgreSQL
- API Key de OpenAI

### Pasos de Instalación

1. **Clonar el repositorio**
```bash
git clone <repository-url>
cd Asesor_Legal
```

2. **Crear entorno virtual**
```bash
python -m venv venv
source venv/bin/activate  # En Windows: venv\Scripts\activate
```

3. **Instalar dependencias**
```bash
pip install -r requirements.txt
```

4. **Configurar base de datos PostgreSQL**
```bash
# Crear base de datos
psql -U postgres
CREATE DATABASE asesor_ambiental_db;
```

5. **Configurar variables de entorno**
Crear archivo `.env` con:
```env
OPENAI_API_KEY=tu-api-key-de-openai
DATABASE_URL=postgresql://postgres:password@127.0.0.1:5432/asesor_ambiental_db
```

6. **Ejecutar la aplicación**
```bash
uvicorn main:app --reload --host 0.0.0.0 --port 8000
```

## Uso

### Interfaz Web
Abrir en navegador: `http://localhost:8000`

### Tipos de Análisis

#### 1. Análisis General
- Consultas legales generales
- No requiere nombre de empresa
- Proporciona información legal orientativa

#### 2. Análisis Empresarial
- Búsqueda específica de empresas
- Integra datos del SEIA y SNIFA
- Muestra proyectos, sanciones, RCA y ubicaciones
- Permite consultas específicas sobre la empresa

### Funcionalidades

- **Búsqueda en SEIA**: Proyectos de evaluación ambiental
- **Búsqueda en SNIFA**: Sanciones y fiscalizaciones
- **Mapas Interactivos**: Ubicación de proyectos
- **Análisis de Cumplimiento**: Evaluación de obligaciones ambientales
- **Referencias Legales**: Enlaces a normativas relevantes

## Estructura del Proyecto

```
Asesor_Legal/
├── main.py                 # Aplicación FastAPI principal
├── templates/
│   └── index.html          # Interfaz web
├── static/                 # Archivos estáticos
├── engine/
│   └── analysis_engine.py  # Motor de análisis IA
├── scrapers/
│   ├── seia_scraper.py     # Scraper del SEIA
│   └── snifa_scraper.py    # Scraper del SNIFA
├── models/
│   └── models.py           # Modelos de base de datos
├── config/
│   ├── database.py         # Configuración de BD
│   └── schema.sql          # Esquema de base de datos
└── requirements.txt        # Dependencias
```

## API Endpoints

- `GET /` - Interfaz principal
- `POST /analisis_general/` - Análisis legal general
- `POST /analisis_empresarial/` - Análisis específico de empresa
- `GET /test` - Test de conectividad

## Tecnologías Utilizadas

- **Backend**: FastAPI, SQLAlchemy, PostgreSQL
- **Frontend**: HTML5, CSS3, JavaScript, Leaflet Maps
- **IA**: OpenAI GPT-3.5
- **Web Scraping**: BeautifulSoup, Requests
- **Base de Datos**: PostgreSQL

## Licencia

Este proyecto está bajo licencia privada. Todos los derechos reservados.

## Contacto

Para soporte técnico o consultas, contactar al desarrollador del proyecto.

---

⚠️ **Disclaimer**: MERLIN proporciona información orientativa y no constituye asesoría legal profesional. Para decisiones importantes, consulte con un abogado especializado.