
import sys
import os

# Add the current directory to sys.path
sys.path.append(os.getcwd())

try:
    from app import create_app
    app = create_app()
    print("SUCCESS: Application created successfully")
    
    # Verify blueprints
    print("Registered Blueprints:")
    for name, blueprint in app.blueprints.items():
        print(f"- {name}")
        
    # Verify specific routes
    with app.test_client() as client:
        # Check if admin routes exist (by checking url_map)
        print("\nChecking Routes:")
        routes = [r.rule for r in app.url_map.iter_rules()]
        required_routes = [
            '/',
            '/admin/dashboard',
            '/admin/veterinarios',
            '/admin/veterinario/nuevo',
            '/admin/tutores',
            '/admin/api/estadisticas/especies',
            '/admin/inventario/',
            '/admin/pagos/',
            '/admin/reportes/',
            '/tutor/dashboard',
            '/veterinario/dashboard'
        ]
        
        for req in required_routes:
            found = any(req in r for r in routes)
            print(f"- {req}: {'FOUND' if found else 'MISSING'}")
            
except Exception as e:
    print(f"ERROR: {e}")
    import traceback
    traceback.print_exc()
