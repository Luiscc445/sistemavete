from app import create_app, db
from app.models.servicio import Servicio
from app.models.user import Usuario
from datetime import date

app = create_app()

def seed_services():
    """Sembrar servicios iniciales"""
    servicios = [
        {
            'codigo': 'CONS-GEN',
            'nombre': 'Consulta General',
            'categoria': 'Consulta',
            'descripcion': 'Evaluación general del estado de salud de la mascota.',
            'precio': 100.00,
            'duracion': 30
        },
        {
            'codigo': 'CONS-CARD',
            'nombre': 'Cardiología',
            'categoria': 'Especialidad',
            'descripcion': 'Evaluación especializada del corazón y sistema circulatorio.',
            'precio': 250.00,
            'duracion': 45
        },
        {
            'codigo': 'CONS-DERM',
            'nombre': 'Dermatología',
            'categoria': 'Especialidad',
            'descripcion': 'Diagnóstico y tratamiento de enfermedades de la piel.',
            'precio': 200.00,
            'duracion': 40
        },
        {
            'codigo': 'CONS-CIR',
            'nombre': 'Evaluación Quirúrgica',
            'categoria': 'Cirugía',
            'descripcion': 'Evaluación pre-operatoria para procedimientos quirúrgicos.',
            'precio': 180.00,
            'duracion': 40
        },
        {
            'codigo': 'VAC-GEN',
            'nombre': 'Vacunación',
            'categoria': 'Preventiva',
            'descripcion': 'Aplicación de vacunas anuales y refuerzos.',
            'precio': 80.00,
            'duracion': 20
        }
    ]

    print("Sembrando servicios...")
    for s in servicios:
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

def seed_veterinarians():
    """Sembrar veterinarios iniciales"""
    veterinarios = [
        {
            'nombre': 'Ana',
            'apellido': 'Martinez',
            'email': 'ana.martinez@vet.com',
            'password': 'vet123',
            'especialidad': 'Cardiología',
            'licencia': 'VET-001'
        },
        {
            'nombre': 'Carlos',
            'apellido': 'Ruiz',
            'email': 'carlos.ruiz@vet.com',
            'password': 'vet123',
            'especialidad': 'Dermatología',
            'licencia': 'VET-002'
        },
        {
            'nombre': 'Sofia',
            'apellido': 'Lopez',
            'email': 'sofia.lopez@vet.com',
            'password': 'vet123',
            'especialidad': 'Cirugía',
            'licencia': 'VET-003'
        },
        {
            'nombre': 'Miguel',
            'apellido': 'Angel',
            'email': 'miguel.angel@vet.com',
            'password': 'vet123',
            'especialidad': 'Medicina General',
            'licencia': 'VET-004'
        }
    ]

    print("\nSembrando veterinarios...")
    for v in veterinarios:
        user = Usuario.query.filter_by(email=v['email']).first()
        if not user:
            nuevo_vet = Usuario(
                username=v['email'].split('@')[0],
                email=v['email'],
                password=v['password'],
                nombre=v['nombre'],
                apellido=v['apellido'],
                rol='veterinario',
                especialidad=v['especialidad'],
                licencia_profesional=v['licencia'],
                activo=True
            )
            db.session.add(nuevo_vet)
            print(f"  + Creado: Dr. {v['nombre']} {v['apellido']}")
        else:
            print(f"  * Ya existe: Dr. {v['nombre']} {v['apellido']}")

    db.session.commit()

if __name__ == '__main__':
    with app.app_context():
        print("=== INICIANDO SEED DE DATOS ===")
        try:
            seed_services()
            seed_veterinarians()
            print("\n=== SEED COMPLETADO EXITOSAMENTE ===")
        except Exception as e:
            print(f"\nERROR: {str(e)}")
            db.session.rollback()
