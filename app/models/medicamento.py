"""
Modelo de Medicamento y Receta
Gestiona el inventario de medicamentos y las recetas médicas
"""
from datetime import datetime, timedelta, date
from app import db


class Medicamento(db.Model):
    """Modelo de Medicamentos e Inventario"""
    __tablename__ = 'medicamentos'

    id = db.Column(db.Integer, primary_key=True)
    codigo = db.Column(db.String(50), unique=True)
    nombre = db.Column(db.String(100), nullable=False)
    principio_activo = db.Column(db.String(100))
    presentacion = db.Column(db.String(100))
    concentracion = db.Column(db.String(50))

    # Categoría
    categoria = db.Column(db.String(50))  # antibiotico, analgesico, vacuna, etc.
    via_administracion = db.Column(db.String(50))  # oral, inyectable, topico

    # Stock
    stock_actual = db.Column(db.Integer, default=0)
    stock_minimo = db.Column(db.Integer, default=5)
    unidad_medida = db.Column(db.String(20))  # unidad, ml, mg, etc.

    # Precios
    precio_compra = db.Column(db.Float)
    precio_venta = db.Column(db.Float)

    # Información adicional
    laboratorio = db.Column(db.String(100))
    lote = db.Column(db.String(50))
    fecha_vencimiento = db.Column(db.Date)

    # Control
    requiere_receta = db.Column(db.Boolean, default=False)
    controlado = db.Column(db.Boolean, default=False)

    # Estado
    activo = db.Column(db.Boolean, default=True)

    # Ubicación en almacén
    ubicacion_almacen = db.Column(db.String(50))

    fecha_registro = db.Column(db.DateTime, default=datetime.utcnow)
    ultima_actualizacion = db.Column(db.DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)

    # Relación con Lotes
    lotes = db.relationship('Lote', backref='medicamento', lazy=True, order_by='Lote.fecha_vencimiento')

    @property
    def esta_por_vencer(self):
        """Verifica si el medicamento está próximo a vencer (30 días)"""
        # Verificar si algún lote está por vencer
        fecha_limite = datetime.now().date() + timedelta(days=30)
        hoy = datetime.now().date()
        
        for lote in self.lotes:
            if lote.cantidad > 0 and lote.fecha_vencimiento:
                if hoy < lote.fecha_vencimiento <= fecha_limite:
                    return True
        
        # Fallback para compatibilidad si no hay lotes pero hay fecha en medicamento
        if not self.lotes and self.fecha_vencimiento:
            dias_restantes = (self.fecha_vencimiento - hoy).days
            return 0 < dias_restantes <= 30
            
        return False

    @property
    def esta_vencido(self):
        """Verifica si el medicamento está vencido"""
        hoy = datetime.now().date()
        
        # Verificar si algún lote con stock está vencido
        for lote in self.lotes:
            if lote.cantidad > 0 and lote.fecha_vencimiento and lote.fecha_vencimiento <= hoy:
                return True
                
        # Fallback
        if not self.lotes and self.fecha_vencimiento:
            return self.fecha_vencimiento <= hoy
            
        return False

    @property
    def necesita_restock(self):
        """Verifica si necesita reabastecimiento"""
        return self.stock_actual <= self.stock_minimo

    def reducir_stock(self, cantidad):
        """
        Reduce el stock del medicamento usando PEPS (Primero en Entrar, Primero en Salir)
        basado en fechas de vencimiento (los más próximos a vencer salen primero)

        Args:
            cantidad: Cantidad a reducir

        Returns:
            bool: True si se pudo reducir, False si no hay suficiente stock
        """
        if self.stock_actual < cantidad:
            return False

        cantidad_restante = cantidad
        
        # Ordenar lotes por fecha de vencimiento (los nulos al final o principio según lógica, 
        # pero idealmente todos deberían tener fecha. Asumimos orden por query)
        # Filtramos solo lotes con cantidad > 0
        lotes_disponibles = [l for l in self.lotes if l.cantidad > 0]
        # Aseguramos orden por fecha de vencimiento
        lotes_disponibles.sort(key=lambda x: x.fecha_vencimiento if x.fecha_vencimiento else date.max)

        for lote in lotes_disponibles:
            if cantidad_restante <= 0:
                break
                
            if lote.cantidad >= cantidad_restante:
                lote.cantidad -= cantidad_restante
                cantidad_restante = 0
            else:
                cantidad_restante -= lote.cantidad
                lote.cantidad = 0
        
        # Si por alguna razón no se cubrió con lotes (inconsistencia), descontamos del global igual
        # para mantener consistencia, aunque idealmente stock_actual debería ser la suma de lotes.
        self.stock_actual -= cantidad
        self.ultima_actualizacion = datetime.utcnow()
        return True

    def aumentar_stock(self, cantidad, lote_codigo=None, fecha_vencimiento=None, precio_compra=None):
        """
        Aumenta el stock del medicamento creando o actualizando un lote
        """
        from app.models.lote import Lote
        
        # Crear nuevo lote
        nuevo_lote = Lote(
            medicamento_id=self.id,
            cantidad=cantidad,
            lote=lote_codigo or f"LOTE-{datetime.now().strftime('%Y%m%d')}",
            fecha_vencimiento=fecha_vencimiento
        )
        db.session.add(nuevo_lote)
        
        # Actualizar precio si se provee
        if precio_compra:
            self.precio_compra = precio_compra
            
        # Actualizar fecha de vencimiento global (informativa, la más próxima)
        if fecha_vencimiento:
            if not self.fecha_vencimiento or fecha_vencimiento < self.fecha_vencimiento:
                self.fecha_vencimiento = fecha_vencimiento

        self.stock_actual += cantidad
        self.ultima_actualizacion = datetime.utcnow()


class Receta(db.Model):
    """
    Modelo de Receta Médica
    Relaciona medicamentos con citas
    """
    __tablename__ = 'recetas'

    # Campos principales
    id = db.Column(db.Integer, primary_key=True)

    # Relaciones
    cita_id = db.Column(db.Integer, db.ForeignKey('citas.id'), nullable=False)
    medicamento_id = db.Column(db.Integer, db.ForeignKey('medicamentos.id'), nullable=False)

    # Información de la receta
    cantidad = db.Column(db.Integer, nullable=False)
    dosis = db.Column(db.String(200))  # Ej: "1 tableta cada 8 horas"
    duracion = db.Column(db.String(100))  # Ej: "7 días"
    indicaciones = db.Column(db.Text)

    # Timestamps
    fecha_receta = db.Column(db.DateTime, default=datetime.utcnow)

    def __init__(self, cita_id, medicamento_id, cantidad, **kwargs):
        """
        Constructor del modelo Receta
        """
        self.cita_id = cita_id
        self.medicamento_id = medicamento_id
        self.cantidad = cantidad

        # Campos opcionales
        self.dosis = kwargs.get('dosis')
        self.duracion = kwargs.get('duracion')
        self.indicaciones = kwargs.get('indicaciones')

    def __repr__(self):
        return f'<Receta {self.id} - Cita: {self.cita_id} - Medicamento: {self.medicamento_id}>'
