from app.main import app

for route in app.routes:
    # Most interesting are APIRoute objects
    if hasattr(route, "path"):
        methods = getattr(route, "methods", [])
        print(f"{methods} {route.path}")
