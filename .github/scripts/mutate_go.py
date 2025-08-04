import random
import re
from pathlib import Path

def is_real_code(line):
    line_strip = line.strip()
    if not line_strip:
        return False
    if line_strip.startswith('//'):
        return False
    if line_strip in ['{', '}']:
        return False
    if line_strip == '':
        return False
    return True

def pick_file(ext=".go"):
    files = [
        f for f in Path('.').rglob(f'*{ext}')
        if 'vendor' not in str(f) and 'test' not in str(f).lower() and '/.git/' not in str(f)
    ]
    return random.choice(files) if files else None

def mutate_return(line):
    # Mutate a Go return statement to zero/nil/false values
    m = re.match(r'(\s*)return (.+)', line)
    if not m:
        return None
    indent, returns = m.groups()
    # Split by commas, ignore nested for simplicity
    values = [v.strip() for v in returns.split(',')]
    chaos = []
    for v in values:
        # Guess type by name/shape, fallback to 0
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
            # fallback
            chaos.append(random.choice(['nil', '0', 'false', '""']))
    return f"{indent}return {', '.join(chaos)}\n"

def invert_condition(line):
    # Attempt to invert a boolean condition in an if statement
    condition = line
    # Replace common comparison operators
    swaps = {'==': '!=', '!=': '==', '>=': '<', '<=': '>', '>': '<', '<': '>'}
    for a, b in swaps.items():
        if a in condition:
            return condition.replace(a, b, 1)
    # Flip true/false literals
    if ' true' in condition:
        return condition.replace(' true', ' false', 1)
    if ' false' in condition:
        return condition.replace(' false', ' true', 1)
    return '!' + condition.lstrip()  # add ! for something that looks like a bool expr

def mutate_assignment(line):
    m = re.match(r'(\s*[\w\d_\.]+\s*(?:[:=]{1,2})\s*)(.+)', line)
    if not m:
        return None
    left, right = m.groups()
    # assign a chaos value
    chaos_value = random.choice(['nil', '0', 'false', '""'])
    return f"{left}{chaos_value} // chaos-mutation\n"

def mutate_file(filepath):
    with open(filepath, 'r') as f:
        lines = f.readlines()

    # Gather mutatable candidates by line type
    candidates = []
    for i, line in enumerate(lines):
        if not is_real_code(line):
            continue
        if line.strip().startswith('return'):
            candidates.append((i, 'return'))
        elif re.match(r'\s*if\s+.+{', line):
            candidates.append((i, 'if'))
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
        if mutated:
            print(f"Mutated return: {original.strip()} → {mutated.strip()}")
            lines[idx] = mutated
        else:
            print("Fallback: breaking line.")
            lines[idx] = 'THIS WILL NOT COMPILE // chaos mutation\n'

    elif linetype == 'if':
        # Try to invert condition
        m = re.match(r'(\s*if\s+)(.+)({)', original)
        if m:
            prefix, condition, suffix = m.groups()
            inverted = invert_condition(condition)
            new_line = f"{prefix}{inverted}{suffix}\n"
            print(f"Inverted if condition: {original.strip()} → {new_line.strip()}")
            lines[idx] = new_line
        else:
            lines[idx] = '// failed to invert if condition, original: ' + original

    elif linetype == 'assign':
        mutated = mutate_assignment(original)
        if mutated:
            print(f"Mutated assignment: {original.strip()} → {mutated.strip()}")
            lines[idx] = mutated
        else:
            lines[idx] = '// failed to mutate assignment, original: ' + original

    else:
        # For any other code line, just break it.
        print(f"Breaking random code line {idx+1}: {original.strip()}")
        lines[idx] = 'THIS WILL NOT COMPILE // chaos mutation\n'

    with open(filepath, 'w') as f:
        f.writelines(lines)
    return True

if __name__ == "__main__":
    file = pick_file(ext=".go")
    if file:
        mutate_file(file)
    else:
        print("No Go files found to mutate.")
