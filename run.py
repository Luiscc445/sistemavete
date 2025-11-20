"""
Punto de entrada de la aplicación Flask Veterinaria
"""
import os
from app import create_app, db, init_database
from app.models import *

# Obtener configuración del entorno
# CORRECCIÓN: Leer 'FLASK_CONFIG' y usar 'default' (SQL Server) como fallback
config_name = os.getenv('FLASK_CONFIG', 'default')

# Crear la aplicación
app = create_app(config_name)

# Contexto de la aplicación
with app.app_context():
    # Crear todas las tablas
    db.create_all()
    
    # Inicializar datos de ejemplo
    init_database()
    
    print(f"""
    ========================================
    Sistema Veterinario v2.0.0
    ========================================
    Configuración: {config_name}
    Base de datos: {app.config['SQLALCHEMY_DATABASE_URI']}
    
    Credenciales de acceso:
    - Usuario: admin
    - Contraseña: admin123
    
    Servidor iniciado en: http://localhost:5000
    ========================================
    """)

if __name__ == '__main__':
    # Ejecutar la aplicación
    app.run(
        host='0.0.0.0',
        port=5000,
        # El debug se tomará de la configuración (ya está en 'default')
        debug=app.config.get('DEBUG', False) 
    )