"""
Script de Reorganización MVC - Veterinaria Flask
Reorganiza la estructura del proyecto siguiendo el patrón MVC correctamente.

Uso:
    python scripts/reorganize_mvc.py [--dry-run] [--backup-only]
    
Opciones:
    --dry-run: Muestra qué cambios se harían sin ejecutarlos
    --backup-only: Solo crea el backup sin reorganizar
"""

import os
import shutil
from datetime import datetime
from pathlib import Path
import sys

class MVCReorganizer:
    def __init__(self, project_root, dry_run=False):
        self.project_root = Path(project_root)
        self.app_dir = self.project_root / 'app'
        self.dry_run = dry_run
        self.timestamp = datetime.now().strftime('%Y-%m-%d_%H-%M-%S')
        self.backup_dir = self.app_dir / '_backups' / self.timestamp
        
    def log(self, message, level="INFO"):
        """Log con colores"""
        colors = {
            "INFO": "\033[94m",    # Azul
            "SUCCESS": "\033[92m", # Verde
            "WARNING": "\033[93m", # Amarillo
            "ERROR": "\033[91m",   # Rojo
            "RESET": "\033[0m"
        }
        prefix = f"{colors.get(level, '')}{level}{colors['RESET']}"
        print(f"[{prefix}] {message}")
        
    def create_backup(self):
        """Crea backup completo antes de reorganizar"""
        self.log("Creando backup de seguridad...", "INFO")
        
        if self.dry_run:
            self.log(f"[DRY RUN] Crearí backup en: {self.backup_dir}", "WARNING")
            return
            
        try:
            # Crear carpeta de backup
            self.backup_dir.mkdir(parents=True, exist_ok=True)
            
            # Backup de templates
            templates_src = self.app_dir / 'templates'
            templates_backup = self.backup_dir / 'templates_backup'
            if templates_src.exists():
                shutil.copytree(templates_src, templates_backup)
                self.log(f"✓ Backup de templates creado", "SUCCESS")
            
            # Backup de controllers
            controllers_src = self.app_dir / 'controllers'
            controllers_backup = self.backup_dir / 'controllers_backup'
            if controllers_src.exists():
                shutil.copytree(controllers_src, controllers_backup)
                self.log(f"✓ Backup de controllers creado", "SUCCESS")
                
            self.log(f"Backup completo guardado en: {self.backup_dir}", "SUCCESS")
            
        except Exception as e:
            self.log(f"Error creando backup: {e}", "ERROR")
            sys.exit(1)
    
    def create_scripts_folder(self):
        """Crea la carpeta scripts/ con estructura"""
        self.log("Creando carpeta scripts/...", "INFO")
        
        scripts_dir = self.app_dir / 'scripts'
        utils_dir = scripts_dir / 'utils'
        
        if self.dry_run:
            self.log("[DRY RUN] Crearía carpeta scripts/", "WARNING")
            return
            
        try:
            scripts_dir.mkdir(exist_ok=True)
            utils_dir.mkdir(exist_ok=True)
            
            # Crear __init__.py
            (scripts_dir / '__init__.py').write_text('"""Scripts de automatización"""')
            (utils_dir / '__init__.py').write_text('"""Utilidades para scripts"""')
            
            # Crear archivo README
            readme_content = """# Scripts de Automatización

Esta carpeta contiene scripts para automatizar tareas del proyecto.

## Scripts Disponibles

- `reorganize_mvc.py` - Reorganiza estructura MVC
- `backup_database.py` - Backup de base de datos
- `seed_data.py` - Pobla datos de prueba

## Uso

```bash
python scripts/nombre_script.py
```
"""
            (scripts_dir / 'README.md').write_text(readme_content)
            
            self.log("✓ Carpeta scripts/ creada", "SUCCESS")
            
        except Exception as e:
            self.log(f"Error creando scripts/: {e}", "ERROR")
    
    def rename_templates_to_views(self):
        """Renombra carpeta templates/ a views/"""
        self.log("Renombrando templates/ → views/...", "INFO")
        
        templates_dir = self.app_dir / 'templates'
        views_dir = self.app_dir / 'views'
        
        if self.dry_run:
            self.log(f"[DRY RUN] Renombraría {templates_dir} → {views_dir}", "WARNING")
            return
            
        try:
            if templates_dir.exists() and not views_dir.exists():
                templates_dir.rename(views_dir)
                self.log("✓ templates/ renombrado a views/", "SUCCESS")
            elif views_dir.exists():
                self.log("views/ ya existe, omitiendo", "WARNING")
            else:
                self.log("templates/ no encontrado", "WARNING")
                
        except Exception as e:
            self.log(f"Error renombrando: {e}", "ERROR")
    
    def organize_views(self):
        """Organiza las vistas en la nueva estructura"""
        self.log("Organizando vistas...", "INFO")
        
        views_dir = self.app_dir / 'views'
        
        if not views_dir.exists():
            self.log("views/ no existe, saltando", "WARNING")
            return
            
        if self.dry_run:
            self.log("[DRY RUN] Organizaría vistas en views/", "WARNING")
            return
        
        try:
            # Crear carpeta shared para archivos compartidos
            shared_dir = views_dir / 'shared'
            shared_dir.mkdir(exist_ok=True)
            
            # Mover base.html a shared/
            base_html = views_dir / 'shared/base.html'
            if base_html.exists():
                shutil.move(str(base_html), str(shared_dir / 'shared/base.html'))
                self.log("✓ base.html movido a shared/", "SUCCESS")
            
            # Mover errors a shared/
            errors_dir = views_dir / 'errors'
            if errors_dir.exists():
                shutil.move(str(errors_dir), str(shared_dir / 'errors'))
                self.log("✓ errors/ movido a shared/", "SUCCESS")
                
            # Consolidar dashboards/ con tutor/
            dashboards_dir = views_dir / 'dashboards'
            tutor_dir = views_dir / 'tutor'
            if dashboards_dir.exists() and tutor_dir.exists():
                for item in dashboards_dir.iterdir():
                    if item.name.startswith('tutor'):
                        shutil.move(str(item), str(tutor_dir / item.name))
                self.log("✓ Dashboards consolidados", "SUCCESS")
                
            self.log("✓ Vistas organizadas", "SUCCESS")
            
        except Exception as e:
            self.log(f"Error organizando vistas: {e}", "ERROR")
    
    def update_references(self):
        """Actualiza referencias de templates/ a views/ en archivos Python"""
        self.log("Actualizando referencias en código...", "INFO")
        
        if self.dry_run:
            self.log("[DRY RUN] Actualizaría referencias en archivos .py", "WARNING")
            return
        
        try:
            count = 0
            controllers_dir = self.app_dir / 'controllers'
            
            for py_file in controllers_dir.rglob('*.py'):
                content = py_file.read_text(encoding='utf-8')
                updated_content = content.replace(
                    "render_template('", 
                    "render_template('"
                ).replace("'templates/", "'views/")
                
                if content != updated_content:
                    py_file.write_text(updated_content, encoding='utf-8')
                    count += 1
                    
            self.log(f"✓ {count} archivos actualizados", "SUCCESS")
            
        except Exception as e:
            self.log(f"Error actualizando referencias: {e}", "ERROR")
    
    def create_summary_report(self):
        """Crea un reporte del resumen de cambios"""
        report_path = self.backup_dir / 'reorganization_report.txt'
        
        report = f"""
REPORTE DE REORGANIZACIÓN MVC
================================
Fecha: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}
Proyecto: Veterinaria Flask

CAMBIOS REALIZADOS:
✓ Backup creado en: _backups/{self.timestamp}/
✓ Carpeta scripts/ creada
✓ templates/ renombrado a views/
✓ Vistas organizadas (shared/, errors/)
✓ Referencias actualizadas en controladores

NUEVA ESTRUCTURA:
app/
├── models/          (sin cambios)
├── views/           (antes templates/)
│   ├── admin/
│   ├── veterinario/
│   ├── tutor/
│   └── shared/      (nuevo)
├── controllers/     (sin cambios)
├── static/          (sin cambios)
├── scripts/         (nuevo)
└── _backups/        (nuevo)

Para revertir cambios: Restaurar desde _backups/{self.timestamp}/
"""
        
        if not self.dry_run:
            report_path.write_text(report, encoding='utf-8')
            
        print(report)
    
    def run(self):
        """Ejecuta la reorganización completa"""
        self.log("="*60, "INFO")
        self.log("REORGANIZACIÓN MVC - VETERINARIA FLASK", "INFO")
        self.log("="*60, "INFO")
        
        if self.dry_run:
            self.log("MODO DRY RUN - No se realizarán cambios reales", "WARNING")
        
        # Paso 1: Backup
        self.create_backup()
        
        # Paso 2: Crear scripts/
        self.create_scripts_folder()
        
        # Paso 3: Renombrar templates → views
        self.rename_templates_to_views()
        
        # Paso 4: Organizar vistas
        self.organize_views()
        
        # Paso 5: Actualizar referencias
        self.update_references()
        
        # Paso 6: Reporte
        self.create_summary_report()
        
        self.log("="*60, "SUCCESS")
        self.log("REORGANIZACIÓN COMPLETADA", "SUCCESS")
        self.log("="*60, "SUCCESS")

if __name__ == '__main__':
    # Obtener directorio del proyecto
    script_dir = Path(__file__).parent
    project_root = script_dir.parent.parent.parent  # app/scripts/ -> veterinaria_flask/
    
    # Verificar argumentos
    dry_run = '--dry-run' in sys.argv
    backup_only = '--backup-only' in sys.argv
    
    # Crear reorganizador
    reorganizer = MVCReorganizer(project_root, dry_run=dry_run)
    
    if backup_only:
        reorganizer.create_backup()
    else:
        reorganizer.run()
