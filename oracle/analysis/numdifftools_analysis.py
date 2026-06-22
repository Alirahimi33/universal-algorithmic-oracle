"""Numerical differentiation using numdifftools."""
import logging
import numpy as np
from oracle.utils.safe_eval import safe_lambda_eval

logger = logging.getLogger(__name__)

HAS_NUMDIFF = False
try:
    import numdifftools as nd
    HAS_NUMDIFF = True
except ImportError:
    pass


class NumericalDifferentiationAnalyzer:
    """Numerical differentiation, Jacobian, and Hessian computation."""

    def __init__(self):
        self.available = HAS_NUMDIFF

    def compute_derivative(self, func_str: str, x0: float, n: int = 1) -> dict:
        if not self.available:
            return {"error": "numdifftools not available"}
        try:
            if isinstance(func_str, str):
                func = safe_lambda_eval(func_str, ["x"])
            else:
                func = func_str
            deriv = nd.Derivative(func, n=n)
            result = deriv(x0)
            return {
                "derivative_order": n,
                "x0": x0,
                "result": float(result),
                "func": func_str if isinstance(func_str, str) else "lambda",
            }
        except Exception as e:
            return {"error": str(e)}

    def compute_jacobian(self, func_strs: list[str], x0: list[float]) -> dict:
        if not self.available:
            return {"error": "numdifftools not available"}
        try:
            funcs = [safe_lambda_eval(f, ["x"]) for f in func_strs]
            jacobian = nd.Jacobian(lambda x: [f(x) for f in funcs])
            result = jacobian(np.array(x0))
            return {
                "jacobian": result.tolist(),
                "x0": x0,
                "n_functions": len(func_strs),
            }
        except Exception as e:
            return {"error": str(e)}

    def analyze(self, data: dict) -> dict:
        func_str = data.get("function", "x**2")
        x0 = data.get("x0", 1.0)
        n = data.get("n", 1)
        return self.compute_derivative(func_str, x0, n)
