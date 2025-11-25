"""
Controlador de Veterinario
Gestiona las acciones de los veterinarios
"""
from flask import Blueprint, render_template, redirect, url_for, flash, request, make_response
from flask_login import login_required, current_user
from functools import wraps
from app import db
from app.models.cita import Cita
from app.models.mascota import Mascota
from app.models.historial_clinico import HistorialClinico
from app.models.medicamento import Medicamento, Receta
from app.models.pago import Pago
from datetime import datetime
from sqlalchemy import func, or_, desc
from io import BytesIO

veterinario_bp = Blueprint('veterinario', __name__)


def veterinario_required(f):
    """Decorador para rutas que requieren rol de veterinario"""
    @wraps(f)
    @login_required
    def decorated_function(*args, **kwargs):
        if not current_user.is_veterinario():
            flash('No tienes permisos para acceder a esta página.', 'danger')
            return redirect(url_for('auth.login'))
        return f(*args, **kwargs)
    return decorated_function


@veterinario_bp.route('/dashboard')
@veterinario_required
def dashboard():
    """Dashboard del veterinario"""
    # Estadísticas
    citas_pendientes = Cita.query.filter_by(
        veterinario_id=current_user.id,
        estado='pendiente'
    ).count()

    citas_aceptadas = Cita.query.filter_by(
        veterinario_id=current_user.id,
        estado='aceptada'
    ).count()

    total_atendidas = Cita.query.filter_by(
        veterinario_id=current_user.id,
        estado='atendida'
    ).count()

    # Citas de hoy - CORREGIDO para SQL Server
    hoy = datetime.now().date()
    citas_hoy = Cita.query.filter_by(
        veterinario_id=current_user.id,
        estado='pendiente'
    ).filter(
        db.func.cast(Cita.fecha, db.Date) == hoy
    ).order_by(Cita.fecha.asc()).all()

    # Ingresos del veterinario (su porcentaje de los pagos)
    ingresos_totales = db.session.query(
        func.sum(Pago.monto_veterinario)
    ).filter(
        Pago.veterinario_id == current_user.id,
        Pago.estado == 'completado'
    ).scalar() or 0.0

    # Ingresos del mes actual
    primer_dia_mes = datetime.now().replace(day=1, hour=0, minute=0, second=0, microsecond=0)
    ingresos_mes = db.session.query(
        func.sum(Pago.monto_veterinario)
    ).filter(
        Pago.veterinario_id == current_user.id,
        Pago.estado == 'completado',
        Pago.fecha_pago >= primer_dia_mes
    ).scalar() or 0.0

    # Número de pagos recibidos
    total_pagos = Pago.query.filter_by(
        veterinario_id=current_user.id,
        estado='completado'
    ).count()

    return render_template('dashboards/veterinario/veterinario_dashboard.html',
                         citas_pendientes=citas_pendientes,
                         citas_aceptadas=citas_aceptadas,
                         total_atendidas=total_atendidas,
                         citas_hoy=citas_hoy,
                         ingresos_totales=ingresos_totales,
                         ingresos_mes=ingresos_mes,
                         total_pagos=total_pagos)


@veterinario_bp.route('/citas/pendientes')
@veterinario_required
def citas_pendientes():
    """Ver citas pendientes"""
    citas = Cita.query.filter_by(estado='pendiente').order_by(Cita.fecha.asc()).all()
    return render_template('veterinario/citas/citas_pendientes.html', citas=citas)

