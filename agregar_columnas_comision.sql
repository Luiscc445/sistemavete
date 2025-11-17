-- Script para agregar columnas de división de ingresos a la tabla pagos

-- Verificar si las columnas ya existen
IF NOT EXISTS (SELECT * FROM INFORMATION_SCHEMA.COLUMNS
               WHERE TABLE_NAME = 'pagos' AND COLUMN_NAME = 'porcentaje_empresa')
BEGIN
    ALTER TABLE pagos ADD porcentaje_empresa FLOAT DEFAULT 57.14;
    PRINT '✓ Columna porcentaje_empresa agregada';
END
ELSE
BEGIN
    PRINT '⚠ Columna porcentaje_empresa ya existe';
END

IF NOT EXISTS (SELECT * FROM INFORMATION_SCHEMA.COLUMNS
               WHERE TABLE_NAME = 'pagos' AND COLUMN_NAME = 'porcentaje_veterinario')
BEGIN
    ALTER TABLE pagos ADD porcentaje_veterinario FLOAT DEFAULT 42.86;
    PRINT '✓ Columna porcentaje_veterinario agregada';
END
ELSE
BEGIN
    PRINT '⚠ Columna porcentaje_veterinario ya existe';
END

IF NOT EXISTS (SELECT * FROM INFORMATION_SCHEMA.COLUMNS
               WHERE TABLE_NAME = 'pagos' AND COLUMN_NAME = 'monto_empresa')
BEGIN
    ALTER TABLE pagos ADD monto_empresa FLOAT DEFAULT 0;
    PRINT '✓ Columna monto_empresa agregada';
END
ELSE
BEGIN
    PRINT '⚠ Columna monto_empresa ya existe';
END

IF NOT EXISTS (SELECT * FROM INFORMATION_SCHEMA.COLUMNS
               WHERE TABLE_NAME = 'pagos' AND COLUMN_NAME = 'monto_veterinario')
BEGIN
    ALTER TABLE pagos ADD monto_veterinario FLOAT DEFAULT 0;
    PRINT '✓ Columna monto_veterinario agregada';
END
ELSE
BEGIN
    PRINT '⚠ Columna monto_veterinario ya existe';
END

-- Verificar que se agregaron correctamente
SELECT
    COLUMN_NAME,
    DATA_TYPE,
    COLUMN_DEFAULT
FROM INFORMATION_SCHEMA.COLUMNS
WHERE TABLE_NAME = 'pagos'
  AND COLUMN_NAME IN ('porcentaje_empresa', 'porcentaje_veterinario', 'monto_empresa', 'monto_veterinario')
ORDER BY COLUMN_NAME;

PRINT '';
PRINT '========================================';
PRINT 'Columnas de división de ingresos agregadas correctamente';
PRINT 'Ahora los pagos se dividen automáticamente entre:';
PRINT '  - Empresa (57.14% por defecto)';
PRINT '  - Veterinario (42.86% por defecto)';
PRINT '========================================';
