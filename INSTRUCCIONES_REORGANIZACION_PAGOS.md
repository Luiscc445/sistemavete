# 📋 Instrucciones - Reorganización del Sistema de Pagos

## 🎯 Resumen de Cambios Implementados

Se ha reorganizado completamente el flujo de pagos según tus especificaciones:

### ✅ Cambios Completados:

1. **Pago durante el agendamiento de citas (Tutores)**
   - Ahora cuando un tutor agenda una cita, es redirigido automáticamente a la página de pago
   - El pago se procesa en la sección de tutores (no en admin)
   - Al completar el pago, la cita se confirma automáticamente

2. **División de Ingresos (Empresa vs Veterinario)**
   - Cada pago se divide automáticamente:
     - **57.14%** para la empresa → `monto_empresa`
     - **42.86%** para el veterinario → `monto_veterinario`
   - Los porcentajes son configurables por pago

3. **Dashboard de Veterinarios con Ingresos Personales**
   - Los veterinarios ven sus ingresos personales (solo su porcentaje)
   - Muestra: Ingresos totales y del mes actual
   - No ven el monto total ni la porción de la empresa

4. **Dashboard de Admin (Pagos) con Ingresos de la Empresa**
   - El admin ve solo la porción de la empresa
   - Panel informativo que muestra la división: Total Bruto / Empresa / Veterinarios
   - Todos los gráficos muestran solo la porción de la empresa

---

## 🚀 Pasos para Completar la Instalación

### 1. Ejecutar la Migración de Base de Datos

La migración agregará las siguientes columnas a la tabla `pagos`:
- `porcentaje_empresa` (FLOAT, default: 57.14)
- `porcentaje_veterinario` (FLOAT, default: 42.86)
- `monto_empresa` (FLOAT, default: 0)
- `monto_veterinario` (FLOAT, default: 0)

**Opción A: Usando el script Python** (Recomendado)

```powershell
python migrar_columnas_comision.py
```

Este script:
- Verifica si las columnas ya existen
- Agrega solo las columnas faltantes
- Actualiza los registros existentes con la división de ingresos
- Muestra un resumen de lo realizado

**Opción B: Ejecutar manualmente en SQL Server**

Si prefieres hacerlo manualmente, ejecuta el archivo `agregar_columnas_comision.sql` en SQL Server Management Studio.

### 2. Reiniciar Flask

```powershell
# Detener Flask (Ctrl+C)
# Luego reiniciar:
python run.py
```

---

## 📖 Cómo Funciona el Nuevo Flujo

### Para Tutores:

1. **Agendar Cita**:
   - Va a: Citas → Nueva Cita
   - Llena el formulario (mascota, veterinario, fecha, motivo)
   - Click en "Solicitar Cita"

2. **Pagar la Cita**:
   - Automáticamente es redirigido a `/tutor/pagar-cita/<id>`
   - Selecciona método de pago:
     - 💵 Efectivo
     - 💳 Tarjeta de Crédito/Débito (simulado)
     - 📱 QR (Simple, Tigo Money, Bancario)
     - 🏦 Transferencia
   - Ingresa el monto (cualquier valor, es simulado)
   - Si es tarjeta: llena datos simulados (cualquier valor)
   - Si es QR: se genera código QR automáticamente

3. **Confirmación Automática**:
   - Al completar el pago, la cita cambia a estado "confirmada"
   - El veterinario recibe la cita en su dashboard
   - El pago se divide automáticamente (empresa/veterinario)

### Para Veterinarios:

1. **Ver Ingresos Personales**:
   - Dashboard muestra: "Mis Ingresos Totales" y "Ingresos del Mes"
   - Solo ve su porcentaje (42.86% por defecto)
   - Ejemplo: Si un tutor pagó 35 Bs, el vet ve 15 Bs (su porción)

2. **Panel Informativo**:
   - Alerta azul explica que los montos son solo su porcentaje
   - El resto va a la empresa

### Para Administradores:

1. **Dashboard de Pagos** (`/pagos/`):
   - Panel informativo muestra división de ingresos:
     - Total Recibido (Bruto): Ej. 35 Bs
     - Porción Empresa: 20 Bs (57.14%)
     - Porción Veterinarios: 15 Bs (42.86%)
   - Todos los gráficos muestran solo la porción de la empresa
   - "Ingresos Empresa" en lugar de "Ingresos Totales"

2. **Control de Pagos**:
   - El admin puede ver todos los pagos
   - Puede crear pagos manualmente si es necesario
   - Puede emitir reembolsos
   - Controla los ingresos de la empresa

---

## 🎨 Archivos Modificados

### Modelos:
- ✅ `app/models/pago.py` - Agregadas columnas de comisión y método `calcular_division_ingresos()`

### Controladores:
- ✅ `app/controllers/tutor_controller.py` - Agregada ruta `/pagar-cita/<id>` para procesar pagos
- ✅ `app/controllers/veterinario_controller.py` - Dashboard actualizado con ingresos personales
- ✅ `app/controllers/pagos_controller.py` - Dashboard actualizado para mostrar solo porción de empresa

### Templates:
- ✅ `app/templates/tutor/pagar_cita.html` - **NUEVO** - Formulario de pago para tutores
- ✅ `app/templates/veterinario/dashboard.html` - Actualizado con sección de ingresos personales
- ✅ `app/templates/admin/pagos/dashboard.html` - Actualizado con división de ingresos

### Scripts:
- ✅ `migrar_columnas_comision.py` - Script de migración Python
- ✅ `agregar_columnas_comision.sql` - Script SQL alternativo

---

## 🧪 Cómo Probar el Sistema

### Prueba 1: Flujo Completo de Pago