@veterinario_bp.route('/citas/mis-citas')
@veterinario_required
def mis_citas():
    """Ver mis citas aceptadas y atendidas"""
    # Obtener parámetros de filtro
    estado_filtro = request.args.get('estado', 'todos')
    fecha_desde = request.args.get('fecha_desde', '')
    fecha_hasta = request.args.get('fecha_hasta', '')
    buscar = request.args.get('buscar', '')
    
    # Query base - todas las citas del veterinario
    query = Cita.query.filter_by(veterinario_id=current_user.id)
    
    # Filtrar por estado si no es "todos"
    if estado_filtro and estado_filtro != 'todos':
        query = query.filter_by(estado=estado_filtro)
    
    # Filtrar por rango de fechas
    if fecha_desde:
        try:
            fecha_desde_dt = datetime.strptime(fecha_desde, '%Y-%m-%d')
            query = query.filter(Cita.fecha >= fecha_desde_dt)
        except ValueError:
            pass
    
    if fecha_hasta:
        try:
            fecha_hasta_dt = datetime.strptime(fecha_hasta, '%Y-%m-%d')
            # Agregar un día para incluir todo el día hasta
            from datetime import timedelta
            fecha_hasta_dt = fecha_hasta_dt + timedelta(days=1)
            query = query.filter(Cita.fecha < fecha_hasta_dt)
        except ValueError:
            pass
    
    # Búsqueda por mascota o tutor
    if buscar:
        from app.models.mascota import Mascota
        from app.models.usuario import Usuario
        query = query.join(Mascota).join(Usuario, Mascota.tutor_id == Usuario.id).filter(
            db.or_(
                Mascota.nombre.ilike(f'%{buscar}%'),
                Usuario.nombre.ilike(f'%{buscar}%'),
                Usuario.apellido.ilike(f'%{buscar}%')
            )
        )
    
    # Ordenar por fecha descendente
    citas = query.order_by(Cita.fecha.desc()).all()
    
    # Obtener citas agrupadas por mes para el calendario
    citas_por_fecha = {}
    for cita in Cita.query.filter_by(veterinario_id=current_user.id).all():
        fecha_str = cita.fecha.strftime('%Y-%m-%d')
        if fecha_str not in citas_por_fecha:
            citas_por_fecha[fecha_str] = []
        citas_por_fecha[fecha_str].append({
            'estado': cita.estado,
            'mascota': cita.mascota.nombre if cita.mascota else 'N/A'
        })

    return render_template('veterinario/citas/mis_citas.html', 
                         citas=citas,
                         citas_por_fecha=citas_por_fecha,
                         estado_filtro=estado_filtro,
                         fecha_desde=fecha_desde,
                         fecha_hasta=fecha_hasta,
                         buscar=buscar)



@veterinario_bp.route('/cita/<int:id>/aceptar', methods=['POST'])
@veterinario_required
def aceptar_cita(id):
    """Aceptar una cita pendiente"""
    cita = Cita.query.get_or_404(id)

    if cita.estado != 'pendiente':
        flash('Esta cita ya no está pendiente.', 'warning')
        return redirect(url_for('veterinario.citas_pendientes'))

    try:
        # Asignar veterinario y confirmar la cita
        cita.veterinario_id = current_user.id
        cita.confirmar()
        flash('Cita aceptada exitosamente.', 'success')
    except Exception as e:
        db.session.rollback()
        flash(f'Error al aceptar cita: {str(e)}', 'danger')

    return redirect(url_for('veterinario.citas_pendientes'))


@veterinario_bp.route('/cita/<int:id>/posponer', methods=['GET', 'POST'])
@veterinario_required
def posponer_cita(id):
    """Posponer una cita"""
    cita = Cita.query.get_or_404(id)

    if cita.estado not in ['pendiente', 'aceptada']:
        flash('Esta cita no puede ser pospuesta.', 'warning')
        return redirect(url_for('veterinario.citas_pendientes'))

    if request.method == 'POST':
        motivo = request.form.get('motivo')
        nueva_fecha = request.form.get('nueva_fecha')
        nueva_hora = request.form.get('nueva_hora')

        if not motivo:
            flash('Debes proporcionar un motivo para posponer.', 'danger')
            return render_template('veterinario/citas/posponer_cita.html', cita=cita)

        # Nueva fecha sugerida (opcional)
        nueva_fecha_hora = None
        if nueva_fecha and nueva_hora:
            try:
                nueva_fecha_hora = datetime.strptime(f"{nueva_fecha} {nueva_hora}", '%Y-%m-%d %H:%M')
            except ValueError:
                flash('Formato de fecha u hora inválido.', 'danger')
                return render_template('veterinario/citas/posponer_cita.html', cita=cita)

        try:
            if nueva_fecha_hora:
                cita.fecha = nueva_fecha_hora
            cita.estado = 'pendiente'
            cita.razon_cancelacion = f"Pospuesta: {motivo}"
            db.session.commit()
            flash('Cita pospuesta. El tutor será notificado.', 'success')
            return redirect(url_for('veterinario.citas_pendientes'))
        except Exception as e:
            db.session.rollback()
            flash(f'Error al posponer cita: {str(e)}', 'danger')

    return render_template('veterinario/citas/posponer_cita.html', cita=cita)


