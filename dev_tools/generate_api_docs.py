import os
import importlib
import traceback
from collections import defaultdict

PACKAGE = "waterrocketpy"
DOCS_DIR = "docs/api"
DOCS_ROOT = "api"  # relative to 'docs'

def get_module_path(py_path: str) -> str:
    """Convert a file path to Python module path."""
    rel_path = os.path.relpath(py_path, PACKAGE)
    mod_path = os.path.splitext(rel_path)[0].replace(os.sep, ".")
    return f"{PACKAGE}.{mod_path}"

def get_doc_path(py_path: str) -> str:
    """Convert Python file path to corresponding Markdown path."""
    rel_path = os.path.relpath(py_path, PACKAGE)
    md_path = os.path.join(DOCS_DIR, rel_path).replace(".py", ".md")
    return md_path

def is_importable(module: str) -> bool:
    """Check if a module is importable."""
    try:
        importlib.import_module(module)
        return True
    except Exception:
        print(f"❌ Skipping (not importable): {module}")
        print(traceback.format_exc(limit=1))
        return False

def write_md(module: str, md_path: str):
    """Write MkDocs-compatible Markdown file with mkdocstrings directive."""
    os.makedirs(os.path.dirname(md_path), exist_ok=True)
    with open(md_path, "w", encoding="utf-8") as f:
        f.write(f"# {module}\n\n::: {module}\n")

def insert_nested(nav_tree, parts, path):
    """Insert path into nested nav structure."""
    if not parts:
        return
    head, *tail = parts
    if tail:
        nav_tree.setdefault(head, {})
        insert_nested(nav_tree[head], tail, path)
    else:
        nav_tree[head] = path

def build_nav_yaml(tree, indent=4):
    """Recursively build YAML nav from a nested dictionary."""
    lines = []
    for key in sorted(tree):
        value = tree[key]
        if isinstance(value, dict):
            lines.append(" " * indent + f"- {key}:")
            lines.extend(build_nav_yaml(value, indent + 2))
        else:
            lines.append(" " * indent + f"- {key}: {value}")
    return lines

def walk_and_generate():
    """Walk the package and generate Markdown docs with a nav tree."""
    nav_tree = {}
    for root, _, files in os.walk(PACKAGE):
        for file in sorted(files):
            if not file.endswith(".py") or file.startswith("_"):
                continue
            full_path = os.path.join(root, file)
            module = get_module_path(full_path)
            md_path = get_doc_path(full_path)
            if not is_importable(module):
                continue
            write_md(module, md_path)

            rel_parts = os.path.relpath(md_path, "docs").replace("\\", "/").split("/")
            rel_parts[-1] = rel_parts[-1].replace(".md", "")
            label_parts = [part.title().replace("_", " ") for part in rel_parts[1:]]
            insert_nested(nav_tree, label_parts, "/".join(rel_parts))
    return nav_tree

def print_nav_block(nav_tree):
    """Print the YAML nav block."""
    print("\n📄 Paste this into your mkdocs.yml under `nav:`:\n")
    print("nav:")
    print("  - API Reference:")
    lines = build_nav_yaml(nav_tree, indent=6)
    print("\n".join(lines))

if __name__ == "__main__":
    print(f"🔍 Scanning '{PACKAGE}' and generating Markdown docs in '{DOCS_DIR}'...")
    nav_structure = walk_and_generate()
    print_nav_block(nav_structure)
    print(f"\n✅ Finished generating API documentation.")
