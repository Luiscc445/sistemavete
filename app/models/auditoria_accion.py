"""
Modelo de Auditoría de Acciones
"""
from datetime import datetime
from app import db


class AuditoriaAccion(db.Model):
    """Registro de auditoría de acciones en el sistema"""
    __tablename__ = 'auditoria_acciones'

    id = db.Column(db.Integer, primary_key=True)
    usuario_id = db.Column(db.Integer, db.ForeignKey('usuarios.id'))

    accion = db.Column(db.String(100))  # login, logout, crear_cita, editar_mascota, etc.
    entidad = db.Column(db.String(50))  # usuario, mascota, cita, etc.
    entidad_id = db.Column(db.Integer)

    descripcion = db.Column(db.Text, nullable=False)
    datos_anteriores = db.Column(db.Text, nullable=True)  # Cambiado de JSON a Text para SQL Server
    datos_nuevos = db.Column(db.Text, nullable=True)  # Cambiado de JSON a Text para SQL Server

    ip_address = db.Column(db.String(45), nullable=True)
    user_agent = db.Column(db.Text, nullable=True)  # Cambiado a Text para user-agents largos

    fecha = db.Column(db.DateTime, default=datetime.utcnow)
