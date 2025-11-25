"""
Configuración de la aplicación Flask Veterinaria
"""
import os
from datetime import timedelta
from dotenv import load_dotenv
from urllib.parse import quote_plus

# Cargar variables de entorno
load_dotenv()

class Config:
    """Configuración base"""
    # Configuración de la aplicación
    SECRET_KEY = os.environ.get('SECRET_KEY') or 'dev-secret-key-change-in-production'
    
    # Configuración de la base de datos
    SQLALCHEMY_DATABASE_URI = os.environ.get('DATABASE_URL') or 'sqlite:///veterinaria.db'
    SQLALCHEMY_TRACK_MODIFICATIONS = False
    SQLALCHEMY_ECHO = False
    
    # Configuración de sesión
    PERMANENT_SESSION_LIFETIME = timedelta(hours=24)
    SESSION_COOKIE_SECURE = True
    SESSION_COOKIE_HTTPONLY = True
    SESSION_COOKIE_SAMESITE = 'Lax'
    
    # Configuración de Flask-Login
    LOGIN_VIEW = 'auth.login'
    LOGIN_MESSAGE = 'Por favor, inicia sesión para acceder a esta página.'
    LOGIN_MESSAGE_CATEGORY = 'info'
    
    # Configuración de correo
    MAIL_SERVER = os.environ.get('MAIL_SERVER') or 'smtp.gmail.com'
    MAIL_PORT = int(os.environ.get('MAIL_PORT') or 587)
    MAIL_USE_TLS = os.environ.get('MAIL_USE_TLS', 'true').lower() in ['true', 'on', '1']
    MAIL_USERNAME = os.environ.get('MAIL_USERNAME')
    MAIL_PASSWORD = os.environ.get('MAIL_PASSWORD')
    MAIL_DEFAULT_SENDER = os.environ.get('MAIL_DEFAULT_SENDER') or 'noreply@veterinaria.com'
    
    # Configuración de uploads
    UPLOAD_FOLDER = os.path.join(os.path.dirname(os.path.abspath(__file__)), 'uploads')
    MAX_CONTENT_LENGTH = 16 * 1024 * 1024  # 16MB max file size
    ALLOWED_EXTENSIONS = {'png', 'jpg', 'jpeg', 'gif', 'pdf', 'doc', 'docx'}
    
    # Configuración de paginación
    ITEMS_PER_PAGE = 10
    
    # Configuración de la aplicación
    APP_NAME = 'Rambopet'
    APP_VERSION = '2.0.0'
    APP_DESCRIPTION = 'Sistema de Gestión Veterinaria Profesional'
    
    # Colores corporativos
    PRIMARY_COLOR = '#2563eb'  # Azul profesional
    SECONDARY_COLOR = '#10b981'  # Verde médico
    DANGER_COLOR = '#ef4444'
    WARNING_COLOR = '#f59e0b'
    INFO_COLOR = '#3b82f6'
    SUCCESS_COLOR = '#22c55e'
    
    # Configuración de notificaciones
    ENABLE_NOTIFICATIONS = True
    NOTIFICATION_TIMEOUT = 5000  # 5 segundos

class DevelopmentConfig(Config):
    """Configuración de desarrollo (SQLite)"""
    DEBUG = True
    SQLALCHEMY_ECHO = True
    SQLALCHEMY_DATABASE_URI = 'sqlite:///veterinaria.db'

class DevelopmentSQLServerConfig(Config):
    """Configuración de desarrollo con SQL Server"""
    DEBUG = True
    SQLALCHEMY_ECHO = True
    
    # SQL Server Configuration
    # --- CORRECCIÓN ---
    # Se usa el driver ODBC moderno en lugar del driver antiguo
    SQLSERVER_DRIVER = '{ODBC Driver 17 for SQL Server}'
    SQLSERVER_SERVER = r'LUIS_CARLOS69\SQLDEV'
    SQLSERVER_DATABASE = 'VeterinariaDB'
    
    # Construir cadena de conexión
    connection_params = (
        f'DRIVER={SQLSERVER_DRIVER};'
        f'SERVER={SQLSERVER_SERVER};'
        f'DATABASE={SQLSERVER_DATABASE};'
        f'Trusted_Connection=yes;'
        f'TrustServerCertificate=yes;'
    )
    
    SQLALCHEMY_DATABASE_URI = f'mssql+pyodbc:///?odbc_connect={quote_plus(connection_params)}'
    SQLALCHEMY_ENGINE_OPTIONS = {
        'pool_pre_ping': True,
        'pool_recycle': 3600,
    }
    
