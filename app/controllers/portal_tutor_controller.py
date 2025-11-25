"""
Controlador de Tutor
Gestiona las acciones de los tutores de mascotas
"""
from flask import Blueprint, render_template, redirect, url_for, flash, request, send_file, current_app
from flask_login import login_required, current_user
from functools import wraps
from app import db
from app.models.user import Usuario
from app.models.mascota import Mascota
from app.models.cita import Cita
from app.models.pago import Pago
from datetime import datetime
import base64
import os
from io import BytesIO

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
    
    # Obtener mascotas para mostrar en el dashboard
    mis_mascotas = Mascota.query.filter_by(
        tutor_id=current_user.id,
        activo=True
    ).order_by(Mascota.nombre.asc()).limit(6).all()

    return render_template('dashboards/tutor/dashboard.html',
                         total_mascotas=total_mascotas,
                         total_citas=total_citas,
                         citas_pendientes=citas_pendientes,
                         citas_proximas=citas_proximas,
                         mis_mascotas=mis_mascotas)


@tutor_bp.route('/mascotas')
@tutor_required
def mascotas():
    """Lista de mascotas del tutor"""
    mis_mascotas = Mascota.query.filter_by(
        tutor_id=current_user.id,
        activo=True
    ).order_by(Mascota.nombre.asc()).all()

    return render_template('tutor/mascotas/mascotas.html', mascotas=mis_mascotas)


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
            return render_template('tutor/mascotas/nueva_mascota.html')

        # Convertir fecha
        fecha_nac = None
        if fecha_nacimiento:
            try:
                fecha_nac = datetime.strptime(fecha_nacimiento, '%Y-%m-%d').date()
            except ValueError:
                flash('Formato de fecha inválido.', 'danger')
                return render_template('tutor/mascotas/nueva_mascota.html')

        # Convertir peso
        peso_float = None
        if peso:
            try:
                peso_float = float(peso)
            except ValueError:
                flash('El peso debe ser un número válido.', 'danger')
                return render_template('tutor/mascotas/nueva_mascota.html')

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

    return render_template('tutor/mascotas/nueva_mascota.html')


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

    return render_template('tutor/mascotas/ver_mascota.html', mascota=mascota, citas=citas)


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

    return render_template('tutor/mascotas/editar_mascota.html', mascota=mascota)


@tutor_bp.route('/citas')
@tutor_required
def citas():
    """Lista de citas del tutor"""
    mis_citas = Cita.query.filter_by(tutor_id=current_user.id).order_by(Cita.fecha.desc()).all()
    return render_template('tutor/citas/citas.html', citas=mis_citas)


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
    
    # Obtener servicios activos
    from app.models.servicio import Servicio
    servicios = Servicio.query.filter_by(activo=True).order_by(Servicio.nombre.asc()).all()

    if request.method == 'POST':
        mascota_id = request.form.get('mascota_id')
        veterinario_id = request.form.get('veterinario_id')
        servicio_id = request.form.get('servicio_id')
        fecha = request.form.get('fecha')
        hora = request.form.get('hora')
        motivo = request.form.get('motivo')

        # Validaciones
        if not all([mascota_id, veterinario_id, servicio_id, fecha, hora]):
            flash('Por favor complete todos los campos obligatorios.', 'danger')
            return render_template('tutor/citas/nueva_cita.html', mascotas=mascotas, veterinarios=veterinarios, servicios=servicios)

        # Verificar que la mascota pertenece al tutor
        mascota = Mascota.query.get(mascota_id)
        if not mascota or mascota.tutor_id != current_user.id:
            flash('Mascota no válida.', 'danger')
            return render_template('tutor/citas/nueva_cita.html', mascotas=mascotas, veterinarios=veterinarios, servicios=servicios)

        # Verificar servicio
        servicio = Servicio.query.get(servicio_id)
        if not servicio:
            flash('Servicio no válido.', 'danger')
            return render_template('tutor/citas/nueva_cita.html', mascotas=mascotas, veterinarios=veterinarios, servicios=servicios)

        # Combinar fecha y hora
        try:
            fecha_hora = datetime.strptime(f"{fecha} {hora}", '%Y-%m-%d %H:%M')
        except ValueError:
            flash('Formato de fecha u hora inválido.', 'danger')
            return render_template('tutor/citas/nueva_cita.html', mascotas=mascotas, veterinarios=veterinarios, servicios=servicios)

        # Verificar que la fecha sea futura
        if fecha_hora < datetime.now():
            flash('La fecha de la cita debe ser futura.', 'danger')
            return render_template('tutor/citas/nueva_cita.html', mascotas=mascotas, veterinarios=veterinarios, servicios=servicios)

        # Crear cita con veterinario asignado pero en estado PENDIENTE
        # El veterinario elegido debe aceptarla para confirmarla
        motivo_final = motivo or servicio.descripcion or f"Consulta de {servicio.nombre}"
        
        nueva_cita = Cita(
            mascota_id=mascota_id,
            tutor_id=current_user.id,
            veterinario_id=veterinario_id,  # Asignado pero pendiente de aceptación
            fecha=fecha_hora,
            tipo=servicio.nombre,
            motivo=motivo_final,
            costo=servicio.precio,
            estado='pendiente'  # Esperando que el veterinario acepte
        )

        try:
            db.session.add(nueva_cita)
            db.session.commit()
            flash(f'Cita solicitada al Dr. elegido. Costo: Bs. {servicio.precio}. Esperando confirmación del veterinario.', 'success')
            return redirect(url_for('tutor.pagar_cita', cita_id=nueva_cita.id))
        except Exception as e:
            db.session.rollback()
            flash(f'Error al solicitar cita: {str(e)}', 'danger')

    return render_template('tutor/citas/nueva_cita.html', mascotas=mascotas, veterinarios=veterinarios, servicios=servicios)


