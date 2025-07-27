# waterrocketpy


[![image](https://img.shields.io/pypi/v/waterrocketpy.svg)](https://pypi.python.org/pypi/waterrocketpy)
[![Build Status](https://github.com/Cube002/waterrocketpy/actions/workflows/windows.yml/badge.svg)](https://github.com/Cube002/waterrocketpy/actions)




**A modular Python package for simulating water rockets.**


-   Free software: MIT License
-   Documentation: https://Cube002.github.io/waterrocketpy
    

## Features

-   Simulates Waterrockets and provides time series values of Altetude, Speed, Waterconsumption, Airpressure, Air Temperature and much more!
-   To install, just do pip install waterrocketpy

## Project File Organization and Thoughts
### Structure:
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
    -    └── README.md
