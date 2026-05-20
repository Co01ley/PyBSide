import re

variables = {}

def evaluate_value(value):
    value = value.strip()

    # string literal
    if value.startswith('"') and value.endswith('"'):
        return value[1:-1]

    # variable
    if value in variables:
        return variables[value]

    # fallback
    return value


def parse_arguments(arg_string):
    # split by commas not inside quotes
    parts = re.findall(r'"[^"]*"|[^,]+', arg_string)
    return [evaluate_value(p.strip()) for p in parts]


def run_line(line):
    line = line.strip()

    # empty line
    if not line:
        return

    # assignment: x = something
    if "=" in line and not line.startswith("speech."):
        var, expr = line.split("=", 1)
        var = var.strip()
        expr = expr.strip()

        # speech.input()
        if expr.startswith("speech.input()"):
            variables[var] = input("> ")
            return

        # string or variable assignment
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