@veterinario_bp.route('/cita/<int:id>/atender', methods=['GET', 'POST'])
@veterinario_required
def atender_cita(id):
    """Atender una cita"""
    cita = Cita.query.get_or_404(id)

    # Verificar que la cita está confirmada y asignada a este veterinario
    if cita.veterinario_id != current_user.id:
        flash('No tienes permiso para atender esta cita.', 'danger')
        return redirect(url_for('veterinario.mis_citas'))

    if cita.estado not in ['confirmada', 'pendiente']:
        flash('Esta cita no puede ser atendida.', 'warning')
        return redirect(url_for('veterinario.mis_citas'))

    # Obtener medicamentos disponibles
    medicamentos = Medicamento.query.filter_by(activo=True).order_by(Medicamento.nombre.asc()).all()

    if request.method == 'POST':
        diagnostico = request.form.get('diagnostico')
        tratamiento = request.form.get('tratamiento')
        observaciones = request.form.get('observaciones')

        # Validaciones
        if not diagnostico or not tratamiento:
            flash('Diagnóstico y tratamiento son obligatorios.', 'danger')
            return render_template('veterinario/citas/atender_cita.html', cita=cita, medicamentos=medicamentos)

        try:
            # Iniciar atención si aún no se ha iniciado
            if cita.estado == 'confirmada' or cita.estado == 'pendiente':
                cita.iniciar_atencion()

            # Registrar datos de la consulta
            cita.diagnostico = diagnostico
            cita.tratamiento = tratamiento
            cita.observaciones = observaciones

            # Procesar medicamentos recetados
            medicamentos_ids = request.form.getlist('medicamento_id[]')
            cantidades = request.form.getlist('cantidad[]')
            dosis_list = request.form.getlist('dosis[]')
            duraciones = request.form.getlist('duracion[]')
            indicaciones = request.form.getlist('indicaciones[]')

            for i, med_id in enumerate(medicamentos_ids):
                if med_id and cantidades[i]:
                    medicamento = Medicamento.query.get(int(med_id))
                    cantidad = int(cantidades[i])

                    if medicamento and cantidad > 0:
                        # Verificar stock
                        if medicamento.stock_actual < cantidad:
                            flash(f'Stock insuficiente de {medicamento.nombre}. Disponible: {medicamento.stock_actual}', 'warning')
                            continue

                        # Crear receta
                        receta = Receta(
                            cita_id=cita.id,
                            medicamento_id=medicamento.id,
                            cantidad=cantidad,
                            dosis=dosis_list[i] if i < len(dosis_list) else None,
                            duracion=duraciones[i] if i < len(duraciones) else None,
                            indicaciones=indicaciones[i] if i < len(indicaciones) else None
                        )
                        db.session.add(receta)

                        # Reducir stock automáticamente
                        if not medicamento.reducir_stock(cantidad):
                            flash(f'Error al reducir stock de {medicamento.nombre}', 'warning')

            # Completar la cita y guardar todos los cambios
            cita.completar()
            flash('Cita atendida exitosamente. Stock actualizado.', 'success')
            return redirect(url_for('veterinario.mis_citas'))

        except Exception as e:
            db.session.rollback()
            flash(f'Error al atender cita: {str(e)}', 'danger')

    return render_template('veterinario/citas/atender_cita.html', cita=cita, medicamentos=medicamentos)


@veterinario_bp.route('/cita/<int:id>')
@veterinario_required
def ver_cita(id):
    """Ver detalles de una cita"""
    cita = Cita.query.get_or_404(id)

    # Verificar permiso
    if cita.veterinario_id != current_user.id and cita.estado == 'pendiente':
        # Puede ver citas pendientes sin asignar
        pass
    elif cita.veterinario_id != current_user.id:
        flash('No tienes permiso para ver esta cita.', 'danger')
        return redirect(url_for('veterinario.dashboard'))

    return render_template('veterinario/citas/ver_cita.html', cita=cita)


