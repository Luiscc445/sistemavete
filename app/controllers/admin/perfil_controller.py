from flask import Blueprint, render_template, request, flash, redirect, url_for
from flask_login import login_required, current_user
from app import db
from app.controllers.admin.utils import admin_required

perfil_bp = Blueprint('admin_perfil', __name__)

@perfil_bp.route('/perfil', methods=['GET', 'POST'])
@login_required
@admin_required
def ver_perfil():
    return render_template('admin/perfil.html')
