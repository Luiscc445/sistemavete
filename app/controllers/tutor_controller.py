"""
Controlador de Tutor
Gestiona las acciones de los tutores de mascotas
"""
from flask import Blueprint, render_template, redirect, url_for, flash, request
from flask_login import login_required, current_user
from functools import wraps
from app import db
from app.models.user import Usuario
from app.models.mascota import Mascota
from app.models.cita import Cita
from app.models.pago import Pago
from datetime import datetime
import base64

tutor_bp = Blueprint('tutor', __name__)


def tutor_required(f):
    """Decorador para rutas que requieren rol de tutor"""
    @wraps(f)
    @login_required
    def decorated_function(*args, **kwargs):
        if not current_user.is_tutor():
            flash('No tienes permisos para acceder a esta página.', 'danger')
            return redirect(url_for('auth.index'))
        return f(*args, **kwargs)
    return decorated_function


@tutor_bp.route('/dashboard')
@tutor_required
def dashboard():
    """Dashboard del tutor"""
    # Obtener estadísticas
    total_mascotas = Mascota.query.filter_by(tutor_id=current_user.id, activo=True).count()
    total_citas = Cita.query.filter_by(tutor_id=current_user.id).count()
    citas_pendientes = Cita.query.filter_by(
        tutor_id=current_user.id,
        estado='pendiente'
    ).count()
    citas_proximas = Cita.query.filter_by(
        tutor_id=current_user.id,
        estado='pendiente'
    ).filter(
        Cita.fecha >= datetime.now()
    ).order_by(Cita.fecha.asc()).limit(5).all()

    return render_template('tutor/dashboard.html',
                         total_mascotas=total_mascotas,
                         total_citas=total_citas,
                         citas_pendientes=citas_pendientes,
                         citas_proximas=citas_proximas)


@tutor_bp.route('/mascotas')
@tutor_required
def mascotas():
    """Lista de mascotas del tutor"""
    mis_mascotas = Mascota.query.filter_by(
        tutor_id=current_user.id,
        activo=True
    ).order_by(Mascota.nombre.asc()).all()

    return render_template('tutor/mascotas.html', mascotas=mis_mascotas)


@tutor_bp.route('/mascota/nueva', methods=['GET', 'POST'])
@tutor_required
def nueva_mascota():
    """Registrar nueva mascota"""
    if request.method == 'POST':
        # Obtener datos del formulario
        nombre = request.form.get('nombre')
        especie = request.form.get('especie')
        raza = request.form.get('raza')
        fecha_nacimiento = request.form.get('fecha_nacimiento')
        sexo = request.form.get('sexo')
        color = request.form.get('color')
        peso = request.form.get('peso')
        esterilizado = request.form.get('esterilizado') == 'on'
        chip = request.form.get('chip')
        notas_comportamiento = request.form.get('notas_comportamiento') or request.form.get('observaciones')

        # Validaciones
        if not nombre or not especie:
            flash('Nombre y especie son obligatorios.', 'danger')
            return render_template('tutor/nueva_mascota.html')

        # Convertir fecha
        fecha_nac = None
        if fecha_nacimiento:
            try:
                fecha_nac = datetime.strptime(fecha_nacimiento, '%Y-%m-%d').date()
            except ValueError:
                flash('Formato de fecha inválido.', 'danger')
                return render_template('tutor/nueva_mascota.html')

        # Convertir peso
        peso_float = None
        if peso:
            try:
                peso_float = float(peso)
            except ValueError:
                flash('El peso debe ser un número válido.', 'danger')
                return render_template('tutor/nueva_mascota.html')

        # Crear mascota
        nueva_mascota = Mascota(
            nombre=nombre,
            especie=especie,
            tutor_id=current_user.id,
            raza=raza,
            fecha_nacimiento=fecha_nac,
            sexo=sexo,
            color=color,
            peso=peso_float,
            esterilizado=esterilizado,
            chip_identificacion=chip,
            notas_comportamiento=notas_comportamiento
        )

        try:
            db.session.add(nueva_mascota)
            db.session.commit()
            flash(f'¡Mascota {nombre} registrada exitosamente!', 'success')
            return redirect(url_for('tutor.mascotas'))
        except Exception as e:
            db.session.rollback()
            flash(f'Error al registrar mascota: {str(e)}', 'danger')

    return render_template('tutor/nueva_mascota.html')


@tutor_bp.route('/mascota/<int:id>')
@tutor_required
def ver_mascota(id):
    """Ver detalles de una mascota"""
    mascota = Mascota.query.get_or_404(id)

    # Verificar que la mascota pertenece al tutor
    if mascota.tutor_id != current_user.id:
        flash('No tienes permiso para ver esta mascota.', 'danger')
        return redirect(url_for('tutor.mascotas'))

    # Obtener historial de citas
    citas = Cita.query.filter_by(mascota_id=id).order_by(Cita.fecha.desc()).all()

    return render_template('tutor/ver_mascota.html', mascota=mascota, citas=citas)


