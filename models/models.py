# models/models.py
from sqlalchemy import Column, Integer, String, Date, Text, TIMESTAMP, ForeignKey
from sqlalchemy.orm import relationship
from config.database import Base

class Empresa(Base):
    __tablename__ = "empresas"

    id = Column(Integer, primary_key=True, index=True)
    rut = Column(String(12), unique=True, index=True)
    nombre = Column(String(255), nullable=False, index=True)
    fecha_actualizacion = Column(TIMESTAMP(timezone=True), server_default='NOW()', onupdate='NOW()')

    # Relaciones
    proyectos = relationship("ProyectoSEIA", back_populates="titular")
    sanciones = relationship("SancionSNIFA", back_populates="infractor")

class ProyectoSEIA(Base):
    __tablename__ = "proyectos_seia"

    id = Column(Integer, primary_key=True, index=True)
    id_empresa = Column(Integer, ForeignKey("empresas.id"))

    codigo_expediente = Column(Text, unique=True, nullable=False, index=True)
    nombre = Column(Text, nullable=False)
    tipo = Column(Text)
    region = Column(Text)
    tipologia = Column(Text)
    estado = Column(Text)
    link_expediente = Column(Text)
    fecha_presentacion = Column(Date)
    fecha_actualizacion = Column(TIMESTAMP(timezone=True), server_default='NOW()', onupdate='NOW()')

    titular = relationship("Empresa", back_populates="proyectos")

class SancionSNIFA(Base):
    __tablename__ = "sanciones_snifa"

    id = Column(Integer, primary_key=True, index=True)
    id_empresa = Column(Integer, ForeignKey("empresas.id"))

    expediente = Column(Text, unique=True, nullable=False, index=True)
    nombre_infractor = Column(Text)
    categoria = Column(Text)
    unidad_fiscalizable = Column(Text)
    estado = Column(Text)
    link_expediente = Column(Text)
    fecha_actualizacion = Column(TIMESTAMP(timezone=True), server_default='NOW()', onupdate='NOW()')

    infractor = relationship("Empresa", back_populates="sanciones")
