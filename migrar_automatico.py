"""MIGRACIÓN AUTOMÁTICA SQLite a SQL Server - ORDEN CORRECTO"""
import sqlite3, pyodbc, sys
from datetime import datetime
from pathlib import Path

class Color:
    GREEN = '\033[92m'
    YELLOW = '\033[93m'
    RED = '\033[91m'
    CYAN = '\033[96m'
    WHITE = '\033[97m'
    RESET = '\033[0m'
    BOLD = '\033[1m'

def pc(msg, color='\033[97m'):
    print(f"{color}{msg}\033[0m")

def find_db():
    pc("Buscando veterinaria.db...", Color.WHITE)
    for p in [Path.cwd()/"instance"/"veterinaria.db", Path.cwd()/"veterinaria.db"]:
        if p.exists():
            pc(f"✓ Encontrado: {p}", Color.GREEN)
            return str(p)
    for db in Path.cwd().rglob("veterinaria.db"):
        pc(f"✓ Encontrado: {db}", Color.GREEN)
        return str(db)
    pc("✗ No se encontró veterinaria.db", Color.RED)
    return None

def convert_type(t):
    m = {'INTEGER':'INT','TEXT':'NVARCHAR(MAX)','REAL':'FLOAT','BLOB':'VARBINARY(MAX)','DATETIME':'DATETIME2','DATE':'DATE'}
    for k,v in m.items():
        if k in t.upper(): return v
    return 'NVARCHAR(MAX)'

def order_tables(schema):
    """Ordenar tablas por dependencias (padres primero)"""
    ordered = []
    remaining = set(schema.keys())
    
    # Tablas sin FKs primero
    no_fk = [t for t in remaining if not schema[t]['fks']]
    ordered.extend(no_fk)
    remaining -= set(no_fk)
    
    # Ordenar el resto por dependencias
    max_iterations = 100
    iteration = 0
    while remaining and iteration < max_iterations:
        added_this_round = []
        for table in list(remaining):
            # Verificar si todas las tablas referenciadas ya están en ordered
            fk_tables = [fk['ref_table'] for fk in schema[table]['fks']]
            if all(ref in ordered or ref == table for ref in fk_tables):
                ordered.append(table)
                added_this_round.append(table)
        
        remaining -= set(added_this_round)
        iteration += 1
        
        if not added_this_round and remaining:
            # Ciclo de dependencias, agregar el resto
            ordered.extend(remaining)
            break
    
    return ordered

pc("\n" + "="*60, Color.CYAN)
pc("  MIGRACIÓN AUTOMÁTICA SQLite → SQL Server", Color.CYAN + Color.BOLD)
pc("="*60 + "\n", Color.CYAN)

