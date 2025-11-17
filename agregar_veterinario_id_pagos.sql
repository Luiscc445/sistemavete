-- Script para agregar columna veterinario_id a la tabla pagos
-- Esta columna almacena qué veterinario atendió la cita asociada al pago

-- Verificar si la columna ya existe
IF NOT EXISTS (SELECT * FROM INFORMATION_SCHEMA.COLUMNS
               WHERE TABLE_NAME = 'pagos' AND COLUMN_NAME = 'veterinario_id')
BEGIN
    ALTER TABLE pagos ADD veterinario_id INT NULL;
    PRINT '✓ Columna veterinario_id agregada a la tabla pagos';

    -- Agregar foreign key a la tabla usuarios
    ALTER TABLE pagos ADD CONSTRAINT FK_pagos_veterinario
        FOREIGN KEY (veterinario_id) REFERENCES usuarios(id);
    PRINT '✓ Foreign key FK_pagos_veterinario agregada';
END
ELSE
BEGIN
    PRINT '⚠ La columna veterinario_id ya existe en la tabla pagos';
END

-- Actualizar registros existentes que tienen cita asociada
-- para asignar el veterinario_id de la cita
UPDATE p
SET p.veterinario_id = c.veterinario_id
FROM pagos p
INNER JOIN citas c ON p.cita_id = c.id
WHERE p.veterinario_id IS NULL
  AND c.veterinario_id IS NOT NULL;

PRINT '✓ Registros existentes actualizados con veterinario_id';

-- Verificar la actualización
SELECT
    COUNT(*) as total_pagos,
    COUNT(veterinario_id) as pagos_con_veterinario,
    COUNT(*) - COUNT(veterinario_id) as pagos_sin_veterinario
FROM pagos;

PRINT '';
PRINT '========================================';
PRINT 'Columna veterinario_id agregada correctamente';
PRINT 'Ahora los pagos pueden rastrear qué veterinario';
PRINT 'atendió cada cita para calcular comisiones.';
PRINT '========================================';
