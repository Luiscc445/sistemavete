"""
Controlador para Mascotas
"""
from flask import Blueprint, render_template, redirect, url_for, flash
from app import db
from app.models import Mascota, HistorialClinico, Vacuna, Cita, DocumentoMascota
from .utils import admin_required, registrar_auditoria

mascotas_bp = Blueprint('admin_mascotas', __name__)

@mascotas_bp.route('/mascota/<int:mascota_id>')
@admin_required
def ver(mascota_id):
    """Ver detalles completos de una mascota"""
    mascota = Mascota.query.get_or_404(mascota_id)
    
    historiales = mascota.historiales.order_by(HistorialClinico.fecha.desc()).limit(10).all()
    vacunas = mascota.vacunas.order_by(Vacuna.fecha_aplicacion.desc()).all()
    citas = mascota.citas.order_by(Cita.fecha.desc()).limit(10).all()
    documentos = mascota.documentos.order_by(DocumentoMascota.fecha_subida.desc()).all()
    
    registrar_auditoria('ver_mascota', 'mascota', mascota_id, 
                       f'Visualización de mascota: {mascota.nombre}')
    db.session.commit()
    
    return render_template('admin/mascotas/ver.html',
                         mascota=mascota,
                         historiales=historiales,
                         vacunas=vacunas,
                         citas=citas,
                         documentos=documentos)