try:
    # 1. BUSCAR SQLITE
    pc("PASO 1: Detectando base de datos", Color.CYAN)
    sqlite_path = find_db()
    if not sqlite_path:
        input("\nPresiona Enter para salir...")
        sys.exit(1)
    
    # 2. CONFIGURACIÓN
    pc("\nPASO 2: Configuración", Color.CYAN)
    server = r'LUIS_CARLOS69\SQLDEV'
    dbname = 'VeterinariaDB'
    pc(f"  SQLite: {sqlite_path}", Color.WHITE)
    pc(f"  Server: {server}", Color.WHITE)
    pc(f"  DB: {dbname}", Color.WHITE)
    
    # 3. CONECTAR SQLITE
    pc("\nPASO 3: Conectando a SQLite", Color.CYAN)
    sqlite_conn = sqlite3.connect(sqlite_path)
    sqlite_conn.row_factory = sqlite3.Row
    sc = sqlite_conn.cursor()
    pc("✓ Conectado", Color.GREEN)
    
    # 4. EXTRAER ESQUEMA
    pc("\nPASO 4: Extrayendo esquema", Color.CYAN)
    sc.execute("SELECT name FROM sqlite_master WHERE type='table' AND name NOT LIKE 'sqlite_%' ORDER BY name")
    tables = [r[0] for r in sc.fetchall()]
    pc(f"✓ {len(tables)} tablas encontradas", Color.GREEN)
    
    schema = {}
    for table in tables:
        sc.execute(f"PRAGMA table_info({table})")
        cols = [{'name':r[1],'type':r[2],'notnull':r[3],'pk':r[5]} for r in sc.fetchall()]
        sc.execute(f"PRAGMA foreign_key_list({table})")
        fks = [{'col':r[3],'ref_table':r[2],'ref_col':r[4]} for r in sc.fetchall()]
        schema[table] = {'columns':cols,'fks':fks}
    
    # Ordenar tablas por dependencias
    ordered_tables = order_tables(schema)
    pc(f"  Orden de migración: {', '.join(ordered_tables)}", Color.WHITE)
    
    # 5. CONECTAR SQL SERVER
    pc("\nPASO 5: Conectando a SQL Server", Color.CYAN)
    conn_master = f"DRIVER={{SQL Server}};SERVER={server};DATABASE=master;Trusted_Connection=yes;TrustServerCertificate=yes;"
    
    try:
        master_conn = pyodbc.connect(conn_master, autocommit=True)
        pc("✓ Conectado a SQL Server", Color.GREEN)
    except Exception as e:
        pc(f"✗ Error: {e}", Color.RED)
        pc("\nVerifica:", Color.YELLOW)
        pc("  1. SQL Server está corriendo", Color.WHITE)
        pc("  2. Nombre: LUIS_CARLOS69\\SQLDEV", Color.WHITE)
        input("\nPresiona Enter para salir...")
        sys.exit(1)
    
    # 6. CREAR BASE DE DATOS
    pc("\nPASO 6: Creando base de datos", Color.CYAN)
    mc = master_conn.cursor()
    
    mc.execute(f"SELECT database_id FROM sys.databases WHERE name='{dbname}'")
    if mc.fetchone():
        pc(f"⚠ {dbname} existe, eliminando...", Color.YELLOW)
        mc.execute(f"ALTER DATABASE [{dbname}] SET SINGLE_USER WITH ROLLBACK IMMEDIATE")
        mc.execute(f"DROP DATABASE [{dbname}]")
    
    mc.execute(f"CREATE DATABASE [{dbname}]")
    master_conn.close()
    pc(f"✓ Base de datos {dbname} creada", Color.GREEN)
    
    # 7. CONECTAR A LA NUEVA BD
    conn_str = f"DRIVER={{SQL Server}};SERVER={server};DATABASE={dbname};Trusted_Connection=yes;TrustServerCertificate=yes;"
    sql_conn = pyodbc.connect(conn_str, autocommit=False)
    sqlc = sql_conn.cursor()
    
    # 8. CREAR TABLAS
    pc("\nPASO 7: Creando tablas", Color.CYAN)
    for tbl in ordered_tables:
        info = schema[tbl]
        cols_sql = []
        pks = []
        
        for col in info['columns']:
            sqltype = convert_type(col['type'])
            null = "NOT NULL" if col['notnull'] else "NULL"
            
            if col['pk'] and col['type'].upper()=='INTEGER':
                cols_sql.append(f"[{col['name']}] INT IDENTITY(1,1) NOT NULL")
            else:
                cols_sql.append(f"[{col['name']}] {sqltype} {null}")
            
            if col['pk']:
                pks.append(col['name'])
        
        if pks:
            pk_str = ','.join([f"[{p}]" for p in pks])
            cols_sql.append(f"CONSTRAINT [PK_{tbl}] PRIMARY KEY ({pk_str})")
        
        create_sql = f"CREATE TABLE [{tbl}] ({','.join(cols_sql)})"
        sqlc.execute(create_sql)
        pc(f"  ✓ {tbl}", Color.GREEN)
    
    sql_conn.commit()
    
    # 9. CREAR FKs
    pc("\nPASO 8: Creando relaciones", Color.CYAN)
    for tbl in ordered_tables:
        for fk in schema[tbl]['fks']:
            try:
                fk_name = f"FK_{tbl}_{fk['col']}"
                sqlc.execute(f"ALTER TABLE [{tbl}] ADD CONSTRAINT [{fk_name}] FOREIGN KEY ([{fk['col']}]) REFERENCES [{fk['ref_table']}] ([{fk['ref_col']}])")
            except Exception as e:
                pc(f"  ⚠ {fk_name}: {str(e)[:50]}", Color.YELLOW)
    sql_conn.commit()
    pc("✓ Relaciones creadas", Color.GREEN)
    
    # 10. MIGRAR DATOS (EN ORDEN CORRECTO)
    pc("\nPASO 9: Migrando datos", Color.CYAN)
    total = 0
    
    for tbl in ordered_tables:
        info = schema[tbl]
        sc.execute(f"SELECT * FROM [{tbl}]")
        rows = sc.fetchall()
        
        if not rows:
            pc(f"  {tbl}: 0 filas", Color.WHITE)
            continue
        
        cols = [c for c in info['columns'] if not (c['pk'] and c['type'].upper()=='INTEGER')]
        col_names = [c['name'] for c in cols]
        
        for i in range(0, len(rows), 100):
            batch = rows[i:i+100]
            placeholders = ','.join(['?' for _ in col_names])
            insert_sql = f"INSERT INTO [{tbl}] ({','.join([f'[{c}]' for c in col_names])}) VALUES ({placeholders})"
            batch_data = [[dict(r)[c] for c in col_names] for r in batch]
            sqlc.executemany(insert_sql, batch_data)
            sql_conn.commit()
        
        total += len(rows)
        pc(f"  ✓ {tbl}: {len(rows)} filas", Color.GREEN)
    
    pc(f"\n✓ TOTAL: {total} filas migradas", Color.GREEN + Color.BOLD)
    
    # 11. VERIFICAR
    pc("\nPASO 10: Verificando", Color.CYAN)
    ok = True
    for tbl in schema.keys():
        sc.execute(f"SELECT COUNT(*) FROM [{tbl}]")
        sqlite_count = sc.fetchone()[0]
        sqlc.execute(f"SELECT COUNT(*) FROM [{tbl}]")
        sql_count = sqlc.fetchone()[0]
        
        if sqlite_count == sql_count:
            pc(f"  ✓ {tbl}: {sql_count}", Color.GREEN)
        else:
            pc(f"  ✗ {tbl}: ERROR (SQLite={sqlite_count}, SQL={sql_count})", Color.RED)
            ok = False
    
    sqlite_conn.close()
    sql_conn.close()
    
    # RESULTADO
    pc("\n" + "="*60, Color.CYAN)
    if ok:
        pc("  ✓✓✓ MIGRACIÓN COMPLETADA EXITOSAMENTE ✓✓✓", Color.GREEN + Color.BOLD)
    else:
        pc("  ⚠⚠⚠ MIGRACIÓN CON ADVERTENCIAS ⚠⚠⚠", Color.YELLOW + Color.BOLD)
    pc("="*60 + "\n", Color.CYAN)
    
    pc("SIGUIENTES PASOS:", Color.YELLOW + Color.BOLD)
    pc("1. Actualiza config.py con SQL Server", Color.WHITE)
    pc("2. pip install pyodbc pymssql", Color.WHITE)
    pc("3. Prueba tu app Flask\n", Color.WHITE)
    
    pc("CONFIG PARA FLASK:", Color.CYAN + Color.BOLD)
    print("""from urllib.parse import quote_plus
SQLSERVER_DRIVER = '{SQL Server}'
SQLSERVER_SERVER = r'LUIS_CARLOS69\\SQLDEV'
SQLSERVER_DATABASE = 'VeterinariaDB'
connection_params = (
    f'DRIVER={SQLSERVER_DRIVER};'
    f'SERVER={SQLSERVER_SERVER};'
    f'DATABASE={SQLSERVER_DATABASE};'
    f'Trusted_Connection=yes;'
    f'TrustServerCertificate=yes;'
)
SQLALCHEMY_DATABASE_URI = f'mssql+pyodbc:///?odbc_connect={quote_plus(connection_params)}'
""")

except Exception as e:
    pc("\n" + "="*60, Color.RED)
    pc("  ✗✗✗ ERROR ✗✗✗", Color.RED + Color.BOLD)
    pc("="*60 + "\n", Color.RED)
    pc(str(e), Color.RED)
    import traceback
    traceback.print_exc()

finally:
    input("\nPresiona Enter para salir...")
