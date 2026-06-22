"""Safe evaluation utilities for expressions and formulas."""
import ast
import logging
import operator
import math

logger = logging.getLogger(__name__)

# Allowed operators for safe evaluation
_SAFE_OPERATORS = {
    ast.Add: operator.add,
    ast.Sub: operator.sub,
    ast.Mult: operator.mul,
    ast.Div: operator.truediv,
    ast.Mod: operator.mod,
    ast.Pow: operator.pow,
    ast.USub: operator.neg,
    ast.UAdd: operator.pos,
}

# Allowed comparison operators
_SAFE_COMPARISONS = {
    ast.Eq: operator.eq,
    ast.NotEq: operator.ne,
    ast.Lt: operator.lt,
    ast.LtE: operator.le,
    ast.Gt: operator.gt,
    ast.GtE: operator.ge,
}

# Allowed functions for safe evaluation
_SAFE_FUNCTIONS = {
    "abs": abs,
    "round": round,
    "min": min,
    "max": max,
    "sum": sum,
    "len": len,
    "int": int,
    "float": float,
    "sin": math.sin,
    "cos": math.cos,
    "tan": math.tan,
    "sqrt": math.sqrt,
    "log": math.log,
    "exp": math.exp,
    "pi": math.pi,
    "e": math.e,
    "ceil": math.ceil,
    "floor": math.floor,
}


def safe_eval(expr: str, variables: dict = None, allowed_functions: dict = None) -> float:
    """
    Safely evaluate a mathematical expression string.
    
    This function provides a sandboxed evaluation environment that only allows
    mathematical operations and safe functions. It prevents code injection by
    rejecting any expression containing attribute access, function calls to
    unapproved functions, or other potentially dangerous constructs.
    
    Args:
        expr: The mathematical expression string to evaluate (e.g., "x**2 + 1")
        variables: Optional dictionary of variable names and their values
        allowed_functions: Optional dictionary of additional safe functions
        
    Returns:
        The numerical result of evaluating the expression
        
    Raises:
        ValueError: If the expression contains unsafe constructs
        ZeroDivisionError: If division by zero is attempted
        SyntaxError: If the expression is malformed
    """
    if not isinstance(expr, str):
        raise ValueError(f"Expression must be a string, got {type(expr).__name__}")
    
    # Block dangerous patterns
    dangerous_patterns = [
        "__", "import", "exec", "eval", "open", "file", "os.", "sys.",
        "subprocess", "shutil", "glob", "socket", "http", "urllib",
    ]
    expr_lower = expr.lower()
    for pattern in dangerous_patterns:
        if pattern in expr_lower:
            raise ValueError(f"Expression contains forbidden pattern: {pattern}")
    
    # Parse the expression into an AST
    try:
        tree = ast.parse(expr, mode='eval')
    except SyntaxError as e:
        raise ValueError(f"Invalid expression syntax: {e}")
    
    # Merge allowed functions
    funcs = {**_SAFE_FUNCTIONS}
    if allowed_functions:
        funcs.update(allowed_functions)
    
    # Merge variables
    vars_dict = {}
    if variables:
        vars_dict.update(variables)
    
    def _eval_node(node):
        if isinstance(node, ast.Expression):
            return _eval_node(node.body)
        elif isinstance(node, ast.Constant):
            return node.value
        elif isinstance(node, ast.BinOp):
            op = _SAFE_OPERATORS.get(type(node.op))
            if op is None:
                raise ValueError(f"Unsupported operator: {type(node.op).__name__}")
            left = _eval_node(node.left)
            right = _eval_node(node.right)
            return op(left, right)
        elif isinstance(node, ast.UnaryOp):
            op = _SAFE_OPERATORS.get(type(node.op))
            if op is None:
                raise ValueError(f"Unsupported unary operator: {type(node.op).__name__}")
            return op(_eval_node(node.operand))
        elif isinstance(node, ast.Compare):
            if len(node.ops) != 1:
                raise ValueError("Only single comparisons are supported")
            op = _SAFE_COMPARISONS.get(type(node.ops[0]))
            if op is None:
                raise ValueError(f"Unsupported comparison operator: {type(node.ops[0]).__name__}")
            left = _eval_node(node.left)
            right = _eval_node(node.comparators[0])
            return op(left, right)
        elif isinstance(node, ast.Name):
            if node.id in vars_dict:
                return vars_dict[node.id]
            if node.id in funcs:
                return funcs[node.id]
            raise ValueError(f"Unknown variable or function: {node.id}")
        elif isinstance(node, ast.Call):
            if not isinstance(node.func, ast.Name):
                raise ValueError("Only simple function calls are allowed")
            func_name = node.func.id
            if func_name not in funcs:
                raise ValueError(f"Function not allowed: {func_name}")
            func = funcs[func_name]
            args = [_eval_node(arg) for arg in node.args]
            return func(*args)
        elif isinstance(node, ast.List):
            return [_eval_node(elem) for elem in node.elts]
        elif isinstance(node, ast.Tuple):
            return tuple(_eval_node(elem) for elem in node.elts)
        else:
            raise ValueError(f"Unsupported expression type: {type(node).__name__}")
    
    return _eval_node(tree)


def safe_lambda_eval(func_str: str, allowed_vars: list[str] = None):
    """
    Safely create a lambda function from a string expression.
    
    This function parses a string like "x**2 + 1" and returns a callable
    lambda function. It only allows safe mathematical operations.
    
    Args:
        func_str: The function expression string (e.g., "x**2 + 1")
        allowed_vars: List of allowed variable names (default: ["x"])
        
    Returns:
        A callable lambda function
        
    Raises:
        ValueError: If the expression contains unsafe constructs
    """
    if allowed_vars is None:
        allowed_vars = ["x"]
    
    # Create a lambda by evaluating with the allowed variables
    def lambda_func(*args):
        variables = {}
        for i, var in enumerate(allowed_vars):
            if i < len(args):
                variables[var] = args[i]
        return safe_eval(func_str, variables)
    
    return lambda_func


def safe_constraint_eval(func_str: str, variables: list[str] = None):
    """
    Safely create a constraint function from a string expression.
    
    This function creates a callable that can be used as a constraint
    in constraint satisfaction problems. It evaluates the expression
    and returns True if the constraint is satisfied.
    
    Args:
        func_str: The constraint expression string (e.g., "x != y")
        variables: List of variable names the function depends on
        
    Returns:
        A callable constraint function
        
    Raises:
        ValueError: If the expression contains unsafe constructs
    """
    if variables is None:
        variables = []
    
    def constraint_func(*args):
        env = {}
        for i, var in enumerate(variables):
            if i < len(args):
                env[var] = args[i]
        result = safe_eval(func_str, env)
        return bool(result)
    
    return constraint_func
