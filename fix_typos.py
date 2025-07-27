import subprocess
import pathlib
import sys

# File extensions and paths to skip
SKIP_PATTERNS = [
    "*.csv", "*.geojson", "*.json", "*.js", "*.html",
    "*cff", "*.pdf", "*.ipynb","*.pyc","*.png","*.jpg", "./.git"
]
IGNORE_WORDS = "aci,acount,hist"

def should_skip(file_path):
    for pattern in SKIP_PATTERNS:
        if pathlib.PurePath(file_path).match(pattern):
            return True
    return False

INCLUDE_DIRS = ["waterrocketpy", "docs", "examples", "test"]

def find_files_to_check():
    files = []
    for directory in INCLUDE_DIRS:
        dir_path = pathlib.Path(directory)
        if dir_path.exists():
            files.extend([
                str(f) for f in dir_path.rglob("*")
                if f.is_file() and not should_skip(str(f))
            ])
    return files

def run_codespell_check(file_path):
    print(f"\n🔍 Checking: {file_path}")
    result = subprocess.run(
        ["codespell", "--ignore-words-list=" + IGNORE_WORDS, file_path],
        stdout=subprocess.PIPE,
        stderr=subprocess.PIPE,
        text=True
    )
    output = result.stdout.strip()
    if output:
        print("⚠️ Typos found:")
        print(output)
        return True
    else:
        print("✅ No typos found.")
        return False

def run_codespell_fix(file_path):
    print(f"✏️ Applying fixes to: {file_path}")
    subprocess.run(
        ["codespell", "-w", "--ignore-words-list=" + IGNORE_WORDS, file_path]
    )

def main():
    files = find_files_to_check()
    if not files:
        print("📁 No files found to check.")
        return

    for file_path in files:
        has_typos = run_codespell_check(file_path)
        if has_typos:
            choice = input("👉 Apply fixes to this file? [y/N]: ").strip().lower()
            if choice == "y":
                run_codespell_fix(file_path)
            else:
                print("⏭️ Skipping fix.")

if __name__ == "__main__":
    try:
        main()
    except KeyboardInterrupt:
        print("\n❌ Interrupted by user.")
        sys.exit(1)
