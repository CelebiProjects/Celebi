def format_output(result):
    """Format shell function output for CLI display."""
    if result is not None:
        if hasattr(result, 'colored'):
            return result.colored()
        else:
            return str(result)
    return ""