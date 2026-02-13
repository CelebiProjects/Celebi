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
            # After skipping first line and dedenting, all lines should be unindented
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


if __name__ == '__main__':
    unittest.main()