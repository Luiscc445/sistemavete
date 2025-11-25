"""
Script to seed comprehensive list of specialists and services.
"""
from app import create_app, db
from app.models.servicio import Servicio
from app.models.user import Usuario

app = create_app()

def seed_data():
    # 1. Services
    services_data = [
        {
            'codigo': 'CONS-ODON',
            'nombre': 'Limpieza Dental',
            'categoria': 'Odontología',
            'descripcion': 'Limpieza profunda y revisión dental.',
            'precio': 150.00,
            'duracion': 45
        },
        {
            'codigo': 'CONS-TRAU',
            'nombre': 'Consulta Traumatológica',
            'categoria': 'Traumatología',
            'descripcion': 'Evaluación de huesos, articulaciones y fracturas.',
            'precio': 220.00,
            'duracion': 40
        },
        {
            'codigo': 'CONS-OFT',
            'nombre': 'Consulta Oftalmológica',
            'categoria': 'Oftalmología',
            'descripcion': 'Revisión especializada de la vista y ojos.',
            'precio': 200.00,
            'duracion': 30
        },
        {
            'codigo': 'CONS-NEURO',
            'nombre': 'Consulta Neurológica',
            'categoria': 'Neurología',
            'descripcion': 'Evaluación del sistema nervioso y conducta.',
            'precio': 280.00,
            'duracion': 60
        },
        {
            'codigo': 'CONS-ONCO',
            'nombre': 'Consulta Oncológica',
            'categoria': 'Oncología',
            'descripcion': 'Diagnóstico y tratamiento del cáncer.',
            'precio': 300.00,
            'duracion': 50
        },
        {
            'codigo': 'IMG-ECO',
            'nombre': 'Ecografía',
            'categoria': 'Imagenología',
            'descripcion': 'Ultrasonido abdominal o pélvico.',
            'precio': 180.00,
            'duracion': 30
        }
    ]

    print("=== SEMBRANDO SERVICIOS ===")
    for s in services_data:
        servicio = Servicio.query.filter_by(codigo=s['codigo']).first()
        if not servicio:
            nuevo_servicio = Servicio(
                codigo=s['codigo'],
                nombre=s['nombre'],
                categoria=s['categoria'],
                descripcion=s['descripcion'],
                precio=s['precio'],
                duracion_estimada=s['duracion']
            )
            db.session.add(nuevo_servicio)
            print(f"  + Creado: {s['nombre']}")
        else:
            print(f"  * Ya existe: {s['nombre']}")
    
    db.session.commit()

    # 2. Veterinarians
    vets_data = [
        {
            'nombre': 'Laura',
            'apellido': 'Torres',
            'email': 'laura.torres@vet.com',
            'especialidad': 'Limpieza Dental', # Matches Service Name
            'licencia': 'VET-DENT-01'
        },
        {
            'nombre': 'Pedro',
            'apellido': 'Huesos',
            'email': 'pedro.huesos@vet.com',
            'especialidad': 'Consulta Traumatológica',
            'licencia': 'VET-TRAU-01'
        },
        {
            'nombre': 'Clara',
            'apellido': 'Vision',
            'email': 'clara.vision@vet.com',
            'especialidad': 'Consulta Oftalmológica',
            'licencia': 'VET-OFT-01'
        },
        {
            'nombre': 'Cerebro',
            'apellido': 'Mente',
            'email': 'cerebro.mente@vet.com',
            'especialidad': 'Consulta Neurológica',
            'licencia': 'VET-NEURO-01'
        },
        {
            'nombre': 'Wilson',
            'apellido': 'Tumor',
            'email': 'wilson.tumor@vet.com',
            'especialidad': 'Consulta Oncológica',
            'licencia': 'VET-ONCO-01'
        },
        {
            'nombre': 'Rayos',
            'apellido': 'X',
            'email': 'rayos.x@vet.com',
            'especialidad': 'Ecografía',
            'licencia': 'VET-IMG-01'
        }
    ]

    print("\n=== SEMBRANDO VETERINARIOS ===")
    for v in vets_data:
        user = Usuario.query.filter_by(email=v['email']).first()
        if not user:
            nuevo_vet = Usuario(
                username=v['email'].split('@')[0],
                email=v['email'],
                password='vet123', # Default password
                nombre=v['nombre'],
                apellido=v['apellido'],
                rol='veterinario',
                especialidad=v['especialidad'],
                licencia_profesional=v['licencia'],
                activo=True,
                verificado=True
            )
            db.session.add(nuevo_vet)
            print(f"  + Creado: Dr. {v['nombre']} {v['apellido']} ({v['especialidad']})")
        else:
            print(f"  * Ya existe: Dr. {v['nombre']} {v['apellido']}")
            # Update specialty if needed to match new service names
            if user.especialidad != v['especialidad']:
                user.especialidad = v['especialidad']
                print(f"    -> Actualizada especialidad a: {v['especialidad']}")

    db.session.commit()
    print("\n=== PROCESO COMPLETADO ===")

if __name__ == '__main__':
    with app.app_context():
        try:
            seed_data()
        except Exception as e:
            print(f"ERROR: {e}")
            db.session.rollback()
