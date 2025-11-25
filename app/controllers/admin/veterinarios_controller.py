"""
Controlador CRUD para Veterinarios
"""
from flask import Blueprint, render_template, redirect, url_for, flash, request
from app import db
from app.models import Usuario, Cita, Servicio
from .utils import admin_required, registrar_auditoria

veterinarios_bp = Blueprint('admin_veterinarios', __name__)

@veterinarios_bp.route('/veterinarios')
@admin_required
def lista():
    """Lista de veterinarios con estadísticas y filtrado"""
    page = request.args.get('page', 1, type=int)
    especialidad_filtro = request.args.get('especialidad')
    
    query = Usuario.query.filter_by(rol='veterinario')
    
    if especialidad_filtro:
        query = query.filter(Usuario.especialidad == especialidad_filtro)
        
    veterinarios = query.order_by(Usuario.nombre).paginate(
        page=page, per_page=10, error_out=False
    )
    
    # Obtener servicios para el filtro
    servicios = Servicio.query.filter_by(activo=True).order_by(Servicio.nombre).all()
    
    # Obtener estadísticas de forma segura
    if veterinarios.items:
        for vet in veterinarios.items:
            try:
                vet.stats = vet.get_estadisticas_veterinario()
            except Exception as e:
                print(f"Error al obtener estadísticas del veterinario {vet.id}: {e}")
                vet.stats = {
                    'citas_completadas': 0,
                    'citas_pendientes': 0,
                    'total_citas': 0
                }
    
    return render_template('admin/veterinarios/lista.html', 
                         veterinarios=veterinarios,
                         servicios=servicios,
                         especialidad_actual=especialidad_filtro)

@veterinarios_bp.route('/veterinario/nuevo', methods=['GET', 'POST'])
@admin_required
def nuevo():
    """Crear un nuevo veterinario"""
    # Obtener servicios activos para el dropdown de especialidades
    servicios = Servicio.query.filter_by(activo=True).order_by(Servicio.nombre).all()
    
    if request.method == 'POST':
        username = request.form.get('username')
        email = request.form.get('email')
        password = request.form.get('password')
        nombre = request.form.get('nombre')
        apellido = request.form.get('apellido')
        telefono = request.form.get('telefono')
        licencia = request.form.get('licencia_profesional')
        especialidad = request.form.get('especialidad')
        
        # Validaciones
        if Usuario.query.filter_by(username=username).first():
            flash('El nombre de usuario ya está registrado', 'danger')
            return render_template('admin/veterinarios/nuevo.html', servicios=servicios)
        
        if Usuario.query.filter_by(email=email).first():
            flash('El email ya está registrado', 'danger')
            return render_template('admin/veterinarios/nuevo.html', servicios=servicios)
        
        if not all([username, email, password, nombre, apellido, especialidad]):
            flash('Por favor complete todos los campos obligatorios (*)', 'danger')
            return render_template('admin/veterinarios/nuevo.html', servicios=servicios)
        
        nuevo_vet = Usuario(
            username=username,
            email=email,
            password=password,
            nombre=nombre,
            apellido=apellido,
            telefono=telefono,
            rol='veterinario',
            especialidad=especialidad,
            licencia_profesional=licencia,
            activo=True,
            verificado=True
        )
        
        try:
            db.session.add(nuevo_vet)
            db.session.flush()
            registrar_auditoria('crear_veterinario', 'usuario', nuevo_vet.id, 
                              f'Admin creó nuevo veterinario: {nuevo_vet.nombre_completo}')
            db.session.commit()
            flash('Veterinario creado exitosamente', 'success')
            return redirect(url_for('admin_veterinarios.lista'))
        except Exception as e:
            db.session.rollback()
            flash(f'Error al crear veterinario: {str(e)}', 'danger')
    
    return render_template('admin/veterinarios/nuevo.html', servicios=servicios)

