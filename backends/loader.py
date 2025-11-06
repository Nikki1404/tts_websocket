import importlib, pkgutil, backends

def auto_import(pkg_name="backends"):
    """Dynamically import all backend modules under the 'backends' package."""
    pkg = importlib.import_module(pkg_name)
    for _, mod_name, _ in pkgutil.iter_modules(pkg.__path__):
        if mod_name not in {"__init__", "base", "loader"}:
            importlib.import_module(f"{pkg_name}.{mod_name}")
