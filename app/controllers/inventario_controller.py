"""
Controlador de Inventario - CRUD de Medicamentos
"""
from flask import Blueprint, render_template, redirect, url_for, flash, request, jsonify
from flask_login import login_required, current_user
from functools import wraps
from datetime import datetime, timedelta, date
from sqlalchemy import func, and_, or_
from app import db
from app.models import Medicamento

inventario_bp = Blueprint('inventario', __name__)


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


@inventario_bp.route('/')
@admin_required
def lista():
    """Lista de medicamentos con filtros"""
    page = request.args.get('page', 1, type=int)
    search = request.args.get('search', '', type=str)
    categoria = request.args.get('categoria', '', type=str)
    estado = request.args.get('estado', '', type=str)

    query = Medicamento.query

    # Filtrar por búsqueda
    if search:
        query = query.filter(
            or_(
                Medicamento.nombre.ilike(f'%{search}%'),
                Medicamento.codigo.ilike(f'%{search}%'),
                Medicamento.principio_activo.ilike(f'%{search}%'),
                Medicamento.laboratorio.ilike(f'%{search}%')
            )
        )

    # Filtrar por categoría
    if categoria:
        query = query.filter(Medicamento.categoria == categoria)

    # Filtrar por estado
    if estado == 'bajo_stock':
        query = query.filter(Medicamento.stock_actual <= Medicamento.stock_minimo)
    elif estado == 'por_vencer':
        fecha_limite = date.today() + timedelta(days=30)
        query = query.filter(
            and_(
                Medicamento.fecha_vencimiento <= fecha_limite,
                Medicamento.fecha_vencimiento > date.today()
            )
        )
    elif estado == 'vencido':
        query = query.filter(Medicamento.fecha_vencimiento <= date.today())
    elif estado == 'activo':
        query = query.filter(Medicamento.activo == True)
    elif estado == 'inactivo':
        query = query.filter(Medicamento.activo == False)

    medicamentos = query.order_by(Medicamento.nombre.asc()).paginate(
        page=page, per_page=15, error_out=False
    )

    # Obtener categorías únicas para el filtro
    categorias = db.session.query(Medicamento.categoria).distinct().filter(
        Medicamento.categoria.isnot(None)
    ).all()
    categorias = [c[0] for c in categorias if c[0]]

    # Estadísticas rápidas
    stats = {
        'total': Medicamento.query.count(),
        'activos': Medicamento.query.filter_by(activo=True).count(),
        'bajo_stock': Medicamento.query.filter(
            Medicamento.stock_actual <= Medicamento.stock_minimo
        ).count(),
        'por_vencer': Medicamento.query.filter(
            and_(
                Medicamento.fecha_vencimiento <= date.today() + timedelta(days=30),
                Medicamento.fecha_vencimiento > date.today()
            )
        ).count(),
        'vencidos': Medicamento.query.filter(
            Medicamento.fecha_vencimiento <= date.today()
        ).count()
    }

    return render_template(
        'admin/inventario/lista.html',
        medicamentos=medicamentos,
        categorias=categorias,
        search=search,
        categoria=categoria,
        estado=estado,
        stats=stats
    )


@inventario_bp.route('/nuevo', methods=['GET', 'POST'])
@admin_required
def nuevo():
    """Crear un nuevo medicamento"""
    if request.method == 'POST':
        try:
            # Obtener datos del formulario
            codigo = request.form.get('codigo')
            nombre = request.form.get('nombre')
            principio_activo = request.form.get('principio_activo')
            presentacion = request.form.get('presentacion')
            concentracion = request.form.get('concentracion')
            categoria = request.form.get('categoria')
            via_administracion = request.form.get('via_administracion')
            stock_actual = int(request.form.get('stock_actual', 0))
            stock_minimo = int(request.form.get('stock_minimo', 5))
            unidad_medida = request.form.get('unidad_medida')
            precio_compra = float(request.form.get('precio_compra', 0))
            precio_venta = float(request.form.get('precio_venta', 0))
            laboratorio = request.form.get('laboratorio')
            lote = request.form.get('lote')
            fecha_vencimiento = request.form.get('fecha_vencimiento')
            requiere_receta = request.form.get('requiere_receta') == 'on'
            controlado = request.form.get('controlado') == 'on'
            ubicacion_almacen = request.form.get('ubicacion_almacen')

            # Validar que no exista un medicamento con el mismo código
            if codigo and Medicamento.query.filter_by(codigo=codigo).first():
                flash('Ya existe un medicamento con ese código.', 'danger')
                return redirect(url_for('inventario.nuevo'))

            # Crear medicamento
            medicamento = Medicamento(
                codigo=codigo,
                nombre=nombre,
                principio_activo=principio_activo,
                presentacion=presentacion,
                concentracion=concentracion,
                categoria=categoria,
                via_administracion=via_administracion,
                stock_actual=stock_actual,
                stock_minimo=stock_minimo,
                unidad_medida=unidad_medida,
                precio_compra=precio_compra,
                precio_venta=precio_venta,
                laboratorio=laboratorio,
                lote=lote,
                fecha_vencimiento=datetime.strptime(fecha_vencimiento, '%Y-%m-%d').date() if fecha_vencimiento else None,
                requiere_receta=requiere_receta,
                controlado=controlado,
                ubicacion_almacen=ubicacion_almacen,
                activo=True
            )

            db.session.add(medicamento)
            db.session.commit()

            flash(f'Medicamento "{nombre}" creado exitosamente.', 'success')
            return redirect(url_for('inventario.lista'))

        except Exception as e:
            db.session.rollback()
            flash(f'Error al crear el medicamento: {str(e)}', 'danger')
            return redirect(url_for('inventario.nuevo'))

    # GET request
    return render_template('admin/inventario/nuevo.html')


