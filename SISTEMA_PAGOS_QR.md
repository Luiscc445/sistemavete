# 💰 Sistema de Pagos con QR - Documentación Completa

## 📋 Índice

1. [Introducción](#introducción)
2. [Características Principales](#características-principales)
3. [Métodos de Pago Soportados](#métodos-de-pago-soportados)
4. [Arquitectura del Sistema](#arquitectura-del-sistema)
5. [Instalación y Configuración](#instalación-y-configuración)
6. [Guía de Uso](#guía-de-uso)
7. [API y Endpoints](#api-y-endpoints)
8. [Base de Datos](#base-de-datos)
9. [Integración con Citas](#integración-con-citas)
10. [Códigos QR](#códigos-qr)
11. [Facturación](#facturación)
12. [Reportes e Ingresos](#reportes-e-ingresos)
13. [Seguridad](#seguridad)
14. [Solución de Problemas](#solución-de-problemas)

---

## 🎯 Introducción

El Sistema de Pagos con QR es una solución completa y modernizada para gestionar todos los pagos de la veterinaria. Incluye:

- **Múltiples métodos de pago** (efectivo, tarjetas, transferencias, QR)
- **Generación automática de códigos QR** para pagos digitales
- **Dashboard de ingresos** con gráficos interactivos
- **Pagos parciales** y reembolsos
- **Facturación electrónica** (NIT, razón social)
- **Auditoría completa** de todas las transacciones

---

## ✨ Características Principales

### 1. **Gestión Completa de Pagos**
- Crear, ver, editar y eliminar pagos
- Estados: Pendiente, Procesando, Completado, Fallido, Reembolsado, Cancelado
- Pagos asociados a citas específicas
- Historial detallado de cada pago

### 2. **Códigos QR Automáticos**
- Generación automática de QR para pagos digitales
- QR con vencimiento (24 horas por defecto)
- Regeneración de QR vencidos
- Descarga de imagen QR

### 3. **Pagos Parciales**
- Permite registrar pagos por cuotas
- Seguimiento del saldo pendiente
- Historial de pagos parciales

### 4. **Reembolsos**
- Procesamiento de reembolsos con razón
- Actualización automática del estado de la cita
- Registro en historial de auditoría

### 5. **Dashboard de Ingresos**
- Estadísticas en tiempo real
- Gráficos de ingresos por día
- Distribución por método de pago
- Top 10 de pagos más grandes
- Alertas de pagos vencidos

### 6. **Facturación**
- Soporte para factura con NIT
- Razón social del cliente
- Generación de número de factura automático

---

## 💳 Métodos de Pago Soportados

| Método | Código | Descripción | QR |
|--------|--------|-------------|-----|
| Efectivo | `efectivo` | Pago en efectivo | No |
| Tarjeta de Crédito | `tarjeta_credito` | Visa, Mastercard, etc. | No |
| Tarjeta de Débito | `tarjeta_debito` | Débito bancario | No |
| Transferencia Bancaria | `transferencia_bancaria` | Transferencia entre cuentas | No |
| QR Simple | `qr_simple` | Código QR genérico | ✅ |
| Tigo Money QR | `qr_tigo_money` | QR de Tigo Money | ✅ |
| QR Bancario | `qr_banco` | QR de bancos (BNB, BCP, etc.) | ✅ |

---

## 🏗️ Arquitectura del Sistema

### Componentes

```
Sistema de Pagos
│
├── Modelos (app/models/pago.py)
│   ├── Pago
│   └── HistorialPago
│
├── Controlador (app/controllers/pagos_controller.py)
│   ├── Dashboard
│   ├── CRUD de Pagos
│   ├── Procesamiento
│   ├── QR Generation
│   └── APIs
│
└── Vistas (app/templates/admin/pagos/)
    ├── dashboard.html
    ├── listar.html
    ├── crear.html
    └── ver.html
```

### Flujo de Pago

```
1. Crear Pago
   ↓
2. Seleccionar Método
   ↓
3. [Si es QR] → Generar Código QR
   ↓
4. Cliente Paga
   ↓
5. Marcar como Completado
   ↓
6. Actualizar Cita (si aplica)
   ↓
7. Registrar en Historial
```

---

## 🔧 Instalación y Configuración

### 1. **Instalar Dependencias**

```bash
pip install qrcode==7.4.2
pip install Pillow==10.4.0
```

O usar el requirements.txt:

```bash
pip install -r requirements.txt
```

### 2. **Ejecutar Migraciones**

```bash
# Crear migración
flask db migrate -m "Agregar tablas de pagos"

# Aplicar migración
flask db upgrade
```

### 3. **Verificar Instalación**

El blueprint de pagos ya está registrado en `app/__init__.py`:

```python
from app.controllers.pagos_controller import pagos_bp
app.register_blueprint(pagos_bp, url_prefix='/pagos')
```

### 4. **Acceder al Sistema**

Una vez instalado, el sistema de pagos estará disponible en:

- **Dashboard**: `http://localhost:5000/pagos/`
- **Crear Pago**: `http://localhost:5000/pagos/crear`
- **Listar Pagos**: `http://localhost:5000/pagos/listar`

---

## 📖 Guía de Uso

### Crear un Nuevo Pago

1. Ir a **Pagos** → **Nuevo Pago**
2. Completar el formulario:
   - **Monto**: Cantidad en Bs.
   - **Método de Pago**: Seleccionar de la lista
   - **Cliente**: Seleccionar tutor
   - **Cita Asociada** (opcional): Si el pago es por una cita
   - **Requiere Factura**: Marcar si necesita factura

3. Si seleccionas una **cita pendiente**, se autocompleta:
   - El monto (costo de la cita)
   - El cliente (tutor de la cita)
   - La descripción

4. Hacer clic en **Crear Pago**

### Procesar un Pago

1. Ir al detalle del pago
2. Hacer clic en **Marcar como Completado**
3. Completar información adicional:
   - Número de transacción (opcional)
   - Número de autorización (opcional)
   - Banco (para tarjetas)
   - Últimos 4 dígitos (para tarjetas)

4. El sistema automáticamente:
   - Marca el pago como completado
   - Actualiza la fecha de pago
   - Si hay cita asociada, la marca como pagada
   - Registra en el historial

### Registrar Pago Parcial

1. Ir al detalle del pago pendiente
2. Hacer clic en **Registrar Pago Parcial**
3. Ingresar el monto del pago parcial
4. El sistema calcula automáticamente el saldo pendiente

### Procesar Reembolso

1. Ir al detalle del pago completado
2. Hacer clic en **Procesar Reembolso**
3. Ingresar la razón del reembolso
4. Confirmar

⚠️ **Nota**: Solo se pueden reembolsar pagos completados.

### Generar/Regenerar Código QR

Para métodos de pago con QR:

1. El QR se genera **automáticamente** al crear el pago
2. Si el QR vence (24 horas), hacer clic en **Regenerar QR**
3. Descargar la imagen del QR si es necesario

---

## 🌐 API y Endpoints

### Rutas Principales

| Método | Ruta | Descripción |
|--------|------|-------------|
| GET | `/pagos/` | Dashboard de pagos |
| GET | `/pagos/listar` | Lista de todos los pagos |
| GET/POST | `/pagos/crear` | Crear nuevo pago |
| GET | `/pagos/<id>` | Ver detalle de pago |
| POST | `/pagos/<id>/procesar` | Marcar como completado |
| POST | `/pagos/<id>/pago-parcial` | Registrar pago parcial |
| POST | `/pagos/<id>/reembolsar` | Procesar reembolso |
| POST | `/pagos/<id>/regenerar-qr` | Regenerar código QR |
| GET | `/pagos/<id>/qr-image` | Descargar imagen QR |

### APIs Auxiliares

| Método | Ruta | Descripción |
|--------|------|-------------|
| GET | `/pagos/api/buscar-usuario` | Buscar usuarios (autocompletado) |
| GET | `/pagos/api/cita/<id>` | Obtener información de cita |

---

## 🗄️ Base de Datos

### Tabla: `pagos`

| Campo | Tipo | Descripción |
|-------|------|-------------|
| `id` | Integer | ID único |
| `codigo_pago` | String(50) | Código único (PAG-YYYYMMDD-NNNN) |
| `monto` | Float | Monto total |
| `monto_pagado` | Float | Monto pagado (para pagos parciales) |
| `metodo_pago` | String(50) | Método de pago |
| `estado` | String(20) | Estado del pago |
| `qr_code_data` | Text | Datos del QR |
| `qr_code_image` | Text | Imagen QR en base64 |
| `qr_vencimiento` | DateTime | Vencimiento del QR |
| `numero_transaccion` | String(100) | Número de transacción |
| `numero_autorizacion` | String(100) | Número de autorización |
| `banco` | String(100) | Banco emisor |
| `ultimos_digitos_tarjeta` | String(4) | Últimos 4 dígitos |
| `descripcion` | Text | Descripción |
| `notas` | Text | Notas adicionales |
| `comprobante_url` | String(500) | URL del comprobante |
| `requiere_factura` | Boolean | Si requiere factura |
| `numero_factura` | String(50) | Número de factura |
| `nit_cliente` | String(50) | NIT del cliente |
| `razon_social_cliente` | String(200) | Razón social |
| `fecha_creacion` | DateTime | Fecha de creación |
| `fecha_pago` | DateTime | Fecha de pago |
| `fecha_vencimiento` | DateTime | Fecha de vencimiento |
| `fecha_reembolso` | DateTime | Fecha de reembolso |
| `cita_id` | Integer | FK a citas |
| `usuario_id` | Integer | FK a usuarios (cliente) |
| `procesado_por_id` | Integer | FK a usuarios (quien procesó) |

### Tabla: `historial_pagos`

| Campo | Tipo | Descripción |
|-------|------|-------------|
| `id` | Integer | ID único |
| `pago_id` | Integer | FK a pagos |
| `accion` | String(50) | Acción realizada |
| `estado_anterior` | String(20) | Estado anterior |
| `estado_nuevo` | String(20) | Estado nuevo |
| `monto_anterior` | Float | Monto anterior |
| `monto_nuevo` | Float | Monto nuevo |
| `descripcion` | Text | Descripción |
| `fecha` | DateTime | Fecha del cambio |
| `usuario_id` | Integer | FK a usuarios (quien hizo el cambio) |

---

## 🔗 Integración con Citas

### Relación Cita-Pago

Un pago puede estar asociado a una cita:

```python
# Crear pago desde una cita
cita = Cita.query.get(cita_id)
pago = Pago(
    monto=cita.costo,
    usuario_id=cita.tutor_id,
    cita_id=cita.id,
    ...
)
```

### Actualización Automática

Cuando un pago se completa, si está asociado a una cita:

```python
if pago.cita_id:
    cita = Cita.query.get(pago.cita_id)
    cita.pagado = True
    cita.metodo_pago = pago.metodo_pago
```

---

## 📱 Códigos QR

### Generación Automática

Los códigos QR se generan automáticamente para métodos:
- `qr_simple`
- `qr_tigo_money`
- `qr_banco`

### Formato del QR

El QR contiene un JSON con:

```json
{
  "codigo": "PAG-20251117-0001",
  "monto": 150.00,
  "descripcion": "Pago de consulta para Max",
  "veterinaria": "Sistema Veterinario",
  "fecha": "2025-11-17T15:30:00"
}
```

### Vencimiento

- Por defecto: **24 horas**
- Configurable en el modelo
- Se puede regenerar si vence

### Descarga de QR

La imagen QR está disponible en:

```
GET /pagos/<id>/qr-image
```

Retorna un PNG con el código QR.

---

## 🧾 Facturación

### Campos de Factura

- **NIT/CI**: Número de identificación tributaria
- **Razón Social**: Nombre completo o razón social
- **Número de Factura**: Generado automáticamente

### Flujo de Facturación

1. Al crear el pago, marcar **Requiere Factura**
2. Completar NIT y Razón Social
3. El sistema genera número de factura automáticamente
4. El número sigue el formato: `FACT-YYYYMMDD-NNNN`

---

## 📊 Reportes e Ingresos

### Dashboard de Ingresos

Muestra:

1. **Estadísticas Generales**:
   - Ingresos totales del período
   - Cantidad de pagos completados
   - Pagos pendientes
   - Monto total pendiente
   - Pagos vencidos

2. **Gráficos**:
   - **Ingresos por Día**: Gráfico de línea
   - **Métodos de Pago**: Gráfico de dona

3. **Tablas**:
   - Pagos recientes (últimos 10)
   - Top 10 pagos más grandes

### Filtros de Fecha

- Por defecto: Último mes
- Personalizable con fecha inicio y fin
- Los gráficos se actualizan automáticamente

---

## 🔒 Seguridad

### Control de Acceso

Solo usuarios **admin** pueden:
- Ver el dashboard de pagos
- Crear pagos
- Procesar pagos
- Emitir reembolsos

### Auditoría

Toda acción se registra en `historial_pagos`:
- Quién hizo la acción
- Cuándo se hizo
- Qué cambió (estado, monto)

### Validaciones

- Montos positivos
- Estados válidos
- QR no vencidos para procesamiento
- Reembolsos solo de pagos completados

---

## 🐛 Solución de Problemas

### Error: "No module named 'qrcode'"

**Solución**:
```bash
pip install qrcode Pillow
```

### Error: "Tabla 'pagos' no existe"

**Solución**:
```bash
flask db migrate -m "Crear tablas de pagos"
flask db upgrade
```

### El QR no se genera

**Verificar**:
1. Que el método de pago sea uno con QR
2. Que Pillow esté instalado
3. Que no haya errores en la consola

### Los pagos no aparecen en el dashboard

**Verificar**:
1. Rango de fechas seleccionado
2. Estado del pago
3. Que estés logueado como admin

### Error al procesar pago: "Pago no encontrado"

**Verificar**:
1. Que el pago exista en la base de datos
2. Que tengas permisos de admin
3. Que el ID sea correcto

---

## 📝 Notas Importantes

### Para Desarrolladores

1. **Extender Métodos de Pago**:
   - Agregar en el enum de `metodo_pago`
   - Actualizar `metodo_pago_label` property
   - Agregar en los formularios

2. **Personalizar QR**:
   - Modificar `_generar_datos_qr_estandar()` en el modelo
   - Cambiar formato JSON según estándar del país

3. **Integrar con Pasarelas**:
   - Usar webhooks para actualizar estado automáticamente
   - Implementar verificación de firma digital

### Para Administradores

1. **Backup Regular**: Hacer backup de la tabla `pagos`
2. **Conciliación**: Conciliar pagos con extractos bancarios
3. **Reportes**: Exportar reportes mensuales para contabilidad

---

## 🚀 Próximas Mejoras (Roadmap)

- [ ] Integración con pasarelas de pago (Stripe, PayPal)
- [ ] Envío de recibo por email automático
- [ ] Generación de PDF para recibos
- [ ] Recordatorios de pagos vencidos
- [ ] Planes de pago (cuotas programadas)
- [ ] Descuentos y cupones
- [ ] Programa de lealtad/puntos
- [ ] Integración con sistemas contables
- [ ] App móvil para escanear QR

---

## 📞 Soporte

Para problemas o consultas sobre el sistema de pagos:

1. Revisar esta documentación
2. Verificar logs en la consola
3. Contactar al equipo de desarrollo

---

## 📄 Licencia

Este sistema es parte del Sistema Veterinario v2.0.0

---

**Última actualización**: 17 de Noviembre, 2025
**Versión del Sistema de Pagos**: 1.0.0
