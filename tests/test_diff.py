from dcas.symbols import x, y
from dcas.transformers import Differentiator, Simplifier


def test_diff():
    expr = x**x + y
    d = Differentiator()
    s = Simplifier()
    ret = (d.differentiate(d.differentiate(x**y, x), y))
    print(f"d/dy[d/dx[{expr}]]={ret}")
