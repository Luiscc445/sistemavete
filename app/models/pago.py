"""
Modelo de Pago - Sistema de Pagos Modernizado
"""
from datetime import datetime
from app import db
import qrcode
from io import BytesIO
import base64

class Pago(db.Model):
    """Modelo de Pago con múltiples métodos de pago y QR"""
    __tablename__ = 'pagos'

    id = db.Column(db.Integer, primary_key=True)

    # Información básica del pago
    codigo_pago = db.Column(db.String(50), unique=True, nullable=False)  # Ej: PAG-20251117-001
    monto = db.Column(db.Float, nullable=False)  # Monto total que paga el cliente
    monto_pagado = db.Column(db.Float, default=0)  # Para pagos parciales

    # División de ingresos (Empresa vs Veterinario)
    porcentaje_empresa = db.Column(db.Float, default=57.14)  # % para la empresa (ej: 57.14% de 35 = 20)
    porcentaje_veterinario = db.Column(db.Float, default=42.86)  # % para el veterinario (ej: 42.86% de 35 = 15)
    monto_empresa = db.Column(db.Float, default=0)  # Monto que va para la empresa
    monto_veterinario = db.Column(db.Float, default=0)  # Monto que va para el veterinario

    # Método de pago
    metodo_pago = db.Column(db.String(50), nullable=False)
    # Métodos: efectivo, tarjeta_credito, tarjeta_debito, transferencia_bancaria,
    #          qr_simple, qr_tigo_money, qr_banco

    # Estado del pago
    estado = db.Column(db.String(20), default='pendiente')
    # Estados: pendiente, procesando, completado, fallido, reembolsado, cancelado

    # Información del QR (para pagos con QR)
    qr_code_data = db.Column(db.Text)  # Datos del QR en formato de texto
    qr_code_image = db.Column(db.Text)  # Imagen del QR en base64
    qr_vencimiento = db.Column(db.DateTime)  # Cuándo expira el QR

    # Información de la transacción
    numero_transaccion = db.Column(db.String(100))  # Número de referencia bancaria
    numero_autorizacion = db.Column(db.String(100))  # Código de autorización
    banco = db.Column(db.String(100))  # Banco emisor (para tarjetas/transferencias)
    ultimos_digitos_tarjeta = db.Column(db.String(4))  # Últimos 4 dígitos de tarjeta

    # Detalles adicionales
    descripcion = db.Column(db.Text)
    notas = db.Column(db.Text)
    comprobante_url = db.Column(db.String(500))  # URL del comprobante/recibo subido

    # Facturación
    requiere_factura = db.Column(db.Boolean, default=False)
    numero_factura = db.Column(db.String(50))
    nit_cliente = db.Column(db.String(50))
    razon_social_cliente = db.Column(db.String(200))

    # Timestamps
    fecha_creacion = db.Column(db.DateTime, default=datetime.utcnow, nullable=False)
    fecha_pago = db.Column(db.DateTime)  # Cuándo se completó el pago
    fecha_vencimiento = db.Column(db.DateTime)  # Fecha límite de pago
    fecha_reembolso = db.Column(db.DateTime)

    # Relaciones
    cita_id = db.Column(db.Integer, db.ForeignKey('citas.id'))
    usuario_id = db.Column(db.Integer, db.ForeignKey('usuarios.id'), nullable=False)  # Quien paga (tutor)
    veterinario_id = db.Column(db.Integer, db.ForeignKey('usuarios.id'))  # Veterinario que atendió
    procesado_por_id = db.Column(db.Integer, db.ForeignKey('usuarios.id'))  # Quien procesó el pago

    # Relación con cita
    cita = db.relationship('Cita', backref=db.backref('pagos', lazy='dynamic'))
    usuario = db.relationship('Usuario', foreign_keys=[usuario_id], backref=db.backref('pagos_realizados', lazy='dynamic'))
    veterinario = db.relationship('Usuario', foreign_keys=[veterinario_id], backref=db.backref('pagos_recibidos', lazy='dynamic'))
    procesado_por = db.relationship('Usuario', foreign_keys=[procesado_por_id], backref=db.backref('pagos_procesados', lazy='dynamic'))

    @property
    def saldo_pendiente(self):
        """Calcula el saldo pendiente del pago"""
        return self.monto - self.monto_pagado

    @property
    def esta_pagado(self):
        """Verifica si el pago está completamente pagado"""
        return self.monto_pagado >= self.monto and self.estado == 'completado'

    @property
    def esta_vencido(self):
        """Verifica si el pago está vencido"""
        if not self.fecha_vencimiento:
            return False
        return datetime.utcnow() > self.fecha_vencimiento and not self.esta_pagado

    @property
    def qr_esta_vencido(self):
        """Verifica si el QR está vencido"""
        if not self.qr_vencimiento:
            return False
        return datetime.utcnow() > self.qr_vencimiento

    def generar_codigo_pago(self):
        """Genera un código único de pago"""
        from datetime import datetime
        fecha = datetime.utcnow().strftime('%Y%m%d')
        # Obtener el último pago del día
        ultimo_pago = Pago.query.filter(
            Pago.codigo_pago.like(f'PAG-{fecha}-%')
        ).order_by(Pago.id.desc()).first()

        if ultimo_pago:
            # Extraer el número secuencial y incrementar
            try:
                ultimo_num = int(ultimo_pago.codigo_pago.split('-')[-1])
                nuevo_num = ultimo_num + 1
            except:
                nuevo_num = 1
        else:
            nuevo_num = 1

        self.codigo_pago = f'PAG-{fecha}-{nuevo_num:04d}'
        return self.codigo_pago

    def generar_qr(self, datos_qr=None):
        """
        Genera un código QR para el pago

        Args:
            datos_qr (str): Datos para el QR. Si no se proporciona, usa formato estándar.

        Returns:
            str: Imagen del QR en base64
        """
        if not datos_qr:
            # Formato estándar para QR de pagos en Bolivia
            datos_qr = self._generar_datos_qr_estandar()

        self.qr_code_data = datos_qr

        # Generar imagen QR
        qr = qrcode.QRCode(
            version=1,
            error_correction=qrcode.constants.ERROR_CORRECT_L,
            box_size=10,
            border=4,
        )
        qr.add_data(datos_qr)
        qr.make(fit=True)

        # Crear imagen
        img = qr.make_image(fill_color="black", back_color="white")

        # Convertir a base64
        buffered = BytesIO()
        img.save(buffered, format="PNG")
        img_str = base64.b64encode(buffered.getvalue()).decode()

        self.qr_code_image = img_str

        # Establecer vencimiento del QR (24 horas)
        from datetime import timedelta
        self.qr_vencimiento = datetime.utcnow() + timedelta(hours=24)

        return img_str

    def _generar_datos_qr_estandar(self):
        """Genera datos estándar para el QR de pago"""
        # Formato básico - puedes personalizarlo según el estándar de tu país
        datos = {
            'codigo': self.codigo_pago,
            'monto': self.monto,
            'descripcion': self.descripcion or 'Pago de servicios veterinarios',
            'veterinaria': 'Sistema Veterinario',
            'fecha': datetime.utcnow().isoformat()
        }

        # Convertir a string para QR
        import json
        return json.dumps(datos, ensure_ascii=False)

    def calcular_division_ingresos(self):
        """
        Calcula automáticamente la división de ingresos entre empresa y veterinario
        Ejemplo: Si monto=35, empresa=20 (57.14%), veterinario=15 (42.86%)
        """
        # Asignar valores por defecto si son None
        if self.porcentaje_empresa is None:
            self.porcentaje_empresa = 57.14
        if self.porcentaje_veterinario is None:
            self.porcentaje_veterinario = 42.86

        # Calcular montos
        self.monto_empresa = round(self.monto * (self.porcentaje_empresa / 100), 2)
        self.monto_veterinario = round(self.monto * (self.porcentaje_veterinario / 100), 2)
        return (self.monto_empresa, self.monto_veterinario)

    def marcar_como_completado(self, numero_transaccion=None, procesado_por=None):
        """Marca el pago como completado"""
        self.estado = 'completado'
        self.fecha_pago = datetime.utcnow()
        self.monto_pagado = self.monto

        if numero_transaccion:
            self.numero_transaccion = numero_transaccion

        if procesado_por:
            self.procesado_por_id = procesado_por

        db.session.commit()
        return True

    def marcar_como_fallido(self, razon=None):
        """Marca el pago como fallido"""
        self.estado = 'fallido'
        if razon:
            self.notas = (self.notas or '') + f'\nFallido: {razon}'
        db.session.commit()

    def procesar_reembolso(self, procesado_por=None):
        """Procesa un reembolso"""
        if self.estado != 'completado':
            return False

        self.estado = 'reembolsado'
        self.fecha_reembolso = datetime.utcnow()

        if procesado_por:
            self.procesado_por_id = procesado_por

        db.session.commit()
        return True

    def agregar_pago_parcial(self, monto):
        """Agrega un pago parcial"""
        self.monto_pagado += monto

        if self.monto_pagado >= self.monto:
            self.estado = 'completado'
            self.fecha_pago = datetime.utcnow()
        else:
            self.estado = 'procesando'

        db.session.commit()

    @property
    def metodo_pago_label(self):
        """Retorna el nombre legible del método de pago"""
        metodos = {
            'efectivo': 'Efectivo',
            'tarjeta_credito': 'Tarjeta de Crédito',
            'tarjeta_debito': 'Tarjeta de Débito',
            'transferencia_bancaria': 'Transferencia Bancaria',
            'qr_simple': 'QR Simple',
            'qr_tigo_money': 'Tigo Money QR',
            'qr_banco': 'QR Bancario'
        }
        return metodos.get(self.metodo_pago, self.metodo_pago)

    @property
    def estado_badge_class(self):
        """Retorna la clase CSS para el badge del estado"""
        clases = {
            'pendiente': 'warning',
            'procesando': 'info',
            'completado': 'success',
            'fallido': 'danger',
            'reembolsado': 'secondary',
            'cancelado': 'dark'
        }
        return clases.get(self.estado, 'secondary')

    def __repr__(self):
        return f'<Pago {self.codigo_pago} - {self.monto} Bs. - {self.estado}>'


class HistorialPago(db.Model):
    """Historial de cambios en los pagos (para auditoría)"""
    __tablename__ = 'historial_pagos'

    id = db.Column(db.Integer, primary_key=True)
    pago_id = db.Column(db.Integer, db.ForeignKey('pagos.id'), nullable=False)

    accion = db.Column(db.String(50), nullable=False)  # creado, modificado, completado, reembolsado
    estado_anterior = db.Column(db.String(20))
    estado_nuevo = db.Column(db.String(20))

    monto_anterior = db.Column(db.Float)
    monto_nuevo = db.Column(db.Float)

    descripcion = db.Column(db.Text)

    fecha = db.Column(db.DateTime, default=datetime.utcnow, nullable=False)
    usuario_id = db.Column(db.Integer, db.ForeignKey('usuarios.id'))

    # Relaciones
    pago = db.relationship('Pago', backref=db.backref('historial', lazy='dynamic', order_by='HistorialPago.fecha.desc()'))
    usuario = db.relationship('Usuario', backref=db.backref('historial_pagos', lazy='dynamic'))

    def __repr__(self):
        return f'<HistorialPago {self.pago_id} - {self.accion} - {self.fecha}>'
