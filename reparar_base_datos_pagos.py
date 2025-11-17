#!/usr/bin/env python
"""
Script de Reparación de Base de Datos - Sistema de Pagos
Verifica y corrige automáticamente la estructura de la tabla pagos
"""
import os
import sys

# Añadir el directorio raíz al path
sys.path.insert(0, os.path.abspath(os.path.dirname(__file__)))

# Importar la aplicación Flask
from app import create_app, db
from sqlalchemy import text, inspect
from sqlalchemy.exc import SQLAlchemyError

def verificar_y_reparar():
    """Verifica y repara la base de datos de pagos"""
    print("=" * 70)
    print("SCRIPT DE REPARACIÓN DE BASE DE DATOS - SISTEMA DE PAGOS")
    print("=" * 70)
    print()

    # Crear aplicación
    app = create_app()

    with app.app_context():
        try:
            # Paso 1: Verificar conexión
            print("📡 Paso 1: Verificando conexión a la base de datos...")
            db.session.execute(text("SELECT 1"))
            print("✅ Conexión exitosa")
            print()

            # Paso 2: Verificar existencia de tabla pagos
            print("📋 Paso 2: Verificando tabla 'pagos'...")
            inspector = inspect(db.engine)
            tablas = inspector.get_table_names()

            if 'pagos' not in tablas:
                print("❌ ERROR: La tabla 'pagos' no existe")
                print("   Por favor, ejecuta primero las migraciones principales del sistema")
                return False

            print("✅ Tabla 'pagos' existe")
            print()

            # Paso 3: Obtener columnas actuales
            print("🔍 Paso 3: Inspeccionando columnas actuales...")
            columnas_actuales = [col['name'] for col in inspector.get_columns('pagos')]
            print(f"   Columnas encontradas: {len(columnas_actuales)}")
            print(f"   {', '.join(columnas_actuales[:10])}...")
            print()

            # Paso 4: Definir columnas requeridas
            print("📝 Paso 4: Verificando columnas requeridas...")
            columnas_requeridas = {
                'veterinario_id': {
                    'tipo': 'INT',
                    'nullable': True,
                    'descripcion': 'ID del veterinario que atendió la cita'
                },
                'porcentaje_empresa': {
                    'tipo': 'FLOAT',
                    'default': 57.14,
                    'descripcion': 'Porcentaje de ingreso para la empresa'
                },
                'porcentaje_veterinario': {
                    'tipo': 'FLOAT',
                    'default': 42.86,
                    'descripcion': 'Porcentaje de ingreso para el veterinario'
                },
                'monto_empresa': {
                    'tipo': 'FLOAT',
                    'default': 0,
                    'descripcion': 'Monto que va para la empresa'
                },
                'monto_veterinario': {
                    'tipo': 'FLOAT',
                    'default': 0,
                    'descripcion': 'Monto que va para el veterinario'
                }
            }

            columnas_faltantes = []
            columnas_existentes_ok = []

            for nombre, info in columnas_requeridas.items():
                if nombre not in columnas_actuales:
                    columnas_faltantes.append(nombre)
                    print(f"   ⚠️  Falta columna: {nombre} - {info['descripcion']}")
                else:
                    columnas_existentes_ok.append(nombre)
                    print(f"   ✅ Columna existe: {nombre}")

            print()

            # Paso 5: Agregar columnas faltantes
            if columnas_faltantes:
                print("🔧 Paso 5: Agregando columnas faltantes...")
                print()

                for nombre in columnas_faltantes:
                    info = columnas_requeridas[nombre]
                    try:
                        if nombre == 'veterinario_id':
                            # Columna especial con NULL
                            sql = f"ALTER TABLE pagos ADD {nombre} {info['tipo']} NULL"
                        else:
                            # Columnas con valor por defecto
                            sql = f"ALTER TABLE pagos ADD {nombre} {info['tipo']} DEFAULT {info['default']}"

                        print(f"   Ejecutando: {sql}")
                        db.session.execute(text(sql))
                        db.session.commit()
                        print(f"   ✅ Columna '{nombre}' agregada exitosamente")

                    except SQLAlchemyError as e:
                        print(f"   ❌ Error al agregar '{nombre}': {str(e)}")
                        db.session.rollback()

                        # Intentar método alternativo sin DEFAULT
                        try:
                            print(f"   🔄 Intentando método alternativo...")
                            sql_alt = f"ALTER TABLE pagos ADD {nombre} {info['tipo']} NULL"
                            db.session.execute(text(sql_alt))
                            db.session.commit()
                            print(f"   ✅ Columna '{nombre}' agregada (método alternativo)")
                        except SQLAlchemyError as e2:
                            print(f"   ❌ Falló método alternativo: {str(e2)}")
                            db.session.rollback()

                print()
            else:
                print("✅ Paso 5: Todas las columnas ya existen")
                print()

            # Paso 6: Actualizar valores por defecto si son NULL
            print("🔄 Paso 6: Actualizando valores por defecto...")
            try:
                # Actualizar porcentajes a valores por defecto si son NULL
                db.session.execute(text("""
                    UPDATE pagos
                    SET porcentaje_empresa = 57.14
                    WHERE porcentaje_empresa IS NULL OR porcentaje_empresa = 0
                """))

                db.session.execute(text("""
                    UPDATE pagos
                    SET porcentaje_veterinario = 42.86
                    WHERE porcentaje_veterinario IS NULL OR porcentaje_veterinario = 0
                """))

                db.session.commit()
                print("   ✅ Valores por defecto actualizados")
            except SQLAlchemyError as e:
                print(f"   ⚠️  Advertencia: {str(e)}")
                db.session.rollback()
            print()

            # Paso 7: Actualizar veterinario_id desde citas
            print("🔗 Paso 7: Vinculando veterinarios a pagos...")
            try:
                result = db.session.execute(text("""
                    UPDATE p
                    SET p.veterinario_id = c.veterinario_id
                    FROM pagos p
                    INNER JOIN citas c ON p.cita_id = c.id
                    WHERE p.veterinario_id IS NULL
                      AND c.veterinario_id IS NOT NULL
                """))
                db.session.commit()
                print(f"   ✅ {result.rowcount} pagos vinculados a veterinarios")
            except SQLAlchemyError as e:
                print(f"   ⚠️  Advertencia: {str(e)}")
                db.session.rollback()
            print()

            # Paso 8: Calcular división de ingresos
            print("💰 Paso 8: Calculando división de ingresos...")
            try:
                result = db.session.execute(text("""
                    UPDATE pagos
                    SET
                        monto_empresa = monto * (porcentaje_empresa / 100.0),
                        monto_veterinario = monto * (porcentaje_veterinario / 100.0)
                    WHERE (monto_empresa IS NULL OR monto_empresa = 0)
                       OR (monto_veterinario IS NULL OR monto_veterinario = 0)
                """))
                db.session.commit()
                print(f"   ✅ {result.rowcount} pagos actualizados con división de ingresos")
            except SQLAlchemyError as e:
                print(f"   ⚠️  Advertencia: {str(e)}")
                db.session.rollback()
            print()

            # Paso 9: Verificar integridad final
            print("🔍 Paso 9: Verificando integridad de datos...")

            # Contar pagos totales
            total_pagos = db.session.execute(text("""
                SELECT COUNT(*) as total FROM pagos
            """)).scalar()

            # Contar pagos con veterinario
            pagos_con_vet = db.session.execute(text("""
                SELECT COUNT(*) as total FROM pagos WHERE veterinario_id IS NOT NULL
            """)).scalar()

            # Contar pagos con división calculada
            pagos_con_division = db.session.execute(text("""
                SELECT COUNT(*) as total FROM pagos
                WHERE monto_empresa > 0 AND monto_veterinario > 0
            """)).scalar()

            print(f"   📊 Total de pagos: {total_pagos}")
            print(f"   👨‍⚕️ Pagos con veterinario: {pagos_con_vet}")
            print(f"   💵 Pagos con división calculada: {pagos_con_division}")
            print()

            # Paso 10: Crear foreign key si no existe
            print("🔗 Paso 10: Verificando foreign keys...")
            try:
                # Intentar crear FK para veterinario_id
                db.session.execute(text("""
                    IF NOT EXISTS (
                        SELECT * FROM sys.foreign_keys
                        WHERE name = 'FK_pagos_veterinario'
                    )
                    BEGIN
                        ALTER TABLE pagos ADD CONSTRAINT FK_pagos_veterinario
                            FOREIGN KEY (veterinario_id) REFERENCES usuarios(id)
                    END
                """))
                db.session.commit()
                print("   ✅ Foreign key 'FK_pagos_veterinario' verificada")
            except SQLAlchemyError as e:
                print(f"   ℹ️  Foreign key: {str(e)}")
                db.session.rollback()
            print()

            # Paso 11: Verificación final de columnas
            print("✔️  Paso 11: Verificación final...")
            columnas_finales = [col['name'] for col in inspector.get_columns('pagos')]

            todas_existen = all(col in columnas_finales for col in columnas_requeridas.keys())

            if todas_existen:
                print("   ✅ TODAS las columnas requeridas están presentes")
            else:
                print("   ❌ FALTAN algunas columnas:")
                for col in columnas_requeridas.keys():
                    if col not in columnas_finales:
                        print(f"      - {col}")
            print()

            # Resumen Final
            print("=" * 70)
            print("RESUMEN DE LA REPARACIÓN")
            print("=" * 70)
            print()
            print("✅ Columnas agregadas:")
            for col in columnas_faltantes:
                print(f"   • {col} - {columnas_requeridas[col]['descripcion']}")

            if not columnas_faltantes:
                print("   • Todas las columnas ya existían")

            print()
            print("📊 Estado de la base de datos:")
            print(f"   • Total de pagos: {total_pagos}")
            print(f"   • Pagos con veterinario asignado: {pagos_con_vet}")
            print(f"   • Pagos con división calculada: {pagos_con_division}")
            print()

            print("💡 División de ingresos configurada:")
            print("   • Empresa: 57.14% (por defecto)")
            print("   • Veterinario: 42.86% (por defecto)")
            print()

            if todas_existen:
                print("=" * 70)
                print("✅ BASE DE DATOS REPARADA Y LISTA PARA USAR")
                print("=" * 70)
                print()
                print("Próximos pasos:")
                print("1. Reinicia Flask: python run.py")
                print("2. Prueba crear un pago como tutor")
                print("3. Verifica que no haya errores")
                print()
                return True
            else:
                print("=" * 70)
                print("⚠️  REPARACIÓN INCOMPLETA")
                print("=" * 70)
                print()
                print("Algunas columnas no pudieron agregarse.")
                print("Por favor, revisa los errores arriba y ejecuta manualmente:")
                print("  - agregar_columnas_comision.sql")
                print("  - agregar_veterinario_id_pagos.sql")
                print()
                return False

        except Exception as e:
            print()
            print("=" * 70)
            print("❌ ERROR CRÍTICO")
            print("=" * 70)
            print(f"Error: {str(e)}")
            print()
            import traceback
            traceback.print_exc()
            return False


if __name__ == '__main__':
    print()
    print("🔧 Script de Reparación de Base de Datos")
    print("   Este script verificará y reparará automáticamente")
    print("   la estructura de la tabla 'pagos'")
    print()

    input("Presiona ENTER para continuar...")
    print()

    try:
        exito = verificar_y_reparar()

        if exito:
            print("✅ Script completado exitosamente")
            sys.exit(0)
        else:
            print("⚠️  Script completado con advertencias")
            sys.exit(1)

    except KeyboardInterrupt:
        print("\n\n❌ Operación cancelada por el usuario")
        sys.exit(1)
    except Exception as e:
        print(f"\n❌ Error inesperado: {e}")
        import traceback
        traceback.print_exc()
        sys.exit(1)
