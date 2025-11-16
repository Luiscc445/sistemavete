"""
Controlador de Administrador con funcionalidades completas
"""
from flask import Blueprint, render_template, redirect, url_for, flash, request, jsonify
from flask_login import login_required, current_user
from functools import wraps
from datetime import datetime, timedelta, date
from sqlalchemy import func, and_, or_
from app import db
from app.models import (
    Usuario, Mascota, Cita, HistorialClinico, 
    Servicio, Medicamento, Notificacion, Vacuna,
    ConfiguracionSistema, AuditoriaAccion, DocumentoMascota,
    ServicioCita
)

admin_bp = Blueprint('admin', __name__)

# --- TU REQUERIMIENTO: Lista de especialidades ---
# El admin ahora seleccionará de esta lista.
LISTA_ESPECIALIDADES = [
    'Medicina General',
    'Cirugía',
    'Dermatología',
    'Cardiología',
    'Oncología',
    'Animales Exóticos',
    'Fisioterapia'
]
# -------------------------------------------------

def admin_required(f):
    """Decorador para requerir rol de administrador"""
    @wraps(f)
    @login_required
    def decorated_function(*args, **kwargs):
        if not current_user.is_admin():
            flash('No tienes permisos para acceder a esta página', 'danger')
            return redirect(url_for('index')) # Redirige a la página principal
        return f(*args, **kwargs)
    return decorated_function

def registrar_auditoria(accion, entidad, entidad_id, descripcion, datos_anteriores=None, datos_nuevos=None):
    """Registra una acción en el sistema de auditoría"""
    # Esta función es importante para el control
    try:
        auditoria = AuditoriaAccion(
            usuario_id=current_user.id,
            accion=accion,
            entidad=entidad,
            entidad_id=entidad_id,
            descripcion=descripcion,
            datos_anteriores=datos_anteriores,
            datos_nuevos=datos_nuevos,
            ip_address=request.remote_addr,
            user_agent=request.headers.get('User-Agent')
        )
        db.session.add(auditoria)
        # El commit se hará junto con la operación principal
    except Exception as e:
        print(f"Error al registrar auditoria: {e}")


@admin_bp.route('/dashboard')
@admin_required
def dashboard():
    """Dashboard principal del administrador con estadísticas"""
    stats = {}
    ultimos_tutores = []
    proximas_citas = []
    try:
        # Estadísticas generales
        stats = {
            'total_usuarios': Usuario.query.count(),
            'total_veterinarios': Usuario.query.filter_by(rol='veterinario').count(),
            'total_tutores': Usuario.query.filter_by(rol='tutor').count(),
            'total_mascotas': Mascota.query.filter_by(activo=True).count(),
            'citas_hoy': Cita.query.filter(func.date(Cita.fecha) == date.today()).count(), # CORREGIDO: Usa Cita.fecha
            'citas_pendientes': Cita.query.filter_by(estado='pendiente').count(),
            'medicamentos_bajo_stock': Medicamento.query.filter(
                Medicamento.stock_actual <= Medicamento.stock_minimo
            ).count()
        }
        
        # Últimos tutores
        ultimos_tutores = Usuario.query.filter_by(rol='tutor').order_by(Usuario.fecha_registro.desc()).limit(5).all()

        # Próximas citas de hoy
        proximas_citas = Cita.query.filter(
            func.date(Cita.fecha) == date.today(), # CORREGIDO: Usa Cita.fecha
            Cita.estado.in_(['pendiente', 'aceptada']) # 'aceptada' es el estado correcto
        ).order_by(Cita.fecha).limit(10).all()

    except Exception as e:
        flash(f'Error al cargar el dashboard: {e}', 'danger')
        print(f"Error en dashboard: {e}")

    
    return render_template('admin/dashboard.html',
                         stats=stats,
                         ultimos_tutores=ultimos_tutores,
                         proximas_citas=proximas_citas)

# --- SECCIÓN DE TUTORES (CRUD COMPLETO) ---

