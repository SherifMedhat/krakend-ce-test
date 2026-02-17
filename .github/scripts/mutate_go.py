import random
import re
from pathlib import Path

def is_real_logic(line):
    line_strip = line.strip()
    if not line_strip or line_strip.startswith('//'):
        return False
    if line_strip in ['{', '}', ')', '}', '),', '},', ')', '});', '});', '}', '})', '})']:
        return False
    # Exclude lines that are only brackets, or close test blocks
    if re.fullmatch(r'[\)\}\],; ]*', line_strip):
        return False
    return True

def pick_file(ext=".go"):
    files = [
        f for f in Path('.').rglob(f'*{ext}')
        if 'vendor' not in str(f) and 'test' not in str(f).lower() and '/.git/' not in str(f)
    ]
    return random.choice(files) if files else None

def mutate_return(line):
    m = re.match(r'(\s*)return (.+)', line)
    if not m:
        return None
    indent, returns = m.groups()
    values = [v.strip() for v in returns.split(',')]
    chaos = []
    for v in values:
        # Guess type by variable naming and context
        if v.startswith('"') and v.endswith('"'):
            chaos.append('""')
        elif v in ['nil', '0', 'false', 'true']:
            chaos.append(v)
        elif v.isdigit():
            chaos.append('0')
        elif v == 'err' or v.endswith('Err') or 'err' in v.lower():
            chaos.append('nil')
        elif v == 'true':
            chaos.append('false')
        elif v == 'false':
            chaos.append('true')
        else:
            chaos.append(random.choice(['nil', '0', 'false', '""']))
    return f"{indent}return {', '.join(chaos)}\n"

def invert_condition(line):
    # Invert a boolean condition in an if statement, e.g. `if x == 5 {` to `if x != 5 {`
    condition = line
    swaps = {'==': '!=', '!=': '==', '>=': '<', '<=': '>', '>': '<', '<': '>'}
    for a, b in swaps.items():
        if a in condition:
            return condition.replace(a, b, 1)
    if ' true' in condition:
        return condition.replace(' true', ' false', 1)
    if ' false' in condition:
        return condition.replace(' false', ' true', 1)
    # If can't be inverted, prefix with '!' (if not already present)
    if re.match(r'(\s*if\s+)(.+)({)', line):
        prefix, cond, suffix = re.match(r'(\s*if\s+)(.+)({)', line).groups()
        if cond.strip().startswith('!'):
            cond = cond.strip()[1:]
        else:
            cond = '!' + cond.strip()
        return f"{prefix}{cond}{suffix}\n"
    return line

def mutate_assignment(line):
    m = re.match(r'(\s*[\w\d_\.]+\s*(?:[:=]{1,2})\s*)(.+)', line)
    if not m:
        return None
    left, right = m.groups()
    chaos_value = random.choice(['nil', '0', 'false', '""'])
    return f"{left}{chaos_value} // chaos-mutation\n"

def mutate_func_call(line):
    # Simple: if a function call has arguments, zero one of them out
    m = re.match(r'(\s*\w+\s*:=\s*\w+\()(.*)(\).*)', line)
    if not m:
        return None
    left, args, right = m.groups()
    arg_list = [a.strip() for a in args.split(',')]
    if not arg_list:
        return None
    idx = random.randrange(len(arg_list))
    arg_list[idx] = random.choice(['nil', '0', 'false', '""'])
    return f"{left}{', '.join(arg_list)}{right}\n"

def mutate_file(filepath):
    with open(filepath, 'r') as f:
        lines = f.readlines()

    candidates = []
    for i, line in enumerate(lines):
        if not is_real_logic(line):
            continue
        lstrip = line.strip()
        if lstrip.startswith('return'):
            candidates.append((i, 'return'))
        elif re.match(r'\s*if\s+.+{', line):
            candidates.append((i, 'if'))
        elif re.match(r'.*:=.*\(.+\).*', line):  # function call with assignment
            candidates.append((i, 'func_call'))
        elif re.match(r'\s*[\w\d_\.]+\s*(?:[:=]{1,2})\s*.+', line):
            candidates.append((i, 'assign'))
        else:
            candidates.append((i, 'other'))

    if not candidates:
        print("No suitable code lines found to mutate.")
        return False

    idx, linetype = random.choice(candidates)
    original = lines[idx]

    if linetype == 'return':
        mutated = mutate_return(original)
        if mutated and mutated != original:
            print(f"Mutated return: {original.strip()} → {mutated.strip()}")
            lines[idx] = mutated
    elif linetype == 'if':
        mutated = invert_condition(original)
        if mutated and mutated != original:
            print(f"Inverted if: {original.strip()} → {mutated.strip()}")
            lines[idx] = mutated
    elif linetype == 'func_call':
        mutated = mutate_func_call(original)
        if mutated and mutated != original:
            print(f"Mutated function call: {original.strip()} → {mutated.strip()}")
            lines[idx] = mutated
    elif linetype == 'assign':
        mutated = mutate_assignment(original)
        if mutated and mutated != original:
            print(f"Mutated assignment: {original.strip()} → {mutated.strip()}")
            lines[idx] = mutated
    else:
        # For other code, comment out the line as a last resort, never break syntax
        print(f"Commented out line {idx+1}: {original.strip()}")
        lines[idx] = f"// chaos mutation: {original}"

    with open(filepath, 'w') as f:
        f.writelines(lines)
    return True

if __name__ == "__main__":
    file = pick_file(ext=".go")
    if file:
        mutate_file(file)
    else:
        print("No Go files found to mutate.")
