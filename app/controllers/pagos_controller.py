"""
Controlador de Pagos - Sistema Modernizado
"""
from flask import Blueprint, render_template, redirect, url_for, flash, request, jsonify, send_file
from flask_login import login_required, current_user
from functools import wraps
from datetime import datetime, timedelta, date
from sqlalchemy import func, and_, or_, extract
from app import db
from app.models import Pago, HistorialPago, Cita, Usuario
from io import BytesIO
import base64

pagos_bp = Blueprint('pagos', __name__)


def admin_required(f):
    """Decorador para verificar que el usuario sea administrador"""
    @wraps(f)
    @login_required
    def decorated_function(*args, **kwargs):
        if not current_user.is_admin():
            flash('No tienes permisos para acceder a esta sección.', 'danger')
            return redirect(url_for(f'{current_user.rol}.dashboard'))
        return f(*args, **kwargs)
    return decorated_function


@pagos_bp.route('/')
@admin_required
def dashboard():
    """Dashboard principal de pagos e ingresos"""
    # Obtener rango de fechas (por defecto último mes)
    fecha_fin = date.today()
    fecha_inicio = fecha_fin - timedelta(days=30)

    # Permitir filtrado personalizado
    if request.args.get('fecha_inicio'):
        fecha_inicio = datetime.strptime(request.args.get('fecha_inicio'), '%Y-%m-%d').date()
    if request.args.get('fecha_fin'):
        fecha_fin = datetime.strptime(request.args.get('fecha_fin'), '%Y-%m-%d').date()

    # Estadísticas de pagos
    stats = {
        # Total de ingresos completados
        'ingresos_totales': db.session.query(
            func.sum(Pago.monto)
        ).filter(
            and_(
                func.cast(Pago.fecha_pago, db.Date) >= fecha_inicio,
                func.cast(Pago.fecha_pago, db.Date) <= fecha_fin,
                Pago.estado == 'completado'
            )
        ).scalar() or 0,

        # Pagos pendientes
        'pendientes_total': db.session.query(
            func.sum(Pago.monto - Pago.monto_pagado)
        ).filter(
            Pago.estado == 'pendiente'
        ).scalar() or 0,

        # Cantidad de pagos completados
        'total_pagos_completados': Pago.query.filter(
            and_(
                func.cast(Pago.fecha_pago, db.Date) >= fecha_inicio,
                func.cast(Pago.fecha_pago, db.Date) <= fecha_fin,
                Pago.estado == 'completado'
            )
        ).count(),

        # Cantidad de pagos pendientes
        'total_pagos_pendientes': Pago.query.filter_by(estado='pendiente').count(),

        # Pagos vencidos
        'total_vencidos': Pago.query.filter(
            and_(
                Pago.estado == 'pendiente',
                Pago.fecha_vencimiento < datetime.utcnow()
            )
        ).count(),
    }

    # Ingresos por método de pago
    ingresos_por_metodo = db.session.query(
        Pago.metodo_pago,
        func.count(Pago.id).label('cantidad'),
        func.sum(Pago.monto).label('total')
    ).filter(
        and_(
            func.cast(Pago.fecha_pago, db.Date) >= fecha_inicio,
            func.cast(Pago.fecha_pago, db.Date) <= fecha_fin,
            Pago.estado == 'completado'
        )
    ).group_by(Pago.metodo_pago).all()

    # Ingresos por día (últimos 30 días)
    ingresos_por_dia = db.session.query(
        func.cast(Pago.fecha_pago, db.Date).label('fecha'),
        func.sum(Pago.monto).label('total')
    ).filter(
        and_(
            func.cast(Pago.fecha_pago, db.Date) >= fecha_inicio,
            func.cast(Pago.fecha_pago, db.Date) <= fecha_fin,
            Pago.estado == 'completado'
        )
    ).group_by(func.cast(Pago.fecha_pago, db.Date)).order_by(func.cast(Pago.fecha_pago, db.Date)).all()

    # Top 10 pagos más grandes
    top_pagos = Pago.query.filter(
        and_(
            func.cast(Pago.fecha_pago, db.Date) >= fecha_inicio,
            func.cast(Pago.fecha_pago, db.Date) <= fecha_fin,
            Pago.estado == 'completado'
        )
    ).order_by(Pago.monto.desc()).limit(10).all()

    # Pagos recientes
    pagos_recientes = Pago.query.order_by(Pago.fecha_creacion.desc()).limit(10).all()

    return render_template(
        'admin/pagos/dashboard.html',
        stats=stats,
        ingresos_por_metodo=ingresos_por_metodo,
        ingresos_por_dia=ingresos_por_dia,
        top_pagos=top_pagos,
        pagos_recientes=pagos_recientes,
        fecha_inicio=fecha_inicio,
        fecha_fin=fecha_fin
    )