@veterinario_bp.route('/perfil', methods=['GET', 'POST'])
@veterinario_required
def perfil():
    """Ver y editar perfil del veterinario"""
    if request.method == 'POST':
        # Actualizar información
        current_user.nombre = request.form.get('nombre')
        current_user.apellido = request.form.get('apellido')
        current_user.email = request.form.get('email')
        current_user.telefono = request.form.get('telefono')
        current_user.especialidad = request.form.get('especialidad')
        current_user.licencia_profesional = request.form.get('licencia_profesional')

        # Cambiar contraseña si se proporciona
        password_actual = request.form.get('password_actual')
        password_nueva = request.form.get('password_nueva')
        password_confirmar = request.form.get('password_confirmar')

        if password_actual and password_nueva:
            if not current_user.check_password(password_actual):
                flash('La contraseña actual es incorrecta.', 'danger')
                return render_template('veterinario/perfil.html')

            if password_nueva != password_confirmar:
                flash('Las contraseñas nuevas no coinciden.', 'danger')
                return render_template('veterinario/perfil.html')

            if len(password_nueva) < 6:
                flash('La contraseña debe tener al menos 6 caracteres.', 'danger')
                return render_template('veterinario/perfil.html')

            current_user.set_password(password_nueva)

        try:
            db.session.commit()
            flash('Perfil actualizado exitosamente.', 'success')
            return redirect(url_for('veterinario.perfil'))
        except Exception as e:
            db.session.rollback()
            flash(f'Error al actualizar perfil: {str(e)}', 'danger')

    return render_template('veterinario/perfil.html')


# ============================================
# HISTORIAL MÉDICO
# ============================================

@veterinario_bp.route('/historial')
@veterinario_required
def historial_medico():
    """Lista de pacientes con historial médico"""
    # Obtener parámetros de búsqueda y filtro
    buscar = request.args.get('buscar', '').strip()
    especie_filtro = request.args.get('especie', '')
    orden = request.args.get('orden', 'reciente')
    
    # Query base - obtener mascotas que han tenido citas atendidas por este veterinario
    # o mascotas con historial clínico creado por este veterinario
    subquery_citas = db.session.query(Cita.mascota_id).filter(
        Cita.veterinario_id == current_user.id,
        Cita.estado.in_(['completada', 'atendida'])
    ).distinct()
    
    subquery_historiales = db.session.query(HistorialClinico.mascota_id).filter(
        HistorialClinico.creado_por_id == current_user.id
    ).distinct()
    
    # Combinar ambas consultas
    query = Mascota.query.filter(
        or_(
            Mascota.id.in_(subquery_citas),
            Mascota.id.in_(subquery_historiales)
        ),
        Mascota.activo == True
    )
    
    # Aplicar filtro de búsqueda
    if buscar:
        query = query.filter(
            or_(
                Mascota.nombre.ilike(f'%{buscar}%'),
                Mascota.especie.ilike(f'%{buscar}%'),
                Mascota.raza.ilike(f'%{buscar}%')
            )
        )
    
    # Aplicar filtro de especie
    if especie_filtro:
        query = query.filter(Mascota.especie.ilike(f'%{especie_filtro}%'))
    
    # Ordenar
    if orden == 'nombre':
        query = query.order_by(Mascota.nombre.asc())
    elif orden == 'especie':
        query = query.order_by(Mascota.especie.asc(), Mascota.nombre.asc())
    else:  # reciente
        query = query.order_by(Mascota.ultima_actualizacion.desc())
    
    mascotas = query.all()
    
    # Obtener estadísticas para cada mascota
    mascotas_info = []
    for mascota in mascotas:
        # Contar citas atendidas
        citas_count = Cita.query.filter(
            Cita.mascota_id == mascota.id,
            Cita.veterinario_id == current_user.id,
            Cita.estado.in_(['completada', 'atendida'])
        ).count()
        
        # Obtener última cita
        ultima_cita = Cita.query.filter(
            Cita.mascota_id == mascota.id,
            Cita.veterinario_id == current_user.id,
            Cita.estado.in_(['completada', 'atendida'])
        ).order_by(Cita.fecha.desc()).first()
        
        # Contar historiales
        historiales_count = HistorialClinico.query.filter(
            HistorialClinico.mascota_id == mascota.id
        ).count()
        
        mascotas_info.append({
            'mascota': mascota,
            'citas_count': citas_count,
            'ultima_cita': ultima_cita,
            'historiales_count': historiales_count
        })
    
    # Obtener lista de especies para el filtro
    especies = db.session.query(Mascota.especie).distinct().order_by(Mascota.especie).all()
    especies = [e[0] for e in especies if e[0]]
    
    return render_template('veterinario/historial/lista_pacientes.html',
                         mascotas_info=mascotas_info,
                         especies=especies,
                         buscar=buscar,
                         especie_filtro=especie_filtro,
                         orden=orden,
                         total_pacientes=len(mascotas_info))


