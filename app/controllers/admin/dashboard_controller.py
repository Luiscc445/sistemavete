"""
Controlador del Dashboard de Administración
"""
from flask import Blueprint, render_template
from datetime import datetime, date
from sqlalchemy import func
from app import db
from app.models import Usuario, Mascota, Cita
from .utils import admin_required

dashboard_bp = Blueprint('admin', __name__)

@dashboard_bp.route('/dashboard')
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
            'total_citas': Cita.query.count(),
            'citas_pendientes': Cita.query.filter_by(estado='pendiente').count(),
            'citas_hoy': Cita.query.filter(func.cast(Cita.fecha, db.Date) == date.today()).count()
        }
        
        # Últimos tutores registrados
        ultimos_tutores = Usuario.query.filter_by(rol='tutor').order_by(Usuario.fecha_registro.desc()).limit(5).all()
        
        # Próximas citas de hoy
        proximas_citas = Cita.query.filter(
            func.cast(Cita.fecha, db.Date) == date.today(),
            Cita.estado.in_(['pendiente', 'confirmada'])
        ).order_by(Cita.fecha).limit(10).all()
        
    except Exception as e:
        from flask import flash
        flash(f'Error al cargar el dashboard: {e}', 'danger')
        print(f"Error en dashboard: {e}")
    
    return render_template('dashboards/admin/admin_dashboard.html',
                         stats=stats,
                         ultimos_tutores=ultimos_tutores,
                         proximas_citas=proximas_citas)