@tutor_bp.route('/mascota/<int:id>/editar', methods=['GET', 'POST'])
@tutor_required
def editar_mascota(id):
    """Editar información de mascota"""
    mascota = Mascota.query.get_or_404(id)

    # Verificar que la mascota pertenece al tutor
    if mascota.tutor_id != current_user.id:
        flash('No tienes permiso para editar esta mascota.', 'danger')
        return redirect(url_for('tutor.mascotas'))

    if request.method == 'POST':
        # Actualizar datos
        mascota.nombre = request.form.get('nombre')
        mascota.especie = request.form.get('especie')
        mascota.raza = request.form.get('raza')
        mascota.sexo = request.form.get('sexo')
        mascota.color = request.form.get('color')
        mascota.esterilizado = request.form.get('esterilizado') == 'on'
        mascota.chip_identificacion = request.form.get('chip')
        mascota.notas_comportamiento = request.form.get('notas_comportamiento') or request.form.get('observaciones')

        # Fecha de nacimiento
        fecha_nacimiento = request.form.get('fecha_nacimiento')
        if fecha_nacimiento:
            try:
                mascota.fecha_nacimiento = datetime.strptime(fecha_nacimiento, '%Y-%m-%d').date()
            except ValueError:
                pass

        # Peso
        peso = request.form.get('peso')
        if peso:
            try:
                mascota.peso = float(peso)
            except ValueError:
                pass

        try:
            db.session.commit()
            flash('Información de mascota actualizada exitosamente.', 'success')
            return redirect(url_for('tutor.ver_mascota', id=id))
        except Exception as e:
            db.session.rollback()
            flash(f'Error al actualizar mascota: {str(e)}', 'danger')

    return render_template('tutor/editar_mascota.html', mascota=mascota)


@tutor_bp.route('/citas')
@tutor_required
def citas():
    """Lista de citas del tutor"""
    mis_citas = Cita.query.filter_by(tutor_id=current_user.id).order_by(Cita.fecha.desc()).all()
    return render_template('tutor/citas.html', citas=mis_citas)


@tutor_bp.route('/cita/nueva', methods=['GET', 'POST'])
@tutor_required
def nueva_cita():
    """Solicitar nueva cita médica"""
    # Obtener mascotas del tutor
    mascotas = Mascota.query.filter_by(tutor_id=current_user.id, activo=True).all()

    if not mascotas:
        flash('Debes registrar al menos una mascota antes de solicitar una cita.', 'warning')
        return redirect(url_for('tutor.nueva_mascota'))

    # Obtener veterinarios activos
    veterinarios = Usuario.query.filter_by(rol='veterinario', activo=True).all()

    if request.method == 'POST':
        mascota_id = request.form.get('mascota_id')
        veterinario_id = request.form.get('veterinario_id')
        fecha = request.form.get('fecha')
        hora = request.form.get('hora')
        motivo = request.form.get('motivo')

        # Validaciones
        if not all([mascota_id, veterinario_id, fecha, hora, motivo]):
            flash('Por favor complete todos los campos.', 'danger')
            return render_template('tutor/nueva_cita.html', mascotas=mascotas, veterinarios=veterinarios)

        # Verificar que la mascota pertenece al tutor
        mascota = Mascota.query.get(mascota_id)
        if not mascota or mascota.tutor_id != current_user.id:
            flash('Mascota no válida.', 'danger')
            return render_template('tutor/nueva_cita.html', mascotas=mascotas, veterinarios=veterinarios)

        # Verificar que el veterinario existe
        veterinario = Usuario.query.get(veterinario_id)
        if not veterinario or veterinario.rol != 'veterinario':
            flash('Veterinario no válido.', 'danger')
            return render_template('tutor/nueva_cita.html', mascotas=mascotas, veterinarios=veterinarios)

        # Combinar fecha y hora
        try:
            fecha_hora = datetime.strptime(f"{fecha} {hora}", '%Y-%m-%d %H:%M')
        except ValueError:
            flash('Formato de fecha u hora inválido.', 'danger')
            return render_template('tutor/nueva_cita.html', mascotas=mascotas, veterinarios=veterinarios)

        # Verificar que la fecha sea futura
        if fecha_hora < datetime.now():
            flash('La fecha de la cita debe ser futura.', 'danger')
            return render_template('tutor/nueva_cita.html', mascotas=mascotas, veterinarios=veterinarios)

        # Crear cita con veterinario asignado
        nueva_cita = Cita(
            mascota_id=mascota_id,
            tutor_id=current_user.id,
            veterinario_id=veterinario_id,
            fecha=fecha_hora,
            tipo='Consulta',
            motivo=motivo,
            estado='pendiente'
        )

        try:
            db.session.add(nueva_cita)
            db.session.commit()
            # Redirigir a página de pago para confirmar la cita
            flash(f'Cita creada. Ahora procede con el pago para confirmarla.', 'info')
            return redirect(url_for('tutor.pagar_cita', cita_id=nueva_cita.id))
        except Exception as e:
            db.session.rollback()
            flash(f'Error al solicitar cita: {str(e)}', 'danger')

    return render_template('tutor/nueva_cita.html', mascotas=mascotas, veterinarios=veterinarios)