@veterinario_bp.route('/historial/<int:mascota_id>')
@veterinario_required
def ver_historial_mascota(mascota_id):
    """Ver historial médico de una mascota específica"""
    mascota = Mascota.query.get_or_404(mascota_id)
    
    # Verificar que el veterinario ha atendido a esta mascota
    tiene_acceso = Cita.query.filter(
        Cita.mascota_id == mascota_id,
        Cita.veterinario_id == current_user.id,
        Cita.estado.in_(['completada', 'atendida'])
    ).first() is not None
    
    # O ha creado historiales para esta mascota
    if not tiene_acceso:
        tiene_acceso = HistorialClinico.query.filter(
            HistorialClinico.mascota_id == mascota_id,
            HistorialClinico.creado_por_id == current_user.id
        ).first() is not None
    
    if not tiene_acceso:
        flash('No tienes acceso al historial de esta mascota.', 'danger')
        return redirect(url_for('veterinario.historial_medico'))
    
    # Obtener historial clínico ordenado por fecha
    historiales = HistorialClinico.query.filter(
        HistorialClinico.mascota_id == mascota_id
    ).order_by(HistorialClinico.fecha.desc()).all()
    
    # Obtener citas completadas
    citas_completadas = Cita.query.filter(
        Cita.mascota_id == mascota_id,
        Cita.estado.in_(['completada', 'atendida'])
    ).order_by(Cita.fecha.desc()).all()
    
    # Crear timeline combinando historiales y citas
    timeline = []
    
    for historial in historiales:
        timeline.append({
            'tipo': 'historial',
            'fecha': historial.fecha,
            'titulo': historial.tipo_registro or 'Registro Médico',
            'diagnostico': historial.diagnostico_definitivo or historial.diagnostico_presuntivo,
            'tratamiento': historial.tratamiento_aplicado,
            'datos': historial
        })
    
    for cita in citas_completadas:
        # Evitar duplicados si la cita ya tiene historial asociado
        if not any(h.cita_id == cita.id for h in historiales if h.cita_id):
            timeline.append({
                'tipo': 'cita',
                'fecha': cita.fecha,
                'titulo': f'Consulta - {cita.motivo}' if cita.motivo else 'Consulta Médica',
                'diagnostico': cita.diagnostico,
                'tratamiento': cita.tratamiento,
                'datos': cita
            })
    
    # Ordenar timeline por fecha descendente
    timeline.sort(key=lambda x: x['fecha'], reverse=True)
    
    # Estadísticas del paciente
    stats = {
        'total_consultas': len(citas_completadas),
        'total_historiales': len(historiales),
        'ultima_visita': citas_completadas[0].fecha if citas_completadas else None,
        'peso_actual': mascota.peso,
    }
    
    # Obtener historial de peso si existe
    historial_peso = []
    for h in historiales:
        if h.peso:
            historial_peso.append({
                'fecha': h.fecha.strftime('%d/%m/%Y'),
                'peso': h.peso
            })
    
    return render_template('veterinario/historial/ver_historial.html',
                         mascota=mascota,
                         timeline=timeline,
                         stats=stats,
                         historial_peso=historial_peso)


# ============================================
# GENERACIÓN DE PDF - RECETA/CONSULTA
# ============================================

@veterinario_bp.route('/cita/<int:id>/receta-pdf')
@veterinario_required
def descargar_receta(id):
    """Generar y descargar PDF de la receta/consulta"""
    cita = Cita.query.get_or_404(id)
    
    # Verificar que la cita esté completada y tenga datos
    if cita.estado not in ['completada', 'atendida']:
        flash('Solo puedes generar PDF de citas completadas.', 'warning')
        return redirect(url_for('veterinario.mis_citas'))
    
    # Verificar acceso
    if cita.veterinario_id != current_user.id:
        flash('No tienes permiso para acceder a esta cita.', 'danger')
        return redirect(url_for('veterinario.mis_citas'))
    
    try:
        # Generar PDF
        pdf_buffer = generar_pdf_consulta(cita)
        
        # Crear respuesta
        response = make_response(pdf_buffer.getvalue())
        response.headers['Content-Type'] = 'application/pdf'
        response.headers['Content-Disposition'] = f'attachment; filename=consulta_{cita.mascota.nombre}_{cita.fecha.strftime("%Y%m%d")}.pdf'
        
        return response
    except Exception as e:
        flash(f'Error al generar PDF: {str(e)}', 'danger')
        return redirect(url_for('veterinario.mis_citas'))


