"""
Google-style Docstring Utilities

This module provides utilities for generating, validating, and analyzing
Google-style docstrings for Python functions.

Features:
- Generate Google-style docstring templates
- Validate existing docstrings against Google style requirements
- Analyze docstrings and suggest improvements
- Generate docstrings from function signatures (basic support)

Usage Examples:
    >>> from scripts.doc_utils import generate_google_docstring
    >>> params = [('name', 'str', 'User name')]
    >>> doc = generate_google_docstring('greet', params, 'str', 'Greet user',
    ...                                 ['>>> greet("Alice")'], 'Simple greeting')
    >>> print(doc)

    >>> from scripts.doc_utils import validate_google_docstring
    >>> result = validate_google_docstring(doc)
    >>> print(result['valid'])

    >>> from scripts.doc_utils import analyze_docstring
    >>> analysis = analyze_docstring(doc)
    >>> print(analysis['suggestions'])

    >>> from scripts.doc_utils import generate_docstring_from_signature
    >>> sig = "process(data: List[str], verbose: bool = False)"
    >>> doc = generate_docstring_from_signature("process", sig, "Process data")

Limitations:
- `generate_docstring_from_signature` has limited support for complex type hints
- For production use with complex signatures, consider using `inspect` or `ast` modules
- Type hint parsing is simplified and may not handle all edge cases

Version: 1.0.0
Author: Documentation Utilities Team
"""
from typing import List, Tuple, Dict, Any, Optional, Union

__all__ = [
    'generate_google_docstring',
    'validate_google_docstring',
    'analyze_docstring',
    'generate_docstring_from_signature',
]

def generate_google_docstring(
    func_name: str,
    params: List[Tuple[str, str, str]],
    returns: str,
    description: str,
    examples: List[str],
    notes: Union[str, List[str]]
) -> str:
    """Generate a Google-style docstring template.

    Args:
        func_name: Name of the function
        params: List of (name, type, description) tuples for parameters
        returns: Return value description
        description: Function description
        examples: List of example strings
        notes: Notes as string or list of strings

    Returns:
        Formatted Google-style docstring

    Raises:
        ValueError: If inputs are invalid
        TypeError: If input types are incorrect
    """
    # Input validation
    if not isinstance(func_name, str) or not func_name:
        raise ValueError("func_name must be a non-empty string")

    if not isinstance(params, list):
        raise TypeError("params must be a list")

    for param in params:
        if not isinstance(param, tuple) or len(param) != 3:
            raise ValueError(
                "Each param must be a tuple of (name, type, description)"
            )
        if not all(isinstance(item, str) for item in param):
            raise TypeError("All param elements must be strings")

    if not isinstance(returns, str):
        raise TypeError("returns must be a string")

    if not isinstance(description, str):
        raise TypeError("description must be a string")

    if not isinstance(examples, list):
        raise TypeError("examples must be a list")

    for example in examples:
        if not isinstance(example, str):
            raise TypeError("All examples must be strings")

    if not isinstance(notes, (str, list)):
        raise TypeError("notes must be a string or list")

    if isinstance(notes, list):
        for note in notes:
            if not isinstance(note, str):
                raise TypeError("All notes must be strings")

    docstring = f'"""{description}\n\n'

    if params:
        docstring += 'Args:\n'
        for param_name, param_type, param_desc in params:
            docstring += f'    {param_name} ({param_type}): {param_desc}\n'
        docstring += '\n'

    if returns:
        docstring += f'Returns:\n    {returns}\n\n'

    if examples:
        docstring += 'Examples:\n'
        for example in examples:
            docstring += f'    {example}\n'
        docstring += '\n'

    if notes:
        docstring += 'Note:\n    '
        if isinstance(notes, list):
            docstring += '\n    '.join(notes)
        else:
            docstring += notes
        docstring += '\n'

    docstring += '"""'
    return docstring

