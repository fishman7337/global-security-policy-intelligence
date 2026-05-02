from __future__ import annotations

import ast
import json
from pathlib import Path


DOCUMENTED_MODULES = [
    Path("src/gtd_capstone/data/cleaning.py"),
    Path("src/gtd_capstone/data/repository.py"),
    Path("src/gtd_capstone/monitoring/drift.py"),
    Path("src/gtd_capstone/policy/panel.py"),
    Path("src/gtd_capstone/policy/methods.py"),
    Path("src/gtd_capstone/policy/sources.py"),
    Path("src/gtd_capstone/safety.py"),
]


def test_research_modules_have_docstrings():
    """Check PEP 257-style docstrings on research-critical modules."""
    missing = []
    for path in DOCUMENTED_MODULES:
        tree = ast.parse(path.read_text(encoding="utf-8"))
        if ast.get_docstring(tree) is None:
            missing.append(f"{path}: module")
        for node in ast.walk(tree):
            if isinstance(node, (ast.FunctionDef, ast.AsyncFunctionDef, ast.ClassDef)):
                if ast.get_docstring(node) is None:
                    missing.append(f"{path}:{node.lineno} {node.name}")

    assert missing == []


def test_notebooks_are_valid_json():
    """Check that committed notebooks are compact rendered reports."""
    notebooks = sorted(Path("notebooks").glob("*.ipynb"))

    assert len(notebooks) >= 12
    for path in notebooks:
        assert path.stat().st_size < 1_500_000
        data = json.loads(path.read_text(encoding="utf-8"))
        assert data["nbformat"] == 4
        assert data["cells"]
        assert data["cells"][0]["cell_type"] == "markdown"
        assert data["cells"][0]["source"][0].startswith("# ")
        code_cells = [cell for cell in data["cells"] if cell["cell_type"] == "code"]
        assert code_cells
        assert all(cell.get("execution_count") is not None for cell in code_cells)
