import re

variables = {}

# -----------------------------
# Convert word-based operators → symbols
# -----------------------------
def normalise_expression(expr):
    expr = expr.lower()

    expr = expr.replace(" plus ", " + ")
    expr = expr.replace(" minus ", " - ")
    expr = expr.replace(" times ", " * ")
    expr = expr.replace(" multiplied by ", " * ")
    expr = expr.replace(" divide ", " / ")
    expr = expr.replace(" divided by ", " / ")

    return expr


# -----------------------------
# Evaluate a value or expression
# -----------------------------
def evaluate_value(expr):
    expr = expr.strip()

    # string literal
    if expr.startswith('"') and expr.endswith('"'):
        return expr[1:-1]

    # variable
    if expr in variables:
        return variables[expr]

    # normalise word operators
    expr = normalise_expression(expr)

    # try maths evaluation
    try:
        return eval(expr, {}, variables)
    except:
        return expr


# -----------------------------
# Parse arguments inside speech.print(...)
# -----------------------------
def parse_arguments(arg_string):
    parts = re.findall(r'"[^"]*"|[^,]+', arg_string)
    return [evaluate_value(p.strip()) for p in parts]


# -----------------------------
# Execute a single line
# -----------------------------
def run_line(line):
    line = line.strip()
    if not line:
        return

    # assignment: x = something
    if "=" in line and not line.startswith("speech."):
        var, expr = line.split("=", 1)
        var = var.strip()
        expr = expr.strip()

        # speech.input()
        if expr == "speech.input()":
            variables[var] = input("> ")
            return

        variables[var] = evaluate_value(expr)
        return

    # speech.print(...)
    if line.startswith("speech.print(") and line.endswith(")"):
        inside = line[len("speech.print("):-1]
        args = parse_arguments(inside)
        print(*args)
        return

    # speech.input() without assignment
    if line == "speech.input()":
        input("> ")
        return

    print(f"[ERROR] Unknown command: {line}")


def run_file(path):
    with open(path, "r") as f:
        for line in f:
            run_line(line)


if __name__ == "__main__":
    import sys
    if len(sys.argv) < 2:
        print("Usage: python interpreter.py file.pyb")
    else:
        run_file(sys.argv[1])
