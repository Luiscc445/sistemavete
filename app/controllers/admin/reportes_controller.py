"""
Controlador de Reportes y Estadísticas
"""
from flask import Blueprint, render_template, redirect, url_for, flash, request, jsonify, send_file
from flask_login import login_required, current_user
from functools import wraps
from datetime import datetime, timedelta, date
from sqlalchemy import func, and_, or_, extract
from app import db
from app.models import Usuario, Mascota, Cita, Medicamento, Servicio, HistorialClinico
import pandas as pd
from io import BytesIO

reportes_bp = Blueprint('reportes', __name__)


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


@reportes_bp.route('/')
@admin_required
def dashboard():
    """Dashboard principal de reportes"""
    # Obtener rango de fechas (por defecto último mes)
    fecha_fin = date.today()
    fecha_inicio = fecha_fin - timedelta(days=30)

    # Permitir filtrado personalizado
    if request.args.get('fecha_inicio'):
        fecha_inicio = datetime.strptime(request.args.get('fecha_inicio'), '%Y-%m-%d').date()
    if request.args.get('fecha_fin'):
        fecha_fin = datetime.strptime(request.args.get('fecha_fin'), '%Y-%m-%d').date()

    # Estadísticas generales
    stats = {
        'total_tutores': Usuario.query.filter_by(rol='tutor', activo=True).count(),
        'total_veterinarios': Usuario.query.filter_by(rol='veterinario', activo=True).count(),
        'total_mascotas': Mascota.query.filter_by(activo=True).count(),
        'total_citas': Cita.query.filter(
            and_(
                func.cast(Cita.fecha, db.Date) >= fecha_inicio,
                func.cast(Cita.fecha, db.Date) <= fecha_fin
            )
        ).count(),
        'total_medicamentos': Medicamento.query.filter_by(activo=True).count(),
        'valor_inventario': db.session.query(
            func.sum(Medicamento.stock_actual * Medicamento.precio_compra)
        ).filter(Medicamento.activo == True).scalar() or 0
    }

    # --- GENERACIÓN DE GRÁFICOS CON PLOTLY ---
    import plotly.express as px
    import plotly.io as pio

    # 1. Citas por estado
    citas_por_estado = db.session.query(
        Cita.estado,
        func.count(Cita.id).label('cantidad')
    ).filter(
        and_(
            func.cast(Cita.fecha, db.Date) >= fecha_inicio,
            func.cast(Cita.fecha, db.Date) <= fecha_fin
        )
    ).group_by(Cita.estado).all()

    if citas_por_estado:
        df_estado = pd.DataFrame(citas_por_estado, columns=['Estado', 'Cantidad'])
        df_estado['Estado'] = df_estado['Estado'].str.title()
        fig_estado = px.pie(df_estado, values='Cantidad', names='Estado', hole=0.45,
                            color_discrete_sequence=['#26A69A', '#FFA726', '#42A5F5', '#EF5350', '#66BB6A'])
        fig_estado.update_layout(
            margin=dict(t=20, b=20, l=20, r=20), 
            height=300,
            font=dict(family="Inter, sans-serif", size=11),
            legend=dict(orientation="h", yanchor="bottom", y=-0.15, xanchor="center", x=0.5),
            paper_bgcolor='rgba(0,0,0,0)'
        )
        fig_estado.update_traces(textposition='inside', textinfo='percent+label', textfont_size=10,
                                marker=dict(line=dict(color='#ffffff', width=2)))
        graph_estado = pio.to_html(fig_estado, full_html=False, config={'displayModeBar': False})
    else:
        graph_estado = "<div class='text-center text-muted py-5'>No hay datos disponibles</div>"

    # 2. Citas por mes (últimos 6 meses)
    hace_6_meses = fecha_fin - timedelta(days=180)
    citas_por_mes = db.session.query(
        extract('year', Cita.fecha).label('año'),
        extract('month', Cita.fecha).label('mes'),
        func.count(Cita.id).label('total')
    ).filter(
        func.cast(Cita.fecha, db.Date) >= hace_6_meses
    ).group_by(extract('year', Cita.fecha), extract('month', Cita.fecha)).order_by(extract('year', Cita.fecha), extract('month', Cita.fecha)).all()

    if citas_por_mes:
        df_mes = pd.DataFrame(citas_por_mes, columns=['Año', 'Mes', 'Total'])
        df_mes['Periodo'] = df_mes.apply(lambda x: f"{int(x['Mes'])}/{int(x['Año'])}", axis=1)
        fig_mes = px.area(df_mes, x='Periodo', y='Total', markers=True,
                          line_shape='spline')
        fig_mes.update_traces(
            line_color='#42A5F5', 
            line_width=3,
            fillcolor='rgba(66, 165, 245, 0.15)',
            marker=dict(size=8, color='#42A5F5', line=dict(width=2, color='#ffffff'))
        )
        fig_mes.update_layout(
            margin=dict(t=20, b=40, l=50, r=20), 
            height=300,
            font=dict(family="Inter, sans-serif", size=11),
            xaxis_title=None, 
            yaxis_title=None,
            plot_bgcolor='rgba(0,0,0,0)', 
            paper_bgcolor='rgba(0,0,0,0)'
        )
        fig_mes.update_xaxes(showgrid=False, tickfont=dict(size=10, color='#6c757d'))
        fig_mes.update_yaxes(showgrid=True, gridcolor='rgba(0,0,0,0.06)', tickfont=dict(size=10, color='#6c757d'))
        graph_mes = pio.to_html(fig_mes, full_html=False, config={'displayModeBar': False})
    else:
        graph_mes = "<div class='text-center text-muted py-5'>No hay datos disponibles</div>"

    # 3. Ingresos por mes
    from app.models import Pago
    ingresos_por_mes = db.session.query(
        extract('year', Pago.fecha_pago).label('año'),
        extract('month', Pago.fecha_pago).label('mes'),
        func.sum(Pago.monto).label('total')
    ).filter(
        and_(
            func.cast(Pago.fecha_pago, db.Date) >= hace_6_meses,
            Pago.estado == 'completado'
        )
    ).group_by(extract('year', Pago.fecha_pago), extract('month', Pago.fecha_pago)).order_by(extract('year', Pago.fecha_pago), extract('month', Pago.fecha_pago)).all()

    if ingresos_por_mes:
        df_ingresos = pd.DataFrame(ingresos_por_mes, columns=['Año', 'Mes', 'Total'])
        df_ingresos['Periodo'] = df_ingresos.apply(lambda x: f"{int(x['Mes'])}/{int(x['Año'])}", axis=1)
        fig_ingresos = px.bar(df_ingresos, x='Periodo', y='Total', text='Total')
        fig_ingresos.update_traces(
            marker_color='#26A69A', 
            texttemplate='Bs.%{text:.2s}', 
            textposition='outside',
            marker=dict(
                line=dict(color='rgba(0,0,0,0.1)', width=1),
                cornerradius=5
            )
        )
        fig_ingresos.update_layout(
            margin=dict(t=30, b=40, l=50, r=20), 
            height=300,
            font=dict(family="Inter, sans-serif", size=11),
            xaxis_title=None, 
            yaxis_title=None,
            plot_bgcolor='rgba(0,0,0,0)', 
            paper_bgcolor='rgba(0,0,0,0)',
            bargap=0.3
        )
        fig_ingresos.update_xaxes(showgrid=False, tickfont=dict(size=10, color='#6c757d'))
        fig_ingresos.update_yaxes(showgrid=True, gridcolor='rgba(0,0,0,0.06)', tickfont=dict(size=10, color='#6c757d'))
        graph_ingresos = pio.to_html(fig_ingresos, full_html=False, config={'displayModeBar': False})
    else:
        graph_ingresos = "<div class='text-center text-muted py-5'>No hay datos disponibles</div>"

    # Top 5 veterinarios más activos
    top_veterinarios = db.session.query(
        Usuario.id,
        Usuario.nombre,
        Usuario.apellido,
        func.count(Cita.id).label('total_citas')
    ).join(Cita, Usuario.id == Cita.veterinario_id).filter(
        and_(
            Usuario.rol == 'veterinario',
            func.cast(Cita.fecha, db.Date) >= fecha_inicio,
            func.cast(Cita.fecha, db.Date) <= fecha_fin
        )
    ).group_by(Usuario.id, Usuario.nombre, Usuario.apellido).order_by(func.count(Cita.id).desc()).limit(5).all()

    # Medicamentos con bajo stock
    medicamentos_bajo_stock = Medicamento.query.filter(
        Medicamento.stock_actual <= Medicamento.stock_minimo,
        Medicamento.activo == True
    ).count()

    return render_template(
        'admin/reportes/dashboard.html',
        stats=stats,
        graph_estado=graph_estado,
        graph_mes=graph_mes,
        graph_ingresos=graph_ingresos,
        top_veterinarios=top_veterinarios,
        medicamentos_bajo_stock=medicamentos_bajo_stock,
        fecha_inicio=fecha_inicio,
        fecha_fin=fecha_fin
    )


