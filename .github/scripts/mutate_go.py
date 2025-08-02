import os
import random
from pathlib import Path

def pick_file(ext=".go"):
    files = [
        f for f in Path('.').rglob(f'*{ext}') 
        if 'vendor' not in str(f) and 'test' not in str(f).lower() and '/.git/' not in str(f)
    ]
    return random.choice(files) if files else None

def mutate_file(filepath):
    with open(filepath, 'r') as f:
        lines = f.readlines()
    if not lines:
        return False

    idx = random.randint(0, len(lines) - 1)
    action = random.choice(['remove', 'replace', 'modify'])

    if action == 'remove':
        lines.pop(idx)
    elif action == 'replace':
        lines[idx] = '// chaos mutation: line replaced\n'
    elif action == 'modify':
        if lines[idx].strip().startswith('//'):
            lines[idx] = '// chaos mutation: mutated comment\n'
        else:
            lines[idx] = lines[idx].rstrip('\n') + ' // chaos-mutation\n'

    with open(filepath, 'w') as f:
        f.writelines(lines)
    print(f"Mutated {filepath}: {action} at line {idx+1}")
    return True

if __name__ == "__main__":
    file = pick_file(ext=".go")
    if file:
        mutate_file(file)
    else:
        print("No Go files found to mutate.")
