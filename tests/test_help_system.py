"""Test help system functionality."""
import unittest
from unittest.mock import patch, MagicMock
import sys
import os

# Add the parent directory to the path so we can import CelebiChrono
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from CelebiChrono.main import _get_command_docstring


class TestHelpSystem(unittest.TestCase):
    """Test help system functionality."""

    def test_get_command_docstring_skips_first_line(self):
        """Test that _get_command_docstring returns docstring without first line."""
        # Create a simple mock function with a docstring
        class MockFunction:
            """First line summary.

            This is the detailed description.
            It has multiple lines.

            More details here."""
            pass

        # Create a mock shell module with our mock function as an attribute
        mock_shell_module = MagicMock()
        mock_shell_module.mock_func = MockFunction

        # Mock the shell module import inside _get_command_docstring
        with patch('CelebiChrono.interface.shell', mock_shell_module):
            # Call the function
            result = _get_command_docstring('mock_func')

            # Verify the result doesn't include the first line
            # Note: Implementation preserves original formatting (does not dedent)
            expected = """This is the detailed description.
            It has multiple lines.

            More details here."""

            self.assertEqual(result, expected)
            self.assertNotIn('First line summary.', result)

    def test_get_command_docstring_empty_docstring(self):
        """Test _get_command_docstring with empty docstring."""
        # Create a mock function with no docstring
        class MockFunction:
            pass

        # Create a mock shell module with our mock function as an attribute
        mock_shell_module = MagicMock()
        mock_shell_module.mock_func = MockFunction

        # Mock the shell module import inside _get_command_docstring
        with patch('CelebiChrono.interface.shell', mock_shell_module):
            result = _get_command_docstring('mock_func')
            self.assertEqual(result, "")

    def test_get_command_docstring_single_line(self):
        """Test _get_command_docstring with single line docstring."""
        # Create a mock function with single line docstring
        class MockFunction:
            """Single line summary."""
            pass

        # Create a mock shell module with our mock function as an attribute
        mock_shell_module = MagicMock()
        mock_shell_module.mock_func = MockFunction

        # Mock the shell module import inside _get_command_docstring
        with patch('CelebiChrono.interface.shell', mock_shell_module):
            result = _get_command_docstring('mock_func')
            # Single line should return empty string after skipping first line
            self.assertEqual(result, "")

    def test_get_command_docstring_function_not_found(self):
        """Test _get_command_docstring when function doesn't exist."""
        # Create a mock shell module without the function
        mock_shell_module = MagicMock()
        # When getattr is called for 'non_existent_func', it will return None
        mock_shell_module.non_existent_func = None

        # Mock the shell module import inside _get_command_docstring
        with patch('CelebiChrono.interface.shell', mock_shell_module):
            result = _get_command_docstring('non_existent_func')
            self.assertEqual(result, "")

    def test_all_commands_use_full_doc(self):
        """Test that all command registrations use help=full_doc."""
        import os
        import re

        # Read the main.py file
        main_py_path = os.path.join(os.path.dirname(os.path.dirname(os.path.abspath(__file__))),
                                   'CelebiChrono', 'main.py')

        with open(main_py_path, 'r') as f:
            content = f.read()

        # Find the else clause for variable arguments - look for the specific pattern
        # We need to be more precise to avoid matching too much
        else_clause_pattern = r'else:\s*\n\s+# Fallback: use variable arguments\s*\n(?:.*?\n)*?\s*command_func = cli_sh\.command\(name=cname, help=desc\)\(command_func\)'
        match = re.search(else_clause_pattern, content, re.MULTILINE | re.DOTALL)

        # The test should fail if we find the else clause using help=desc
        self.assertIsNone(match, "Found else clause using help=desc instead of help=full_doc")

        # Check that the correct pattern exists somewhere in the file
        correct_pattern = r'command_func = cli_sh\.command\(name=cname, short_help=desc, help=full_doc\)\(command_func\)'
        self.assertIsNotNone(re.search(correct_pattern, content),
                           "Missing correct command registration pattern with help=full_doc")


if __name__ == '__main__':
    unittest.main()