@reportes_bp.route('/tutores')
@admin_required
def tutores():
    """Reporte detallado de tutores y sus mascotas"""
    # Obtener todos los tutores con sus mascotas
    tutores_data = []

    tutores = Usuario.query.filter_by(rol='tutor', activo=True).order_by(Usuario.nombre).all()

    for tutor in tutores:
        mascotas_list = []
        for mascota in tutor.mascotas.filter_by(activo=True).all():
            # Contar citas por mascota
            total_citas = Cita.query.filter_by(mascota_id=mascota.id).count()

            mascotas_list.append({
                'nombre': mascota.nombre,
                'especie': mascota.especie,
                'raza': mascota.raza or 'N/A',
                'edad': mascota.edad_detallada,
                'total_citas': total_citas
            })

        tutores_data.append({
            'id': tutor.id,
            'nombre_completo': tutor.nombre_completo,
            'email': tutor.email,
            'telefono': tutor.telefono or 'N/A',
            'total_mascotas': len(mascotas_list),
            'mascotas': mascotas_list,
            'fecha_registro': tutor.fecha_registro
        })

    return render_template(
        'admin/reportes/tutores.html',
        tutores_data=tutores_data
    )


@reportes_bp.route('/veterinarios')
@admin_required
def veterinarios():
    """Reporte de desempeño de veterinarios"""
    veterinarios_data = []

    vets = Usuario.query.filter_by(rol='veterinario', activo=True).order_by(Usuario.nombre).all()

    for vet in vets:
        try:
            stats = vet.get_estadisticas_veterinario()
        except Exception as e:
            print(f"Error al obtener estadísticas del veterinario {vet.id}: {e}")
            stats = {
                'total_citas': 0,
                'citas_pendientes': 0,
                'citas_completadas': 0,
                'citas_hoy': 0,
                'pacientes_unicos': 0,
                'ingresos_mes': 0,
                'tasa_completacion': 0
            }

        veterinarios_data.append({
            'id': vet.id,
            'nombre_completo': vet.nombre_completo,
            'especialidad': vet.especialidad or 'General',
            'email': vet.email,
            'stats': stats
        })

    return render_template(
        'admin/reportes/veterinarios.html',
        veterinarios_data=veterinarios_data
    )


