#!/usr/bin/env python
"""
Script para agregar columnas de comisión a la tabla pagos
Ejecutar con: python migrar_columnas_comision.py
"""
import os
import sys

# Añadir el directorio raíz al path
sys.path.insert(0, os.path.abspath(os.path.dirname(__file__)))

# Importar la aplicación Flask
from app import create_app, db
from sqlalchemy import text, inspect
from sqlalchemy.exc import SQLAlchemyError

def ejecutar_migracion():
    """Ejecuta la migración de columnas de comisión"""
    print("=" * 60)
    print("MIGRACIÓN: Agregar Columnas de Comisión a Pagos")
    print("=" * 60)

    # Crear aplicación
    app = create_app()

    with app.app_context():
        # Inspeccionar la tabla pagos
        inspector = inspect(db.engine)

        if 'pagos' not in inspector.get_table_names():
            print("✗ Error: La tabla 'pagos' no existe")
            return False

        columnas_existentes = [col['name'] for col in inspector.get_columns('pagos')]
        print(f"\nColumnas existentes en 'pagos': {', '.join(columnas_existentes)}\n")

        # Lista de columnas a agregar
        columnas_nuevas = {
            'veterinario_id': {
                'sql': "ALTER TABLE pagos ADD veterinario_id INT NULL",
                'descripcion': 'ID del veterinario que atendió'
            },
            'porcentaje_empresa': {
                'sql': "ALTER TABLE pagos ADD porcentaje_empresa FLOAT DEFAULT 57.14",
                'descripcion': 'Porcentaje para la empresa'
            },
            'porcentaje_veterinario': {
                'sql': "ALTER TABLE pagos ADD porcentaje_veterinario FLOAT DEFAULT 42.86",
                'descripcion': 'Porcentaje para el veterinario'
            },
            'monto_empresa': {
                'sql': "ALTER TABLE pagos ADD monto_empresa FLOAT DEFAULT 0",
                'descripcion': 'Monto que va para la empresa'
            },
            'monto_veterinario': {
                'sql': "ALTER TABLE pagos ADD monto_veterinario FLOAT DEFAULT 0",
                'descripcion': 'Monto que va para el veterinario'
            }
        }

        # Agregar cada columna
        columnas_agregadas = []
        columnas_existian = []

        for columna, info in columnas_nuevas.items():
            if columna in columnas_existentes:
                print(f"⚠  La columna '{columna}' ya existe - Saltando")
                columnas_existian.append(columna)
            else:
                try:
                    db.session.execute(text(info['sql']))
                    db.session.commit()
                    print(f"✓  Columna '{columna}' agregada - {info['descripcion']}")
                    columnas_agregadas.append(columna)
                except SQLAlchemyError as e:
                    print(f"✗  Error al agregar columna '{columna}': {e}")
                    db.session.rollback()

        # Actualizar registros existentes (calcular división de ingresos)
        if columnas_agregadas or 'monto_empresa' in columnas_existentes:
            print("\n" + "=" * 60)
            print("Actualizando registros existentes...")
            print("=" * 60)

            try:
                # Actualizar veterinario_id de pagos existentes basándose en citas
                if 'veterinario_id' in columnas_agregadas or 'veterinario_id' in columnas_existentes:
                    update_vet_sql = """
                    UPDATE p
                    SET p.veterinario_id = c.veterinario_id
                    FROM pagos p
                    INNER JOIN citas c ON p.cita_id = c.id
                    WHERE p.veterinario_id IS NULL
                      AND c.veterinario_id IS NOT NULL
                    """
                    result_vet = db.session.execute(text(update_vet_sql))
                    db.session.commit()
                    print(f"✓  {result_vet.rowcount} pagos actualizados con veterinario_id")

                # Actualizar monto_empresa y monto_veterinario basados en los porcentajes
                update_sql = """
                UPDATE pagos
                SET
                    monto_empresa = monto * (porcentaje_empresa / 100),
                    monto_veterinario = monto * (porcentaje_veterinario / 100)
                WHERE monto_empresa = 0 OR monto_veterinario = 0
                """
                result = db.session.execute(text(update_sql))
                db.session.commit()
                print(f"✓  {result.rowcount} registros actualizados con división de ingresos")
            except SQLAlchemyError as e:
                print(f"✗  Error al actualizar registros: {e}")
                db.session.rollback()

        # Resumen
        print("\n" + "=" * 60)
        print("RESUMEN DE LA MIGRACIÓN")
        print("=" * 60)
        print(f"✓ Columnas agregadas: {len(columnas_agregadas)}")
        if columnas_agregadas:
            for col in columnas_agregadas:
                print(f"  - {col}")

        print(f"\n⚠ Columnas que ya existían: {len(columnas_existian)}")
        if columnas_existian:
            for col in columnas_existian:
                print(f"  - {col}")

        print("\n" + "=" * 60)
        print("División de Ingresos Configurada:")
        print("  - Empresa: 57.14% (por defecto)")
        print("  - Veterinario: 42.86% (por defecto)")
        print("=" * 60)

        print("\n✓ Migración completada exitosamente\n")
        return True


if __name__ == '__main__':
    try:
        exito = ejecutar_migracion()
        sys.exit(0 if exito else 1)
    except KeyboardInterrupt:
        print("\n\n✗ Migración cancelada por el usuario")
        sys.exit(1)
    except Exception as e:
        print(f"\n✗ Error inesperado: {e}")
        import traceback
        traceback.print_exc()
        sys.exit(1)
