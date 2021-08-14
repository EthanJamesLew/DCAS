"""
DCAS Pre-Defined Symbols

symbols.py

Collection of Common Symbols
"""
from .symmath import *

# common real valued variables
x = Variable("x")
y = Variable("y")

# common numerics
zero = NumericVariable(0)
one = NumericVariable(1)

# common functions
cos = Function("cos")
sin = Function("sin")
tan = Function("tan")
sec = Function("sec")
exp = Function("exp")
ln = Function("ln")

