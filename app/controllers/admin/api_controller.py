"""
Controlador de APIs para Estadísticas
"""
from flask import Blueprint, jsonify
from datetime import datetime
from sqlalchemy import func
from app import db
from app.models import Mascota
from .utils import admin_required

api_bp = Blueprint('admin_api', __name__)

@api_bp.route('/api/estadisticas/citas-mes')
@admin_required
def estadisticas_citas_mes():
    """API para obtener estadísticas de citas del mes actual"""
    mes_actual = datetime.now().month
    año_actual = datetime.now().year
    
    dias_mes = []
    # (Lógica para obtener citas por día)
    
    return jsonify(dias_mes)

@api_bp.route('/api/estadisticas/especies')
@admin_required
def estadisticas_especies():
    """API para obtener distribución de especies"""
    especies = db.session.query(
        Mascota.especie,
        func.count(Mascota.id).label('cantidad')
    ).filter(Mascota.activo == True).group_by(Mascota.especie).all()
    
    return jsonify([{
        'especie': e.especie,
        'cantidad': e.cantidad
    } for e in especies])
