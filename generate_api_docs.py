import os
import importlib
import traceback

PACKAGE = "waterrocketpy"
DOCS_DIR = "docs/api"


def get_module_path(py_path: str) -> str:
    """Convert a Python file path to a module path."""
    rel_path = os.path.relpath(py_path, PACKAGE)
    mod_path = os.path.splitext(rel_path)[0].replace(os.sep, ".")
    return f"{PACKAGE}.{mod_path}"


def get_doc_path(py_path: str) -> str:
    """Get output .md path from Python file path."""
    rel_path = os.path.relpath(py_path, PACKAGE)
    md_path = os.path.join(DOCS_DIR, rel_path).replace(".py", ".md")
    return md_path


def is_importable(module: str) -> bool:
    """Try importing the module path."""
    try:
        importlib.import_module(module)
        return True
    except Exception:
        print(f"❌ Skipping (not importable): {module}")
        print(traceback.format_exc(limit=1))
        return False


def write_md(module: str, md_path: str):
    """Create .md file with mkdocstrings block."""
    os.makedirs(os.path.dirname(md_path), exist_ok=True)
    with open(md_path, "w", encoding="utf-8") as f:
        f.write(f"# {module}\n\n::: {module}\n")


def walk_and_generate():
    """Walk through the package and generate valid .md files."""
    nav_entries = []
    for root, _, files in os.walk(PACKAGE):
        for file in files:
            if not file.endswith(".py") or file.startswith("__"):
                continue
            full_path = os.path.join(root, file)
            module = get_module_path(full_path)
            md_path = get_doc_path(full_path)
            if is_importable(module):
                write_md(module, md_path)
                nav_label = module.replace(f"{PACKAGE}.", "").replace(".", " / ").title()
                nav_path = os.path.relpath(md_path, "docs").replace("\\", "/")
                nav_entries.append((nav_label, nav_path))
    return nav_entries


def print_nav_block(entries):
    """Print YAML snippet for mkdocs.yml."""
    print("\n📄 Paste this into your mkdocs.yml under `nav:`:\n")
    print("  - API Reference:")
    for label, path in entries:
        print(f"      - {label}: {path}")


if __name__ == "__main__":
    print(f"🔍 Scanning '{PACKAGE}' and generating valid API docs...")
    valid_entries = walk_and_generate()
    print_nav_block(valid_entries)
    print(f"\n✅ Finished. {len(valid_entries)} valid module(s) documented.")
