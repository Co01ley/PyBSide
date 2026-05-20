import re

variables = {}

# -----------------------------
# Error helper
# -----------------------------
def error(kind, message):
    print(f"{kind} Error: {message}")


# -----------------------------
# Normalise word-based operators
# -----------------------------
def normalise_expression(expr):
    expr = re.sub(r'\bplus\b', '+', expr, flags=re.IGNORECASE)
    expr = re.sub(r'\bminus\b', '-', expr, flags=re.IGNORECASE)
    expr = re.sub(r'\btimes\b', '*', expr, flags=re.IGNORECASE)
    expr = re.sub(r'\bmultiplied by\b', '*', expr, flags=re.IGNORECASE)
    expr = re.sub(r'\bdivide\b', '/', expr, flags=re.IGNORECASE)
    expr = re.sub(r'\bdivided by\b', '/', expr, flags=re.IGNORECASE)
    return expr


# -----------------------------
# Split arguments safely
# -----------------------------
def split_args(s):
    args = []
    current = []
    depth = 0
    in_quote = False

    for i, ch in enumerate(s):
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
                args.append(''.join(current).strip())
                current = []
            else:
                current.append(ch)
        else:
            current.append(ch)

    last = ''.join(current).strip()
    if last:
        args.append(last)

    return args


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

    # function call (supports dots: speech.input)
    m = re.match(r'^([a-zA-Z_][\w\.]*)\((.*)\)$', expr)
    if m:
        fname = m.group(1)
        inside = m.group(2)

        args = split_args(inside)
        eval_args = [evaluate_value(a) for a in args]

        # built-in conversions
        try:
            if fname == "int":
                return int(float(eval_args[0]))
            if fname == "float":
                return float(eval_args[0])
            if fname == "str":
                return str(eval_args[0])
            if fname == "bool":
                return bool(eval_args[0])
            if fname == "speech.input":
                return input("> ")
        except:
            error("Type", f"Invalid conversion in {fname}({inside})")
            return None

        error("Function", f"Unknown function '{fname}'")
        return None

    # normalise word operators
    expr_norm = normalise_expression(expr)

    # try maths
    try:
        return eval(expr_norm, {}, variables)
    except NameError:
        error("Name", f"Unknown variable in expression '{expr}'")
    except ZeroDivisionError:
        error("Math", "Division by zero")
    except:
        error("Math", f"Invalid maths expression '{expr}'")

    return None


# -----------------------------
# Parse arguments for speech.print
# -----------------------------
def parse_arguments(arg_string):
    parts = split_args(arg_string)
    return [evaluate_value(p) for p in parts]


# -----------------------------
# Execute a block of lines
# -----------------------------
def run_block(lines, start_index, indent_level):
    i = start_index
    while i < len(lines):
        line = lines[i]
        stripped = line.lstrip()
        current_indent = len(line) - len(stripped)

        if current_indent < indent_level:
            return i - 1

        if current_indent > indent_level:
            error("Syntax", "Unexpected indentation")
            return i

        run_line(stripped)
        i += 1

    return i


# -----------------------------
# Execute a single line
# -----------------------------
def run_line(line):
    # IF
    if line.startswith("if ") and " then:" in line:
        condition = line[3:line.index(" then:")].strip()
        result = evaluate_value(condition)
        return ("IF", result)

    # ELSIF
    if line.startswith("elsif ") and " then:" in line:
        condition = line[6:line.index(" then:")].strip()
        result = evaluate_value(condition)
        return ("ELSIF", result)

    # ELSE
    if line == "else:":
        return ("ELSE", True)

    # assignment
    if "=" in line and not line.startswith("speech."):
        var, expr = line.split("=", 1)
        var = var.strip()
        expr = expr.strip()

        if not re.match(r'^[a-zA-Z_]\w*$', var):
            error("Syntax", f"Invalid variable name '{var}'")
            return

        value = evaluate_value(expr)
        variables[var] = value
        return

    # speech.print(...)
    if line.startswith("speech.print(") and line.endswith(")"):
        inside = line[len("speech.print("):-1]
        args = parse_arguments(inside)
        print(*args)
        return

    # speech.input() alone
    if re.match(r'^speech\.input\(\s*\)$', line):
        input("> ")
        return

    error("Syntax", f"Unknown command '{line}'")


# -----------------------------
# Run file with block support
# -----------------------------
def run_file(path):
    with open(path, "r", encoding="utf-8") as f:
        lines = f.readlines()

    i = 0
    skip_until = None
    active = False

    while i < len(lines):
        raw = lines[i]
        stripped = raw.lstrip()
        indent = len(raw) - len(stripped)

        result = run_line(stripped)

        # IF / ELSIF / ELSE handling
        if isinstance(result, tuple):
            kind, cond = result

            if kind == "IF":
                active = cond
                skip_until = indent + 4

            elif kind == "ELSIF":
                if active:
                    active = False
                else:
                    active = cond

            elif kind == "ELSE":
                active = not active

            i += 1
            continue

        # normal line
        i += 1


if __name__ == "__main__":
    import sys
    if len(sys.argv) < 2:
        print("Usage: python interpreter.py file.pyb")
    else:
        run_file(sys.argv[1])
