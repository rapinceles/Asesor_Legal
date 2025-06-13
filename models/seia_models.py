# models/seia_models.py
# Define las clases ORM que mapean a las tablas de nuestra base de datos.

from sqlalchemy import Column, Integer, String, Date, Text, TIMESTAMP, ForeignKey
from sqlalchemy.orm import relationship
from config.database import Base # Importamos la Base declarativa

class Empresa(Base):
    __tablename__ = "empresas" # Nombre exacto de la tabla en la DB

    id = Column(Integer, primary_key=True, index=True)
    rut = Column(String(12), unique=True, index=True)
    nombre = Column(String(255), nullable=False, index=True)
    fecha_actualizacion = Column(TIMESTAMP(timezone=True), server_default='NOW()', onupdate='NOW()')

    # Relación: Una empresa puede tener muchos proyectos
    proyectos = relationship("ProyectoSEIA", back_populates="titular")


class ProyectoSEIA(Base):
    __tablename__ = "proyectos_seia" # Nombre exacto de la tabla en la DB

    id = Column(Integer, primary_key=True, index=True)
    id_empresa = Column(Integer, ForeignKey("empresas.id"))
    codigo_expediente = Column(String(20), unique=True, nullable=False, index=True)
    nombre = Column(String(500), nullable=False)
    tipo = Column(String(50))
    region = Column(String(100))
    tipologia = Column(String(255))
    estado = Column(String(50))
    fecha_presentacion = Column(Date)
    link_expediente = Column(Text)
    fecha_actualizacion = Column(TIMESTAMP(timezone=True), server_default='NOW()', onupdate='NOW()')

    # Relación inversa: Un proyecto pertenece a una empresa titular
    titular = relationship("Empresa", back_populates="proyectos")
