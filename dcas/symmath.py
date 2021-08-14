"""
DCAS Symbolic Math

symmath.py

Symbolic Math Base Objects
"""
import typing as typ

# type decs
NumericType = typ.Union[float, int]


def _process_inp(arg):
    if isinstance(arg, int) or isinstance(arg, float):
        return NumericVariable(arg)
    if isinstance(arg, str):
        return Variable(arg)
    if not isinstance(arg, SymbolicMath):
        raise ValueError
    return arg


class SymbolicMath:
    def __init__(self):
        self.props = {}

    def __add__(self, other: "SymbolicMath"):
        return Add(self, other)

    def __sub__(self, other: "SymbolicMath"):
        return Subtract(self, other)

    def __pow__(self, other: "SymbolicMath"):
        return Pow(self, other)

    def __mul__(self, other: "SymbolicMath"):
        return Mult(self, other)

    def __repr__(self):
        return "<NONE>"

    def __truediv__(self, other: "SymbolicMath"):
        return Div(self, other)

    def traverse_dfs(self):
        for pname in self.props:
            p = getattr(self, pname)
            yield from p.traverse_dfs()
            yield p

    def traverse_bfs(self):
        for pname in self.props:
            p = getattr(self, pname)
            yield p
            yield from p.traverse_bfs()


class Function(SymbolicMath):
    def __init__(self, func_name: SymbolicMath, appl=None):
        self.func_name = _process_inp(func_name)
        self.appl = appl
        self.props = {"appl"}

    def __call__(self, expr: SymbolicMath):
        return Function(self.func_name, appl=_process_inp(expr))

    def __repr__(self):
        if self.appl:
            return f"{self.func_name}({self.appl})"
        return f"{self.func_name}"

class Variable(SymbolicMath):
    def __init__(self, var_name: str):
        super().__init__()
        self.var_name = var_name

    def __repr__(self):
        return f"{self.var_name}"


class NumericVariable(Variable):
    def __init__(self, value: NumericType):
        # what would be the correct identifier name?
        super().__init__(str(value))
        self.num_val = value


class BinOp(SymbolicMath):
    def __init__(self, symbol_name: str, lhs: SymbolicMath, rhs: SymbolicMath):
        super().__init__()
        self.sym_name = symbol_name
        self.lhs = _process_inp(lhs)
        self.rhs = _process_inp(rhs)
        self.props = {"lhs", "rhs"}

    def __repr__(self):
        return f"({self.lhs} {self.sym_name} {self.rhs})"


class Add(BinOp):
    def __init__(self, lhs, rhs):
        super().__init__("+", lhs, rhs)


class Mult(BinOp):
    def __init__(self, lhs, rhs):
        super().__init__("*", lhs, rhs)



class Subtract(BinOp):
    def __init__(self, lhs, rhs):
        super().__init__("-", lhs, rhs)



class Pow(BinOp):
    def __init__(self, lhs, rhs):
        super().__init__("^", lhs, rhs)


class Div(BinOp):
    def __init__(self, lhs, rhs):
        super().__init__("/", lhs, rhs)


def numeric_eq(expr, num):
    if isinstance(expr, NumericVariable):
        if expr.num_val == num:
            return True
        else:
            return False
    else:
        return False

