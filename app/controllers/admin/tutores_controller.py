"""
Controlador CRUD para Tutores
"""
from flask import Blueprint, render_template, redirect, url_for, flash, request
from sqlalchemy import or_
from app import db
from app.models import Usuario, Mascota, Cita
from .utils import admin_required, registrar_auditoria

tutores_bp = Blueprint('admin_tutores', __name__)

@tutores_bp.route('/tutores')
@admin_required
def lista():
    """Lista de tutores con sus mascotas"""
    page = request.args.get('page', 1, type=int)
    search = request.args.get('search', '')
    
    query = Usuario.query.filter_by(rol='tutor')
    
    if search:
        query = query.filter(
            or_(
                Usuario.nombre.ilike(f'%{search}%'),
                Usuario.apellido.ilike(f'%{search}%'),
                Usuario.email.ilike(f'%{search}%')
            )
        )
    
    tutores = query.order_by(Usuario.nombre.asc()).paginate(page=page, per_page=10, error_out=False)
    
    # Calcular total de mascotas de forma segura
    if tutores.items:
        for tutor in tutores.items:
            try:
                tutor.total_mascotas = tutor.mascotas.count()
            except Exception as e:
                print(f"Error al contar mascotas del tutor {tutor.id}: {e}")
                tutor.total_mascotas = 0
    
    return render_template('admin/tutores/lista.html', tutores=tutores, search=search)

@tutores_bp.route('/tutor/nuevo', methods=['GET', 'POST'])
@admin_required
def nuevo():
    """Crear un nuevo tutor"""
    if request.method == 'POST':
        username = request.form.get('username')
        email = request.form.get('email')
        password = request.form.get('password')
        nombre = request.form.get('nombre')
        apellido = request.form.get('apellido')
        telefono = request.form.get('telefono')
        direccion = request.form.get('direccion')
        
        if Usuario.query.filter_by(username=username).first():
            flash('El nombre de usuario ya está registrado', 'danger')
            return render_template('admin/tutores/nuevo.html')
        
        if Usuario.query.filter_by(email=email).first():
            flash('El email ya está registrado', 'danger')
            return render_template('admin/tutores/nuevo.html')
        
        if not all([username, email, password, nombre, apellido]):
            flash('Por favor complete todos los campos obligatorios (*)', 'danger')
            return render_template('admin/tutores/nuevo.html')
        
        nuevo_tutor = Usuario(
            username=username,
            email=email,
            password=password,
            nombre=nombre,
            apellido=apellido,
            telefono=telefono,
            direccion=direccion,
            rol='tutor',
            activo=True,
            verificado=True
        )
        
        try:
            db.session.add(nuevo_tutor)
            db.session.flush()
            registrar_auditoria('crear_tutor', 'usuario', nuevo_tutor.id, 
                              f'Admin creó nuevo tutor: {nuevo_tutor.nombre_completo}')
            db.session.commit()
            flash('Tutor creado exitosamente', 'success')
            return redirect(url_for('admin_tutores.lista'))
        except Exception as e:
            db.session.rollback()
            flash(f'Error al crear tutor: {str(e)}', 'danger')
    
    return render_template('admin/tutores/nuevo.html')

@tutores_bp.route('/tutor/<int:tutor_id>')
@admin_required
def ver(tutor_id):
    """Ver detalles de un tutor y sus mascotas"""
    tutor = Usuario.query.get_or_404(tutor_id)
    
    if tutor.rol != 'tutor':
        flash('El usuario especificado no es un tutor', 'warning')
        return redirect(url_for('admin_tutores.lista'))
    
    mascotas = tutor.mascotas.order_by(Mascota.nombre.asc()).all()
    citas = tutor.citas_como_tutor.order_by(Cita.fecha.desc()).limit(10).all()
    
    stats = {
        'total_mascotas': len(mascotas),
        'total_citas': tutor.citas_como_tutor.count(),
        'citas_pendientes': tutor.citas_como_tutor.filter_by(estado='pendiente').count(),
        'proxima_cita': tutor.citas_como_tutor.filter(
            Cita.fecha >= db.func.now(),
            Cita.estado == 'aceptada'
        ).order_by(Cita.fecha).first()
    }
    
    registrar_auditoria('ver_tutor', 'usuario', tutor_id, 
                       f'Visualización de tutor: {tutor.nombre_completo}')
    db.session.commit()
    
    return render_template('admin/tutores/ver.html',
                         tutor=tutor,
                         mascotas=mascotas,
                         citas=citas,
                         stats=stats)

@tutores_bp.route('/tutor/<int:tutor_id>/editar', methods=['GET', 'POST'])
@admin_required
def editar(tutor_id):
    """Editar un tutor existente"""
    tutor = Usuario.query.get_or_404(tutor_id)
    
    if tutor.rol != 'tutor':
        flash('El usuario especificado no es un tutor', 'warning')
        return redirect(url_for('admin_tutores.lista'))
    
    if request.method == 'POST':
        tutor.nombre = request.form.get('nombre')
        tutor.apellido = request.form.get('apellido')
        tutor.email = request.form.get('email')
        tutor.telefono = request.form.get('telefono')
        tutor.direccion = request.form.get('direccion')
        tutor.activo = request.form.get('activo') == 'on'
        
        nueva_password = request.form.get('nueva_password')
        if nueva_password:
            tutor.set_password(nueva_password)
        
        try:
            registrar_auditoria('editar_tutor', 'usuario', tutor.id, 
                              f'Admin editó al tutor: {tutor.nombre_completo}')
            db.session.commit()
            flash('Tutor actualizado exitosamente', 'success')
            return redirect(url_for('admin_tutores.ver', tutor_id=tutor.id))
        except Exception as e:
            db.session.rollback()
            flash(f'Error al actualizar tutor: {str(e)}', 'danger')
    
    return render_template('admin/tutores/editar.html', tutor=tutor)

@tutores_bp.route('/tutor/<int:tutor_id>/eliminar', methods=['POST'])
@admin_required
def eliminar(tutor_id):
    """Eliminar un tutor y todas sus relaciones"""
    tutor = Usuario.query.get_or_404(tutor_id)
    
    if tutor.rol != 'tutor':
        flash('El usuario especificado no es un tutor', 'warning')
        return redirect(url_for('admin_tutores.lista'))
    
    try:
        nombre_tutor = tutor.nombre_completo
        total_mascotas = tutor.mascotas.count()
        
        # Eliminar mascotas asociadas (esto también eliminará citas, historiales, etc. por CASCADE)
        for mascota in tutor.mascotas:
            db.session.delete(mascota)
        
        # Eliminar citas del tutor
        for cita in tutor.citas_como_tutor:
            db.session.delete(cita)
        
        # Eliminar el tutor
        db.session.delete(tutor)
        
        # Registrar auditoría
        registrar_auditoria(
            'eliminar_tutor', 
            'usuario', 
            tutor_id, 
            f'Admin eliminó al tutor: {nombre_tutor} (con {total_mascotas} mascotas)'
        )
        
        db.session.commit()
        flash(f'Tutor "{nombre_tutor}" eliminado exitosamente', 'success')
        
    except Exception as e:
        db.session.rollback()
        flash(f'Error al eliminar tutor: {str(e)}', 'danger')
        print(f"Error al eliminar tutor {tutor_id}: {e}")
    
    return redirect(url_for('admin_tutores.lista'))