@tutor_bp.route('/cita/<int:id>')
@tutor_required
def ver_cita(id):
    """Ver detalles de una cita"""
    cita = Cita.query.get_or_404(id)

    # Verificar que la cita pertenece al tutor
    if cita.tutor_id != current_user.id:
        flash('No tienes permiso para ver esta cita.', 'danger')
        return redirect(url_for('tutor.citas'))

    return render_template('tutor/citas/ver_cita.html', cita=cita)


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
        # El monto viene del formulario pero lo validamos con el costo de la cita
        monto_form = request.form.get('monto')
        
        # Datos de facturación
        requiere_factura = request.form.get('requiere_factura') == '1'
        nit_cliente = request.form.get('nit_cliente', '').strip()
        razon_social = request.form.get('razon_social', '').strip()
        email_factura = request.form.get('email_factura', '').strip()
        tipo_documento = request.form.get('tipo_documento', 'nit')
        
        # Usamos el costo de la cita como autoridad, o el del form si es válido
        monto_final = cita.costo if cita.costo > 0 else float(monto_form)

        # Validaciones
        if not metodo_pago:
            flash('Por favor seleccione un método de pago.', 'danger')
            return render_template('tutor/pagos/pagar_cita.html', cita=cita)

        # Generar número de factura si requiere factura
        numero_factura = None
        if requiere_factura:
            # Formato: FAC-AAAAMMDD-XXXX
            fecha_str = datetime.now().strftime('%Y%m%d')
            ultimo_pago_factura = Pago.query.filter(
                Pago.numero_factura.like(f'FAC-{fecha_str}-%')
            ).order_by(Pago.id.desc()).first()
            
            if ultimo_pago_factura and ultimo_pago_factura.numero_factura:
                try:
                    ultimo_num = int(ultimo_pago_factura.numero_factura.split('-')[-1])
                    nuevo_num = ultimo_num + 1
                except:
                    nuevo_num = 1
            else:
                nuevo_num = 1
            
            numero_factura = f'FAC-{fecha_str}-{nuevo_num:04d}'

        # Crear el pago
        nuevo_pago = Pago(
            monto=monto_final,
            metodo_pago=metodo_pago,
            estado='completado',  # Pago simulado, automáticamente completado
            descripcion=f'Pago de cita #{cita_id} - {cita.tipo}',
            usuario_id=current_user.id,  # Tutor que paga
            cita_id=cita_id,
            veterinario_id=cita.veterinario_id,
            porcentaje_empresa=57.14,  # Porcentaje para la empresa
            porcentaje_veterinario=42.86,  # Porcentaje para el veterinario
            fecha_pago=datetime.now(),  # Fecha del pago
            # Datos de facturación
            requiere_factura=requiere_factura,
            numero_factura=numero_factura,
            nit_cliente=nit_cliente if requiere_factura else None,
            razon_social_cliente=razon_social if requiere_factura else None
        )

        # Generar código de pago único
        nuevo_pago.generar_codigo_pago()

        # Calcular división de ingresos (empresa vs veterinario)
        nuevo_pago.calcular_division_ingresos()

        # Si es método QR, generar código QR
        if 'qr' in metodo_pago.lower():
            nuevo_pago.generar_qr()

        try:
            db.session.add(nuevo_pago)

            # Confirmar automáticamente la cita
            cita.estado = 'confirmada'
            # Asegurar que el costo final quede registrado en la cita si era 0
            if cita.costo == 0:
                cita.costo = monto_final

            db.session.commit()

            # Redirigir a página de éxito con el ID del pago
            return redirect(url_for('tutor.pago_exitoso', pago_id=nuevo_pago.id))
        except Exception as e:
            db.session.rollback()
            flash(f'Error al procesar el pago: {str(e)}', 'danger')

    return render_template('tutor/pagos/pagar_cita.html', cita=cita)