@reportes_bp.route('/inventario')
@admin_required
def inventario():
    """Reporte de inventario"""
    # Estadísticas de inventario
    stats = {
        'total_items': Medicamento.query.filter_by(activo=True).count(),
        'valor_total': db.session.query(
            func.sum(Medicamento.stock_actual * Medicamento.precio_compra)
        ).filter(Medicamento.activo == True).scalar() or 0,
        'bajo_stock': Medicamento.query.filter(
            Medicamento.stock_actual <= Medicamento.stock_minimo,
            Medicamento.activo == True
        ).count(),
        'por_vencer': Medicamento.query.filter(
            and_(
                Medicamento.fecha_vencimiento <= date.today() + timedelta(days=30),
                Medicamento.fecha_vencimiento > date.today(),
                Medicamento.activo == True
            )
        ).count()
    }

    # Medicamentos por categoría
    por_categoria = db.session.query(
        Medicamento.categoria,
        func.count(Medicamento.id).label('cantidad'),
        func.sum(Medicamento.stock_actual * Medicamento.precio_compra).label('valor')
    ).filter(
        Medicamento.activo == True,
        Medicamento.categoria.isnot(None)
    ).group_by(Medicamento.categoria).all()

    # Medicamentos más utilizados (basado en recetas si está disponible)
    # Por ahora mostramos los que tienen menor stock relativo
    mas_utilizados = Medicamento.query.filter_by(activo=True).order_by(
        (Medicamento.stock_actual / (Medicamento.stock_minimo + 1)).asc()
    ).limit(10).all()

    return render_template(
        'admin/reportes/inventario.html',
        stats=stats,
        por_categoria=por_categoria,
        mas_utilizados=mas_utilizados
    )


