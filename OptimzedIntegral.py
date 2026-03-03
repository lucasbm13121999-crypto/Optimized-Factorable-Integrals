"""
Module for term-by-term numerical integration of algebraic expressions using SymPy and SciPy.

How to use:
1) Define the algebraic expressions using SymPy (e.g., sym.exp, sym.log).
2) Call `smart_integrate(expression, var, a, b)` to numerically integrate the desired 
   variable within the specified limits, returning the resulting symbolic expression.
"""

import sympy as sym
from scipy.integrate import quad_vec
from typing import List, Tuple, Any, Callable

def recover_expression(factored_terms: List[Tuple[Any, Any]]) -> Any:
    """
    Reconstructs the symbolic expression from the list of factored terms.

    Args:
        factored_terms: List of tuples where each tuple is (independent_part, dependent_part).

    Returns:
        Reassembled symbolic expression as the sum of the multiplied terms.
    """
    # Sums the multiplication of the independent and dependent parts of each term
    return sum(indep * dep for indep, dep in factored_terms)

def factor_expression(expression: Any, var: sym.Symbol) -> List[Tuple[Any, Any]]:
    """
    Expands the expression and separates each term into parts independent and dependent on `var`.

    Args:
        expression: SymPy symbolic expression.
        var: Variable (Symbol) that will serve as the basis for the separation.

    Returns:
        A list of tuples containing (independent_part, dependent_part) for each term.
    """
    expanded = sym.expand(expression)
    # sym.Add.make_args is the safe way to separate added terms, even if there is only one term
    terms = sym.Add.make_args(expanded)
    
    factored_terms = []
    for term in terms:
        # as_independent divides the term into (independent_of_var, dependent_on_var)
        indep, dep = term.as_independent(var)
        factored_terms.append((indep, dep))
        
    return factored_terms

def create_numpy_functions(factored_terms: List[Tuple[Any, Any]], var: sym.Symbol) -> List[Callable]:
    """
    Converts the variable-dependent parts of each term into executable NumPy functions.

    Args:
        factored_terms: List of tuples with the divided terms.
        var: The integration variable present in the expressions.

    Returns:
        List of compiled functions (lambdify) ready for numerical execution.
    """
    functions = []
    for _, dep_expr in factored_terms:
        # Creates an evaluable function using NumPy, capable of handling arrays and complex numbers
        numpy_func = sym.lambdify(var, dep_expr, modules='numpy')
        functions.append(numpy_func)
    return functions

def smart_integrate(expression: Any, var: sym.Symbol, a: float, b: float) -> Any:
    """
    Numerically integrates a symbolic expression term by term with respect to a variable.

    Args:
        expression: Algebraic expression to be integrated.
        var: The variable (Symbol) that will be integrated numerically.
        a: Lower integration limit.
        b: Upper integration limit.

    Returns:
        Symbolic expression with the `var` variable integrated, keeping other variables free.
    """
    factored_terms = factor_expression(expression, var)
    
    try:
        functions = create_numpy_functions(factored_terms, var)
    except Exception as e:
        print(f"ERROR: Failed to compile numpy functions. Details: {e}")
        return 0
        
    result_terms = []
    for i, func in enumerate(functions):
        # quad_vec supports complex values. [0] is the integral result, [1] is the error estimate
        integral_result, _ = quad_vec(func, a, b)
        
        # Keeps the original independent part, and replaces the dependent part with the integral result
        indep_part = factored_terms[i][0]
        result_terms.append((indep_part, integral_result))
        
    # Reconstructs the final expression
    return recover_expression(result_terms)

def clean_small_numbers(expr: Any, threshold: float = 1e-15) -> Any:
    """
    Cleans up extremely small floating-point numbers that arise as noise from numerical integration.

    Args:
        expr: The symbolic expression to be cleaned.
        threshold: Limit below which the number is considered zero.

    Returns:
        Cleaned expression.
    """
    return expr.replace(lambda e: e.is_Float, lambda f: 0 if abs(f) < threshold else f)

# ==============================================================================
# SCRIPT TEST
# ==============================================================================
if __name__ == "__main__":
    # 1. Define the symbols
    xSym, thSym, fSym, test = sym.symbols('x th f test')
    
    # 2. Create the expression
    expression = (xSym * thSym * sym.exp(1j*2*fSym) + 
                  xSym**2 * thSym * sym.exp(1j*2*fSym) + 
                  sym.log(xSym**2) * thSym * sym.exp(1j*2*fSym))**3
                  
    print("--- Original Expanded Expression ---")
    print(sym.expand(expression))
    print("\n--- Processing Integration ---")
    
    # 3. Call the smart integration
    intX = smart_integrate(expression, xSym, 0, 2)
    
    # 4. Clean the result for easier mathematical reading
    intX_clean = clean_small_numbers(intX)
    
    print("\n--- Integral Result (Cleaned) ---")
    print(intX_clean)