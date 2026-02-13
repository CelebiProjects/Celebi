#!/usr/bin/env python3
"""
Validate execution management function docstrings.
"""

import ast
import re
import sys

# List of execution management functions to validate
EXECUTION_FUNCTIONS = [
    'submit',
    'purge',
    'purge_old_impressions',
    'collect',
    'collect_outputs',
    'collect_logs'
]

def validate_function_docstring(func_node, docstring):
    """Validate a single function's docstring using logic from the plan."""
    if not docstring:
        return {'valid': False, 'errors': ['Missing docstring']}

    errors = []

    # Check for required sections - using logic from plan
    required_sections = ['Args', 'Returns', 'Examples', 'Note']
    for section in required_sections:
        if section == 'Returns' and func_node.returns is None:
            continue  # Skip Returns for functions returning None
        if section == 'Args' and not func_node.args.args:
            continue  # Skip Args for functions without parameters
        if not re.search(f'{section}:', docstring):
            errors.append(f'Missing {section} section')

    # Check Args format if function has parameters
    if func_node.args.args and 'Args:' in docstring:
        # Simple check for parameter documentation
        args_section = re.search(r'Args:.*?(?=\n\n|\Z)', docstring, re.DOTALL)
        if args_section:
            args_text = args_section.group(0)
            # Should have at least one parameter documented
            param_lines = [l for l in args_text.split('\n') if '):' in l]
            if len(param_lines) < len(func_node.args.args):
                errors.append('Incomplete Args documentation')

    return {'valid': len(errors) == 0, 'errors': errors}

def validate_functions():
    """Validate execution management function docstrings."""
    with open('/Users/zhaomr/workdir/Chern/Celebi/CelebiChrono/interface/shell.py', 'r') as f:
        content = f.read()

    tree = ast.parse(content)

    print("Execution Management Function Documentation Validation")
    print("=" * 60)

    all_valid = True
    for node in ast.walk(tree):
        if isinstance(node, ast.FunctionDef) and node.name in EXECUTION_FUNCTIONS:
            docstring = ast.get_docstring(node)
            validation = validate_function_docstring(node, docstring)
            status = "✓" if validation['valid'] else "✗"
            print(f"{status} {node.name:30}")

            if not validation['valid']:
                all_valid = False
                for error in validation['errors']:
                    print(f"    - {error}")

    print("\n" + "=" * 60)
    if all_valid:
        print("✓ All execution management functions have valid Google-style docstrings!")
    else:
        print("✗ Some functions need documentation improvements.")

    return all_valid

if __name__ == '__main__':
    success = validate_functions()
    sys.exit(0 if success else 1)