1. **Como Tutor**:
   ```
   1. Login como tutor
   2. Ir a: Citas → Nueva Cita
   3. Llenar formulario y enviar
   4. En la página de pago:
      - Seleccionar "Tarjeta de Crédito"
      - Ingresar monto: 35
      - Llenar datos simulados
      - Confirmar
   5. Verificar que la cita está confirmada
   ```

2. **Como Veterinario**:
   ```
   1. Login como veterinario
   2. Ir al Dashboard
   3. Verificar sección "Mis Ingresos Totales"
   4. Debería mostrar: Bs. 15.00 (42.86% de 35)
   5. Ver "Ingresos del Mes": Bs. 15.00
   ```

3. **Como Admin**:
   ```
   1. Login como admin
   2. Ir a: Pagos (nueva opción en menú)
   3. Verificar panel de división:
      - Total Recibido: Bs. 35.00
      - Porción Empresa: Bs. 20.00
      - Porción Veterinarios: Bs. 15.00
   4. Ver "Ingresos Empresa": Bs. 20.00
   ```

### Prueba 2: Pago con QR

```
1. Como tutor, crear nueva cita
2. En página de pago:
   - Seleccionar "Código QR Simple"
   - Ingresar monto: 50
   - Confirmar
3. Verificar que se generó código QR
4. Verificar división:
   - Empresa: 28.57 Bs
   - Veterinario: 21.43 Bs
```

### Prueba 3: Múltiples Pagos

```
1. Crear 3 pagos con montos diferentes:
   - 35 Bs (Empresa: 20, Vet: 15)
   - 50 Bs (Empresa: 28.57, Vet: 21.43)
   - 100 Bs (Empresa: 57.14, Vet: 42.86)

2. Verificar dashboard admin:
   - Total Recibido: 185 Bs
   - Empresa: 105.71 Bs
   - Veterinarios: 79.29 Bs

3. Verificar dashboard veterinario:
   - Ingresos: 79.29 Bs
```

---

## 🔧 Configuración Avanzada

### Cambiar Porcentajes de División

Si quieres cambiar los porcentajes por defecto, modifica en `app/models/pago.py`:

```python
porcentaje_empresa = db.Column(db.Float, default=60.0)  # 60% empresa
porcentaje_veterinario = db.Column(db.Float, default=40.0)  # 40% veterinario
```

También debes actualizar en `migrar_columnas_comision.py`:

```python
'porcentaje_empresa': {
    'sql': "ALTER TABLE pagos ADD porcentaje_empresa FLOAT DEFAULT 60.0",
    ...
}
```

### Métodos de Pago Disponibles

Los siguientes métodos están configurados:
- `efectivo` - Efectivo
- `tarjeta_credito` - Tarjeta de Crédito (simulado)
- `tarjeta_debito` - Tarjeta de Débito (simulado)
- `qr_simple` - Código QR Simple
- `qr_tigo` - Tigo Money QR
- `qr_bancario` - QR Bancario
- `transferencia` - Transferencia Bancaria

Todos los métodos QR generan códigos QR automáticamente.

---

## ⚠️ Notas Importantes

1. **Pagos Simulados**:
   - Los pagos con tarjeta y QR son simulados
   - Aceptan cualquier valor ingresado
   - No hay validación de tarjetas reales
   - No hay integración con pasarelas de pago

2. **Confirmación Automática**:
   - Al completar un pago, la cita cambia automáticamente a "confirmada"
   - El veterinario asignado recibe la cita en su dashboard
   - No requiere aprobación adicional

3. **División de Ingresos**:
   - La división se calcula automáticamente al crear el pago
   - Se puede consultar en cualquier momento
   - Los porcentajes se pueden modificar por pago si es necesario

4. **Base de Datos**:
   - Asegúrate de ejecutar la migración antes de usar el sistema
   - Los registros existentes se actualizarán automáticamente
   - No se perderán datos

---

## 📊 Ejemplo de División

**Pago de 35 Bs:**
```
Total: 35.00 Bs (100%)
├── Empresa:      20.00 Bs (57.14%)
└── Veterinario:  15.00 Bs (42.86%)
```

**Pago de 100 Bs:**
```
Total: 100.00 Bs (100%)
├── Empresa:      57.14 Bs (57.14%)
└── Veterinario:  42.86 Bs (42.86%)
```

---

## ✅ Checklist de Instalación

- [ ] Ejecuté la migración (`python migrar_columnas_comision.py`)
- [ ] La migración completó exitosamente
- [ ] Reinicié Flask
- [ ] Probé el flujo completo (tutor → pago → confirmación)
- [ ] Verifiqué dashboard de veterinario con ingresos
- [ ] Verifiqué dashboard de admin con división de ingresos
- [ ] Los pagos se dividen correctamente
- [ ] Las citas se confirman automáticamente

---

## 📞 Solución de Problemas

### Error: "Column 'porcentaje_empresa' already exists"
**Solución**: Las columnas ya existen. Puedes omitir la migración o el script las detectará automáticamente.

### Error: "Table 'pagos' does not exist"
**Solución**: Primero debes crear la tabla pagos. Ejecuta las migraciones principales del sistema.

### Los montos no se dividen correctamente
**Solución**:
1. Verifica que ejecutaste la migración
2. Los pagos creados DESPUÉS de la migración se dividirán automáticamente
3. Los pagos existentes deben actualizarse con el UPDATE del script

### El veterinario no ve ingresos
**Solución**:
1. Verifica que existan pagos completados con `veterinario_id` asignado
2. Verifica que `monto_veterinario` > 0 en la tabla
3. Reinicia Flask

---

## 🎉 ¡Listo!

Si completaste todos los pasos del checklist, el sistema está funcionando correctamente.

**Fecha**: 17 de Noviembre, 2025
**Versión**: 2.0.0
**Sistema**: Veterinaria - Reorganización de Pagos