@inventario_bp.route('/<int:med_id>')
@admin_required
def ver(med_id):
    """Ver detalles de un medicamento"""
    medicamento = Medicamento.query.get_or_404(med_id)
    return render_template('admin/inventario/ver.html', medicamento=medicamento)


@inventario_bp.route('/<int:med_id>/editar', methods=['GET', 'POST'])
@admin_required
def editar(med_id):
    """Editar un medicamento existente"""
    medicamento = Medicamento.query.get_or_404(med_id)

    if request.method == 'POST':
        try:
            # Actualizar datos
            medicamento.codigo = request.form.get('codigo')
            medicamento.nombre = request.form.get('nombre')
            medicamento.principio_activo = request.form.get('principio_activo')
            medicamento.presentacion = request.form.get('presentacion')
            medicamento.concentracion = request.form.get('concentracion')
            medicamento.categoria = request.form.get('categoria')
            medicamento.via_administracion = request.form.get('via_administracion')
            medicamento.stock_actual = int(request.form.get('stock_actual', 0))
            medicamento.stock_minimo = int(request.form.get('stock_minimo', 5))
            medicamento.unidad_medida = request.form.get('unidad_medida')
            medicamento.precio_compra = float(request.form.get('precio_compra', 0))
            medicamento.precio_venta = float(request.form.get('precio_venta', 0))
            medicamento.laboratorio = request.form.get('laboratorio')
            medicamento.lote = request.form.get('lote')

            fecha_vencimiento = request.form.get('fecha_vencimiento')
            if fecha_vencimiento:
                medicamento.fecha_vencimiento = datetime.strptime(fecha_vencimiento, '%Y-%m-%d').date()

            medicamento.requiere_receta = request.form.get('requiere_receta') == 'on'
            medicamento.controlado = request.form.get('controlado') == 'on'
            medicamento.ubicacion_almacen = request.form.get('ubicacion_almacen')
            medicamento.activo = request.form.get('activo') == 'on'

            medicamento.ultima_actualizacion = datetime.utcnow()

            db.session.commit()

            flash(f'Medicamento "{medicamento.nombre}" actualizado exitosamente.', 'success')
            return redirect(url_for('inventario.ver', med_id=medicamento.id))

        except Exception as e:
            db.session.rollback()
            flash(f'Error al actualizar el medicamento: {str(e)}', 'danger')

    return render_template('admin/inventario/editar.html', medicamento=medicamento)


@inventario_bp.route('/<int:med_id>/ajustar-stock', methods=['POST'])
@admin_required
def ajustar_stock(med_id):
    """Ajustar stock de un medicamento"""
    medicamento = Medicamento.query.get_or_404(med_id)

    try:
        tipo_ajuste = request.form.get('tipo_ajuste')
        cantidad = int(request.form.get('cantidad', 0))
        motivo = request.form.get('motivo', '')

        if cantidad <= 0:
            flash('La cantidad debe ser mayor a 0.', 'danger')
            return redirect(url_for('inventario.ver', med_id=med_id))

        if tipo_ajuste == 'entrada':
            medicamento.aumentar_stock(cantidad)
            flash(f'Se agregaron {cantidad} {medicamento.unidad_medida} al stock. Motivo: {motivo}', 'success')
        elif tipo_ajuste == 'salida':
            if medicamento.reducir_stock(cantidad):
                flash(f'Se retiraron {cantidad} {medicamento.unidad_medida} del stock. Motivo: {motivo}', 'success')
            else:
                flash('Stock insuficiente para realizar la salida.', 'danger')
                return redirect(url_for('inventario.ver', med_id=med_id))

        db.session.commit()

    except Exception as e:
        db.session.rollback()
        flash(f'Error al ajustar stock: {str(e)}', 'danger')

    return redirect(url_for('inventario.ver', med_id=med_id))


@inventario_bp.route('/<int:med_id>/eliminar', methods=['POST'])
@admin_required
def eliminar(med_id):
    """Desactivar un medicamento (soft delete)"""
    medicamento = Medicamento.query.get_or_404(med_id)

    try:
        medicamento.activo = False
        db.session.commit()
        flash(f'Medicamento "{medicamento.nombre}" desactivado exitosamente.', 'success')
    except Exception as e:
        db.session.rollback()
        flash(f'Error al desactivar el medicamento: {str(e)}', 'danger')

    return redirect(url_for('inventario.lista'))


@inventario_bp.route('/alertas')
@admin_required
def alertas():
    """Vista de alertas de inventario"""
    # Medicamentos con bajo stock
    bajo_stock = Medicamento.query.filter(
        Medicamento.stock_actual <= Medicamento.stock_minimo,
        Medicamento.activo == True
    ).all()

    # Medicamentos por vencer (próximos 30 días)
    fecha_limite = date.today() + timedelta(days=30)
    por_vencer = Medicamento.query.filter(
        and_(
            Medicamento.fecha_vencimiento <= fecha_limite,
            Medicamento.fecha_vencimiento > date.today(),
            Medicamento.activo == True
        )
    ).all()

    # Medicamentos vencidos
    vencidos = Medicamento.query.filter(
        Medicamento.fecha_vencimiento <= date.today(),
        Medicamento.activo == True
    ).all()

    return render_template(
        'admin/inventario/alertas.html',
        bajo_stock=bajo_stock,
        por_vencer=por_vencer,
        vencidos=vencidos
    )
