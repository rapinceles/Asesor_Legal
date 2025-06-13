# models/snifa_models.py
from sqlalchemy import Column, Integer, String, Text, TIMESTAMP, ForeignKey
from config.database import Base
from sqlalchemy.orm import relationship

# Importamos la clase Empresa para poder definir la relación
from .seia_models import Empresa

class SancionSNIFA(Base):
    __tablename__ = "sanciones_snifa"

    id = Column(Integer, primary_key=True, index=True)
    id_empresa = Column(Integer, ForeignKey("empresas.id"))
    expediente = Column(String(50), unique=True, nullable=False, index=True)
    nombre_infractor = Column(String(255))
    categoria = Column(String(100))
    unidad_fiscalizable = Column(Text)
    estado = Column(String(100))
    link_expediente = Column(Text)
    fecha_actualizacion = Column(TIMESTAMP(timezone=True), server_default='NOW()', onupdate='NOW()')

    # Relación: Una sanción pertenece a una empresa infractora
    infractor = relationship("Empresa")
