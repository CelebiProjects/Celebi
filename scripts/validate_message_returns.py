#!/usr/bin/env python3
"""
Validate Returns sections for functions that return Message objects.

Specifically checks that Returns sections for Message-returning functions
describe content/meaning, not just say "Message object".
"""

import ast
import re
import sys
from typing import List, Dict, Any, Tuple

def get_return_type(func_node: ast.FunctionDef) -> str:
    """Get the return type annotation as a string."""
    if func_node.returns is None:
        return "None"

    if isinstance(func_node.returns, ast.Constant):
        if func_node.returns.value is None:
            return "None"
        return str(func_node.returns.value)
    elif isinstance(func_node.returns, ast.Name):
        return func_node.returns.id
    elif isinstance(func_node.returns, ast.Attribute):
        # Handle qualified names
        try:
            return ast.unparse(func_node.returns)
        except AttributeError:
            # Fallback for older Python versions
            return f"{func_node.returns.value.id}.{func_node.returns.attr}"
    elif isinstance(func_node.returns, ast.Subscript):
        try:
            return ast.unparse(func_node.returns)
        except AttributeError:
            return "ComplexType"
    else:
        return str(type(func_node.returns).__name__)

def check_message_return_functions() -> List[Tuple[str, str, str]]:
    """Check all functions that return Message objects."""
    shell_py_path = '/Users/zhaomr/workdir/Chern/Celebi/CelebiChrono/interface/shell.py'

    with open(shell_py_path, 'r') as f:
        content = f.read()

    tree = ast.parse(content)
    results = []

    for node in ast.walk(tree):
        if isinstance(node, ast.FunctionDef) and not node.name.startswith('_'):
            return_type = get_return_type(node)

            # Check if returns Message or Message-like type
            if 'Message' in return_type:
                docstring = ast.get_docstring(node)
                returns_text = ""

                if docstring:
                    # Extract Returns section
                    returns_match = re.search(r'Returns:\s*(.*?)(?=\n\n|\Z)', docstring, re.DOTALL)
                    if returns_match:
                        returns_text = returns_match.group(1).strip()

                results.append((node.name, return_type, returns_text))

    return results

def analyze_returns_quality(returns_text: str) -> Dict[str, Any]:
    """Analyze the quality of a Returns section for Message-returning functions."""
    if not returns_text:
        return {
            'has_returns': False,
            'is_generic': True,
            'word_count': 0,
            'suggestions': ['Missing Returns section for Message-returning function']
        }

    # Check for generic descriptions
    generic_patterns = [
        r'^\s*Message\s+object\s*\.?\s*$',
        r'^\s*Message\s*\.?\s*$',
        r'^\s*Returns\s+a\s+message\s*\.?\s*$',
        r'^\s*.*\s+message\s*object\s*\.?\s*$',
    ]

    is_generic = False
    for pattern in generic_patterns:
        if re.search(pattern, returns_text, re.IGNORECASE):
            is_generic = True
            break

    # Count words
    word_count = len(returns_text.split())

    suggestions = []
    if is_generic:
        suggestions.append('Returns section is too generic - describe what the Message contains')
    if word_count < 5:
        suggestions.append('Returns section may be too brief - describe content/meaning of the Message')

    return {
        'has_returns': True,
        'is_generic': is_generic,
        'word_count': word_count,
        'suggestions': suggestions
    }

def main() -> int:
    """Main function."""
    print("=" * 80)
    print("MESSAGE-RETURNING FUNCTIONS RETURNS SECTION VALIDATION")
    print("=" * 80)
    print("Checking that Returns sections describe content/meaning, not just 'Message object'")
    print()

    results = check_message_return_functions()

    if not results:
        print("No functions found that return Message objects.")
        return 0

    print(f"Found {len(results)} functions that return Message objects:")
    print()

    needs_improvement = []
    good = []

    for func_name, return_type, returns_text in results:
        analysis = analyze_returns_quality(returns_text)

        if analysis['suggestions']:
            needs_improvement.append((func_name, return_type, returns_text, analysis))
        else:
            good.append((func_name, return_type, returns_text))

    # Print functions needing improvement
    if needs_improvement:
        print("FUNCTIONS NEEDING IMPROVEMENT:")
        print("-" * 40)

        for func_name, return_type, returns_text, analysis in needs_improvement:
            print(f"✗ {func_name:30} -> {return_type}")
            if returns_text:
                print(f"  Returns: {returns_text[:100]}...")
            else:
                print(f"  Returns: [MISSING]")
            for suggestion in analysis['suggestions']:
                print(f"  SUGGESTION: {suggestion}")
            print()

    # Print good functions
    if good:
        print("GOOD RETURNS SECTIONS:")
        print("-" * 40)

        for func_name, return_type, returns_text in good:
            print(f"✓ {func_name:30} -> {return_type}")
            if returns_text:
                # Truncate long returns text
                display_text = returns_text
                if len(display_text) > 80:
                    display_text = display_text[:77] + "..."
                print(f"  Returns: {display_text}")
            print()

    # Summary
    print("SUMMARY:")
    print("-" * 40)
    print(f"Total Message-returning functions: {len(results)}")
    print(f"✓ Good Returns sections: {len(good)}")
    print(f"⚠ Needs improvement: {len(needs_improvement)}")

    if len(needs_improvement) == 0:
        print("\n✅ SUCCESS: All Message-returning functions have descriptive Returns sections!")
        return 0
    else:
        print(f"\n❌ ISSUES: {len(needs_improvement)} Message-returning functions need Returns section improvements")
        return 1

if __name__ == '__main__':
    sys.exit(main())