@admin_bp.route('/tutores')
@admin_required
def tutores():
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
    
    for tutor in tutores.items:
        tutor.total_mascotas = tutor.mascotas.count()
    
    return render_template('admin/tutores/lista.html', tutores=tutores, search=search)

@admin_bp.route('/tutor/<int:tutor_id>')
@admin_required
def ver_tutor(tutor_id):
    """Ver detalles de un tutor y sus mascotas"""
    tutor = Usuario.query.get_or_404(tutor_id)
    
    if tutor.rol != 'tutor':
        flash('El usuario especificado no es un tutor', 'warning')
        return redirect(url_for('admin.tutores'))
    
    mascotas = tutor.mascotas.order_by(Mascota.nombre.asc()).all()
    citas = tutor.citas_como_tutor.order_by(Cita.fecha.desc()).limit(10).all()
    
    stats = {
        'total_mascotas': len(mascotas),
        'total_citas': tutor.citas_como_tutor.count(),
        'citas_completadas': tutor.citas_como_tutor.filter_by(estado='atendida').count(), # 'atendida' es el estado final
        'proxima_cita': tutor.citas_como_tutor.filter(
            Cita.fecha >= datetime.now(),
            Cita.estado == 'aceptada'
        ).order_by(Cita.fecha).first()
    }
    
    registrar_auditoria('ver_tutor', 'usuario', tutor_id, f'Visualización de tutor: {tutor.nombre_completo}')
    db.session.commit() # Commit de la auditoría
    
    return render_template('admin/tutores/ver.html',
                         tutor=tutor,
                         mascotas=mascotas,
                         citas=citas,
                         stats=stats)

@admin_bp.route('/tutor/nuevo', methods=['GET', 'POST'])
@admin_required
def nuevo_tutor():
    """Crear un nuevo tutor (Esta ruta faltaba)"""
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
            password=password, # El modelo Usuario (user.py) hashea la contraseña automáticamente
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
            db.session.flush() # Para obtener el ID del nuevo tutor
            registrar_auditoria('crear_tutor', 'usuario', nuevo_tutor.id, f'Admin creó nuevo tutor: {nuevo_tutor.nombre_completo}')
            db.session.commit()
            flash('Tutor creado exitosamente', 'success')
            return redirect(url_for('admin.tutores'))
        except Exception as e:
            db.session.rollback()
            flash(f'Error al crear tutor: {str(e)}', 'danger')
    
    return render_template('admin/tutores/nuevo.html')

@admin_bp.route('/tutor/<int:tutor_id>/editar', methods=['GET', 'POST'])
@admin_required
def editar_tutor(tutor_id):
    """Editar un tutor existente (Esta ruta faltaba)"""
    tutor = Usuario.query.get_or_404(tutor_id)
    if tutor.rol != 'tutor':
        flash('El usuario especificado no es un tutor', 'warning')
        return redirect(url_for('admin.tutores'))

    if request.method == 'POST':
        tutor.nombre = request.form.get('nombre')
        tutor.apellido = request.form.get('apellido')
        tutor.email = request.form.get('email')
        tutor.telefono = request.form.get('telefono')
        tutor.direccion = request.form.get('direccion')
        tutor.activo = request.form.get('activo') == 'on'
        
        nueva_password = request.form.get('nueva_password')
        if nueva_password:
            tutor.set_password(nueva_password) # Hashear la nueva contraseña
            
        try:
            registrar_auditoria('editar_tutor', 'usuario', tutor.id, f'Admin editó al tutor: {tutor.nombre_completo}')
            db.session.commit()
            flash('Tutor actualizado exitosamente', 'success')
            return redirect(url_for('admin.ver_tutor', tutor_id=tutor.id))
        except Exception as e:
            db.session.rollback()
            flash(f'Error al actualizar tutor: {str(e)}', 'danger')
            
    return render_template('admin/tutores/editar.html', tutor=tutor)


# --- SECCIÓN DE VETERINARIOS (CRUD COMPLETO) ---

