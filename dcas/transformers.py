"""
DCAS Symbolic Expression Transformers

transformers.py

Transformer Definitions for Symbolic Expressions
"""
from .symmath import *
from .symbols import *

class Transformer:
    pass


class Simplifier(Transformer):
    def __init__(self):
        self.rules = {Add: self.add_rule,
                      Variable: self.var_rule,
                      NumericVariable: self.var_rule,
                      Pow: self.pow_rule,
                      Mult: self.mul_rule,
                      Function: self.func_rule,
                      Subtract: self.sub_rule,
                      Div: self.div_rule}

    def simplify(self, expr: SymbolicMath):
        return self.rules[expr.__class__](expr)

    def n_simplify(self, expr: SymbolicMath, n):
        ret = self.simplify(expr)
        for i in range(0, n-1):
            ret = self.simplify(ret)
        return ret

    def add_rule(self, expr: SymbolicMath):
        if isinstance(expr.lhs, NumericVariable) and isinstance(expr.rhs, NumericVariable):
            return NumericVariable(expr.lhs.num_val + expr.rhs.num_val)
        if numeric_eq(expr.lhs, 0):
            return self.simplify(expr.rhs)
        elif numeric_eq(expr.rhs, 0):
            return self.simplify(expr.lhs)
        return Add(self.simplify(expr.lhs), self.simplify(expr.rhs))

    def var_rule(self, expr: SymbolicMath):
        return expr

    def pow_rule(self, expr: SymbolicMath):
        if isinstance(expr.lhs, NumericVariable) and isinstance(expr.rhs, NumericVariable):
            return NumericVariable(expr.lhs.num_val ** expr.rhs.num_val)
        if numeric_eq(expr.rhs, 1):
            return self.simplify(expr.lhs)
        return Pow(self.simplify(expr.lhs), self.simplify(expr.rhs))

    def mul_rule(self, expr: SymbolicMath):
        if isinstance(expr.lhs, NumericVariable) and isinstance(expr.rhs, NumericVariable):
            return NumericVariable(expr.lhs.num_val * expr.rhs.num_val)
        if numeric_eq(expr.lhs, 1):
            return self.simplify(expr.rhs)
        elif numeric_eq(expr.rhs, 1):
            return self.simplify(expr.lhs)
        if numeric_eq(expr.lhs, 0):
            return zero
        elif numeric_eq(expr.rhs, 0):
            return zero
        return Mult(self.simplify(expr.lhs), self.simplify(expr.rhs))

    def func_rule(self, expr: SymbolicMath):
        return expr

    def sub_rule(self, expr: SymbolicMath):
        if isinstance(expr.lhs, NumericVariable) and isinstance(expr.rhs, NumericVariable):
            return NumericVariable(expr.lhs.num_val - expr.rhs.num_val)
        if numeric_eq(expr.lhs, 0):
            return self.simplify(expr.rhs)
        elif numeric_eq(expr.rhs, 0):
            return NumericVariable(-1)*self.simplify(expr.lhs)
        return Subtract(self.simplify(expr.lhs), self.simplify(expr.rhs))

    def div_rule(self, expr: SymbolicMath):
        if isinstance(expr.lhs, NumericVariable) and isinstance(expr.rhs, NumericVariable):
            return NumericVariable(expr.lhs.num_val / expr.rhs.num_val)
        if numeric_eq(expr.rhs, 1):
            return self.simplify(expr.lhs)
        return Div(self.simplify(expr.lhs), self.simplify(expr.rhs))


class Differentiator(Transformer):
    def __init__(self):
        super().__init__()
        #self.func_map = {"sin": cos, "exp": exp}
        self.func_map = {"sin": self.sin_d_rule,
                         "cos": self.cos_d_rule,
                         "tan": self.tan_d_rule,
                         "ln": self.ln_d_rule,
                         "exp": self.exp_d_rule}
        self.rules = {Add: self.add_rule,
                      Variable: self.var_rule,
                      NumericVariable: self.var_rule,
                      Pow: self.pow_rule,
                      Mult: self.mul_rule,
                      Function: self.func_rule,
                      Subtract: self.sub_rule,
                      Div: self.div_rule}

    def diff(self, expr: SymbolicMath, wrt: Variable):
        return self.rules[expr.__class__](expr, wrt)

    def differentiate(self, expr: SymbolicMath, wrt: Variable, simplify_its = 5):
        s = Simplifier()
        ret = self.diff(expr, wrt)
        return s.n_simplify(ret, simplify_its)

    def var_rule(self, expr, wrt: Variable):
        if expr is wrt:
            return one
        else:
            return zero

    def add_rule(self, expr, wrt: Variable):
        return self.diff(expr.lhs, wrt) + self.diff(expr.rhs, wrt)

    def pow_rule(self, expr, wrt: Variable):
        return expr.rhs * (expr.lhs ** (expr.rhs - one)) * self.diff(expr.lhs, wrt) + \
            ln(expr.lhs) * (expr.lhs ** expr.rhs) * self.diff(expr.rhs, wrt)

    def mul_rule(self, expr, wrt: Variable):
        return self.diff(expr.lhs, wrt) * expr.rhs + self.diff(expr.rhs, wrt) * expr.lhs

    def div_rule(self, expr, wrt: Variable):
        # TODO: check this
        return (self.diff(expr.lhs, wrt) * expr.rhs - self.diff(expr.rhs, wrt) * expr.lhs) / expr.rhs **2

    def func_rule(self, expr: Function, wrt: Variable):
        """TODO: make method to transform the functions for more flexibility"""
        if expr.func_name.var_name in self.func_map:
            deriv = self.func_map[expr.func_name.var_name](expr, wrt)
            return deriv * self.diff(expr.appl, wrt)
        else:
            deriv = Function(f"D_{wrt}[{expr.func_name}]")
            return deriv(expr.appl) * self.diff(expr.appl, wrt)

    def sub_rule(self, expr: Function, wrt: Variable):
        return self.diff(expr.lhs, wrt) - self.diff(expr.rhs, wrt)

    def sin_d_rule(self, expr: Function, wrt: Variable):
        return cos(expr.appl)

    def cos_d_rule(self, expr: Function, wrt: Variable):
        return NumericVariable(-1)*sin(expr.appl)

    def tan_d_rule(self, expr: Function, wrt: Variable):
        return one / cos(expr.appl)**2

    def ln_d_rule(self, expr: Function, wrt: Variable):
        return one / (expr.appl)

    def exp_d_rule(self, expr: Function, wrt: Variable):
        return exp(expr.appl)
