#!/usr/bin/env python3
"""
Script de Refactorización de Templates - VetSystem
==================================================
Este script inteligente refactoriza las vistas del tutor separando:
- CSS inline -> archivos CSS externos en /static/css/tutor/
- JavaScript inline -> archivos JS externos (opcional)
- HTML limpio que referencia los archivos externos

Mantiene toda la funcionalidad intacta mientras mejora la organización del código.
"""

import os
import re
from pathlib import Path
from typing import Dict, Tuple, List
import shutil
from datetime import datetime


class TemplateRefactor:
    """Clase principal para refactorizar templates HTML."""
    
    def __init__(self, base_path: str):
        self.base_path = Path(base_path)
        self.templates_dir = self.base_path / "app" / "templates" / "views" / "tutor"
        self.static_dir = self.base_path / "app" / "static"
        self.css_dir = self.static_dir / "css" / "tutor"
        self.js_dir = self.static_dir / "js" / "tutor"
        self.backup_dir = self.base_path / "backup_templates" / datetime.now().strftime("%Y%m%d_%H%M%S")
        
        # Crear directorios necesarios
        self.css_dir.mkdir(parents=True, exist_ok=True)
        self.js_dir.mkdir(parents=True, exist_ok=True)
        self.backup_dir.mkdir(parents=True, exist_ok=True)
        
        self.stats = {
            'processed': 0,
            'css_extracted': 0,
            'js_extracted': 0,
            'errors': []
        }
    
    def extract_css(self, html_content: str, filename: str) -> Tuple[str, str]:
        """
        Extrae todo el CSS inline de un archivo HTML.
        
        Returns:
            Tuple[str, str]: (HTML sin CSS, CSS extraído)
        """
        css_blocks = []
        
        # Buscar todos los bloques <style>...</style>
        style_pattern = r'<style[^>]*>(.*?)</style>'
        matches = re.finditer(style_pattern, html_content, re.DOTALL | re.IGNORECASE)
        
        for match in matches:
            css_content = match.group(1).strip()
            if css_content:
                css_blocks.append(css_content)
        
        # Eliminar los bloques de style del HTML
        html_cleaned = re.sub(style_pattern, '', html_content, flags=re.DOTALL | re.IGNORECASE)
        
        # Unir todo el CSS
        combined_css = '\n\n'.join(css_blocks)
        
        return html_cleaned, combined_css
    
    def extract_javascript(self, html_content: str, filename: str) -> Tuple[str, str]:
        """
        Extrae JavaScript inline (opcional, solo si es grande).
        
        Returns:
            Tuple[str, str]: (HTML sin JS inline grande, JS extraído)
        """
        js_blocks = []
        
        # Buscar bloques <script> que NO sean referencias externas
        script_pattern = r'<script(?![^>]*src=)[^>]*>(.*?)</script>'
        matches = list(re.finditer(script_pattern, html_content, re.DOTALL | re.IGNORECASE))
        
        # Solo extraer si hay mucho JavaScript (más de 1000 caracteres)
        for match in matches:
            js_content = match.group(1).strip()
            if len(js_content) > 1000:  # Solo bloques grandes
                js_blocks.append(js_content)
                # Reemplazar con referencia externa
                html_content = html_content.replace(match.group(0), 
                    f'<script src="{{{{ url_for(\'static\', filename=\'js/tutor/{filename.replace(".html", ".js")}\') }}}}"></script>')
        
        combined_js = '\n\n'.join(js_blocks)
        
        return html_content, combined_js
    
    def add_css_reference(self, html_content: str, css_filename: str) -> str:
        """
        Agrega la referencia al archivo CSS externo en el <head> del HTML.
        """
        # Buscar el cierre de </head>
        head_close_pattern = r'(</head>)'
        
        css_link = f'''    <link rel="stylesheet" href="{{{{ url_for('static', filename='css/tutor/{css_filename}') }}}}">
'''
        
        # Insertar antes del cierre de </head>
        if re.search(head_close_pattern, html_content, re.IGNORECASE):
            html_content = re.sub(
                head_close_pattern, 
                css_link + r'\1', 
                html_content, 
                count=1,
                flags=re.IGNORECASE
            )
        else:
            # Si no hay </head>, buscar después de los últimos <link> o <style>
            # Insertar después de {% block title %} o al inicio del {% block content %}
            block_content_pattern = r'({% block content %})'
            if re.search(block_content_pattern, html_content):
                html_content = re.sub(
                    block_content_pattern,
                    css_link + '\n' + r'\1',
                    html_content,
                    count=1
                )
        
        return html_content
    
    def clean_empty_lines(self, content: str) -> str:
        """Limpia líneas vacías excesivas."""
        # Reemplazar más de 2 líneas vacías consecutivas por solo 2
        content = re.sub(r'\n{3,}', '\n\n', content)
        return content.strip() + '\n'
    
    def process_template(self, template_path: Path) -> bool:
        """
        Procesa un template individual.
        
        Returns:
            bool: True si se procesó exitosamente
        """
        try:
            print(f"\n[>] Procesando: {template_path.name}")
            
            # Leer contenido original
            with open(template_path, 'r', encoding='utf-8') as f:
                original_content = f.read()
            
            # Crear backup
            backup_path = self.backup_dir / template_path.name
            shutil.copy2(template_path, backup_path)
            print(f"   [+] Backup creado en: {backup_path.relative_to(self.base_path)}")
            
            # Extraer CSS
            html_without_css, css_content = self.extract_css(original_content, template_path.name)
            
            if css_content:
                # Guardar CSS en archivo externo
                css_filename = template_path.stem + '.css'
                css_path = self.css_dir / css_filename
                
                with open(css_path, 'w', encoding='utf-8') as f:
                    f.write(f"/* CSS extraido de {template_path.name} */\n")
                    f.write(f"/* Generado automaticamente el {datetime.now().strftime('%Y-%m-%d %H:%M:%S')} */\n\n")
                    f.write(css_content)
                
                print(f"   [+] CSS extraido: {css_path.relative_to(self.base_path)} ({len(css_content)} caracteres)")
                self.stats['css_extracted'] += 1
                
                # Agregar referencia al CSS
                html_final = self.add_css_reference(html_without_css, css_filename)
            else:
                html_final = html_without_css
                print(f"   [!] No se encontro CSS inline")
            
            # Extraer JavaScript (opcional, solo si es muy grande)
            html_final, js_content = self.extract_javascript(html_final, template_path.name)
            
            if js_content:
                js_filename = template_path.stem + '.js'
                js_path = self.js_dir / js_filename
                
                with open(js_path, 'w', encoding='utf-8') as f:
                    f.write(f"// JavaScript extraido de {template_path.name}\n")
                    f.write(f"// Generado automaticamente el {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}\n\n")
                    f.write(js_content)
                
                print(f"   [+] JS extraido: {js_path.relative_to(self.base_path)} ({len(js_content)} caracteres)")
                self.stats['js_extracted'] += 1
            
            # Limpiar líneas vacías excesivas
            html_final = self.clean_empty_lines(html_final)
            
            # Guardar HTML refactorizado
            with open(template_path, 'w', encoding='utf-8') as f:
                f.write(html_final)
            
            print(f"   [+] Template refactorizado guardado")
            self.stats['processed'] += 1
            return True
            
        except Exception as e:
            error_msg = f"Error procesando {template_path.name}: {str(e)}"
            print(f"   [X] {error_msg}")
            self.stats['errors'].append(error_msg)
            return False
    
    def run(self):
        """Ejecuta el proceso de refactorización completo."""
        print("=" * 80)
        print("[*] INICIANDO REFACTORIZACION DE TEMPLATES")
        print("=" * 80)
        print(f"\n[+] Directorio de templates: {self.templates_dir}")
        print(f"[+] Directorio CSS: {self.css_dir}")
        print(f"[+] Directorio JS: {self.js_dir}")
        print(f"[+] Directorio de backups: {self.backup_dir}")
        
        # Obtener todos los archivos HTML
        html_files = list(self.templates_dir.glob('*.html'))
        
        if not html_files:
            print("\n[!] No se encontraron archivos HTML en el directorio de templates")
            return
        
        print(f"\n[+] Se encontraron {len(html_files)} archivos HTML para procesar")
        
        # Procesar cada archivo
        for template_path in html_files:
            self.process_template(template_path)
        
        # Mostrar resumen
        print("\n" + "=" * 80)
        print("[*] RESUMEN DE REFACTORIZACION")
        print("=" * 80)
        print(f"[+] Templates procesados: {self.stats['processed']}/{len(html_files)}")
        print(f"[+] Archivos CSS creados: {self.stats['css_extracted']}")
        print(f"[+] Archivos JS creados: {self.stats['js_extracted']}")
        
        if self.stats['errors']:
            print(f"\n[!] Errores encontrados: {len(self.stats['errors'])}")
            for error in self.stats['errors']:
                print(f"   - {error}")
        else:
            print("\n[+] Refactorizacion completada sin errores!")
        
        print(f"\n[+] Backups guardados en: {self.backup_dir}")
        print("\n" + "=" * 80)
        
        # Instrucciones finales
        print("\n[*] PROXIMOS PASOS:")
        print("1. Verifica que la aplicacion funcione correctamente")
        print("2. Revisa los archivos CSS creados en: app/static/css/tutor/")
        print("3. Si todo funciona bien, puedes eliminar el directorio de backup")
        print("4. Si hay problemas, restaura desde: " + str(self.backup_dir))
        print("\n" + "=" * 80)


def main():
    """Función principal."""
    # Obtener el directorio base del proyecto
    script_dir = Path(__file__).parent
    
    print("\n[*] Script de Refactorizacion de Templates - VetSystem")
    print(f"[+] Directorio base: {script_dir}\n")
    
    # Confirmar antes de proceder
    response = input("Deseas continuar con la refactorizacion? (si/no): ").strip().lower()
    
    if response not in ['si', 's', 'yes', 'y', 'sí']:
        print("\n[-] Refactorizacion cancelada por el usuario")
        return
    
    # Crear instancia y ejecutar
    refactor = TemplateRefactor(str(script_dir))
    refactor.run()


if __name__ == "__main__":
    main()

