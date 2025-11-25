# Scripts de Automatización

Esta carpeta contiene scripts para automatizar tareas del proyecto.

## Scripts Disponibles

### `reorganize_mvc.py`
Reorganiza la estructura del proyecto siguiendo el patrón MVC.

**Uso:**
```bash
# Ver qué cambios se harían (recomendado primero)
python app/scripts/reorganize_mvc.py --dry-run

# Ejecutar reorganización
python app/scripts/reorganize_mvc.py

# Solo crear backup
python app/scripts/reorganize_mvc.py --backup-only
```

### Próximamente
- `backup_database.py` - Backup de base de datos
- `seed_data.py` - Poblar datos de prueba

## Cómo Usar

Los scripts se ejecutan desde la raíz del proyecto:

```bash
cd veterinaria_flask/
python app/scripts/nombre_script.py
```