@pagos_bp.route('/listar')
@admin_required
def listar():
    """Lista todos los pagos con filtros"""
    # Filtros
    estado = request.args.get('estado', '')
    metodo = request.args.get('metodo', '')
    buscar = request.args.get('buscar', '')

    # Query base
    query = Pago.query

    # Aplicar filtros
    if estado:
        query = query.filter_by(estado=estado)
    if metodo:
        query = query.filter_by(metodo_pago=metodo)
    if buscar:
        query = query.filter(
            or_(
                Pago.codigo_pago.contains(buscar),
                Pago.descripcion.contains(buscar),
                Pago.numero_transaccion.contains(buscar)
            )
        )

    # Paginación
    page = request.args.get('page', 1, type=int)
    per_page = 20

    pagos = query.order_by(Pago.fecha_creacion.desc()).paginate(
        page=page, per_page=per_page, error_out=False
    )

    return render_template(
        'admin/pagos/listar.html',
        pagos=pagos,
        estado=estado,
        metodo=metodo,
        buscar=buscar
    )


@pagos_bp.route('/crear', methods=['GET', 'POST'])
@admin_required
def crear():
    """Crea un nuevo pago"""
    if request.method == 'POST':
        try:
            # Datos del formulario
            monto = float(request.form.get('monto'))
            metodo_pago = request.form.get('metodo_pago')
            usuario_id = int(request.form.get('usuario_id'))
            cita_id = request.form.get('cita_id')
            descripcion = request.form.get('descripcion')
            requiere_factura = request.form.get('requiere_factura') == 'on'

            # Crear el pago
            pago = Pago(
                monto=monto,
                metodo_pago=metodo_pago,
                usuario_id=usuario_id,
                descripcion=descripcion,
                requiere_factura=requiere_factura
            )

            if cita_id:
                pago.cita_id = int(cita_id)

            # Generar código de pago
            pago.generar_codigo_pago()

            # Si el método es QR, generar el código QR
            if 'qr' in metodo_pago.lower():
                pago.generar_qr()

            # Si requiere factura, guardar datos
            if requiere_factura:
                pago.nit_cliente = request.form.get('nit_cliente')
                pago.razon_social_cliente = request.form.get('razon_social_cliente')

            db.session.add(pago)
            db.session.commit()

            # Registrar en historial
            historial = HistorialPago(
                pago_id=pago.id,
                accion='creado',
                estado_nuevo='pendiente',
                monto_nuevo=monto,
                descripcion=f'Pago creado por {current_user.nombre_completo}',
                usuario_id=current_user.id
            )
            db.session.add(historial)
            db.session.commit()

            flash(f'Pago {pago.codigo_pago} creado exitosamente', 'success')
            return redirect(url_for('pagos.ver', pago_id=pago.id))

        except Exception as e:
            db.session.rollback()
            flash(f'Error al crear pago: {str(e)}', 'danger')
            return redirect(url_for('pagos.crear'))

    # GET - Mostrar formulario
    # Obtener usuarios (tutores) para el dropdown
    usuarios = Usuario.query.filter_by(rol='tutor', activo=True).order_by(Usuario.nombre).all()

    # Obtener citas pendientes de pago
    citas_pendientes = Cita.query.filter(
        and_(
            Cita.pagado == False,
            Cita.estado.in_(['completada', 'pendiente'])
        )
    ).order_by(Cita.fecha.desc()).limit(50).all()

    return render_template(
        'admin/pagos/crear.html',
        usuarios=usuarios,
        citas_pendientes=citas_pendientes
    )


