#!/usr/bin/env python3

from pathlib import Path
from pdoc import pdoc, render
import os

here = Path(__file__).parent

with open(here / "index.py", "w") as index_py:
    print("'''", file=index_py)
    with open(here / "INDEX.md", "r") as index_md:
        index = index_md.read()
        print(index.replace("docs/", "./"), file=index_py)
    print("'''", file=index_py)

render.configure(docformat="numpy", template_directory=here / "pdoc-template")
pdoc("run", "index", output_directory=here / "docs")

os.remove(here / "index.py")
