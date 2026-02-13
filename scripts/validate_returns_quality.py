#!/usr/bin/env python3
"""
Validate Returns section quality in shell.py docstrings.

This script specifically checks that Returns sections describe content/meaning,
not just say "Message object" or similar generic descriptions.

Requirements from the plan:
- Returns sections should describe content/meaning, not just say "Message object"
- Focus on public functions only
"""

import ast
import re
import sys
from typing import List, Dict, Any, Tuple

def analyze_returns_section(docstring: str) -> Dict[str, Any]:
    """Analyze the quality of the Returns section in a docstring.

    Returns:
        Dictionary with analysis results including:
        - has_returns: bool
        - returns_text: str (the Returns section content)
        - is_generic: bool (True if just says "Message object" or similar)
        - word_count: int
        - suggestions: List[str]
    """
    if not docstring:
        return {
            'has_returns': False,
            'returns_text': '',
            'is_generic': False,
            'word_count': 0,
            'suggestions': ['Missing Returns section']
        }

    # Find Returns section
    returns_match = re.search(r'Returns:\s*(.*?)(?=\n\n|\Z)', docstring, re.DOTALL)
    if not returns_match:
        return {
            'has_returns': False,
            'returns_text': '',
            'is_generic': False,
            'word_count': 0,
            'suggestions': ['Missing Returns section']
        }

    returns_text = returns_match.group(1).strip()

    # Check for generic descriptions
    # Only flag if it's specifically about Message objects or very generic
    generic_patterns = [
        r'^\s*Message\s+object\s*\.?\s*$',  # Just "Message object" or "Message object."
        r'^\s*Message\s*\.?\s*$',           # Just "Message" or "Message."
        r'^\s*Returns\s+a\s+message\s*\.?\s*$',  # "Returns a message"
        r'^\s*.*\s+message\s*\.?\s*$',      # Ends with "message"
    ]

    is_generic = False
    for pattern in generic_patterns:
        if re.search(pattern, returns_text, re.IGNORECASE):
            is_generic = True
            break

    # Don't flag None-returning functions that describe side effects
    # Check if returns_text starts with "None:" - this is acceptable for None-returning functions
    if returns_text.lower().startswith('none:'):
        is_generic = False

    # Count words in Returns section (excluding "Returns:" and empty lines)
    lines = returns_text.split('\n')
    word_count = 0
    for line in lines:
        line = line.strip()
        if line and not line.startswith('Returns:'):
            word_count += len(line.split())

    suggestions = []
    if is_generic:
        suggestions.append('Returns section is too generic - describe specific content/meaning')
    if word_count < 5:
        suggestions.append('Returns section may be too brief - add more detail about what is returned')

    return {
        'has_returns': True,
        'returns_text': returns_text,
        'is_generic': is_generic,
        'word_count': word_count,
        'suggestions': suggestions
    }

def check_all_functions() -> List[Tuple[str, Dict[str, Any]]]:
    """Check Returns section quality for all public functions."""
    shell_py_path = '/Users/zhaomr/workdir/Chern/Celebi/CelebiChrono/interface/shell.py'

    with open(shell_py_path, 'r') as f:
        content = f.read()

    tree = ast.parse(content)
    results = []

    for node in ast.walk(tree):
        if isinstance(node, ast.FunctionDef) and not node.name.startswith('_'):
            docstring = ast.get_docstring(node)
            analysis = analyze_returns_section(docstring)
            results.append((node.name, analysis))

    return results

def print_results(results: List[Tuple[str, Dict[str, Any]]]) -> None:
    """Print formatted analysis results."""
    print("=" * 80)
    print("RETURNS SECTION QUALITY ANALYSIS")
    print("=" * 80)
    print("Checking that Returns sections describe content/meaning, not just 'Message object'")
    print()

    # Categorize results
    needs_improvement = []
    good = []
    no_returns_needed = []

    # We need to re-parse to check return types
    shell_py_path = '/Users/zhaomr/workdir/Chern/Celebi/CelebiChrono/interface/shell.py'
    with open(shell_py_path, 'r') as f:
        content = f.read()
    tree = ast.parse(content)

    # Create a mapping of function names to their nodes
    func_nodes = {}
    for node in ast.walk(tree):
        if isinstance(node, ast.FunctionDef) and not node.name.startswith('_'):
            func_nodes[node.name] = node

    for func_name, analysis in results:
        # Check if function needs a Returns section
        # Functions returning None don't need Returns section
        func_returns_none = False
        if func_name in func_nodes:
            node = func_nodes[func_name]
            if node.returns is None:
                func_returns_none = True
            elif isinstance(node.returns, ast.Constant) and node.returns.value is None:
                func_returns_none = True

        if func_returns_none and not analysis['has_returns']:
            no_returns_needed.append(func_name)
        elif analysis['suggestions']:
            needs_improvement.append((func_name, analysis))
        else:
            good.append(func_name)

    # Print functions needing improvement
    if needs_improvement:
        print("FUNCTIONS NEEDING IMPROVEMENT:")
        print("-" * 40)

        for func_name, analysis in needs_improvement:
            print(f"✗ {func_name:30}")
            print(f"  Returns: {analysis['returns_text'][:80]}...")
            for suggestion in analysis['suggestions']:
                print(f"  SUGGESTION: {suggestion}")
            print()

    # Print good functions
    if good:
        print("GOOD RETURNS SECTIONS:")
        print("-" * 40)

        # Group by first letter
        funcs_by_letter = {}
        for func_name in good:
            first_letter = func_name[0].upper()
            if first_letter not in funcs_by_letter:
                funcs_by_letter[first_letter] = []
            funcs_by_letter[first_letter].append(func_name)

        for letter in sorted(funcs_by_letter.keys()):
            funcs = sorted(funcs_by_letter[letter])
            print(f"{letter}: {', '.join(funcs)}")
        print()

    # Print functions that don't need Returns sections
    if no_returns_needed:
        print("FUNCTIONS WITHOUT RETURNS (None-returning):")
        print("-" * 40)

        funcs_by_letter = {}
        for func_name in no_returns_needed:
            first_letter = func_name[0].upper()
            if first_letter not in funcs_by_letter:
                funcs_by_letter[first_letter] = []
            funcs_by_letter[first_letter].append(func_name)

        for letter in sorted(funcs_by_letter.keys()):
            funcs = sorted(funcs_by_letter[letter])
            print(f"{letter}: {', '.join(funcs)}")
        print()

    # Summary
    print("SUMMARY:")
    print("-" * 40)
    print(f"Total functions analyzed: {len(results)}")
    print(f"✓ Good Returns sections: {len(good)}")
    print(f"⚠ Needs improvement: {len(needs_improvement)}")
    print(f"○ No Returns needed (returns None): {len(no_returns_needed)}")

    if len(needs_improvement) == 0:
        print("\n✅ SUCCESS: All Returns sections meet quality requirements!")
    else:
        print(f"\n❌ ISSUES: {len(needs_improvement)} functions need Returns section improvements")

def main() -> int:
    """Main function."""
    print("Analyzing Returns section quality...")

    results = check_all_functions()
    print_results(results)

    # Check if any functions need improvement
    needs_improvement = any(analysis['suggestions'] for _, analysis in results)

    return 1 if needs_improvement else 0

if __name__ == '__main__':
    sys.exit(main())