@pagos_bp.route('/<int:pago_id>')
@admin_required
def ver(pago_id):
    """Ver detalle de un pago"""
    pago = Pago.query.get_or_404(pago_id)

    # Obtener historial
    historial = pago.historial.all()

    return render_template(
        'admin/pagos/ver.html',
        pago=pago,
        historial=historial
    )


@pagos_bp.route('/<int:pago_id>/procesar', methods=['POST'])
@admin_required
def procesar(pago_id):
    """Procesa un pago (marca como completado)"""
    pago = Pago.query.get_or_404(pago_id)

    try:
        numero_transaccion = request.form.get('numero_transaccion')
        numero_autorizacion = request.form.get('numero_autorizacion')
        banco = request.form.get('banco')
        ultimos_digitos = request.form.get('ultimos_digitos_tarjeta')

        # Actualizar información
        if numero_transaccion:
            pago.numero_transaccion = numero_transaccion
        if numero_autorizacion:
            pago.numero_autorizacion = numero_autorizacion
        if banco:
            pago.banco = banco
        if ultimos_digitos:
            pago.ultimos_digitos_tarjeta = ultimos_digitos

        # Marcar como completado
        pago.marcar_como_completado(
            numero_transaccion=numero_transaccion,
            procesado_por=current_user.id
        )

        # Si está asociado a una cita, marcar la cita como pagada
        if pago.cita_id:
            cita = Cita.query.get(pago.cita_id)
            if cita:
                cita.pagado = True
                cita.metodo_pago = pago.metodo_pago
                db.session.commit()

        # Registrar en historial
        historial = HistorialPago(
            pago_id=pago.id,
            accion='completado',
            estado_anterior='pendiente',
            estado_nuevo='completado',
            descripcion=f'Pago procesado por {current_user.nombre_completo}',
            usuario_id=current_user.id
        )
        db.session.add(historial)
        db.session.commit()

        flash(f'Pago {pago.codigo_pago} procesado exitosamente', 'success')

    except Exception as e:
        db.session.rollback()
        flash(f'Error al procesar pago: {str(e)}', 'danger')

    return redirect(url_for('pagos.ver', pago_id=pago.id))


@pagos_bp.route('/<int:pago_id>/pago-parcial', methods=['POST'])
@admin_required
def pago_parcial(pago_id):
    """Registra un pago parcial"""
    pago = Pago.query.get_or_404(pago_id)

    try:
        monto_parcial = float(request.form.get('monto_parcial'))

        if monto_parcial <= 0:
            flash('El monto debe ser mayor a 0', 'warning')
            return redirect(url_for('pagos.ver', pago_id=pago.id))

        if monto_parcial > pago.saldo_pendiente:
            flash('El monto no puede ser mayor al saldo pendiente', 'warning')
            return redirect(url_for('pagos.ver', pago_id=pago.id))

        # Agregar pago parcial
        pago.agregar_pago_parcial(monto_parcial)

        # Registrar en historial
        historial = HistorialPago(
            pago_id=pago.id,
            accion='pago_parcial',
            monto_anterior=pago.monto_pagado - monto_parcial,
            monto_nuevo=pago.monto_pagado,
            descripcion=f'Pago parcial de Bs. {monto_parcial} registrado por {current_user.nombre_completo}',
            usuario_id=current_user.id
        )
        db.session.add(historial)
        db.session.commit()

        flash(f'Pago parcial de Bs. {monto_parcial} registrado exitosamente', 'success')

    except Exception as e:
        db.session.rollback()
        flash(f'Error al registrar pago parcial: {str(e)}', 'danger')

    return redirect(url_for('pagos.ver', pago_id=pago.id))