@admin_bp.route('/veterinarios')
@admin_required
def veterinarios():
    """Lista de veterinarios con estadísticas"""
    page = request.args.get('page', 1, type=int)
    veterinarios = Usuario.query.filter_by(rol='veterinario').paginate(
        page=page, per_page=10, error_out=False
    )
    
    for vet in veterinarios.items:
        vet.stats = vet.get_estadisticas_veterinario()
    
    return render_template('admin/veterinarios/lista.html', veterinarios=veterinarios)

@admin_bp.route('/veterinario/nuevo', methods=['GET', 'POST'])
@admin_required
def nuevo_veterinario():
    """Crear un nuevo veterinario (Ruta modificada)"""
    if request.method == 'POST':
        username = request.form.get('username')
        email = request.form.get('email')
        password = request.form.get('password')
        nombre = request.form.get('nombre')
        apellido = request.form.get('apellido')
        telefono = request.form.get('telefono')
        licencia = request.form.get('licencia_profesional')
        
        # --- LÓGICA DE ESPECIALIDAD MEJORADA ---
        especialidad = request.form.get('especialidad')
        especialidad_otra = request.form.get('especialidad_otra')
        
        if especialidad == 'otra' and especialidad_otra:
            especialidad = especialidad_otra.strip() # Usar el valor del campo 'otra'
        elif especialidad == 'otra':
            flash('Debe especificar la "otra" especialidad.', 'danger')
            return render_template('admin/veterinarios/nuevo.html', especialidades=LISTA_ESPECIALIDADES)
        # --- FIN LÓGICA ---
            
        if Usuario.query.filter_by(username=username).first():
            flash('El nombre de usuario ya está registrado', 'danger')
            return render_template('admin/veterinarios/nuevo.html', especialidades=LISTA_ESPECIALIDADES)
        
        if Usuario.query.filter_by(email=email).first():
            flash('El email ya está registrado', 'danger')
            return render_template('admin/veterinarios/nuevo.html', especialidades=LISTA_ESPECIALIDADES)

        if not all([username, email, password, nombre, apellido]):
            flash('Por favor complete todos los campos obligatorios (*)', 'danger')
            return render_template('admin/veterinarios/nuevo.html', especialidades=LISTA_ESPECIALIDADES)

        nuevo_vet = Usuario(
            username=username,
            email=email,
            password=password, # El modelo Usuario (user.py) hashea la contraseña automáticamente
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
            db.session.flush() # Para obtener el ID del nuevo veterinario
            registrar_auditoria('crear_veterinario', 'usuario', nuevo_vet.id, f'Admin creó nuevo veterinario: {nuevo_vet.nombre_completo}')
            db.session.commit()
            flash('Veterinario creado exitosamente', 'success')
            return redirect(url_for('admin.veterinarios'))
        except Exception as e:
            db.session.rollback()
            flash(f'Error al crear veterinario: {str(e)}', 'danger')
    
    # Enviar la lista de especialidades a la plantilla
    return render_template('admin/veterinarios/nuevo.html', especialidades=LISTA_ESPECIALIDADES)

@admin_bp.route('/veterinario/<int:vet_id>')
@admin_required
def ver_veterinario(vet_id):
    """Ver detalles de un veterinario y sus citas (Esta ruta faltaba)"""
    veterinario = Usuario.query.get_or_404(vet_id)
    
    if not veterinario.is_veterinario():
        flash('El usuario especificado no es un veterinario', 'warning')
        return redirect(url_for('admin.veterinarios'))
    
    citas = veterinario.citas_como_veterinario.order_by(Cita.fecha.desc()).limit(10).all()
    stats = veterinario.get_estadisticas_veterinario()
    
    registrar_auditoria('ver_veterinario', 'usuario', vet_id, f'Visualización de veterinario: {veterinario.nombre_completo}')
    db.session.commit() # Commit de la auditoría
    
    return render_template('admin/veterinarios/ver.html',
                         veterinario=veterinario,
                         citas=citas,
                         stats=stats)

@admin_bp.route('/veterinario/<int:vet_id>/editar', methods=['GET', 'POST'])
@admin_required
def editar_veterinario(vet_id):
    """Editar un veterinario existente (Esta ruta faltaba)"""
    veterinario = Usuario.query.get_or_404(vet_id)
    if not veterinario.is_veterinario():
        flash('El usuario especificado no es un veterinario', 'warning')
        return redirect(url_for('admin.veterinarios'))

    if request.method == 'POST':
        veterinario.nombre = request.form.get('nombre')
        veterinario.apellido = request.form.get('apellido')
        veterinario.email = request.form.get('email')
        veterinario.telefono = request.form.get('telefono')
        veterinario.licencia_profesional = request.form.get('licencia_profesional')
        veterinario.activo = request.form.get('activo') == 'on'
        
        # --- LÓGICA DE ESPECIALIDAD MEJORADA ---
        especialidad = request.form.get('especialidad')
        especialidad_otra = request.form.get('especialidad_otra')
        
        if especialidad == 'otra' and especialidad_otra:
            veterinario.especialidad = especialidad_otra.strip()
        elif especialidad == 'otra':
            flash('Debe especificar la "otra" especialidad.', 'danger')
            return render_template('admin/veterinarios/editar.html', veterinario=veterinario, especialidades=LISTA_ESPECIALIDADES)
        else:
            veterinario.especialidad = especialidad
        # --- FIN LÓGICA ---
        
        nueva_password = request.form.get('nueva_password')
        if nueva_password:
            veterinario.set_password(nueva_password) # Hashear la nueva contraseña
            
        try:
            registrar_auditoria('editar_veterinario', 'usuario', veterinario.id, f'Admin editó al veterinario: {veterinario.nombre_completo}')
            db.session.commit()
            flash('Veterinario actualizado exitosamente', 'success')
            return redirect(url_for('admin.ver_veterinario', vet_id=veterinario.id))
        except Exception as e:
            db.session.rollback()
            flash(f'Error al actualizar veterinario: {str(e)}', 'danger')
            
    return render_template('admin/veterinarios/editar.html', veterinario=veterinario, especialidades=LISTA_ESPECIALIDADES)


# --- SECCIÓN DE MASCOTAS ---

@admin_bp.route('/mascota/<int:mascota_id>')
@admin_required
def ver_mascota(mascota_id):
    """Ver detalles completos de una mascota"""
    mascota = Mascota.query.get_or_404(mascota_id)
    
    historiales = mascota.historiales.order_by(HistorialClinico.fecha.desc()).limit(10).all()
    vacunas = mascota.vacunas.order_by(Vacuna.fecha_aplicacion.desc()).all()
    citas = mascota.citas.order_by(Cita.fecha.desc()).limit(10).all()
    documentos = mascota.documentos.order_by(DocumentoMascota.fecha_subida.desc()).all()
    
    registrar_auditoria('ver_mascota', 'mascota', mascota_id, f'Visualización de mascota: {mascota.nombre}')
    db.session.commit() # Commit de la auditoría
    
    return render_template('admin/mascotas/ver.html',
                         mascota=mascota,
                         historiales=historiales,
                         vacunas=vacunas,
                         citas=citas,
                         documentos=documentos)

# --- Rutas de API (para futuros gráficos) ---

@admin_bp.route('/api/estadisticas/citas-mes')
@admin_required
def api_estadisticas_citas_mes():
    """API para obtener estadísticas de citas del mes actual"""
    mes_actual = datetime.now().month
    año_actual = datetime.now().year
    
    dias_mes = []
    # (Lógica para obtener citas por día)
    
    return jsonify(dias_mes)

@admin_bp.route('/api/estadisticas/especies')
@admin_required
def api_estadisticas_especies():
    """API para obtener distribución de especies"""
    especies = db.session.query(
        Mascota.especie,
        func.count(Mascota.id).label('cantidad')
    ).filter(Mascota.activo == True).group_by(Mascota.especie).all()
    
    return jsonify([{
        'especie': e.especie,
        'cantidad': e.cantidad
    } for e in especies])