@reportes_bp.route('/citas')
@admin_required
def citas():
    """Reporte de citas"""
    # Obtener rango de fechas
    fecha_fin = date.today()
    fecha_inicio = fecha_fin - timedelta(days=30)

    if request.args.get('fecha_inicio'):
        fecha_inicio = datetime.strptime(request.args.get('fecha_inicio'), '%Y-%m-%d').date()
    if request.args.get('fecha_fin'):
        fecha_fin = datetime.strptime(request.args.get('fecha_fin'), '%Y-%m-%d').date()

    # Estadísticas de citas
    total_citas = Cita.query.filter(
        and_(
            func.cast(Cita.fecha, db.Date) >= fecha_inicio,
            func.cast(Cita.fecha, db.Date) <= fecha_fin
        )
    ).count()

    # Por estado
    por_estado = db.session.query(
        Cita.estado,
        func.count(Cita.id).label('cantidad')
    ).filter(
        and_(
            func.cast(Cita.fecha, db.Date) >= fecha_inicio,
            func.cast(Cita.fecha, db.Date) <= fecha_fin
        )
    ).group_by(Cita.estado).all()

    # Ingresos totales (desde tabla de pagos - datos reales)
    ingresos_totales = db.session.query(
        func.sum(Pago.monto)
    ).filter(
        and_(
            func.cast(Pago.fecha_pago, db.Date) >= fecha_inicio,
            func.cast(Pago.fecha_pago, db.Date) <= fecha_fin,
            Pago.estado == 'completado'
        )
    ).scalar() or 0

    # Promedio de citas por día
    dias_periodo = (fecha_fin - fecha_inicio).days + 1
    promedio_diario = total_citas / dias_periodo if dias_periodo > 0 else 0

    return render_template(
        'admin/reportes/citas.html',
        total_citas=total_citas,
        por_estado=por_estado,
        ingresos_totales=ingresos_totales,
        promedio_diario=promedio_diario,
        fecha_inicio=fecha_inicio,
        fecha_fin=fecha_fin
    )


@reportes_bp.route('/exportar/tutores')
@admin_required
def exportar_tutores():
    """Exportar reporte de tutores a Excel"""
    try:
        # Obtener datos
        tutores = Usuario.query.filter_by(rol='tutor', activo=True).all()

        data = []
        for tutor in tutores:
            mascotas_nombres = ', '.join([m.nombre for m in tutor.mascotas.filter_by(activo=True).all()])

            data.append({
                'ID': tutor.id,
                'Nombre Completo': tutor.nombre_completo,
                'Email': tutor.email,
                'Teléfono': tutor.telefono or 'N/A',
                'Dirección': tutor.direccion or 'N/A',
                'Ciudad': tutor.ciudad or 'N/A',
                'Total Mascotas': tutor.mascotas.filter_by(activo=True).count(),
                'Nombres de Mascotas': mascotas_nombres,
                'Fecha Registro': tutor.fecha_registro.strftime('%d/%m/%Y') if tutor.fecha_registro else 'N/A'
            })

        # Crear DataFrame
        df = pd.DataFrame(data)

        # Crear archivo Excel en memoria
        output = BytesIO()
        with pd.ExcelWriter(output, engine='openpyxl') as writer:
            df.to_excel(writer, sheet_name='Tutores', index=False)

        output.seek(0)

        return send_file(
            output,
            mimetype='application/vnd.openxmlformats-officedocument.spreadsheetml.sheet',
            as_attachment=True,
            download_name=f'reporte_tutores_{date.today().strftime("%Y%m%d")}.xlsx'
        )

    except Exception as e:
        flash(f'Error al exportar: {str(e)}', 'danger')
        return redirect(url_for('reportes.tutores'))


@reportes_bp.route('/exportar/inventario')
@admin_required
def exportar_inventario():
    """Exportar reporte de inventario a Excel"""
    try:
        medicamentos = Medicamento.query.filter_by(activo=True).all()

        data = []
        for med in medicamentos:
            data.append({
                'Código': med.codigo or 'N/A',
                'Nombre': med.nombre,
                'Principio Activo': med.principio_activo or 'N/A',
                'Categoría': med.categoria or 'N/A',
                'Presentación': med.presentacion or 'N/A',
                'Stock Actual': med.stock_actual,
                'Stock Mínimo': med.stock_minimo,
                'Unidad': med.unidad_medida or 'N/A',
                'Precio Compra': med.precio_compra or 0,
                'Precio Venta': med.precio_venta or 0,
                'Laboratorio': med.laboratorio or 'N/A',
                'Lote': med.lote or 'N/A',
                'Vencimiento': med.fecha_vencimiento.strftime('%d/%m/%Y') if med.fecha_vencimiento else 'N/A',
                'Estado Stock': 'BAJO' if med.necesita_restock else 'OK',
                'Vencido': 'SÍ' if med.esta_vencido else 'NO'
            })

        df = pd.DataFrame(data)

        output = BytesIO()
        with pd.ExcelWriter(output, engine='openpyxl') as writer:
            df.to_excel(writer, sheet_name='Inventario', index=False)

        output.seek(0)

        return send_file(
            output,
            mimetype='application/vnd.openxmlformats-officedocument.spreadsheetml.sheet',
            as_attachment=True,
            download_name=f'reporte_inventario_{date.today().strftime("%Y%m%d")}.xlsx'
        )

    except Exception as e:
        flash(f'Error al exportar: {str(e)}', 'danger')
        return redirect(url_for('reportes.inventario'))