@pagos_bp.route('/<int:pago_id>/reembolsar', methods=['POST'])
@admin_required
def reembolsar(pago_id):
    """Procesa un reembolso"""
    pago = Pago.query.get_or_404(pago_id)

    try:
        razon = request.form.get('razon_reembolso')

        # Procesar reembolso
        if pago.procesar_reembolso(procesado_por=current_user.id):
            # Si está asociado a una cita, desmarcar como pagada
            if pago.cita_id:
                cita = Cita.query.get(pago.cita_id)
                if cita:
                    cita.pagado = False
                    db.session.commit()

            # Registrar en historial
            historial = HistorialPago(
                pago_id=pago.id,
                accion='reembolsado',
                estado_anterior='completado',
                estado_nuevo='reembolsado',
                descripcion=f'Reembolso procesado por {current_user.nombre_completo}. Razón: {razon}',
                usuario_id=current_user.id
            )
            db.session.add(historial)
            db.session.commit()

            flash('Reembolso procesado exitosamente', 'success')
        else:
            flash('No se pudo procesar el reembolso. El pago debe estar completado.', 'warning')

    except Exception as e:
        db.session.rollback()
        flash(f'Error al procesar reembolso: {str(e)}', 'danger')

    return redirect(url_for('pagos.ver', pago_id=pago.id))


@pagos_bp.route('/<int:pago_id>/regenerar-qr', methods=['POST'])
@admin_required
def regenerar_qr(pago_id):
    """Regenera el código QR de un pago"""
    pago = Pago.query.get_or_404(pago_id)

    try:
        # Regenerar QR
        pago.generar_qr()
        db.session.commit()

        flash('Código QR regenerado exitosamente', 'success')

    except Exception as e:
        db.session.rollback()
        flash(f'Error al regenerar QR: {str(e)}', 'danger')

    return redirect(url_for('pagos.ver', pago_id=pago.id))


@pagos_bp.route('/<int:pago_id>/qr-image')
def obtener_qr_image(pago_id):
    """Retorna la imagen del QR"""
    pago = Pago.query.get_or_404(pago_id)

    if not pago.qr_code_image:
        return "No hay código QR disponible", 404

    # Decodificar base64 a imagen
    img_data = base64.b64decode(pago.qr_code_image)

    return send_file(
        BytesIO(img_data),
        mimetype='image/png',
        as_attachment=False,
        download_name=f'qr-{pago.codigo_pago}.png'
    )


@pagos_bp.route('/api/buscar-usuario')
@admin_required
def api_buscar_usuario():
    """API para buscar usuarios (para autocompletado)"""
    busqueda = request.args.get('q', '')

    usuarios = Usuario.query.filter(
        and_(
            Usuario.rol == 'tutor',
            Usuario.activo == True,
            or_(
                Usuario.nombre.contains(busqueda),
                Usuario.apellido.contains(busqueda),
                Usuario.email.contains(busqueda)
            )
        )
    ).limit(10).all()

    resultados = [{
        'id': u.id,
        'nombre': u.nombre_completo,
        'email': u.email
    } for u in usuarios]

    return jsonify(resultados)


@pagos_bp.route('/api/cita/<int:cita_id>')
@admin_required
def api_obtener_cita(cita_id):
    """API para obtener información de una cita"""
    cita = Cita.query.get_or_404(cita_id)

    return jsonify({
        'id': cita.id,
        'costo': cita.costo,
        'descripcion': f'Consulta para {cita.mascota.nombre} - {cita.motivo}',
        'tutor_id': cita.tutor_id,
        'tutor_nombre': cita.tutor.nombre_completo
    })
