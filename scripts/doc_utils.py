"""
Utilities for generating and validating Google-style docstrings.
"""

def generate_google_docstring(func_name, params, returns, description, examples, notes):
    """Generate a Google-style docstring template."""
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

def validate_google_docstring(docstring):
    """Validate a docstring against Google style requirements."""
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

def analyze_docstring(docstring):
    """
    Analyze an existing docstring and suggest improvements.

    Args:
        docstring (str): The docstring to analyze

    Returns:
        dict: Analysis results with suggestions
    """
    if not docstring:
        return {
            'has_docstring': False,
            'sections_present': [],
            'sections_missing': ['Args', 'Returns', 'Examples', 'Note'],
            'suggestions': ['Add complete Google-style docstring with all required sections']
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
        analysis['suggestions'].append('Add parameter documentation with types and descriptions')

    if 'Returns:' not in docstring and 'Yields:' not in docstring:
        analysis['suggestions'].append('Add return value documentation')

    if 'Examples:' not in docstring:
        analysis['suggestions'].append('Add usage examples')

    if 'Note:' not in docstring and 'Notes:' not in docstring:
        analysis['suggestions'].append('Add notes about edge cases or important considerations')

    return analysis

def generate_docstring_from_signature(func_name, signature, description=""):
    """
    Generate a docstring template from function signature.

    Args:
        func_name (str): Name of the function
        signature (str): Function signature string
        description (str): Optional description of the function

    Returns:
        str: Generated docstring template
    """
    # Parse signature to extract parameters
    # This is a simplified parser - in practice you might use inspect module
    import re

    # Remove function name and parentheses
    params_str = signature.replace(func_name, '').strip('() ')

    # Simple parameter parsing
    params = []
    if params_str:
        param_pattern = r'(\w+)(?:\s*:\s*(\w+))?(?:\s*=\s*[^,]+)?'
        for match in re.finditer(param_pattern, params_str):
            param_name = match.group(1)
            param_type = match.group(2) or 'Any'
            params.append((param_name, param_type, f'Description of {param_name}'))

    # Generate docstring
    docstring = f'"""{description or f"Function {func_name}"}\n\n'

    if params:
        docstring += 'Args:\n'
        for param_name, param_type, param_desc in params:
            docstring += f'    {param_name} ({param_type}): {param_desc}\n'
        docstring += '\n'

    docstring += 'Returns:\n    Return value description\n\n'
    docstring += 'Examples:\n    >>> result = {func_name}()\n    >>> print(result)\n\n'
    docstring += 'Note:\n    Important notes about this function\n'
    docstring += '"""'

    return docstring

def test_generate_google_docstring():
    """Test docstring generation."""
    params = [('line', 'str', 'Path or index to navigate to')]
    returns = 'None'
    description = 'Change directory within current project.'
    examples = ['cd subdir  # Change to subdirectory', 'cd 2      # Change to index 2']
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

def test_analyze_docstring():
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

def test_generate_from_signature():
    """Test docstring generation from signature."""
    signature = "process_data(input_file: str, output_dir: str = '.', verbose: bool = False)"
    docstring = generate_docstring_from_signature("process_data", signature, "Process data file")

    assert 'Args:' in docstring
    assert 'input_file (str):' in docstring
    assert 'output_dir (str):' in docstring
    assert 'verbose (bool):' in docstring
    assert 'Returns:' in docstring
    assert 'Examples:' in docstring
    assert 'Note:' in docstring

    print("✓ Signature-based generation test passed")

def run_all_tests():
    """Run all test functions."""
    test_generate_google_docstring()
    test_analyze_docstring()
    test_generate_from_signature()
    print("\n✅ All tests passed!")

if __name__ == "__main__":
    run_all_tests()