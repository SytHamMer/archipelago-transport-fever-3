import ast
from pathlib import Path

WORLD = Path(__file__).resolve().parent.parent / "tf3_world"
FILES = sorted(WORLD.rglob("*.py"))


def test_no_python_line_of_the_world_is_longer_than_120_characters():
    long = [f"{f.name}:{n}" for f in FILES for n, line in enumerate(f.read_text(encoding="utf-8").splitlines(), 1)
            if len(line) > 120]
    assert not long, long


def test_no_python_line_of_the_world_has_trailing_whitespace():
    bad = [f"{f.name}:{n}" for f in FILES for n, line in enumerate(f.read_text(encoding="utf-8").splitlines(), 1)
           if line != line.rstrip()]
    assert not bad, bad


def test_every_function_of_the_world_has_annotated_parameters_and_return_type():
    missing = []
    for f in FILES:
        for node in ast.walk(ast.parse(f.read_text(encoding="utf-8"))):
            if isinstance(node, (ast.FunctionDef, ast.AsyncFunctionDef)):
                params = [a for a in node.args.args + node.args.kwonlyargs if a.arg not in ("self", "cls")]
                if node.returns is None or any(a.annotation is None for a in params):
                    missing.append(f"{f.name}:{node.name}")
    assert not missing, missing