class ProductionConfig(Config):
    """Configuración de producción con SQL Server"""
    DEBUG = False
    SESSION_COOKIE_SECURE = True
    
    # SQL Server Configuration
    # --- CORRECCIÓN ---
    # Se usa el driver ODBC moderno en lugar del driver antiguo
    SQLSERVER_DRIVER = '{ODBC Driver 17 for SQL Server}'
    SQLSERVER_SERVER = r'LUIS_CARLOS69\SQLDEV'
    SQLSERVER_DATABASE = 'VeterinariaDB'
    
    # Construir cadena de conexión
    connection_params = (
        f'DRIVER={SQLSERVER_DRIVER};'
        f'SERVER={SQLSERVER_SERVER};'
        f'DATABASE={SQLSERVER_DATABASE};'
        f'Trusted_Connection=yes;'
        f'TrustServerCertificate=yes;'
    )
    
    SQLALCHEMY_DATABASE_URI = f'mssql+pyodbc:///?odbc_connect={quote_plus(connection_params)}'
    SQLALCHEMY_ENGINE_OPTIONS = {
        'pool_pre_ping': True,
        'pool_recycle': 3600,
        'pool_size': 10,
        'max_overflow': 20
    }
    
    @classmethod
    def init_app(cls, app):
        Config.init_app(app)
        
        # Log to syslog
        import logging
        from logging.handlers import SysLogHandler
        
        syslog_handler = SysLogHandler()
        syslog_handler.setLevel(logging.WARNING)
        app.logger.addHandler(syslog_handler)

class TestingConfig(Config):
    """Configuración de pruebas"""
    TESTING = True
    SQLALCHEMY_DATABASE_URI = 'sqlite:///:memory:'
    WTF_CSRF_ENABLED = False

class SQLServerConfig(Config):
    """
    Configuración flexible para SQL Server
    
    Puede configurarse mediante variables de entorno o usar valores por defecto.
    
    Variables de entorno opcionales:
    - SQLSERVER_DRIVER: Driver ODBC (default: {ODBC Driver 17 for SQL Server})
    - SQLSERVER_SERVER: Servidor (ejemplo: SERVIDOR\\INSTANCIA)
    - SQLSERVER_DATABASE: Base de datos (default: VeterinariaDB)
    - SQLSERVER_USERNAME: Usuario (si no usa Windows Auth)
    - SQLSERVER_PASSWORD: Contraseña (si no usa Windows Auth)
    - SQLSERVER_TRUSTED: true para Windows Auth (default: true)
    """

    @staticmethod
    def get_sqlserver_uri():
        """Construye la URI de SQL Server desde variables de entorno o valores por defecto"""
        # --- CORRECCIÓN ---
        # Se usa el driver ODBC moderno como valor por defecto
        driver = os.environ.get('SQLSERVER_DRIVER', '{ODBC Driver 17 for SQL Server}')
        server = os.environ.get('SQLSERVER_SERVER', r'LUIS_CARLOS69\SQLDEV')
        database = os.environ.get('SQLSERVER_DATABASE', 'VeterinariaDB')
        username = os.environ.get('SQLSERVER_USERNAME')
        password = os.environ.get('SQLSERVER_PASSWORD')
        trusted = os.environ.get('SQLSERVER_TRUSTED', 'true').lower() == 'true'

        # Autenticación de Windows (por defecto)
        if trusted:
            connection_params = (
                f'DRIVER={driver};'
                f'SERVER={server};'
                f'DATABASE={database};'
                f'Trusted_Connection=yes;'
                f'TrustServerCertificate=yes;'
            )
            return f'mssql+pyodbc:///?odbc_connect={quote_plus(connection_params)}'

        # Autenticación con usuario y contraseña
        if username and password:
            connection_params = (
                f'DRIVER={driver};'
                f'SERVER={server};'
                f'DATABASE={database};'
                f'UID={username};'
                f'PWD={password};'
                f'TrustServerCertificate=yes;'
            )
            return f'mssql+pyodbc:///?odbc_connect={quote_plus(connection_params)}'

        # Fallback a SQLite si no hay configuración completa
        return 'sqlite:///veterinaria.db'

    SQLALCHEMY_DATABASE_URI = get_sqlserver_uri.__func__()
    SQLALCHEMY_ENGINE_OPTIONS = {
        'pool_pre_ping': True,
        'pool_recycle': 3600,
        'echo_pool': False
    }

# Diccionario de configuraciones
config = {
    'development': DevelopmentConfig,
    'development_sqlserver': DevelopmentSQLServerConfig,
    'production': ProductionConfig,
    'testing': TestingConfig,
    'sqlserver': SQLServerConfig,
    'default': DevelopmentSQLServerConfig
}

def get_config(config_name=None):
    """Obtener configuración por nombre o variable de entorno"""
    if config_name is None:
        config_name = os.environ.get('FLASK_CONFIG', 'default')
    return config.get(config_name, config['default'])