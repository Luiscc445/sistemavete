-- Script para arreglar la tabla auditoria_acciones en SQL Server
-- Ejecuta este script en SQL Server Management Studio o tu herramienta de SQL Server

-- 1. Cambiar user_agent a NVARCHAR(MAX) para aceptar user-agents largos
ALTER TABLE auditoria_acciones
ALTER COLUMN user_agent NVARCHAR(MAX);

-- 2. Asegurarse de que descripcion es NVARCHAR(MAX)
ALTER TABLE auditoria_acciones
ALTER COLUMN descripcion NVARCHAR(MAX);

-- 3. Asegurarse de que datos_anteriores es NVARCHAR(MAX) y nullable
ALTER TABLE auditoria_acciones
ALTER COLUMN datos_anteriores NVARCHAR(MAX) NULL;

-- 4. Asegurarse de que datos_nuevos es NVARCHAR(MAX) y nullable
ALTER TABLE auditoria_acciones
ALTER COLUMN datos_nuevos NVARCHAR(MAX) NULL;

-- 5. Asegurarse de que ip_address puede ser NULL
ALTER TABLE auditoria_acciones
ALTER COLUMN ip_address VARCHAR(45) NULL;

-- Verificar los cambios
SELECT
    COLUMN_NAME,
    DATA_TYPE,
    CHARACTER_MAXIMUM_LENGTH,
    IS_NULLABLE
FROM INFORMATION_SCHEMA.COLUMNS
WHERE TABLE_NAME = 'auditoria_acciones'
AND COLUMN_NAME IN ('descripcion', 'datos_anteriores', 'datos_nuevos', 'user_agent', 'ip_address')
ORDER BY COLUMN_NAME;

PRINT 'Cambios aplicados correctamente. Verifica la tabla arriba.';
