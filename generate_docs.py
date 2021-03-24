#!/usr/bin/env python3

from pathlib import Path
from pdoc import pdoc, render
import os

here = Path(__file__).parent

with open(here / "index.py", "w") as readme_py:
    print("'''", file=readme_py)
    with open(here / "README.md", "r") as readme_md:
        readme = readme_md.read()
        print(readme.replace("docs/", "./"), file=readme_py)
    print("'''", file=readme_py)

render.configure(docformat="numpy",
                 template_directory=here / "pdoc-template")
pdoc("run", "index", output_directory=here / "docs")

os.remove(here / "index.py")