@tutor_bp.route('/cita/<int:id>')
@tutor_required
def ver_cita(id):
    """Ver detalles de una cita"""
    cita = Cita.query.get_or_404(id)

    # Verificar que la cita pertenece al tutor
    if cita.tutor_id != current_user.id:
        flash('No tienes permiso para ver esta cita.', 'danger')
        return redirect(url_for('tutor.citas'))

    return render_template('tutor/ver_cita.html', cita=cita)


@tutor_bp.route('/pagar-cita/<int:cita_id>', methods=['GET', 'POST'])
@tutor_required
def pagar_cita(cita_id):
    """Procesar pago de una cita"""
    cita = Cita.query.get_or_404(cita_id)

    # Verificar que la cita pertenece al tutor
    if cita.tutor_id != current_user.id:
        flash('No tienes permiso para pagar esta cita.', 'danger')
        return redirect(url_for('tutor.citas'))

    # Verificar si ya tiene un pago completado
    pago_existente = Pago.query.filter_by(
        cita_id=cita_id,
        estado='completado'
    ).first()

    if pago_existente:
        flash('Esta cita ya fue pagada.', 'info')
        return redirect(url_for('tutor.ver_cita', id=cita_id))

    if request.method == 'POST':
        metodo_pago = request.form.get('metodo_pago')
        monto = request.form.get('monto')

        # Validaciones
        if not metodo_pago or not monto:
            flash('Por favor complete todos los campos.', 'danger')
            return render_template('tutor/pagar_cita.html', cita=cita)

        try:
            monto_float = float(monto)
            if monto_float <= 0:
                flash('El monto debe ser mayor a 0.', 'danger')
                return render_template('tutor/pagar_cita.html', cita=cita)
        except ValueError:
            flash('Monto inválido.', 'danger')
            return render_template('tutor/pagar_cita.html', cita=cita)

        # Crear el pago
        nuevo_pago = Pago(
            monto=monto_float,
            metodo_pago=metodo_pago,
            estado='completado',  # Pago simulado, automáticamente completado
            descripcion=f'Pago de cita #{cita_id} - {cita.tipo}',
            tutor_id=current_user.id,
            cita_id=cita_id,
            veterinario_id=cita.veterinario_id
        )

        # Calcular división de ingresos (empresa vs veterinario)
        nuevo_pago.calcular_division_ingresos()

        # Si es método QR, generar código QR
        if 'qr' in metodo_pago.lower():
            nuevo_pago.generar_qr()

        try:
            db.session.add(nuevo_pago)

            # Confirmar automáticamente la cita
            cita.estado = 'confirmada'

            db.session.commit()

            flash(f'¡Pago de Bs. {monto_float:.2f} procesado exitosamente! Tu cita ha sido confirmada.', 'success')
            return redirect(url_for('tutor.ver_cita', id=cita_id))
        except Exception as e:
            db.session.rollback()
            flash(f'Error al procesar el pago: {str(e)}', 'danger')

    return render_template('tutor/pagar_cita.html', cita=cita)


@tutor_bp.route('/perfil', methods=['GET', 'POST'])
@tutor_required
def perfil():
    """Ver y editar perfil del tutor"""
    if request.method == 'POST':
        # Actualizar información
        current_user.nombre = request.form.get('nombre')
        current_user.apellido = request.form.get('apellido')
        current_user.email = request.form.get('email')
        current_user.telefono = request.form.get('telefono')
        current_user.direccion = request.form.get('direccion')

        # Cambiar contraseña si se proporciona
        password_actual = request.form.get('password_actual')
        password_nueva = request.form.get('password_nueva')
        password_confirmar = request.form.get('password_confirmar')

        if password_actual and password_nueva:
            if not current_user.check_password(password_actual):
                flash('La contraseña actual es incorrecta.', 'danger')
                return render_template('tutor/perfil.html')

            if password_nueva != password_confirmar:
                flash('Las contraseñas nuevas no coinciden.', 'danger')
                return render_template('tutor/perfil.html')

            if len(password_nueva) < 6:
                flash('La contraseña debe tener al menos 6 caracteres.', 'danger')
                return render_template('tutor/perfil.html')

            current_user.set_password(password_nueva)

        try:
            db.session.commit()
            flash('Perfil actualizado exitosamente.', 'success')
            return redirect(url_for('tutor.perfil'))
        except Exception as e:
            db.session.rollback()
            flash(f'Error al actualizar perfil: {str(e)}', 'danger')

    return render_template('tutor/perfil.html')
