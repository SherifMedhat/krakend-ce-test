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
    return True

def pick_file(ext=".go"):
    files = [
        f for f in Path('.').rglob(f'*{ext}')
        if 'vendor' not in str(f) and 'test' not in str(f).lower() and '/.git/' not in str(f)
    ]
    return random.choice(files) if files else None

def mutate_return_line(line):
    """
    Attempts to mutate a Go return statement by swapping each return value
    with a chaos value. Handles simple return forms.
    """
    # Try to match `return ...`
    match = re.match(r'\s*return\s+(.*)', line)
    if not match:
        return None
    values = [v.strip() for v in match.group(1).split(',')]
    chaos_values = []
    for v in values:
        # Simple mapping for common types
        if v in ['nil', '0', '""', 'false', 'true']:
            chaos_values.append(v)
        elif v.isdigit():
            chaos_values.append('0')
        elif v.startswith('"') and v.endswith('"'):
            chaos_values.append('""')
        elif v == 'err' or v.endswith('Err') or v.endswith('error'):
            chaos_values.append('nil')
        elif v in ['true', 'false']:
            chaos_values.append('false' if v == 'true' else 'true')
        else:
            # Guess by name
            if 'err' in v.lower():
                chaos_values.append('nil')
            elif v[0].isupper():
                # Could be struct or interface, return zero value
                chaos_values.append('{}')
            else:
                # Fallbacks: zero, nil, false, ""
                chaos_values.append(random.choice(['0', 'nil', 'false', '""']))
    new_line = re.sub(r'return\s+.*', 'return ' + ', '.join(chaos_values), line)
    return new_line

def mutate_file(filepath):
    with open(filepath, 'r') as f:
        lines = f.readlines()

    # Find indices for real code lines, and separately for return lines
    real_indices = [i for i, line in enumerate(lines) if is_real_code(line)]
    return_indices = [i for i in real_indices if lines[i].strip().startswith('return')]

    if return_indices:
        idx = random.choice(return_indices)
        original = lines[idx]
        mutated = mutate_return_line(original)
        if mutated:
            lines[idx] = mutated + '\n'
            print(f"Mutated return line {idx+1}: {original.strip()} → {mutated.strip()}")
        else:
            print(f"Failed to mutate return line, falling back.")
            idx = random.choice(real_indices)
            mutate_real_code_line(lines, idx)
    elif real_indices:
        idx = random.choice(real_indices)
        mutate_real_code_line(lines, idx)
    else:
        print(f"No real code lines found in {filepath}")
        return False

    with open(filepath, 'w') as f:
        f.writelines(lines)
    return True

def mutate_real_code_line(lines, idx):
    line = lines[idx]
    action = random.choice(['remove', 'replace', 'modify'])

    if action == 'remove':
        print(f"Removed line {idx+1}: {line.strip()}")
        lines.pop(idx)
    elif action == 'replace':
        # Insert a compile error or nonsensical assignment
        lines[idx] = 'THIS WILL NOT COMPILE // chaos mutation\n'
        print(f"Replaced line {idx+1} with syntax error")
    elif action == 'modify':
        # Try to flip a bool, zero a variable, or comment out logic
        if '=' in line:
            # Replace right side with zero/nil/false/empty string
            left = line.split('=')[0]
            lines[idx] = f'{left}= {random.choice(["0", "nil", "false", "\"\""])} // chaos-mutation\n'
            print(f"Mutated assignment at line {idx+1}")
        else:
            # Otherwise, comment out
            lines[idx] = f'// chaos mutation: {line}'
            print(f"Commented out line {idx+1}")

if __name__ == "__main__":
    file = pick_file(ext=".go")
    if file:
        mutate_file(file)
    else:
        print("No Go files found to mutate.")