def validate_google_docstring(docstring: str) -> Dict[str, Any]:
    """Validate a docstring against Google style requirements.

    Args:
        docstring: The docstring to validate

    Returns:
        Dictionary with validation results

    Raises:
        TypeError: If docstring is not a string
    """
    if not isinstance(docstring, str):
        raise TypeError("docstring must be a string")

    # Basic validation logic
    required_sections = ['Args', 'Returns', 'Examples', 'Note']
    missing = []

    for section in required_sections:
        if section.lower() not in docstring.lower():
            missing.append(section)

    return {
        'valid': len(missing) == 0,
        'missing_sections': missing,
        'has_triple_quotes': '"""' in docstring,
    }

def analyze_docstring(docstring: str) -> Dict[str, Any]:
    """
    Analyze an existing docstring and suggest improvements.

    Args:
        docstring: The docstring to analyze

    Returns:
        Dictionary with analysis results and suggestions

    Raises:
        TypeError: If docstring is not a string
    """
    if not isinstance(docstring, str):
        raise TypeError("docstring must be a string")

    if not docstring:
        return {
            'has_docstring': False,
            'sections_present': [],
            'sections_missing': ['Args', 'Returns', 'Examples', 'Note'],
            'suggestions': [
                'Add complete Google-style docstring'
            ]
        }

    analysis = {
        'has_docstring': True,
        'has_triple_quotes': '"""' in docstring,
        'sections_present': [],
        'sections_missing': [],
        'suggestions': []
    }

    # Check for required sections
    required_sections = ['Args', 'Returns', 'Examples', 'Note']
    for section in required_sections:
        if section.lower() in docstring.lower():
            analysis['sections_present'].append(section)
        else:
            analysis['sections_missing'].append(section)

    # Generate suggestions
    if not analysis['has_triple_quotes']:
        analysis['suggestions'].append('Wrap docstring in triple quotes (""")')

    if analysis['sections_missing']:
        missing_str = ', '.join(analysis['sections_missing'])
        analysis['suggestions'].append(f'Add missing sections: {missing_str}')

    # Check for basic structure
    if 'Args:' not in docstring and 'Parameters:' not in docstring:
        analysis['suggestions'].append(
            'Add parameter documentation with types and descriptions'
        )

    if 'Returns:' not in docstring and 'Yields:' not in docstring:
        analysis['suggestions'].append('Add return value documentation')

    if 'Examples:' not in docstring:
        analysis['suggestions'].append('Add usage examples')

    if 'Note:' not in docstring and 'Notes:' not in docstring:
        analysis['suggestions'].append(
            'Add notes about edge cases or important considerations'
        )

    return analysis

