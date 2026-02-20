"""Module for utils."""
def format_output(result):
    """Format shell function output for CLI display."""
    if result is not None:
        if hasattr(result, 'colored'):
            return result.colored()
        return str(result)
    return ""
