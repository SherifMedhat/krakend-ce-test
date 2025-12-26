import random
from pathlib import Path

def is_real_code(line):
    line_strip = line.strip()
    # Skip empty, bracket-only, or comment lines
    if not line_strip:
        return False
    if line_strip.startswith('//'):
        return False
    if line_strip in ['{', '}', '}', '{']:
        return False
    return True

def pick_file(ext=".go"):
    files = [
        f for f in Path('.').rglob(f'*{ext}')
        if 'vendor' not in str(f) and 'test' not in str(f).lower() and '/.git/' not in str(f)
    ]
    return random.choice(files) if files else None

def mutate_file(filepath):
    with open(filepath, 'r') as f:
        lines = f.readlines()

    # Find all "real code" line indices
    real_indices = [i for i, line in enumerate(lines) if is_real_code(line)]
    if not real_indices:
        print(f"No real code lines found in {filepath}")
        return False

    idx = random.choice(real_indices)
    action = random.choice(['remove', 'replace', 'modify'])

    original_line = lines[idx]

    if action == 'remove':
        lines.pop(idx)
        print(f"Removed line {idx+1}: {original_line.strip()}")
    elif action == 'replace':
        # Replace with a broken Go statement
        lines[idx] = 'syntax error // chaos mutation\n'
        print(f"Replaced line {idx+1} with syntax error")
    elif action == 'modify':
        # Mutate variable names or break logic
        mutated = original_line.rstrip('\n') + ' /*chaos*/\n'
        lines[idx] = mutated
        print(f"Modified line {idx+1}: {mutated.strip()}")

    with open(filepath, 'w') as f:
        f.writelines(lines)
    return True

if __name__ == "__main__":
    file = pick_file(ext=".go")
    if file:
        mutate_file(file)
    else:
        print("No Go files found to mutate.")
