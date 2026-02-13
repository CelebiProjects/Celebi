#!/usr/bin/env python3
"""
Validate all public function docstrings in shell.py against Google style requirements.

This script performs comprehensive validation of all 61 public functions in
CelebiChrono/interface/shell.py to ensure they meet Google-style documentation standards.

Validation checks:
1. All public functions must have docstrings
2. Required sections (Args, Returns, Examples, Note) must be present
3. Args section must document all parameters
4. Returns section must describe content/meaning, not just say "Message object"
5. Examples section must contain usage examples
6. Note section must contain important considerations

Usage:
    python scripts/validate_all_docs.py

Exit codes:
    0 - All functions pass validation
    1 - One or more functions fail validation
"""

import ast
import re
import sys
from typing import List, Dict, Any, Tuple, Optional

def get_function_return_type(func_node: ast.FunctionDef) -> Optional[str]:
    """Extract return type annotation from function node."""
    if func_node.returns is None:
        return None

    # Handle different AST node types for return annotations
    if isinstance(func_node.returns, ast.Constant):
        if func_node.returns.value is None:
            return "None"
        return str(func_node.returns.value)
    elif isinstance(func_node.returns, ast.Name):
        return func_node.returns.id
    elif isinstance(func_node.returns, ast.Attribute):
        # Handle qualified names like typing.List
        return ast.unparse(func_node.returns) if hasattr(ast, 'unparse') else str(func_node.returns)
    elif isinstance(func_node.returns, ast.Subscript):
        # Handle generic types like List[str]
        return ast.unparse(func_node.returns) if hasattr(ast, 'unparse') else str(func_node.returns)
    else:
        return str(func_node.returns)

def function_has_parameters(func_node: ast.FunctionDef) -> bool:
    """Check if function has any parameters."""
    return bool(
        func_node.args.args or
        func_node.args.vararg or
        func_node.args.kwonlyargs or
        func_node.args.kwarg or
        func_node.args.posonlyargs
    )

def validate_function_docstring(func_node: ast.FunctionDef, docstring: Optional[str]) -> Dict[str, Any]:
    """Validate a single function's docstring against Google style requirements.

    Args:
        func_node: AST node for the function
        docstring: The function's docstring (None if missing)

    Returns:
        Dictionary with validation results
    """
    if not docstring:
        return {
            'valid': False,
            'errors': ['Missing docstring'],
            'warnings': []
        }

    errors = []
    warnings = []

    # Check for required sections
    required_sections = ['Args', 'Returns', 'Examples', 'Note']

    for section in required_sections:
        # Skip Returns section for functions that return None
        if section == 'Returns':
            return_type = get_function_return_type(func_node)
            if return_type == "None" or return_type is None:
                continue  # No Returns section needed for None-returning functions

        # Skip Args section for functions without parameters
        if section == 'Args':
            if not function_has_parameters(func_node):
                continue  # No Args section needed for parameterless functions

        # Check if section exists
        if not re.search(fr'{section}:', docstring):
            errors.append(f'Missing {section} section')

    # Check Args section quality if present
    if 'Args:' in docstring and function_has_parameters(func_node):
        args_section_match = re.search(r'Args:.*?(?=\n\n|\Z)', docstring, re.DOTALL)
        if args_section_match:
            args_text = args_section_match.group(0)
            # Count documented parameters (lines with "):" pattern)
            param_lines = [line for line in args_text.split('\n') if re.search(r'\):', line)]

            # Count total parameters (excluding self for methods)
            total_params = len(func_node.args.args)
            if total_params > 0 and func_node.args.args[0].arg == 'self':
                total_params -= 1  # Don't count self parameter

            if len(param_lines) < total_params:
                errors.append(f'Incomplete Args documentation: {len(param_lines)}/{total_params} parameters documented')
        else:
            errors.append('Args section exists but is empty or malformed')

    # Check Returns section quality if present
    if 'Returns:' in docstring:
        returns_section_match = re.search(r'Returns:.*?(?=\n\n|\Z)', docstring, re.DOTALL)
        if returns_section_match:
            returns_text = returns_section_match.group(0)
            # Check if Returns just says "Message object" without meaningful description
            if re.search(r'Message\s+object', returns_text, re.IGNORECASE):
                # Look for additional descriptive content
                lines = returns_text.split('\n')
                if len(lines) <= 2 and len(returns_text.strip()) < 50:
                    warnings.append('Returns section may be too brief - describe content/meaning, not just "Message object"')
        else:
            errors.append('Returns section exists but is empty or malformed')

    # Check Examples section quality
    if 'Examples:' in docstring:
        examples_section_match = re.search(r'Examples:.*?(?=\n\n|\Z)', docstring, re.DOTALL)
        if examples_section_match:
            examples_text = examples_section_match.group(0)
            # Count example lines (non-empty lines after "Examples:")
            example_lines = [line.strip() for line in examples_text.split('\n')[1:] if line.strip()]
            if len(example_lines) < 1:
                warnings.append('Examples section should contain at least one example')
        else:
            errors.append('Examples section exists but is empty or malformed')

    # Check Note section quality
    if 'Note:' in docstring:
        note_section_match = re.search(r'Note:.*?(?=\n\n|\Z)', docstring, re.DOTALL)
        if note_section_match:
            note_text = note_section_match.group(0)
            # Check if note is meaningful (more than a few words)
            note_content = ' '.join(note_text.split('\n')[1:]).strip()
            if len(note_content.split()) < 3:
                warnings.append('Note section may be too brief - add important considerations')
        else:
            errors.append('Note section exists but is empty or malformed')

    return {
        'valid': len(errors) == 0,
        'errors': errors,
        'warnings': warnings
    }

