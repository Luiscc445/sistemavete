"""
Script to update existing veterinarians' specialties to match Service names.
"""
from app import create_app, db
from app.models import Usuario, Servicio

app = create_app()

with app.app_context():
    print("=== INICIANDO MIGRACIÓN DE ESPECIALIDADES ===")
    
    veterinarios = Usuario.query.filter_by(rol='veterinario').all()
    servicios = Servicio.query.filter_by(activo=True).all()
    
    # Create a map of normalized service names to actual names
    # e.g., "cardiologia" -> "Cardiología"
    service_map = {s.nombre.lower(): s.nombre for s in servicios}
    
    print(f"Servicios disponibles: {list(service_map.values())}")
    
    updated_count = 0
    
    for vet in veterinarios:
        if not vet.especialidad:
            continue
            
        current_spec = vet.especialidad.lower().strip()
        
        # Try to find a match
        match = None
        
        # Direct match
        if current_spec in service_map:
            match = service_map[current_spec]
        
        # Partial match (e.g., "medicina general" -> "Consulta General")
        elif "general" in current_spec and "consulta general" in service_map:
            match = service_map["consulta general"]
        elif "ciru" in current_spec and "cirugía" in service_map: # cirugia, cirujano
            match = service_map["cirugía"]
        
        if match and match != vet.especialidad:
            print(f"Actualizando {vet.nombre_completo}: '{vet.especialidad}' -> '{match}'")
            vet.especialidad = match
            updated_count += 1
        elif not match:
            print(f"ADVERTENCIA: No se encontró coincidencia para {vet.nombre_completo} ('{vet.especialidad}')")
            # Assign default if needed, or leave as is
            # vet.especialidad = "Consulta General" 
            
    if updated_count > 0:
        db.session.commit()
        print(f"=== MIGRACIÓN COMPLETADA: {updated_count} veterinarios actualizados ===")
    else:
        print("=== MIGRACIÓN COMPLETADA: No se requirieron cambios ===")
