import glob, os, sys
ROOT = os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
sys.path.insert(0, ROOT)
from tools.jbeam import load, loads, dumps, PartDB, resolve, evaluate

TEMPLATE = os.path.join(ROOT, ".cache", "ref", "template")


def test_relaxed_syntax():
    v = loads('{"a":[1 2,3,], "b":{"x":1 "y":-0.00} // c\n /* d */ "c":["n", 0.1 {"w":2}]}')
    assert v["a"] == [1, 2, 3]
    assert v["b"] == {"x": 1, "y": -0.0}
    assert v["c"] == ["n", 0.1, {"w": 2}]


def test_template_files_parse_and_roundtrip():
    files = glob.glob(os.path.join(TEMPLATE, "**", "*.jbeam"), recursive=True)
    if not files:
        import pytest
        pytest.skip("template not downloaded (run tools/fetch_reference.py)")
    for f in files:
        data = load(f)
        again = loads(dumps(data))
        assert again == data, f


def test_expression_eval():
    v = {"$a": 2.0, "$b": None}
    assert evaluate("$=$a*3+1", v) == 7.0
    assert evaluate("$=$b == nil and 5 or 6", v) == 5
    assert evaluate({"x": "$=$a+0.175"}, v) == {"x": 2.175}
    assert evaluate("$a", v) == 2.0


def test_template_tree():
    d = os.path.join(TEMPLATE, "jbeam files")
    if not os.path.isdir(d):
        import pytest
        pytest.skip("template missing")
    db = PartDB(d)
    r = resolve(db, {"parts": {}})
    names = [t.part for t in r.order]
    assert "TutoFormulaBee_engine" in names and "TutoFormulaBee_suspension_F" in names
    assert "fh1r" in r.nodes and "e1l" in r.nodes
