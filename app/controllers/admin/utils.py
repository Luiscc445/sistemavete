"""
Utilidades compartidas para el módulo de administración
"""
from flask import flash, redirect, url_for, request
from flask_login import login_required, current_user
from functools import wraps
from app import db
from app.models import AuditoriaAccion

# --- LISTA DE ESPECIALIDADES VETERINARIAS ---
LISTA_ESPECIALIDADES = [
    'Medicina General',
    'Cirugía',
    'Dermatología',
    'Cardiología',
    'Oncología',
    'Animales Exóticos',
    'Fisioterapia'
]

def admin_required(f):
    """Decorador para requerir rol de administrador"""
    @wraps(f)
    @login_required
    def decorated_function(*args, **kwargs):
        if not current_user.is_admin():
            flash('No tienes permisos para acceder a esta página', 'danger')
            return redirect(url_for('index'))
        return f(*args, **kwargs)
    return decorated_function

def registrar_auditoria(accion, entidad, entidad_id, descripcion, datos_anteriores=None, datos_nuevos=None):
    """Registra una acción en el sistema de auditoría"""
    import json
    try:
        # Convertir datos a JSON string si no son None
        datos_ant_str = json.dumps(datos_anteriores) if datos_anteriores is not None else None
        datos_new_str = json.dumps(datos_nuevos) if datos_nuevos is not None else None
        
        # Obtener user agent de forma segura
        user_agent = request.headers.get('User-Agent', 'Unknown')[:255] if request and hasattr(request, 'headers') else None
        
        auditoria = AuditoriaAccion(
            usuario_id=current_user.id,
            accion=accion,
            entidad=entidad,
            entidad_id=entidad_id,
            descripcion=descripcion,
            datos_anteriores=datos_ant_str,
            datos_nuevos=datos_new_str,
            ip_address=request.remote_addr if request and hasattr(request, 'remote_addr') else None,
            user_agent=user_agent
        )
        db.session.add(auditoria)
        # El commit se hará junto con la operación principal
    except Exception as e:
        print(f"Error al registrar auditoria: {e}")
