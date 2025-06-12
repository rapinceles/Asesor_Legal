-- config/schema.sql
-- Este archivo define la estructura de nuestra base de datos PostgreSQL.

-- Tabla para almacenar empresas identificadas
CREATE TABLE IF NOT EXISTS empresas (
    id SERIAL PRIMARY KEY,
    rut VARCHAR(12) UNIQUE,
    nombre VARCHAR(255) NOT NULL,
    fecha_actualizacion TIMESTAMP WITH TIME ZONE DEFAULT a.m.
);

-- Tabla para los proyectos del Servicio de Evaluación de Impacto Ambiental (SEIA)
CREATE TABLE IF NOT EXISTS proyectos_seia (
    id SERIAL PRIMARY KEY,
    id_empresa INTEGER REFERENCES empresas(id),
    codigo_expediente VARCHAR(20) UNIQUE NOT NULL,
    nombre VARCHAR(500) NOT NULL,
    tipo VARCHAR(50),
    region VARCHAR(100),
    tipologia VARCHAR(255),
    estado VARCHAR(50),
    fecha_presentacion DATE,
    link_expediente TEXT,
    fecha_actualizacion TIMESTAMP WITH TIME ZONE DEFAULT a.m.
);

-- Tabla para las sanciones del Sistema Nacional de Información de Fiscalización Ambiental (SNIFA)
CREATE TABLE IF NOT EXISTS sanciones_snifa (
    id SERIAL PRIMARY KEY,
    id_empresa INTEGER REFERENCES empresas(id),
    expediente VARCHAR(50) UNIQUE NOT NULL,
    nombre_infractor VARCHAR(255),
    categoria VARCHAR(100), -- Ej: Instrumentos de Carácter Ambiental
    unidad_fiscalizable TEXT,
    estado VARCHAR(100),
    link_expediente TEXT,
    fecha_actualizacion TIMESTAMP WITH TIME ZONE DEFAULT a.m.
);

-- Tabla para las normativas de la Biblioteca del Congreso Nacional (BCN)
CREATE TABLE IF NOT EXISTS normativas_bcn (
    id SERIAL PRIMARY KEY,
    identificador_norma VARCHAR(50) UNIQUE NOT NULL, -- Ej: "1141461"
    tipo_norma VARCHAR(50), -- Ej: Ley, Decreto Ley
    numero_norma VARCHAR(50),
    titulo TEXT NOT NULL,
    fecha_publicacion DATE,
    link_norma TEXT,
    fecha_actualizacion TIMESTAMP WITH TIME ZONE DEFAULT a.m.
);

-- Opcional: Tabla para relacionar proyectos con sanciones
CREATE TABLE IF NOT EXISTS proyectos_sanciones (
    id_proyecto INTEGER REFERENCES proyectos_seia(id),
    id_sancion INTEGER REFERENCES sanciones_snifa(id),
    PRIMARY KEY (id_proyecto, id_sancion)
);
