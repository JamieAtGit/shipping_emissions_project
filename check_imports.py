import os
import ast
import importlib.util

PROJECT_ROOT = os.path.abspath(os.getcwd())

def is_import_valid(module_name):
    """Check if an importable module exists."""
    try:
        spec = importlib.util.find_spec(module_name)
        return spec is not None
    except Exception:
        return False

def analyze_file(filepath):
    with open(filepath, "r", encoding="utf-8") as file:
        node = ast.parse(file.read(), filename=filepath)

    errors = []
    for item in ast.walk(node):
        if isinstance(item, ast.Import):
            for alias in item.names:
                module = alias.name
                if not is_import_valid(module):
                    errors.append((filepath, module))
        elif isinstance(item, ast.ImportFrom):
            module = item.module
            if module and not is_import_valid(module):
                errors.append((filepath, module))
    return errors

def scan_directory(path):
    import_errors = []
    for dirpath, dirnames, filenames in os.walk(path):
        # Skip node_modules
        if "node_modules" in dirpath:
            continue
        for filename in filenames:
            if filename.endswith(".py"):
                filepath = os.path.join(dirpath, filename)
                import_errors.extend(analyze_file(filepath))
    return import_errors

if __name__ == "__main__":
    print(f"🔍 Scanning Python imports in: {PROJECT_ROOT}")
    errors = scan_directory(PROJECT_ROOT)
    if errors:
        print("\n❌ Broken imports found:")
        for filepath, module in errors:
            print(f" - {filepath}: `{module}` not found")
    else:
        print("\n✅ All imports look valid!")