def generate_docstring_from_signature(
    func_name: str,
    signature: str,
    description: str = ""
) -> str:
    """
    Generate a docstring template from function signature.

    Note: This is a simplified implementation that handles basic type annotations.
    For complex type hints, consider using the `inspect` module or `ast` parsing.

    Args:
        func_name (str): Name of the function
        signature (str): Function signature string
        description (str): Optional description of the function

    Returns:
        str: Generated docstring template

    Raises:
        ValueError: If the signature cannot be parsed
    """
    import re

    # Validate inputs
    if not func_name or not isinstance(func_name, str):
        raise ValueError("func_name must be a non-empty string")

    if not signature or not isinstance(signature, str):
        raise ValueError("signature must be a non-empty string")

    # Remove function name and parentheses
    # Handle cases where function name might appear multiple times
    pattern = rf'^{re.escape(func_name)}\s*\((.*)\)\s*$'
    match = re.match(pattern, signature)

    if match:
        params_str = match.group(1).strip()
    else:
        # Try to extract parameters by removing function name
        params_str = signature.replace(func_name, '').strip('() ')

    params = []

    if params_str:
        # Improved regex pattern that handles:
        # 1. Simple parameters: x
        # 2. Typed parameters: x: int
        # 3. Default values: x: int = 1
        # 4. *args and **kwargs
        # 5. Complex type hints (though limited)
        # More robust parameter parsing that handles nested brackets
        # We'll parse manually instead of using a complex regex
        params_list = []
        current_param = ''
        bracket_depth = 0

        for char in params_str:
            if char == '[':
                bracket_depth += 1
            elif char == ']':
                bracket_depth -= 1
            elif char == ',' and bracket_depth == 0:
                params_list.append(current_param.strip())
                current_param = ''
                continue
            current_param += char

        if current_param:
            params_list.append(current_param.strip())

        for param_str in params_list:
            if not param_str:
                continue

            # Parse individual parameter
            # Split on first '=' for default value
            if '=' in param_str:
                param_part, default_part = param_str.split('=', 1)
                default_value = default_part.strip()
            else:
                param_part = param_str
                default_value = None

            # Split on first ':' for type annotation
            if ':' in param_part:
                name_part, type_part = param_part.split(':', 1)
                param_name = name_part.strip()
                param_type = type_part.strip()
            else:
                param_name = param_part.strip()
                param_type = 'Any'

            # Generate description
            if param_name.startswith('**'):
                param_desc = f'Keyword arguments {param_name[2:]}'
            elif param_name.startswith('*'):
                param_desc = f'Variable arguments {param_name[1:]}'
            else:
                param_desc = f'Description of {param_name}'

            if default_value:
                param_desc += f' (default: {default_value.strip()})'

            params.append((param_name, param_type, param_desc))

    # Generate docstring
    docstring = f'"""{description or f"Function {func_name}"}\n\n'

    if params:
        docstring += 'Args:\n'
        for param_name, param_type, param_desc in params:
            docstring += f'    {param_name} ({param_type}): {param_desc}\n'
        docstring += '\n'

    docstring += 'Returns:\n    Return value description\n\n'
    docstring += (
        'Examples:\n'
        '    >>> result = {func_name}()\n'
        '    >>> print(result)\n\n'
    )
    docstring += 'Note:\n    Important notes about this function\n'
    docstring += '"""'

    return docstring

def test_generate_google_docstring() -> None:
    """Test docstring generation."""
    params = [('line', 'str', 'Path or index to navigate to')]
    returns = 'None'
    description = 'Change directory within current project.'
    examples = [
        'cd subdir  # Change to subdirectory',
        'cd 2      # Change to index 2'
    ]
    notes = ['Project boundary safety enforced']

    docstring = generate_google_docstring(
        'cd', params, returns, description, examples, notes
    )

    assert 'Args:' in docstring
    assert 'Returns:' in docstring
    assert 'Examples:' in docstring
    assert 'Note:' in docstring
    assert 'line (str): Path or index to navigate to' in docstring
    print("✓ Docstring generation test passed")

def test_analyze_docstring() -> None:
    """Test docstring analysis."""
    # Test with complete docstring
    complete_doc = '''"""Example function.

Args:
    x (int): First parameter
    y (str): Second parameter

Returns:
    bool: True if successful

Examples:
    >>> example(1, "test")
    True

Note:
    This is a test function
"""'''

    analysis = analyze_docstring(complete_doc)
    assert analysis['has_docstring'] == True
    assert analysis['has_triple_quotes'] == True
    assert 'Args' in analysis['sections_present']
    assert 'Returns' in analysis['sections_present']
    assert 'Examples' in analysis['sections_present']
    assert 'Note' in analysis['sections_present']
    assert len(analysis['sections_missing']) == 0

    # Test with incomplete docstring
    incomplete_doc = '''"""Example function without proper sections."""'''
    analysis = analyze_docstring(incomplete_doc)
    assert analysis['has_docstring'] == True
    assert len(analysis['sections_missing']) == 4  # All sections missing
    assert len(analysis['suggestions']) > 0

    print("✓ Docstring analysis test passed")

def test_generate_from_signature() -> None:
    """Test docstring generation from signature."""
    signature = (
        "process_data(input_file: str, output_dir: str = '.', "
        "verbose: bool = False)"
    )
    docstring = generate_docstring_from_signature(
        "process_data", signature, "Process data file"
    )

    assert 'Args:' in docstring
    assert 'input_file (str):' in docstring
    assert 'output_dir (str):' in docstring
    assert 'verbose (bool):' in docstring
    assert 'Returns:' in docstring
    assert 'Examples:' in docstring
    assert 'Note:' in docstring

    print("✓ Signature-based generation test passed")


