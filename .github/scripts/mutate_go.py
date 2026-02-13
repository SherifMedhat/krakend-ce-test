#!/usr/bin/env python3
"""
Chaos mutation script for Go code.
Performs meaningful logic mutations to test quality gates.
"""

import os
import re
import random
import glob
from typing import List, Tuple, Optional

class GoMutator:
    def __init__(self):
        self.mutations_applied = []
        
    def find_go_files(self, root_dir: str = ".") -> List[str]:
        """Find all Go files, excluding vendor and test files for main mutations."""
        go_files = []
        for pattern in ["**/*.go", "*.go"]:
            files = glob.glob(pattern, recursive=True)
            for file in files:
                # Skip vendor, .git, and some test files for main logic mutations
                if not any(x in file for x in ["vendor/", ".git/", "testdata/"]):
                    go_files.append(file)
        return go_files
    
    def read_file(self, filepath: str) -> str:
        """Read file content."""
        try:
            with open(filepath, 'r', encoding='utf-8') as f:
                return f.read()
        except Exception as e:
            print(f"Error reading {filepath}: {e}")
            return ""
    
    def write_file(self, filepath: str, content: str) -> None:
        """Write content to file."""
        try:
            with open(filepath, 'w', encoding='utf-8') as f:
                f.write(content)
        except Exception as e:
            print(f"Error writing {filepath}: {e}")
    
    def mutate_comparison_operators(self, content: str) -> Tuple[str, bool]:
        """Mutate comparison operators (==, !=, <, >, <=, >=)."""
        operators = {
            r'==': '!=',
            r'!=': '==', 
            r'(?<!=)<=(?!=)': '>',
            r'(?<!=)>=(?!=)': '<',
            r'(?<![<>=!])>(?!=)': '<=',
            r'(?<![<>=!])<(?!=)': '>='
        }
        
        for old_op, new_op in operators.items():
            matches = list(re.finditer(old_op, content))
            if matches:
                match = random.choice(matches)
                content = content[:match.start()] + new_op + content[match.end():]
                return content, True
        return content, False
    
    def mutate_arithmetic_operators(self, content: str) -> Tuple[str, bool]:
        """Mutate arithmetic operators (+, -, *, /, %)."""
        operators = {
            r'(?<!\+)\+(?!\+|=)': '-',
            r'(?<!-)-(?!-|=)': '+',
            r'(?<!\*)\*(?!\*|=)': '/',
            r'(?<!/)\/(?!/|=)': '*',
            r'%(?!=)': '*'
        }
        
        for old_op, new_op in operators.items():
            matches = list(re.finditer(old_op, content))
            if matches:
                match = random.choice(matches)
                content = content[:match.start()] + new_op + content[match.end():]
                return content, True
        return content, False
    
    def mutate_logical_operators(self, content: str) -> Tuple[str, bool]:
        """Mutate logical operators (&&, ||)."""
        operators = {
            r'&&': '||',
            r'\|\|': '&&'
        }
        
        for old_op, new_op in operators.items():
            matches = list(re.finditer(old_op, content))
            if matches:
                match = random.choice(matches)
                content = content[:match.start()] + new_op + content[match.end():]
                return content, True
        return content, False
    
    def mutate_boolean_literals(self, content: str) -> Tuple[str, bool]:
        """Mutate boolean literals (true/false)."""
        # Match true/false that are whole words
        true_matches = list(re.finditer(r'\btrue\b', content))
        false_matches = list(re.finditer(r'\bfalse\b', content))
        
        all_matches = [(m, 'false') for m in true_matches] + [(m, 'true') for m in false_matches]
        
        if all_matches:
            match, replacement = random.choice(all_matches)
            content = content[:match.start()] + replacement + content[match.end():]
            return content, True
        return content, False
    
    def mutate_numeric_constants(self, content: str) -> Tuple[str, bool]:
        """Mutate numeric constants by changing small numbers."""
        # Find numeric literals (but avoid changing things like port numbers, versions, etc.)
        number_pattern = r'\b([0-9]+)\b'
        matches = list(re.finditer(number_pattern, content))
        
        if matches:
            match = random.choice(matches)
            original_num = int(match.group(1))
            
            # Only mutate small numbers to avoid breaking things like ports, versions
            if 0 <= original_num <= 100:
                mutations = []
                if original_num > 0:
                    mutations.extend([original_num - 1, 0])
                if original_num < 100:
                    mutations.append(original_num + 1)
                if original_num == 0:
                    mutations.append(1)
                
                if mutations:
                    new_num = random.choice(mutations)
                    content = content[:match.start()] + str(new_num) + content[match.end():]
                    return content, True
        return content, False
    
    def mutate_if_conditions(self, content: str) -> Tuple[str, bool]:
        """Negate if conditions by adding/removing ! operator."""
        # Find if statements with simple conditions
        if_pattern = r'\bif\s+([^{]+)\s*{'
        matches = list(re.finditer(if_pattern, content))
        
        if matches:
            match = random.choice(matches)
            condition = match.group(1).strip()
            
            # Add negation if not present, remove if present
            if condition.startswith('!'):
                new_condition = condition[1:].strip()
            else:
                new_condition = f"!({condition})"
            
            new_if_statement = f"if {new_condition} {{"
            content = content[:match.start()] + new_if_statement + content[match.end():]
            return content, True
        return content, False
    
    def mutate_return_values(self, content: str) -> Tuple[str, bool]:
        """Mutate simple return statements."""
        # Find return statements with simple values
        return_patterns = [
            (r'\breturn\s+true\b', 'return false'),
            (r'\breturn\s+false\b', 'return true'),
            (r'\breturn\s+nil\b', 'return errors.New("mutation error")'),
            (r'\breturn\s+0\b', 'return 1'),
            (r'\breturn\s+1\b', 'return 0'),
            (r'\breturn\s+""', 'return "mutated"'),
        ]
        
        for pattern, replacement in return_patterns:
            matches = list(re.finditer(pattern, content))
            if matches:
                match = random.choice(matches)
                content = content[:match.start()] + replacement + content[match.end():]
                return content, True
        return content, False
    
    def mutate_loop_conditions(self, content: str) -> Tuple[str, bool]:
        """Mutate loop conditions (for loops, while conditions)."""
        # Mutate for loop conditions
        for_pattern = r'\bfor\s+([^{]+)\s*{'
        matches = list(re.finditer(for_pattern, content))
        
        if matches:
            match = random.choice(matches)
            condition = match.group(1).strip()
            
            # Simple mutations for common patterns
            if '<' in condition:
                new_condition = condition.replace('<', '<=', 1)
            elif '<=' in condition:
                new_condition = condition.replace('<=', '<', 1)
            elif '>' in condition:
                new_condition = condition.replace('>', '>=', 1)
            elif '>=' in condition:
                new_condition = condition.replace('>=', '>', 1)
            else:
                return content, False
            
            new_for_statement = f"for {new_condition} {{"
            content = content[:match.start()] + new_for_statement + content[match.end():]
            return content, True
        return content, False
    
    def apply_random_mutation(self, content: str) -> Tuple[str, str]:
        """Apply a random mutation to the content."""
        mutations = [
            ("comparison_operators", self.mutate_comparison_operators),
            ("arithmetic_operators", self.mutate_arithmetic_operators),
            ("logical_operators", self.mutate_logical_operators),
            ("boolean_literals", self.mutate_boolean_literals),
            ("numeric_constants", self.mutate_numeric_constants),
            ("if_conditions", self.mutate_if_conditions),
            ("return_values", self.mutate_return_values),
            ("loop_conditions", self.mutate_loop_conditions),
        ]
        
        # Shuffle to get random order
        random.shuffle(mutations)
        
        for mutation_name, mutation_func in mutations:
            new_content, success = mutation_func(content)
            if success:
                return new_content, mutation_name
        
        return content, "no_mutation_applied"
    
    def mutate_file(self, filepath: str) -> bool:
        """Mutate a single Go file."""
        print(f"Attempting to mutate: {filepath}")
        
        content = self.read_file(filepath)
        if not content:
            return False
        
        # Skip files that look like they might be generated or have special purposes
        if any(marker in content for marker in [
            "// Code generated", 
            "//go:generate",
            "DO NOT EDIT",
            "auto-generated"
        ]):
            print(f"Skipping generated file: {filepath}")
            return False
        
        original_content = content
        new_content, mutation_type = self.apply_random_mutation(content)
        
        if new_content != original_content:
            self.write_file(filepath, new_content)
            mutation_info = f"{filepath}: {mutation_type}"
            self.mutations_applied.append(mutation_info)
            print(f"Applied {mutation_type} mutation to {filepath}")
            return True
        else:
            print(f"No mutation applied to {filepath}")
            return False
    
    def run_chaos_mutation(self) -> None:
        """Run the chaos mutation process."""
        print("🔥 Starting Go code chaos mutation...")
        
        go_files = self.find_go_files()
        if not go_files:
            print("No Go files found!")
            return
        
        print(f"Found {len(go_files)} Go files")
        
        # Filter out test files for main mutations, but keep some for different types of mutations
        main_files = [f for f in go_files if not f.endswith('_test.go')]
        
        if not main_files:
            print("No non-test Go files found!")
            return
        
        # Select 1-3 files to mutate (depending on repo size)
        num_files_to_mutate = min(random.randint(1, 3), len(main_files))
        files_to_mutate = random.sample(main_files, num_files_to_mutate)
        
        mutations_successful = 0
        for filepath in files_to_mutate:
            if self.mutate_file(filepath):
                mutations_successful += 1
        
        print(f"\n✅ Chaos mutation complete!")
        print(f"Files processed: {len(files_to_mutate)}")
        print(f"Successful mutations: {mutations_successful}")
        
        if self.mutations_applied:
            print("\nMutations applied:")
            for mutation in self.mutations_applied:
                print(f"  - {mutation}")
        else:
            print("No mutations were applied.")

def main():
    """Main entry point."""
    mutator = GoMutator()
    mutator.run_chaos_mutation()

if __name__ == "__main__":
    main()