def generar_pdf_consulta(cita):
    """Genera el PDF de la consulta médica"""
    from reportlab.lib import colors
    from reportlab.lib.pagesizes import letter, A4
    from reportlab.lib.styles import getSampleStyleSheet, ParagraphStyle
    from reportlab.lib.units import inch, cm
    from reportlab.platypus import SimpleDocTemplate, Paragraph, Spacer, Table, TableStyle, Image
    from reportlab.lib.enums import TA_CENTER, TA_LEFT, TA_RIGHT
    
    buffer = BytesIO()
    doc = SimpleDocTemplate(buffer, pagesize=A4, topMargin=1*cm, bottomMargin=1*cm, leftMargin=1.5*cm, rightMargin=1.5*cm)
    
    # Estilos
    styles = getSampleStyleSheet()
    
    # Estilos personalizados
    title_style = ParagraphStyle(
        'CustomTitle',
        parent=styles['Heading1'],
        fontSize=20,
        textColor=colors.HexColor('#8B4513'),
        spaceAfter=10,
        alignment=TA_CENTER,
        fontName='Helvetica-Bold'
    )
    
    subtitle_style = ParagraphStyle(
        'CustomSubtitle',
        parent=styles['Normal'],
        fontSize=10,
        textColor=colors.HexColor('#666666'),
        alignment=TA_CENTER,
        spaceAfter=20
    )
    
    section_title_style = ParagraphStyle(
        'SectionTitle',
        parent=styles['Heading2'],
        fontSize=12,
        textColor=colors.HexColor('#8B4513'),
        spaceBefore=15,
        spaceAfter=8,
        fontName='Helvetica-Bold'
    )
    
    normal_style = ParagraphStyle(
        'CustomNormal',
        parent=styles['Normal'],
        fontSize=10,
        spaceAfter=5
    )
    
    bold_style = ParagraphStyle(
        'CustomBold',
        parent=styles['Normal'],
        fontSize=10,
        fontName='Helvetica-Bold'
    )
    
    # Contenido del documento
    elements = []
    
    # === ENCABEZADO ===
    elements.append(Paragraph("🏥 RamboPet - Veterinaria", title_style))
    elements.append(Paragraph("Sistema de Gestión Veterinaria", subtitle_style))
    elements.append(Spacer(1, 10))
    
    # Línea separadora
    elements.append(Table([['']], colWidths=[18*cm], rowHeights=[2]))
    elements[-1].setStyle(TableStyle([
        ('BACKGROUND', (0, 0), (-1, -1), colors.HexColor('#8B4513')),
    ]))
    elements.append(Spacer(1, 15))
    
    # === INFORMACIÓN DE LA CONSULTA ===
    elements.append(Paragraph("📋 RESUMEN DE CONSULTA MÉDICA", section_title_style))
    
    # Datos básicos en tabla
    fecha_consulta = cita.fecha.strftime('%d de %B de %Y a las %H:%M')
    consulta_data = [
        ['Fecha de Consulta:', fecha_consulta],
        ['Veterinario:', f"Dr(a). {current_user.nombre_completo if hasattr(current_user, 'nombre_completo') else current_user.nombre}"],
        ['N° de Cita:', f"#{cita.id}"],
    ]
    
    consulta_table = Table(consulta_data, colWidths=[4*cm, 14*cm])
    consulta_table.setStyle(TableStyle([
        ('FONTNAME', (0, 0), (0, -1), 'Helvetica-Bold'),
        ('FONTSIZE', (0, 0), (-1, -1), 10),
        ('TEXTCOLOR', (0, 0), (0, -1), colors.HexColor('#666666')),
        ('BOTTOMPADDING', (0, 0), (-1, -1), 8),
    ]))
    elements.append(consulta_table)
    elements.append(Spacer(1, 15))
    
    # === INFORMACIÓN DEL PACIENTE ===
    elements.append(Paragraph("🐾 DATOS DEL PACIENTE", section_title_style))
    
    mascota = cita.mascota
    tutor = cita.tutor
    
    paciente_data = [
        ['Nombre:', mascota.nombre, 'Especie:', mascota.especie],
        ['Raza:', mascota.raza or 'No especificada', 'Sexo:', mascota.sexo or 'No especificado'],
        ['Edad:', mascota.edad_detallada if hasattr(mascota, 'edad_detallada') and mascota.fecha_nacimiento else 'No registrada', 
         'Peso:', f"{mascota.peso} kg" if mascota.peso else 'No registrado'],
    ]
    
    paciente_table = Table(paciente_data, colWidths=[3*cm, 6*cm, 3*cm, 6*cm])
    paciente_table.setStyle(TableStyle([
        ('FONTNAME', (0, 0), (0, -1), 'Helvetica-Bold'),
        ('FONTNAME', (2, 0), (2, -1), 'Helvetica-Bold'),
        ('FONTSIZE', (0, 0), (-1, -1), 10),
        ('TEXTCOLOR', (0, 0), (0, -1), colors.HexColor('#666666')),
        ('TEXTCOLOR', (2, 0), (2, -1), colors.HexColor('#666666')),
        ('BOTTOMPADDING', (0, 0), (-1, -1), 8),
        ('BACKGROUND', (0, 0), (-1, -1), colors.HexColor('#FDF5E6')),
        ('BOX', (0, 0), (-1, -1), 1, colors.HexColor('#D2691E')),
        ('INNERGRID', (0, 0), (-1, -1), 0.5, colors.HexColor('#D2691E')),
        ('TOPPADDING', (0, 0), (-1, -1), 8),
        ('LEFTPADDING', (0, 0), (-1, -1), 8),
    ]))
    elements.append(paciente_table)
    elements.append(Spacer(1, 10))
    
    # Tutor
    if tutor:
        tutor_data = [
            ['Tutor:', tutor.nombre_completo if hasattr(tutor, 'nombre_completo') else tutor.nombre, 
             'Teléfono:', tutor.telefono or 'No registrado'],
        ]
        tutor_table = Table(tutor_data, colWidths=[3*cm, 6*cm, 3*cm, 6*cm])
        tutor_table.setStyle(TableStyle([
            ('FONTNAME', (0, 0), (0, -1), 'Helvetica-Bold'),
            ('FONTNAME', (2, 0), (2, -1), 'Helvetica-Bold'),
            ('FONTSIZE', (0, 0), (-1, -1), 10),
            ('TEXTCOLOR', (0, 0), (0, -1), colors.HexColor('#666666')),
            ('TEXTCOLOR', (2, 0), (2, -1), colors.HexColor('#666666')),
            ('BOTTOMPADDING', (0, 0), (-1, -1), 5),
        ]))
        elements.append(tutor_table)
    
    elements.append(Spacer(1, 15))
    
    # === MOTIVO DE CONSULTA ===
    if cita.motivo:
        elements.append(Paragraph("📝 MOTIVO DE CONSULTA", section_title_style))
        elements.append(Paragraph(cita.motivo, normal_style))
        elements.append(Spacer(1, 10))
    
    # === DIAGNÓSTICO ===
    if cita.diagnostico:
        elements.append(Paragraph("🔍 DIAGNÓSTICO", section_title_style))
        
        # Caja de diagnóstico
        diag_data = [[Paragraph(cita.diagnostico, normal_style)]]
        diag_table = Table(diag_data, colWidths=[17*cm])
        diag_table.setStyle(TableStyle([
            ('BACKGROUND', (0, 0), (-1, -1), colors.HexColor('#F5F5F5')),
            ('BOX', (0, 0), (-1, -1), 1, colors.HexColor('#CCCCCC')),
            ('TOPPADDING', (0, 0), (-1, -1), 10),
            ('BOTTOMPADDING', (0, 0), (-1, -1), 10),
            ('LEFTPADDING', (0, 0), (-1, -1), 10),
            ('RIGHTPADDING', (0, 0), (-1, -1), 10),
        ]))
        elements.append(diag_table)
        elements.append(Spacer(1, 10))
    
    # === TRATAMIENTO ===
    if cita.tratamiento:
        elements.append(Paragraph("💊 TRATAMIENTO", section_title_style))
        
        # Caja de tratamiento
        trat_data = [[Paragraph(cita.tratamiento, normal_style)]]
        trat_table = Table(trat_data, colWidths=[17*cm])
        trat_table.setStyle(TableStyle([
            ('BACKGROUND', (0, 0), (-1, -1), colors.HexColor('#E8F5E9')),
            ('BOX', (0, 0), (-1, -1), 1, colors.HexColor('#81C784')),
            ('TOPPADDING', (0, 0), (-1, -1), 10),
            ('BOTTOMPADDING', (0, 0), (-1, -1), 10),
            ('LEFTPADDING', (0, 0), (-1, -1), 10),
            ('RIGHTPADDING', (0, 0), (-1, -1), 10),
        ]))
        elements.append(trat_table)
        elements.append(Spacer(1, 10))
    
    # === MEDICAMENTOS RECETADOS ===
    recetas = Receta.query.filter_by(cita_id=cita.id).all()
    if recetas:
        elements.append(Paragraph("💉 MEDICAMENTOS RECETADOS", section_title_style))
        
        # Tabla de medicamentos
        med_header = ['Medicamento', 'Cantidad', 'Dosis', 'Duración', 'Indicaciones']
        med_data = [med_header]
        
        for receta in recetas:
            med_data.append([
                receta.medicamento.nombre if receta.medicamento else 'N/A',
                str(receta.cantidad) if receta.cantidad else '-',
                receta.dosis or '-',
                receta.duracion or '-',
                receta.indicaciones or '-'
            ])
        
        med_table = Table(med_data, colWidths=[4*cm, 2*cm, 3*cm, 3*cm, 5*cm])
        med_table.setStyle(TableStyle([
            ('BACKGROUND', (0, 0), (-1, 0), colors.HexColor('#8B4513')),
            ('TEXTCOLOR', (0, 0), (-1, 0), colors.white),
            ('FONTNAME', (0, 0), (-1, 0), 'Helvetica-Bold'),
            ('FONTSIZE', (0, 0), (-1, -1), 9),
            ('ALIGN', (0, 0), (-1, -1), 'CENTER'),
            ('VALIGN', (0, 0), (-1, -1), 'MIDDLE'),
            ('BOTTOMPADDING', (0, 0), (-1, -1), 8),
            ('TOPPADDING', (0, 0), (-1, -1), 8),
            ('BACKGROUND', (0, 1), (-1, -1), colors.HexColor('#FFF8DC')),
            ('BOX', (0, 0), (-1, -1), 1, colors.HexColor('#8B4513')),
            ('INNERGRID', (0, 0), (-1, -1), 0.5, colors.HexColor('#D2691E')),
        ]))
        elements.append(med_table)
        elements.append(Spacer(1, 10))
    
    # === OBSERVACIONES ===
    if cita.observaciones:
        elements.append(Paragraph("📋 OBSERVACIONES Y RECOMENDACIONES", section_title_style))
        elements.append(Paragraph(cita.observaciones, normal_style))
        elements.append(Spacer(1, 10))
    
    # === PIE DE PÁGINA ===
    elements.append(Spacer(1, 20))
    elements.append(Table([['']], colWidths=[18*cm], rowHeights=[1]))
    elements[-1].setStyle(TableStyle([
        ('BACKGROUND', (0, 0), (-1, -1), colors.HexColor('#D2691E')),
    ]))
    elements.append(Spacer(1, 10))
    
    # Firma
    firma_style = ParagraphStyle(
        'Firma',
        parent=styles['Normal'],
        fontSize=10,
        alignment=TA_CENTER,
        spaceBefore=30
    )
    
    elements.append(Spacer(1, 30))
    elements.append(Paragraph("_" * 40, firma_style))
    elements.append(Paragraph(f"Dr(a). {current_user.nombre_completo if hasattr(current_user, 'nombre_completo') else current_user.nombre}", firma_style))
    if hasattr(current_user, 'licencia_profesional') and current_user.licencia_profesional:
        elements.append(Paragraph(f"Lic. Prof.: {current_user.licencia_profesional}", firma_style))
    
    # Fecha de generación
    footer_style = ParagraphStyle(
        'Footer',
        parent=styles['Normal'],
        fontSize=8,
        textColor=colors.HexColor('#999999'),
        alignment=TA_CENTER,
        spaceBefore=20
    )
    elements.append(Spacer(1, 20))
    elements.append(Paragraph(f"Documento generado el {datetime.now().strftime('%d/%m/%Y a las %H:%M')}", footer_style))
    elements.append(Paragraph("RamboPet - Sistema de Gestión Veterinaria", footer_style))
    
    # Construir PDF
    doc.build(elements)
    buffer.seek(0)
    
    return buffer
