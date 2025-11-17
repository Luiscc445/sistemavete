"""
Script de diagnóstico para identificar problemas de SQL Server con auditoría
"""
import sys
import os

# Agregar el directorio raíz al path
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

from app import create_app, db
from sqlalchemy import text, inspect
import json

def main():
    print("=" * 80)
    print("DIAGNÓSTICO DE SQL SERVER - Sistema Veterinaria")
    print("=" * 80)
    print()

    app = create_app()

    with app.app_context():
        # 1. Verificar conexión
        print("1. VERIFICANDO CONEXIÓN A SQL SERVER...")
        try:
            result = db.session.execute(text("SELECT @@VERSION"))
            version = result.fetchone()[0]
            print(f"   ✓ Conectado a: {version.split(chr(10))[0]}")
        except Exception as e:
            print(f"   ✗ Error de conexión: {e}")
            return

        print()

        # 2. Verificar estructura de tabla auditoria_acciones
        print("2. VERIFICANDO ESTRUCTURA DE TABLA 'auditoria_acciones'...")
        try:
            inspector = inspect(db.engine)
            columns = inspector.get_columns('auditoria_acciones')

            campos_texto = ['descripcion', 'datos_anteriores', 'datos_nuevos', 'user_agent']

            for col in columns:
                if col['name'] in campos_texto:
                    tipo = str(col['type'])
                    nullable = col['nullable']
                    print(f"   - {col['name']}: {tipo} (Nullable: {nullable})")

                    # Verificar que campos de texto sean NVARCHAR(MAX)
                    if col['name'] in ['descripcion', 'datos_anteriores', 'datos_nuevos']:
                        if 'TEXT' not in tipo.upper() and 'MAX' not in tipo.upper():
                            print(f"     ⚠ PROBLEMA: Este campo debería ser NVARCHAR(MAX), es {tipo}")

                    # Verificar que user_agent tenga tamaño suficiente
                    if col['name'] == 'user_agent':
                        if '200' in tipo:
                            print(f"     ⚠ ADVERTENCIA: User-Agent limitado a 200 chars")
        except Exception as e:
            print(f"   ✗ Error al inspeccionar tabla: {e}")

        print()

        # 3. Probar INSERT con datos de prueba
        print("3. PROBANDO INSERT EN auditoria_acciones...")

        test_cases = [
            {
                'nombre': 'Con datos vacíos (strings vacíos)',
                'datos': {
                    'usuario_id': 1,
                    'accion': 'test',
                    'entidad': 'test',
                    'entidad_id': 1,
                    'descripcion': 'Test de diagnóstico',
                    'datos_anteriores': '',  # String vacío
                    'datos_nuevos': '',      # String vacío
                    'ip_address': '127.0.0.1',
                    'user_agent': 'Test/1.0'
                }
            },
            {
                'nombre': 'Con datos NULL explícitos',
                'datos': {
                    'usuario_id': 1,
                    'accion': 'test',
                    'entidad': 'test',
                    'entidad_id': 1,
                    'descripcion': 'Test de diagnóstico',
                    'datos_anteriores': None,  # NULL
                    'datos_nuevos': None,      # NULL
                    'ip_address': '127.0.0.1',
                    'user_agent': 'Test/1.0'
                }
            }
        ]

        for test in test_cases:
            print(f"\n   Probando: {test['nombre']}")
            try:
                # Construir query INSERT
                cols = ', '.join(test['datos'].keys())
                placeholders = ', '.join([f":{k}" for k in test['datos'].keys()])
                query = f"INSERT INTO auditoria_acciones ({cols}) OUTPUT inserted.id VALUES ({placeholders})"

                result = db.session.execute(text(query), test['datos'])
                inserted_id = result.fetchone()[0]
                print(f"   ✓ INSERT exitoso. ID: {inserted_id}")

                # Limpiar el registro de prueba
                db.session.execute(text(f"DELETE FROM auditoria_acciones WHERE id = {inserted_id}"))
                db.session.commit()

            except Exception as e:
                print(f"   ✗ FALLÓ: {str(e)}")
                db.session.rollback()

        print()

        # 4. Verificar archivo admin_controller.py actual
        print("4. VERIFICANDO CÓDIGO DE admin_controller.py...")
        try:
            controller_path = os.path.join(os.path.dirname(__file__), 'app', 'controllers', 'admin_controller.py')
            with open(controller_path, 'r', encoding='utf-8') as f:
                content = f.read()

                # Buscar la función registrar_auditoria
                if "else ''" in content:
                    print("   ✓ Código tiene el fix (usa string vacío '')")
                elif "else None" in content:
                    print("   ✗ PROBLEMA: Código sigue usando 'else None'")
                    print("   ⚠ Necesitas hacer 'git pull' y reiniciar la aplicación")

                # Buscar línea específica
                lines = content.split('\n')
                for i, line in enumerate(lines, 1):
                    if 'datos_ant_str = ' in line or 'datos_new_str = ' in line:
                        print(f"   Línea {i}: {line.strip()}")
        except Exception as e:
            print(f"   ✗ Error al leer archivo: {e}")

        print()

        # 5. Recomendaciones
        print("=" * 80)
        print("RECOMENDACIONES:")
        print("=" * 80)

        print("""
Si los tests fallaron con strings vacíos (''):
  → SOLUCIÓN 1: Usar NULL en lugar de string vacío
    Modifica admin_controller.py líneas 50-51:
    datos_ant_str = json.dumps(datos_anteriores) if datos_anteriores else None
    datos_new_str = json.dumps(datos_nuevos) if datos_nuevos else None

    Y marca las columnas como nullable en el modelo.

Si el código no tiene el fix:
  → SOLUCIÓN 2: Hacer git pull en el directorio correcto
    1. Ve al directorio donde EJECUTAS la app
    2. Ejecuta: git pull
    3. Reinicia la aplicación Flask completamente

Si user_agent es muy largo:
  → SOLUCIÓN 3: Truncar user_agent a 200 caracteres
    Modifica la línea que asigna user_agent

Si descripcion, datos_anteriores o datos_nuevos no son NVARCHAR(MAX):
  → SOLUCIÓN 4: Ejecutar ALTER TABLE
    ALTER TABLE auditoria_acciones ALTER COLUMN descripcion NVARCHAR(MAX);
    ALTER TABLE auditoria_acciones ALTER COLUMN datos_anteriores NVARCHAR(MAX);
    ALTER TABLE auditoria_acciones ALTER COLUMN datos_nuevos NVARCHAR(MAX);
        """)

if __name__ == '__main__':
    main()
