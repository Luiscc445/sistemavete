"""
Modulo de Administracion - Inicializador
Registra todos los blueprints del modulo admin
"""
from .dashboard_controller import dashboard_bp
from .tutores_controller import tutores_bp
from .veterinarios_controller import veterinarios_bp
from .mascotas_controller import mascotas_bp
from .api_controller import api_bp
from .inventario_controller import inventario_bp
from .pagos_controller import pagos_bp
from .reportes_controller import reportes_bp
from .perfil_controller import perfil_bp
from .servicios_controller import servicios_bp

def register_admin_blueprints(app):
    """Registra todos los blueprints del modulo admin"""
    # Registrar blueprints con el prefijo /admin
    app.register_blueprint(dashboard_bp, url_prefix='/admin')
    app.register_blueprint(tutores_bp, url_prefix='/admin')
    app.register_blueprint(veterinarios_bp, url_prefix='/admin')
    app.register_blueprint(mascotas_bp, url_prefix='/admin')
    app.register_blueprint(api_bp, url_prefix='/admin')
    
    # Nuevos modulos administrativos movidos
    app.register_blueprint(inventario_bp, url_prefix='/admin/inventario')
    app.register_blueprint(pagos_bp, url_prefix='/admin/pagos')
    app.register_blueprint(reportes_bp, url_prefix='/admin/reportes')
    app.register_blueprint(perfil_bp, url_prefix='/admin')
    app.register_blueprint(servicios_bp, url_prefix='/admin')
    
    print("[OK] Modulo admin registrado correctamente")
