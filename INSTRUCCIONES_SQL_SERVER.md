# 🔧 Instrucciones para Configurar SQL Server

## ⚠️ PROBLEMA IDENTIFICADO

Tu aplicación estaba conectándose a **SQLite** en lugar de **SQL Server**. Por eso los cambios que hice para SQL Server no funcionaban.

---

## 📋 PASOS PARA ARREGLAR (EN ORDEN)

### **PASO 1: Configurar el archivo .env** ✅

Ya creé el archivo `.env` por ti. Ahora necesitas **editarlo** con tus credenciales de SQL Server:

1. Abre el archivo `.env` en tu editor
2. Cambia estas líneas con tus datos reales:

```env
SQLSERVER_SERVER=localhost          # Tu servidor SQL Server (puede ser IP)
SQLSERVER_DATABASE=veterinaria      # Nombre de tu base de datos
SQLSERVER_USERNAME=sa               # Tu usuario de SQL Server
SQLSERVER_PASSWORD=TuPasswordAqui   # Tu contraseña
```

**SI USAS AUTENTICACIÓN DE WINDOWS:**
- Comenta las líneas de `USERNAME` y `PASSWORD`
- Descomenta la línea `SQLSERVER_TRUSTED=true`

---

### **PASO 2: Ejecutar el script SQL en SQL Server** 🗄️

1. Abre **SQL Server Management Studio** (SSMS)
2. Conecta a tu servidor
3. Abre el archivo `fix_sql_server_auditoria.sql`
4. Selecciona tu base de datos `veterinaria`
5. Ejecuta el script completo

Este script arreglará las columnas de la tabla `auditoria_acciones`.

---

### **PASO 3: Actualizar el código** 📥

Abre una terminal en tu directorio de proyecto y ejecuta:

```bash
git pull
```

---

### **PASO 4: Reiniciar la aplicación Flask** 🔄

1. Si Flask está corriendo, detenlo (Ctrl+C)
2. Vuelve a ejecutar:
   ```bash
   python run.py
   ```

Deberías ver un mensaje como:
```
========================================
Sistema Veterinario v2.0.0
========================================
Configuración: sqlserver
Base de datos: mssql+pyodbc://sa:***@localhost:1433/veterinaria?driver=ODBC+Driver+17+for+SQL+Server
...
```

---

### **PASO 5: Verificar que funciona** ✨

1. Abre el navegador en `http://localhost:5000`
2. Inicia sesión como admin (usuario: `admin`, contraseña: `admin123`)
3. Ve al panel de administración
4. Intenta **ver un tutor** o **ver un veterinario**
5. Intenta **editar un tutor** o **editar un veterinario**

**¡Todo debería funcionar sin errores 500!**

---

## 🐛 Si aún tienes problemas

Ejecuta el script de diagnóstico:

```bash
python diagnostico_sql_server.py
```

Este script te dirá exactamente qué está mal.

---

## ✅ Cambios que hice

1. **Modelo de datos** (`app/models/auditoria_accion.py`):
   - Campos marcados como `nullable=True`
   - `user_agent` cambiado a Text (sin límite de 200 caracteres)

2. **Controlador** (`app/controllers/admin_controller.py`):
   - Manejo correcto de valores NULL para SQL Server
   - Manejo seguro de user-agent y IP address

3. **Script SQL** (`fix_sql_server_auditoria.sql`):
   - ALTER TABLE para cambiar `user_agent` a NVARCHAR(MAX)
   - ALTER TABLE para marcar campos como nullable
   - Verificación de cambios

4. **Archivo de configuración** (`.env`):
   - Configurado para usar SQL Server
   - `FLASK_CONFIG=sqlserver` activado

---

## 📝 Notas Importantes

- El **user-agent** de navegadores modernos puede ser de 300-400 caracteres, por eso lo cambié a Text sin límite
- SQL Server con pyodbc es muy estricto con tipos NULL/NOT NULL
- Es CRÍTICO ejecutar primero el script SQL antes de usar la aplicación

---

**¿Necesitas ayuda?** Copia y pega el error completo si algo no funciona.
