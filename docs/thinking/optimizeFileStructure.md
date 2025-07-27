
# Project File Organization and Thoughts
## Structure:
    -waterrocketpy/
    -    ├── .github/
    -    │   ├── ISSUE_TEMPLATE/
    -    │   └── workflows/
    -    ├── docs/
    -    │   ├── examples/                   //documentation-specific assets.
    -    │   ├── literature_sources/
    -    │   ├── overrides/
    -    │   ├── reference_runs/
    -    │   └── thinking/
    -    ├── examples/                       //for user-facing demos or runnable use-cases.
    -    │   ├── ...
    -    ├── tests/
    -    │   ├── ...
    -    ├── waterrocketpy/                  //what gets published on PyPI
    -    │   ├── analysis/
    -    │   ├── core/
    -    │   ├── data/
    -    │   ├── legacy/
    -    │   ├── optimization/
    -    │   ├── rocket/
    -    │   ├── utils/
    -    │   └── visualization/
    -    ├── .gitignore
    -    ├── pyproject.toml
    -    ├── README.md
    -    └── setup.cfg / setup.py            //dont need these python 3.6 or higher 

## Examples
    You currently have two places for examples:

    docs/examples/: These are great if they’re tied to documentation generation (e.g., Jupyter Notebooks or markdown files).

    examples/: This is the standard place for users to find runnable .py scripts.

    ✅ Recommendation:

    Keep both, but make it clear:

    Use examples/ for user-facing demos or runnable use-cases.

    Use docs/examples/ for documentation-specific assets.

    📝 Add a note in the README or a top-level CONTRIBUTING.md explaining the difference.
