# Modelo de Lote (FIFO) para Medicamentos

from datetime import datetime
from app import db

class Lote(db.Model):
    """Representa un lote de un medicamento en el inventario.
    Cada lote tiene una cantidad disponible, una fecha de vencimiento y un identificador de lote.
    """
    __tablename__ = 'lotes'

    id = db.Column(db.Integer, primary_key=True)
    medicamento_id = db.Column(db.Integer, db.ForeignKey('medicamentos.id'), nullable=False)
    cantidad = db.Column(db.Integer, nullable=False, default=0)
    lote = db.Column(db.String(50))
    fecha_vencimiento = db.Column(db.Date)
    fecha_ingreso = db.Column(db.DateTime, default=datetime.utcnow)

    def __repr__(self):
        return f"<Lote {self.id} - Medicamento {self.medicamento_id} - Cantidad {self.cantidad}>"