@tutor_bp.route('/pago-exitoso/<int:pago_id>')
@tutor_required
def pago_exitoso(pago_id):
    """Página de confirmación de pago exitoso"""
    pago = Pago.query.get_or_404(pago_id)

    # Verificar que el pago pertenece al usuario
    if pago.usuario_id != current_user.id:
        flash('No tienes permiso para ver este pago.', 'danger')
        return redirect(url_for('tutor.citas'))

    return render_template('tutor/pagos/pago_exitoso.html', pago=pago)


@tutor_bp.route('/descargar-factura/<int:pago_id>')
@tutor_required
def descargar_factura(pago_id):
    """Descargar factura en PDF - Formato Bolivia"""
    from reportlab.lib.pagesizes import letter
    from reportlab.platypus import SimpleDocTemplate, Paragraph, Spacer, Table, TableStyle, Image
    from reportlab.lib.styles import getSampleStyleSheet, ParagraphStyle
    from reportlab.lib.units import inch, cm
    from reportlab.lib.enums import TA_CENTER, TA_LEFT, TA_RIGHT
    from reportlab.lib import colors
    
    pago = Pago.query.get_or_404(pago_id)

    # Verificar que el pago pertenece al usuario
    if pago.usuario_id != current_user.id:
        flash('No tienes permiso para descargar esta factura.', 'danger')
        return redirect(url_for('tutor.citas'))

    # Crear buffer para el PDF
    buffer = BytesIO()
    doc = SimpleDocTemplate(
        buffer, 
        pagesize=letter,
        rightMargin=1*cm,
        leftMargin=1*cm,
        topMargin=1*cm,
        bottomMargin=1*cm
    )
    
    styles = getSampleStyleSheet()
    story = []
    
    # Estilos personalizados
    styles.add(ParagraphStyle(
        name='FacturaTitle',
        alignment=TA_CENTER,
        fontSize=18,
        fontName='Helvetica-Bold',
        textColor=colors.HexColor('#1e293b'),
        spaceAfter=6
    ))
    
    styles.add(ParagraphStyle(
        name='FacturaSubtitle',
        alignment=TA_CENTER,
        fontSize=10,
        fontName='Helvetica',
        textColor=colors.HexColor('#64748b'),
        spaceAfter=20
    ))
    
    styles.add(ParagraphStyle(
        name='SectionTitle',
        alignment=TA_LEFT,
        fontSize=11,
        fontName='Helvetica-Bold',
        textColor=colors.HexColor('#1e293b'),
        spaceBefore=15,
        spaceAfter=8
    ))
    
    styles.add(ParagraphStyle(
        name='NormalText',
        alignment=TA_LEFT,
        fontSize=10,
        fontName='Helvetica',
        textColor=colors.HexColor('#374151')
    ))
    
    styles.add(ParagraphStyle(
        name='SmallText',
        alignment=TA_CENTER,
        fontSize=8,
        fontName='Helvetica',
        textColor=colors.HexColor('#6b7280')
    ))
    
    # Logo (si existe)
    logo_path = os.path.join(current_app.root_path, 'static', 'img', 'logo.png')
    if os.path.exists(logo_path):
        try:
            img = Image(logo_path, width=1.2*inch, height=1.2*inch)
            story.append(img)
        except:
            pass
    
    # Encabezado de la empresa
    story.append(Paragraph("VETERINARIA RAMBOPET", styles['FacturaTitle']))
    story.append(Paragraph("NIT: 1234567890 | Casa Matriz", styles['FacturaSubtitle']))
    
    # Número de Factura y datos fiscales
    factura_info = f"""
    <b>FACTURA</b><br/>
    N° {pago.numero_factura or pago.codigo_pago}<br/>
    <font size="8" color="#64748b">AUTORIZACIÓN: 79040011157827</font>
    """
    story.append(Paragraph(factura_info, ParagraphStyle(
        name='FacturaNum',
        alignment=TA_CENTER,
        fontSize=14,
        fontName='Helvetica-Bold',
        textColor=colors.HexColor('#dc2626'),
        spaceBefore=10,
        spaceAfter=20
    )))
    
    # Línea separadora
    story.append(Spacer(1, 0.1*inch))
    
    # Datos del cliente
    story.append(Paragraph("DATOS DEL CLIENTE", styles['SectionTitle']))
    
    cliente_data = [
        ['NIT/CI:', pago.nit_cliente or 'S/N'],
        ['Razón Social:', pago.razon_social_cliente or current_user.nombre_completo],
        ['Fecha:', pago.fecha_pago.strftime('%d/%m/%Y') if pago.fecha_pago else datetime.now().strftime('%d/%m/%Y')],
        ['Hora:', pago.fecha_pago.strftime('%H:%M:%S') if pago.fecha_pago else datetime.now().strftime('%H:%M:%S')],
    ]
    
    cliente_table = Table(cliente_data, colWidths=[2*inch, 4.5*inch])
    cliente_table.setStyle(TableStyle([
        ('FONTNAME', (0, 0), (0, -1), 'Helvetica-Bold'),
        ('FONTNAME', (1, 0), (1, -1), 'Helvetica'),
        ('FONTSIZE', (0, 0), (-1, -1), 10),
        ('TEXTCOLOR', (0, 0), (0, -1), colors.HexColor('#374151')),
        ('TEXTCOLOR', (1, 0), (1, -1), colors.HexColor('#1e293b')),
        ('BOTTOMPADDING', (0, 0), (-1, -1), 6),
        ('TOPPADDING', (0, 0), (-1, -1), 6),
    ]))
    story.append(cliente_table)
    
    story.append(Spacer(1, 0.3*inch))
    
    # Detalle de la factura
    story.append(Paragraph("DETALLE", styles['SectionTitle']))
    
    # Calcular IVA (13% incluido en Bolivia)
    subtotal = pago.monto / 1.13
    iva = pago.monto - subtotal
    
    detalle_data = [
        ['CANTIDAD', 'DESCRIPCIÓN', 'P. UNITARIO', 'SUBTOTAL'],
        ['1', f'Consulta Veterinaria\n{pago.cita.tipo if pago.cita else "Servicio"}', f'Bs. {subtotal:.2f}', f'Bs. {subtotal:.2f}'],
    ]
    
    detalle_table = Table(detalle_data, colWidths=[1*inch, 3.5*inch, 1.25*inch, 1.25*inch])
    detalle_table.setStyle(TableStyle([
        # Header
        ('BACKGROUND', (0, 0), (-1, 0), colors.HexColor('#f1f5f9')),
        ('FONTNAME', (0, 0), (-1, 0), 'Helvetica-Bold'),
        ('FONTSIZE', (0, 0), (-1, 0), 9),
        ('TEXTCOLOR', (0, 0), (-1, 0), colors.HexColor('#374151')),
        ('ALIGN', (0, 0), (-1, 0), 'CENTER'),
        # Body
        ('FONTNAME', (0, 1), (-1, -1), 'Helvetica'),
        ('FONTSIZE', (0, 1), (-1, -1), 10),
        ('TEXTCOLOR', (0, 1), (-1, -1), colors.HexColor('#1e293b')),
        ('ALIGN', (0, 1), (0, -1), 'CENTER'),
        ('ALIGN', (2, 1), (-1, -1), 'RIGHT'),
        # Borders
        ('LINEBELOW', (0, 0), (-1, 0), 1, colors.HexColor('#e2e8f0')),
        ('LINEBELOW', (0, -1), (-1, -1), 1, colors.HexColor('#e2e8f0')),
        ('TOPPADDING', (0, 0), (-1, -1), 10),
        ('BOTTOMPADDING', (0, 0), (-1, -1), 10),
    ]))
    story.append(detalle_table)
    
    story.append(Spacer(1, 0.3*inch))
    
    # Totales
    totales_data = [
        ['SUBTOTAL:', f'Bs. {subtotal:.2f}'],
        ['IVA (13%):', f'Bs. {iva:.2f}'],
        ['TOTAL:', f'Bs. {pago.monto:.2f}'],
    ]
    
    totales_table = Table(totales_data, colWidths=[5*inch, 1.5*inch])
    totales_table.setStyle(TableStyle([
        ('FONTNAME', (0, 0), (0, 1), 'Helvetica'),
        ('FONTNAME', (0, 2), (-1, 2), 'Helvetica-Bold'),
        ('FONTSIZE', (0, 0), (-1, -1), 11),
        ('TEXTCOLOR', (0, 0), (-1, 1), colors.HexColor('#64748b')),
        ('TEXTCOLOR', (0, 2), (-1, 2), colors.HexColor('#059669')),
        ('ALIGN', (0, 0), (0, -1), 'RIGHT'),
        ('ALIGN', (1, 0), (1, -1), 'RIGHT'),
        ('TOPPADDING', (0, 0), (-1, -1), 6),
        ('BOTTOMPADDING', (0, 0), (-1, -1), 6),
        ('LINEABOVE', (0, 2), (-1, 2), 2, colors.HexColor('#e2e8f0')),
    ]))
    story.append(totales_table)
    
    # Monto en literal
    monto_literal = numero_a_letras(pago.monto)
    story.append(Spacer(1, 0.2*inch))
    story.append(Paragraph(f"<b>Son:</b> {monto_literal} Bolivianos", styles['NormalText']))
    
    story.append(Spacer(1, 0.4*inch))
    
    # Información adicional
    story.append(Paragraph("INFORMACIÓN ADICIONAL", styles['SectionTitle']))
    
    info_data = [
        ['Código de Pago:', pago.codigo_pago],
        ['Método de Pago:', pago.metodo_pago_label],
        ['Estado:', 'PAGADO'],
    ]
    
    if pago.cita:
        info_data.extend([
            ['Mascota:', pago.cita.mascota.nombre if pago.cita.mascota else '-'],
            ['Veterinario:', f'Dr(a). {pago.cita.veterinario.nombre_completo}' if pago.cita.veterinario else '-'],
            ['Fecha de Cita:', pago.cita.fecha.strftime('%d/%m/%Y %H:%M') if pago.cita.fecha else '-'],
        ])
    
    info_table = Table(info_data, colWidths=[2*inch, 4.5*inch])
    info_table.setStyle(TableStyle([
        ('FONTNAME', (0, 0), (0, -1), 'Helvetica-Bold'),
        ('FONTNAME', (1, 0), (1, -1), 'Helvetica'),
        ('FONTSIZE', (0, 0), (-1, -1), 9),
        ('TEXTCOLOR', (0, 0), (-1, -1), colors.HexColor('#64748b')),
        ('BOTTOMPADDING', (0, 0), (-1, -1), 4),
        ('TOPPADDING', (0, 0), (-1, -1), 4),
    ]))
    story.append(info_table)
    
    story.append(Spacer(1, 0.5*inch))
    
    # Pie de página legal
    legal_text = """
    "ESTA FACTURA CONTRIBUYE AL DESARROLLO DEL PAÍS, EL USO ILÍCITO SERÁ SANCIONADO PENALMENTE DE ACUERDO A LEY"
    """
    story.append(Paragraph(legal_text, styles['SmallText']))
    
    story.append(Spacer(1, 0.1*inch))
    story.append(Paragraph(
        f"Documento generado el {datetime.now().strftime('%d/%m/%Y a las %H:%M')} | Veterinaria RamboPet",
        styles['SmallText']
    ))
    
    # Construir PDF
    doc.build(story)
    buffer.seek(0)
    
    # Nombre del archivo
    filename = f"Factura_{pago.numero_factura or pago.codigo_pago}.pdf"
    
    return send_file(
        buffer,
        as_attachment=True,
        download_name=filename,
        mimetype='application/pdf'
    )