@veterinarios_bp.route('/veterinario/<int:vet_id>')
@admin_required
def ver(vet_id):
    """Ver detalles de un veterinario y sus citas"""
    veterinario = Usuario.query.get_or_404(vet_id)
    
    if not veterinario.is_veterinario():
        flash('El usuario especificado no es un veterinario', 'warning')
        return redirect(url_for('admin_veterinarios.lista'))
    
    citas = veterinario.citas_como_veterinario.order_by(Cita.fecha.desc()).limit(10).all()
    stats = veterinario.get_estadisticas_veterinario()
    
    registrar_auditoria('ver_veterinario', 'usuario', vet_id, 
                       f'Visualización de veterinario: {veterinario.nombre_completo}')
    db.session.commit()
    
    return render_template('admin/veterinarios/ver.html',
                         veterinario=veterinario,
                         citas=citas,
                         stats=stats)

@veterinarios_bp.route('/veterinario/<int:vet_id>/editar', methods=['GET', 'POST'])
@admin_required
def editar(vet_id):
    """Editar un veterinario existente"""
    veterinario = Usuario.query.get_or_404(vet_id)
    
    # Obtener servicios activos para el dropdown
    servicios = Servicio.query.filter_by(activo=True).order_by(Servicio.nombre).all()
    
    if not veterinario.is_veterinario():
        flash('El usuario especificado no es un veterinario', 'warning')
        return redirect(url_for('admin_veterinarios.lista'))
    
    if request.method == 'POST':
        veterinario.nombre = request.form.get('nombre')
        veterinario.apellido = request.form.get('apellido')
        veterinario.email = request.form.get('email')
        veterinario.telefono = request.form.get('telefono')
        veterinario.licencia_profesional = request.form.get('licencia_profesional')
        veterinario.activo = request.form.get('activo') == 'on'
        veterinario.especialidad = request.form.get('especialidad')
        
        nueva_password = request.form.get('nueva_password')
        if nueva_password:
            veterinario.set_password(nueva_password)
        
        try:
            registrar_auditoria('editar_veterinario', 'usuario', veterinario.id, 
                              f'Admin editó al veterinario: {veterinario.nombre_completo}')
            db.session.commit()
            flash('Veterinario actualizado exitosamente', 'success')
            return redirect(url_for('admin_veterinarios.ver', vet_id=veterinario.id))
        except Exception as e:
            db.session.rollback()
            flash(f'Error al actualizar veterinario: {str(e)}', 'danger')
    
    return render_template('admin/veterinarios/editar.html', 
                         veterinario=veterinario, 
                         servicios=servicios)

@veterinarios_bp.route('/veterinario/<int:vet_id>/eliminar', methods=['POST'])
@admin_required
def eliminar(vet_id):
    """Eliminar un veterinario y todas sus relaciones"""
    veterinario = Usuario.query.get_or_404(vet_id)
    
    if not veterinario.is_veterinario():
        flash('El usuario especificado no es un veterinario', 'warning')
        return redirect(url_for('admin_veterinarios.lista'))
    
    try:
        nombre_vet = veterinario.nombre_completo
        total_citas = veterinario.citas_como_veterinario.count()
        
        # Eliminar citas asociadas
        for cita in veterinario.citas_como_veterinario:
            db.session.delete(cita)
        
        # Eliminar el veterinario
        db.session.delete(veterinario)
        
        # Registrar auditoría
        registrar_auditoria(
            'eliminar_veterinario', 
            'usuario', 
            vet_id, 
            f'Admin eliminó al veterinario: {nombre_vet} (con {total_citas} citas)'
        )
        
        db.session.commit()
        flash(f'Veterinario "{nombre_vet}" eliminado exitosamente', 'success')
        
    except Exception as e:
        db.session.rollback()
        flash(f'Error al eliminar veterinario: {str(e)}', 'danger')
        print(f"Error al eliminar veterinario {vet_id}: {e}")
    
    return redirect(url_for('admin_veterinarios.lista'))
