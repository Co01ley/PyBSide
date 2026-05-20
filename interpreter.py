import re

variables = {}

# -----------------------------
# Normalise word-based operators
# -----------------------------
def normalise_expression(expr):
    expr = expr.strip()
    # lower only for word operators, keep case for string literals
    # replace common word forms with symbols
    expr = re.sub(r'\bplus\b', '+', expr, flags=re.IGNORECASE)
    expr = re.sub(r'\bminus\b', '-', expr, flags=re.IGNORECASE)
    expr = re.sub(r'\btimes\b', '*', expr, flags=re.IGNORECASE)
    expr = re.sub(r'\bmultiplied by\b', '*', expr, flags=re.IGNORECASE)
    expr = re.sub(r'\bdivided by\b', '/', expr, flags=re.IGNORECASE)
    expr = re.sub(r'\bdivide\b', '/', expr, flags=re.IGNORECASE)
    return expr

# -----------------------------
# Evaluate an expression or single value (supports nested calls)
# -----------------------------
def evaluate_value(expr):
    expr = expr.strip()

    # string literal
    if expr.startswith('"') and expr.endswith('"'):
        return expr[1:-1]

    # variable
    if expr in variables:
        return variables[expr]

    # function call pattern name(arg1, arg2, ...)
    m = re.match(r'^([a-zA-Z_]\w*)\((.*)\)$', expr)
    if m:
        fname = m.group(1)
        inside = m.group(2).strip()

        # parse arguments while respecting quotes and nested parentheses
        args = split_args(inside)
        eval_args = [evaluate_value(a) for a in args]

        # built-in conversions and helpers
        if fname == "int" and len(eval_args) == 1:
            try:
                return int(eval_args[0])
            except:
                return int(float(eval_args[0]))
        if fname == "float" and len(eval_args) == 1:
            return float(eval_args[0])
        if fname == "str" and len(eval_args) == 1:
            return str(eval_args[0])
        if fname == "bool" and len(eval_args) == 1:
            # follow Python truthiness
            return bool(eval_args[0])
        if fname == "speech.input" and len(eval_args) == 0:
            return input("> ")

        # allow nested arithmetic inside function args by falling through
        # if unknown function, return raw expr
        return expr

    # normalise word operators to symbols
    expr_norm = normalise_expression(expr)

    # try numeric evaluation using safe eval with variables
    try:
        # eval with empty globals and variables as locals
        return eval(expr_norm, {}, variables)
    except:
        # fallback: return raw string/identifier
        return expr

# -----------------------------
# Split arguments by commas not inside quotes or parentheses
# -----------------------------
def split_args(s):
    args = []
    current = []
    depth = 0
    in_quote = False
    i = 0
    while i < len(s):
        ch = s[i]
        if ch == '"' and (i == 0 or s[i-1] != '\\'):
            in_quote = not in_quote
            current.append(ch)
        elif not in_quote:
            if ch == '(':
                depth += 1
                current.append(ch)
            elif ch == ')':
                depth -= 1
                current.append(ch)
            elif ch == ',' and depth == 0:
                arg = ''.join(current).strip()
                if arg:
                    args.append(arg)
                current = []
            else:
                current.append(ch)
        else:
            current.append(ch)
        i += 1
    last = ''.join(current).strip()
    if last:
        args.append(last)
    return args

# -----------------------------
# Parse arguments for speech.print
# -----------------------------
def parse_arguments(arg_string):
    parts = split_args(arg_string)
    return [evaluate_value(p.strip()) for p in parts]

# -----------------------------
# Execute a single line
# -----------------------------
def run_line(line):
    line = line.strip()
    if not line:
        return

    # assignment: x = expr
    if "=" in line and not line.startswith("speech."):
        var, expr = line.split("=", 1)
        var = var.strip()
        expr = expr.strip()

        # support assignment from speech.input()
        if re.match(r'^speech\.input\(\s*\)$', expr):
            variables[var] = input("> ")
            return

        variables[var] = evaluate_value(expr)
        return

    # speech.print(...)
    if line.startswith("speech.print(") and line.endswith(")"):
        inside = line[len("speech.print("):-1]
        args = parse_arguments(inside)
        # print with Python semantics
        print(*args)
        return

    # speech.input() alone
    if re.match(r'^speech\.input\(\s*\)$', line):
        input("> ")
        return

    print(f"[ERROR] Unknown command: {line}")

# -----------------------------
# Run file
# -----------------------------
def run_file(path):
    with open(path, "r", encoding="utf-8") as f:
        for raw in f:
            run_line(raw)

if __name__ == "__main__":
    import sys
    if len(sys.argv) < 2:
        print("Usage: python interpreter.py file.pyb")
    else:
        run_file(sys.argv[1])
