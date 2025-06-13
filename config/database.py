# config/database.py
# Este archivo centraliza la configuración y conexión a la base de datos.

from sqlalchemy import create_engine
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy.orm import sessionmaker

# URL de conexión a tu base de datos PostgreSQL.
# FORMATO: "postgresql://usuario:contraseña@host:puerto/nombre_db"
# AJUSTA ESTOS VALORES a los de tu base de datos local o en la nube.
DATABASE_URL = "postgresql://postgres:tu_contraseña@localhost:5432/asesor_ambiental_db"

# El 'engine' es el punto de entrada a la base de datos.
engine = create_engine(DATABASE_URL)

# La 'SessionLocal' es la que usaremos para comunicarnos con la DB en cada operación.
SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)

# 'Base' es una clase base de la cual heredarán todos nuestros modelos de datos (ORM).
Base = declarative_base()

# Función de utilidad para crear todas las tablas definidas en los modelos
def init_db():
    # Importa aquí todos los modelos para que Base los conozca antes de crear las tablas
    # from models.seia_models import Empresa, ProyectoSEIA # Descomentaremos esto más adelante
    print("Creando todas las tablas en la base de datos...")
    Base.metadata.create_all(bind=engine)
    print("Tablas creadas exitosamente.")
