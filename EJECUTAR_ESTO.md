# 🚨 EJECUTA ESTO PARA ARREGLAR LA BASE DE DATOS

## ⚡ Pasos Rápidos

### 1. Hacer Git Pull
```powershell
git pull origin claude/fix-jinja2-templates-01Uem5jCtJFFGfMfBXwUhUyU
```

### 2. Ejecutar el Script de Reparación
```powershell
python reparar_base_datos_pagos.py
```

**Este script va a:**
- ✅ Verificar la conexión a la base de datos
- ✅ Inspeccionar qué columnas faltan
- ✅ Agregar automáticamente las columnas faltantes
- ✅ Actualizar valores por defecto
- ✅ Vincular veterinarios a pagos existentes
- ✅ Calcular división de ingresos
- ✅ Verificar que todo quedó bien

### 3. Reiniciar Flask
```powershell
# Detener Flask (Ctrl+C)
python run.py
```

### 4. Probar el Sistema
```
1. Login como tutor
2. Crear nueva cita
3. Pagar la cita (monto: 35)
4. Ver página bonita de confirmación
```

---

## ❓ Si Algo Sale Mal

Si el script no funciona, ejecuta este SQL manualmente en SQL Server:

```sql
-- Agregar veterinario_id
ALTER TABLE pagos ADD veterinario_id INT NULL;

-- Agregar columnas de comisión
ALTER TABLE pagos ADD porcentaje_empresa FLOAT DEFAULT 57.14;
ALTER TABLE pagos ADD porcentaje_veterinario FLOAT DEFAULT 42.86;
ALTER TABLE pagos ADD monto_empresa FLOAT DEFAULT 0;
ALTER TABLE pagos ADD monto_veterinario FLOAT DEFAULT 0;

-- Actualizar valores
UPDATE pagos SET porcentaje_empresa = 57.14 WHERE porcentaje_empresa IS NULL;
UPDATE pagos SET porcentaje_veterinario = 42.86 WHERE porcentaje_veterinario IS NULL;

-- Vincular veterinarios
UPDATE p
SET p.veterinario_id = c.veterinario_id
FROM pagos p
INNER JOIN citas c ON p.cita_id = c.id
WHERE p.veterinario_id IS NULL AND c.veterinario_id IS NOT NULL;

-- Calcular división
UPDATE pagos
SET
    monto_empresa = monto * (porcentaje_empresa / 100.0),
    monto_veterinario = monto * (porcentaje_veterinario / 100.0)
WHERE monto_empresa = 0 OR monto_veterinario = 0;
```

---

## ✅ ¿Cómo Sé que Funcionó?

El script te mostrará al final:

```
✅ BASE DE DATOS REPARADA Y LISTA PARA USAR

Próximos pasos:
1. Reinicia Flask: python run.py
2. Prueba crear un pago como tutor
3. Verifica que no haya errores
```

---

## 📊 ¿Qué Hace el Script?

El script `reparar_base_datos_pagos.py` es un script inteligente que:

**Paso 1-3**: Verifica conexión y tabla pagos
**Paso 4-5**: Detecta qué columnas faltan y las agrega
**Paso 6**: Actualiza valores por defecto (57.14%, 42.86%)
**Paso 7**: Vincula veterinarios a pagos existentes
**Paso 8**: Calcula división de ingresos (empresa/veterinario)
**Paso 9-10**: Verifica integridad y crea foreign keys
**Paso 11**: Verificación final y reporte

**Muestra progreso en tiempo real** con emojis y colores para que sepas qué está pasando.

---

## 🎯 Resumen

```powershell
# 1. Git pull
git pull origin claude/fix-jinja2-templates-01Uem5jCtJFFGfMfBXwUhUyU

# 2. Reparar base de datos
python reparar_base_datos_pagos.py

# 3. Reiniciar Flask
python run.py

# 4. Probar
# Login → Crear cita → Pagar → Ver confirmación bonita
```

**¡Eso es todo!** 🎉
