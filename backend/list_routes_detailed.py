from app.main import app

for route in app.routes:
    # Handle APIRoute and Mount objects
    path = getattr(route, "path", "No path")
    name = getattr(route, "name", "No name")
    methods = sorted(list(getattr(route, "methods", [])))
    print(f"{methods} {path} ({name})")

    # If it's a Mount, look deeper
    if hasattr(route, "app") and hasattr(route.app, "routes"):
        for subroute in route.app.routes:
            subpath = getattr(subroute, "path", "No path")
            submethods = sorted(list(getattr(subroute, "methods", [])))
            print(f"  └─ {submethods} {path}{subpath}")