def get_all_public_functions(tree: ast.AST) -> List[ast.FunctionDef]:
    """Extract all public function nodes from AST."""
    public_funcs = []
    for node in ast.walk(tree):
        if isinstance(node, ast.FunctionDef) and not node.name.startswith('_'):
            public_funcs.append(node)
    return public_funcs

def validate_all_functions() -> Tuple[bool, List[Tuple[str, Dict[str, Any]]]]:
    """Validate all public functions in shell.py.

    Returns:
        Tuple of (all_valid, results) where results is list of (func_name, validation_result)
    """
    shell_py_path = '/Users/zhaomr/workdir/Chern/Celebi/CelebiChrono/interface/shell.py'

    try:
        with open(shell_py_path, 'r') as f:
            content = f.read()
    except FileNotFoundError:
        print(f"Error: File not found: {shell_py_path}")
        sys.exit(1)

    try:
        tree = ast.parse(content)
    except SyntaxError as e:
        print(f"Error: Syntax error in {shell_py_path}: {e}")
        sys.exit(1)

    public_funcs = get_all_public_functions(tree)
    results = []
    all_valid = True

    for func_node in public_funcs:
        docstring = ast.get_docstring(func_node)
        validation = validate_function_docstring(func_node, docstring)
        results.append((func_node.name, validation))

        if not validation['valid']:
            all_valid = False

    return all_valid, results

def print_validation_results(results: List[Tuple[str, Dict[str, Any]]]) -> None:
    """Print formatted validation results."""
    print("=" * 80)
    print("SHELL INTERFACE DOCUMENTATION VALIDATION REPORT")
    print("=" * 80)
    print(f"Validating all public functions in CelebiChrono/interface/shell.py")
    print(f"Total functions: {len(results)}")
    print()

    # Sort results: errors first, then warnings, then valid
    results_with_issues = []
    results_valid = []

    for func_name, validation in results:
        if not validation['valid'] or validation['warnings']:
            results_with_issues.append((func_name, validation))
        else:
            results_valid.append((func_name, validation))

    # Print functions with issues
    if results_with_issues:
        print("FUNCTIONS NEEDING ATTENTION:")
        print("-" * 40)

        for func_name, validation in results_with_issues:
            status = "✗" if not validation['valid'] else "⚠"
            print(f"{status} {func_name:30}")

            if not validation['valid']:
                for error in validation['errors']:
                    print(f"    ERROR: {error}")

            for warning in validation['warnings']:
                print(f"    WARNING: {warning}")

            print()

    # Print valid functions
    if results_valid:
        print("VALID FUNCTIONS:")
        print("-" * 40)

        # Group by first letter for better readability
        funcs_by_letter = {}
        for func_name, validation in results_valid:
            first_letter = func_name[0].upper()
            if first_letter not in funcs_by_letter:
                funcs_by_letter[first_letter] = []
            funcs_by_letter[first_letter].append(func_name)

        for letter in sorted(funcs_by_letter.keys()):
            funcs = sorted(funcs_by_letter[letter])
            print(f"{letter}: {', '.join(funcs)}")
        print()

    # Summary statistics
    total_funcs = len(results)
    valid_funcs = len([r for r in results if r[1]['valid'] and not r[1]['warnings']])
    warning_funcs = len([r for r in results if r[1]['warnings']])
    error_funcs = len([r for r in results if not r[1]['valid']])

    print("SUMMARY:")
    print("-" * 40)
    print(f"Total public functions: {total_funcs}")
    print(f"✓ Fully valid: {valid_funcs}")
    print(f"⚠ With warnings: {warning_funcs}")
    print(f"✗ With errors: {error_funcs}")

    if valid_funcs == total_funcs:
        print(f"\n✅ SUCCESS: All {total_funcs} functions have valid Google-style docstrings!")
    else:
        print(f"\n❌ ISSUES FOUND: {error_funcs + warning_funcs} functions need attention")

def main() -> int:
    """Main validation function."""
    print("Starting comprehensive documentation validation...")

    all_valid, results = validate_all_functions()
    print_validation_results(results)

    # Return exit code based on validation results
    # Consider it a failure if there are any errors (warnings are ok for now)
    has_errors = any(not validation['valid'] for _, validation in results)

    if has_errors:
        print("\n❌ Validation failed: Some functions have documentation errors.")
        return 1
    else:
        print("\n✅ Validation passed: All functions meet basic requirements.")
        print("   (Warnings indicate areas for improvement but don't block validation)")
        return 0

if __name__ == '__main__':
    sys.exit(main())