def numero_a_letras(numero):
    """Convierte un número a su representación en letras (español)"""
    unidades = ['', 'uno', 'dos', 'tres', 'cuatro', 'cinco', 'seis', 'siete', 'ocho', 'nueve']
    decenas = ['', 'diez', 'veinte', 'treinta', 'cuarenta', 'cincuenta', 'sesenta', 'setenta', 'ochenta', 'noventa']
    especiales = {
        11: 'once', 12: 'doce', 13: 'trece', 14: 'catorce', 15: 'quince',
        16: 'dieciséis', 17: 'diecisiete', 18: 'dieciocho', 19: 'diecinueve',
        21: 'veintiuno', 22: 'veintidós', 23: 'veintitrés', 24: 'veinticuatro',
        25: 'veinticinco', 26: 'veintiséis', 27: 'veintisiete', 28: 'veintiocho', 29: 'veintinueve'
    }
    centenas = ['', 'ciento', 'doscientos', 'trescientos', 'cuatrocientos', 'quinientos',
                'seiscientos', 'setecientos', 'ochocientos', 'novecientos']
    
    def convertir_grupo(n):
        if n == 0:
            return ''
        if n == 100:
            return 'cien'
        if n in especiales:
            return especiales[n]
        
        resultado = ''
        if n >= 100:
            resultado += centenas[n // 100] + ' '
            n = n % 100
        
        if n in especiales:
            resultado += especiales[n]
        elif n >= 10:
            resultado += decenas[n // 10]
            if n % 10 != 0:
                resultado += ' y ' + unidades[n % 10]
        else:
            resultado += unidades[n]
        
        return resultado.strip()
    
    entero = int(numero)
    decimal = int(round((numero - entero) * 100))
    
    if entero == 0:
        resultado = 'cero'
    elif entero == 1:
        resultado = 'un'
    elif entero < 1000:
        resultado = convertir_grupo(entero)
    elif entero < 1000000:
        miles = entero // 1000
        resto = entero % 1000
        if miles == 1:
            resultado = 'mil'
        else:
            resultado = convertir_grupo(miles) + ' mil'
        if resto > 0:
            resultado += ' ' + convertir_grupo(resto)
    else:
        resultado = str(entero)
    
    # Agregar centavos
    if decimal > 0:
        resultado += f' {decimal:02d}/100'
    else:
        resultado += ' 00/100'
    
    return resultado.upper()


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


@tutor_bp.route('/cambiar-password', methods=['POST'])
@tutor_required
def cambiar_password():
    """Procesar cambio de contraseña"""
    password_actual = request.form.get('password_actual')
    password_nueva = request.form.get('password_nueva')
    password_confirmar = request.form.get('password_confirmar')

    if not all([password_actual, password_nueva, password_confirmar]):
        flash('Todos los campos son obligatorios.', 'danger')
        return redirect(url_for('tutor.perfil'))

    if not current_user.check_password(password_actual):
        flash('La contraseña actual es incorrecta.', 'danger')
        return redirect(url_for('tutor.perfil'))

    if password_nueva != password_confirmar:
        flash('Las contraseñas nuevas no coinciden.', 'danger')
        return redirect(url_for('tutor.perfil'))

    if len(password_nueva) < 6:
        flash('La contraseña debe tener al menos 6 caracteres.', 'danger')
        return redirect(url_for('tutor.perfil'))

    try:
        current_user.set_password(password_nueva)
        db.session.commit()
        flash('Contraseña actualizada exitosamente.', 'success')
    except Exception as e:
        db.session.rollback()
        flash(f'Error al actualizar contraseña: {str(e)}', 'danger')

    return redirect(url_for('tutor.perfil'))


@tutor_bp.route('/quienes-somos')
@tutor_required
def quienes_somos():
    """Página Quiénes Somos"""
    return render_template('tutor/quienes_somos.html')
