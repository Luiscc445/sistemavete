#!/usr/bin/env python3
"""
Script para arreglar las referencias CSS en los templates refactorizados
"""

import os
from pathlib import Path

# Mapeo de archivos y sus CSS correspondientes
templates_css = {
    'quienes_somos.html': 'css/tutor/quienes_somos.css',
    'dashboard.html': 'css/tutor/dashboard.css',
    'mascotas.html': 'css/tutor/mascotas.css',
    'ver_mascota.html': 'css/tutor/ver_mascota.css',
}

base_path = Path(__file__).parent
templates_dir = base_path / "app" / "templates" / "views" / "tutor"

for template_name, css_path in templates_css.items():
    template_path = templates_dir / template_name
    
    if not template_path.exists():
        print(f"[!] No existe: {template_name}")
        continue
    
    # Leer contenido
    with open(template_path, 'r', encoding='utf-8') as f:
        lines = f.readlines()
    
    # Buscar si ya tiene el bloque extra_css
    has_extra_css = any('{% block extra_css %}' in line for line in lines)
    
    if has_extra_css:
        print(f"[OK] Ya tiene extra_css: {template_name}")
        continue
    
    # Encontrar la línea del {% block content %}
    content_line_idx = None
    for i, line in enumerate(lines):
        if '{% block content %}' in line:
            content_line_idx = i
            break
    
    if content_line_idx is None:
        print(f"[!] No se encontró block content en: {template_name}")
        continue
    
    # Insertar el bloque extra_css antes del block content
    new_lines = lines[:content_line_idx]
    new_lines.append('\n')
    new_lines.append('{% block extra_css %}\n')
    new_lines.append(f'<link rel="stylesheet" href="{{{{ url_for(\'static\', filename=\'{css_path}\') }}}}">\n')
    new_lines.append('{% endblock %}\n')
    new_lines.append('\n')
    new_lines.extend(lines[content_line_idx:])
    
    # Escribir de vuelta
    with open(template_path, 'w', encoding='utf-8') as f:
        f.writelines(new_lines)
    
    print(f"[+] Arreglado: {template_name}")

print("\n[*] Proceso completado")
