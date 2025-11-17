#!/usr/bin/env python
"""
Script de Verificación - Verifica que la base de datos esté lista
"""
import os
import sys

sys.path.insert(0, os.path.abspath(os.path.dirname(__file__)))

from app import create_app, db
from sqlalchemy import text

def verificar():
    """Verifica el estado de la base de datos"""
    print()
    print("=" * 70)
    print("🔍 VERIFICACIÓN DE BASE DE DATOS")
    print("=" * 70)
    print()

    app = create_app()

    with app.app_context():
        try:
            # Consultar directamente la estructura de la tabla
            print("📊 Consultando columnas de la tabla 'pagos'...")
            print()

            result = db.session.execute(text("""
                SELECT COLUMN_NAME, DATA_TYPE, IS_NULLABLE, COLUMN_DEFAULT
                FROM INFORMATION_SCHEMA.COLUMNS
                WHERE TABLE_NAME = 'pagos'
                ORDER BY ORDINAL_POSITION
            """))

            columnas = result.fetchall()

            # Columnas requeridas
            requeridas = ['veterinario_id', 'porcentaje_empresa', 'porcentaje_veterinario',
                         'monto_empresa', 'monto_veterinario']

            columnas_encontradas = [col[0] for col in columnas]

            print("✅ Columnas en la tabla 'pagos':")
            for col in columnas:
                nombre = col[0]
                tipo = col[1]
                nullable = col[2]
                default = col[3] or 'NULL'

                if nombre in requeridas:
                    print(f"   ✓ {nombre:25} {tipo:10} Nullable:{nullable:3} Default:{default}")

            print()
            print("🔍 Verificando columnas requeridas:")
            print()

            todas_ok = True
            for col in requeridas:
                if col in columnas_encontradas:
                    print(f"   ✅ {col}")
                else:
                    print(f"   ❌ {col} - FALTA")
                    todas_ok = False

            print()

            # Verificar datos
            print("📈 Estado de los datos:")
            print()

            total = db.session.execute(text("SELECT COUNT(*) FROM pagos")).scalar()
            print(f"   Total de pagos: {total}")

            con_vet = db.session.execute(text("""
                SELECT COUNT(*) FROM pagos WHERE veterinario_id IS NOT NULL
            """)).scalar()
            print(f"   Pagos con veterinario: {con_vet}")

            con_division = db.session.execute(text("""
                SELECT COUNT(*) FROM pagos
                WHERE monto_empresa > 0 AND monto_veterinario > 0
            """)).scalar()
            print(f"   Pagos con división: {con_division}")

            print()

            # Verificar foreign keys
            print("🔗 Verificando foreign keys:")
            print()

            fks = db.session.execute(text("""
                SELECT name FROM sys.foreign_keys
                WHERE parent_object_id = OBJECT_ID('pagos')
            """)).fetchall()

            for fk in fks:
                print(f"   ✅ {fk[0]}")

            print()

            # Resultado final
            if todas_ok:
                print("=" * 70)
                print("✅ BASE DE DATOS LISTA PARA USAR")
                print("=" * 70)
                print()
                print("Puedes reiniciar Flask y probar el sistema:")
                print("  python run.py")
                print()
                return True
            else:
                print("=" * 70)
                print("⚠️  FALTAN COLUMNAS")
                print("=" * 70)
                print()
                print("Ejecuta este SQL en SQL Server Management Studio:")
                print()
                print("ALTER TABLE pagos ADD veterinario_id INT NULL;")
                print("ALTER TABLE pagos ADD CONSTRAINT FK_pagos_veterinario")
                print("    FOREIGN KEY (veterinario_id) REFERENCES usuarios(id);")
                print()
                return False

        except Exception as e:
            print()
            print("=" * 70)
            print("❌ ERROR")
            print("=" * 70)
            print(f"Error: {str(e)}")
            print()
            import traceback
            traceback.print_exc()
            return False


if __name__ == '__main__':
    try:
        exito = verificar()
        sys.exit(0 if exito else 1)
    except Exception as e:
        print(f"\n❌ Error: {e}")
        sys.exit(1)
