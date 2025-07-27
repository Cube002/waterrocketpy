import subprocess

def run_codespell():
    # Run codespell in auto-correct mode
    print("Running codespell with --write-changes...")
    result = subprocess.run([
        "codespell",
        "--write-changes",
        "--skip=*.csv,*.geojson,*.json,*.js,*.html,*cff,./.git",
        "--ignore-words-list=aci,hist"
    ], capture_output=True, text=True)
    print(result.stdout)
    print(result.stderr)

def show_changed_files():
    # Show files changed by codespell
    print("Files changed:")
    changed = subprocess.run(
        ["git", "status", "--short"],
        capture_output=True, text=True
    )
    print(changed.stdout)

def commit_changes():
    # Optionally commit the changes
    subprocess.run(["git", "add", "-u"])
    subprocess.run([
        "git", "commit", "-m", "fix: auto-correct typos with codespell"
    ])
    print("Committed codespell corrections.")

if __name__ == "__main__":
    run_codespell()
    show_changed_files()
    ask = input("Commit changes? (y/n): ").strip().lower()
    if ask == "y":
        commit_changes()