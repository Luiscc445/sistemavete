# 🚀 Instrucciones Rápidas - Sistema de Pagos con QR

## ⚡ Instalación Rápida (5 minutos)

### 1. Actualizar el código

```powershell
cd C:\Users\LUISC\Downloads\veterinaria_flask_CORREGIDO\veterinaria_flask\veterinaria_flask
git pull
```

###  2. Instalar dependencias

```powershell
pip install qrcode==7.4.2
pip install Pillow==10.4.0
```

O simplemente:

```powershell
pip install -r requirements.txt
```

### 3. Ejecutar migraciones de base de datos

```powershell
flask db migrate -m "Agregar sistema de pagos"
flask db upgrade
```

### 4. Reiniciar Flask

```powershell
python run.py
```

---

## ✅ Verificar Instalación

1. Abre tu navegador en: `http://localhost:5000`
2. Inicia sesión como admin (usuario: `admin`, contraseña: `admin123`)
3. Ve al menú y busca **"Pagos"** o accede directamente a:
   - Dashboard de Pagos: `http://localhost:5000/pagos/`
   - Crear Nuevo Pago: `http://localhost:5000/pagos/crear`

Si ves el dashboard de pagos, **¡el sistema está instalado correctamente!** ✅

---

## 📖 Uso Rápido

### Crear un Pago

1. **Ir a**: Pagos → Nuevo Pago
2. **Llenar**:
   - Monto: Ej. 150.00
   - Método: Seleccionar (efectivo, tarjeta, QR, etc.)
   - Cliente: Seleccionar tutor
   - Opcionalmente: Seleccionar cita asociada
3. **Guardar**: El sistema genera código QR automáticamente si es método QR

### Procesar un Pago

1. **Ir al detalle del pago**
2. **Click en**: "Marcar como Completado"
3. **Completar** información adicional (número de transacción, etc.)
4. **Confirmar**: El pago queda registrado como completado

### Ver Ingresos

- **Dashboard de Pagos**: `http://localhost:5000/pagos/`
- **Dashboard de Reportes** (actualizado): `http://localhost:5000/reportes/`

---

## 🎨 Características Principales

### 1. Métodos de Pago

- 💵 **Efectivo**
- 💳 **Tarjeta de Crédito**
- 💳 **Tarjeta de Débito**
- 🏦 **Transferencia Bancaria**
- 📱 **QR Simple**
- 📱 **Tigo Money QR**
- 📱 **QR Bancario**

### 2. Códigos QR

Los métodos QR generan códigos QR automáticamente que:
- Incluyen monto, descripción, código de pago
- Tienen vencimiento de 24 horas
- Se pueden regenerar si vencen
- Se pueden descargar como imagen PNG

### 3. Dashboard Moderno

El dashboard de pagos muestra:
- **Estadísticas**: Ingresos totales, pagos completados, pendientes
- **Gráfico de Ingresos por Día** (línea)
- **Gráfico de Métodos de Pago** (dona)
- **Pagos Recientes** (tabla)
- **Top 10 Pagos Más Grandes**

### 4. Integración con Citas

- Al crear un pago, puedes asociarlo a una cita
- Se autocompleta: monto, cliente, descripción
- Al completar el pago, la cita se marca como "pagada"

---

## 🔐 Acceso

Solo usuarios **administradores** pueden:
- Ver el dashboard de pagos
- Crear pagos
- Procesar pagos
- Emitir reembolsos

---

## 📊 Dashboard de Reportes Actualizado

El dashboard de reportes (`/reportes/`) ahora muestra:
- **Ingresos reales** desde la tabla de pagos (no estimados de citas)
- Gráfico de **"Ingresos por Mes"** con datos reales
- Todos los reportes actualizados con información de pagos

---

## 🛠️ Solución Rápida de Problemas

### Error: "No module named 'qrcode'"

**Solución**:
```powershell
pip install qrcode Pillow
```

### Error: "Tabla 'pagos' no existe"

**Solución**:
```powershell
flask db migrate -m "Crear tablas de pagos"
flask db upgrade
```

### Error: "Blueprint 'pagos' not found"

**Verificar**:
1. Que hiciste `git pull`
2. Que reiniciaste Flask completamente
3. Que estás en la rama correcta

### No veo el menú de Pagos

**Verificar**:
1. Que estás logueado como **admin**
2. Que actualizaste el código (`git pull`)
3. Que reiniciaste Flask

---

## 📁 Archivos Importantes

- **Modelo**: `app/models/pago.py`
- **Controlador**: `app/controllers/pagos_controller.py`
- **Templates**: `app/templates/admin/pagos/`
- **Documentación completa**: `SISTEMA_PAGOS_QR.md`

---

## 🎯 Próximos Pasos Recomendados

1. **Crear algunos pagos de prueba**
   - Prueba con diferentes métodos de pago
   - Genera códigos QR para ver cómo funcionan

2. **Explorar el dashboard**
   - Filtra por fechas
   - Ve los gráficos de ingresos

3. **Probar pagos parciales**
   - Crea un pago de Bs. 1000
   - Registra un pago parcial de Bs. 500
   - Luego completa con otros Bs. 500

4. **Integrar con citas**
   - Crea una cita
   - Crea un pago asociado a esa cita
   - Completa el pago
   - Verifica que la cita se marque como "pagada"

5. **Generar reportes**
   - Ve al dashboard de reportes
   - Verifica que los ingresos se muestren correctamente

---

## 📞 Ayuda

Si tienes problemas:

1. **Lee** `SISTEMA_PAGOS_QR.md` (documentación completa)
2. **Verifica** que completaste todos los pasos de instalación
3. **Revisa** los logs en la consola de Flask para ver errores

---

## ✅ Checklist de Instalación

- [ ] Hice `git pull`
- [ ] Instalé `qrcode` y `Pillow`
- [ ] Ejecuté las migraciones (`flask db migrate` y `flask db upgrade`)
- [ ] Reinicié Flask
- [ ] Veo el menú/opción de "Pagos"
- [ ] Puedo acceder a `/pagos/`
- [ ] Puedo crear un pago de prueba
- [ ] El QR se genera automáticamente (para métodos QR)
- [ ] Veo los gráficos en el dashboard de pagos

Si completaste todo el checklist, **¡el sistema está funcionando correctamente!** 🎉

---

**Fecha**: 17 de Noviembre, 2025
**Versión**: 1.0.0
**Sistema**: Veterinaria v2.0.0
