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

    if expr == "":
        return None

    if expr.startswith('"') and expr.endswith('"'):
        return expr[1:-1]

    if expr in variables:
        return variables[expr]

    m = re.match(r'^([a-zA-Z_][\w\.]*)\((.*)\)$', expr)
    if m:
        fname = m.group(1)
        inside = m.group(2)

        args = split_args(inside)
        eval_args = [evaluate_value(a) for a in args]

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

    expr_norm = normalise_expression(expr)

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
# Parse a single line (no execution)
# -----------------------------
def parse_line(line):
    line = line.strip()   # ⭐ FIX: strip indentation here

    if line == "":
        return ("EMPTY", None)

    if line.startswith("if ") and line.endswith(" then:"):
        return ("IF", line[3:-6].strip())

    if line.startswith("elsif ") and line.endswith(" then:"):
        return ("ELSIF", line[6:-6].strip())

    if line == "else:":
        return ("ELSE", None)

    if line == "end":
        return ("END", None)

    if "=" in line and not line.startswith("speech."):
        var, expr = line.split("=", 1)
        return ("ASSIGN", (var.strip(), expr.strip()))

    if line.startswith("speech.print(") and line.endswith(")"):
        return ("PRINT", line[len("speech.print("):-1])

    if re.match(r'^speech\.input\(\s*\)$', line):
        return ("INPUT", None)

    return ("UNKNOWN", line)


# -----------------------------
# Run file with block logic
# -----------------------------
def run_file(path):
    with open(path, "r", encoding="utf-8") as f:
        lines = [l.rstrip("\n") for l in f]

    i = 0
    stack = []

    while i < len(lines):
        parsed_type, data = parse_line(lines[i])

        if parsed_type == "EMPTY":
            i += 1
            continue

        if parsed_type == "IF":
            stack.append(bool(evaluate_value(data)))
            i += 1
            continue

        if parsed_type == "ELSIF":
            if stack[-1] is True:
                stack[-1] = False
            else:
                stack[-1] = bool(evaluate_value(data))
            i += 1
            continue

        if parsed_type == "ELSE":
            stack[-1] = not stack[-1]
            i += 1
            continue

        if parsed_type == "END":
            stack.pop()
            i += 1
            continue

        should_run = all(stack) if stack else True

        if should_run:
            if parsed_type == "ASSIGN":
                var, expr = data
                variables[var] = evaluate_value(expr)

            elif parsed_type == "PRINT":
                print(*parse_arguments(data))

            elif parsed_type == "INPUT":
                input("> ")

            elif parsed_type == "UNKNOWN":
                error("Syntax", f"Unknown command '{data}'")

        i += 1


# -----------------------------
# Entry point
# -----------------------------
if __name__ == "__main__":
    import sys
    if len(sys.argv) < 2:
        print("Usage: python interpreter.py file.pyb")
    else:
        run_file(sys.argv[1])
