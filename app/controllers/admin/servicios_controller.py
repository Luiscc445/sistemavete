"""
Controlador de Servicios (Admin)
Gestiona las áreas médicas y precios
"""
from flask import Blueprint, render_template, redirect, url_for, flash, request
from flask_login import login_required, current_user
from functools import wraps
from app import db
from app.models.servicio import Servicio

servicios_bp = Blueprint('servicios_admin', __name__)

def admin_required(f):
    """Decorador para requerir rol de administrador"""
    @wraps(f)
    @login_required
    def decorated_function(*args, **kwargs):
        if not current_user.is_admin():
            flash('Acceso no autorizado.', 'danger')
            return redirect(url_for('auth.index'))
        return f(*args, **kwargs)
    return decorated_function

@servicios_bp.route('/servicios')
@admin_required
def index():
    """Listar todos los servicios"""
    servicios = Servicio.query.order_by(Servicio.nombre.asc()).all()
    return render_template('admin/servicios/index.html', servicios=servicios)

@servicios_bp.route('/servicios/nuevo', methods=['GET', 'POST'])
@admin_required
def nuevo():
    """Crear nuevo servicio"""
    if request.method == 'POST':
        codigo = request.form.get('codigo')
        nombre = request.form.get('nombre')
        categoria = request.form.get('categoria')
        precio = request.form.get('precio')
        duracion = request.form.get('duracion')
        descripcion = request.form.get('descripcion')

        if not all([codigo, nombre, precio]):
            flash('Código, nombre y precio son obligatorios.', 'danger')
            return render_template('admin/servicios/formulario.html')

        try:
            nuevo_servicio = Servicio(
                codigo=codigo,
                nombre=nombre,
                categoria=categoria,
                precio=float(precio),
                duracion_estimada=int(duracion) if duracion else 30,
                descripcion=descripcion,
                activo=True
            )
            db.session.add(nuevo_servicio)
            db.session.commit()
            flash('Servicio creado exitosamente.', 'success')
            return redirect(url_for('servicios_admin.index'))
        except Exception as e:
            db.session.rollback()
            flash(f'Error al crear servicio: {str(e)}', 'danger')

    return render_template('admin/servicios/formulario.html')

@servicios_bp.route('/servicios/editar/<int:id>', methods=['GET', 'POST'])
@admin_required
def editar(id):
    """Editar servicio existente"""
    servicio = Servicio.query.get_or_404(id)

    if request.method == 'POST':
        servicio.nombre = request.form.get('nombre')
        servicio.categoria = request.form.get('categoria')
        servicio.descripcion = request.form.get('descripcion')
        
        try:
            servicio.precio = float(request.form.get('precio'))
            duracion = request.form.get('duracion')
            if duracion:
                servicio.duracion_estimada = int(duracion)
        except ValueError:
            flash('Precio o duración inválidos.', 'danger')
            return render_template('admin/servicios/formulario.html', servicio=servicio)

        try:
            db.session.commit()
            flash('Servicio actualizado exitosamente.', 'success')
            return redirect(url_for('servicios_admin.index'))
        except Exception as e:
            db.session.rollback()
            flash(f'Error al actualizar servicio: {str(e)}', 'danger')

    return render_template('admin/servicios/formulario.html', servicio=servicio)

@servicios_bp.route('/servicios/eliminar/<int:id>', methods=['POST'])
@admin_required
def eliminar(id):
    """Desactivar servicio (Soft Delete)"""
    servicio = Servicio.query.get_or_404(id)
    servicio.activo = False
    db.session.commit()
    flash('Servicio desactivado.', 'success')
    return redirect(url_for('servicios_admin.index'))