def test_generate_from_signature_edge_cases() -> None:
    """Test edge cases for signature-based generation."""
    # Test with *args and **kwargs
    signature1 = "func(*args, **kwargs)"
    docstring1 = generate_docstring_from_signature("func", signature1)
    assert 'args (Any):' in docstring1 or '*args' in docstring1
    assert 'kwargs (Any):' in docstring1 or '**kwargs' in docstring1

    # Test with complex type hints
    signature2 = "process(items: List[Dict[str, Any]], count: int = 0)"
    docstring2 = generate_docstring_from_signature("process", signature2)
    assert 'items (List[Dict[str, Any]]):' in docstring2
    assert 'count (int):' in docstring2

    # Test with no parameters
    signature3 = "no_params()"
    docstring3 = generate_docstring_from_signature("no_params", signature3)
    assert 'Function no_params' in docstring3

    # Test with qualified type names
    signature4 = "imported(module: typing.List, obj: pathlib.Path)"
    docstring4 = generate_docstring_from_signature("imported", signature4)
    assert 'module (typing.List):' in docstring4
    assert 'obj (pathlib.Path):' in docstring4

    print("✓ Signature edge cases test passed")


def test_input_validation() -> None:
    """Test input validation and error handling."""
    import pytest

    # Test generate_google_docstring validation
    with pytest.raises(TypeError):
        generate_google_docstring(123, [], "", "", [], "")  # func_name not string

    with pytest.raises(TypeError):
        generate_google_docstring("func", "not a list", "", "", [], "")

    with pytest.raises(ValueError):
        generate_google_docstring("func", [("a", "int")], "", "", [], "")

    with pytest.raises(TypeError):
        generate_google_docstring("func", [("a", "int", "desc")], 123, "", [], "")

    # Test validate_google_docstring validation
    with pytest.raises(TypeError):
        validate_google_docstring(123)  # docstring not string

    # Test analyze_docstring validation
    with pytest.raises(TypeError):
        analyze_docstring(456)  # docstring not string

    # Test generate_docstring_from_signature validation
    with pytest.raises(ValueError):
        generate_docstring_from_signature("", "signature")  # empty func_name

    with pytest.raises(ValueError):
        generate_docstring_from_signature("func", "")  # empty signature

    with pytest.raises(ValueError):
        generate_docstring_from_signature(123, "signature")  # func_name not string

    print("✓ Input validation test passed")


def test_complex_signatures() -> None:
    """Test handling of complex function signatures."""
    # Test with nested brackets in type hints
    signature1 = "nested(data: Dict[str, List[Tuple[int, str]]])"
    docstring1 = generate_docstring_from_signature("nested", signature1)
    assert ('data (Dict[str, List[Tuple[int, str]]]):' in docstring1
            or 'data (Any):' in docstring1)

    # Test with multiple defaults
    signature2 = "multi(a: int = 1, b: str = 'test', c: bool = True)"
    docstring2 = generate_docstring_from_signature("multi", signature2)
    assert 'a (int):' in docstring2
    assert 'b (str):' in docstring2
    assert 'c (bool):' in docstring2

    # Test with Union types (simplified handling)
    signature3 = "union_param(value: Union[int, str, None])"
    docstring3 = generate_docstring_from_signature("union_param", signature3)
    # Should at least not crash
    assert 'union_param' in docstring3

    print("✓ Complex signatures test passed")

def run_all_tests() -> None:
    """Run all test functions."""
    test_generate_google_docstring()
    test_analyze_docstring()
    test_generate_from_signature()
    test_generate_from_signature_edge_cases()
    test_complex_signatures()

    # Note: test_input_validation requires pytest and will be skipped
    # in basic test run to avoid dependency issues
    print("\n✅ All basic tests passed!")
    print("Note: Run test_input_validation separately with pytest")

if __name__ == "__main__":
    run_all_tests()