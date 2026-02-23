import unittest
from unittest.mock import patch, MagicMock
from CelebiChrono.kernel.vimpression import VImpression


class TestVImpression(unittest.TestCase):
    """Test cases for VImpression class."""

    def test_vimpression_object_type(self):
        """Test object_type() method returns correct value from config."""
        # Create mock impression with object_type in config
        impression = VImpression("test-uuid")

        # Mock config_file.read_variable to return "task"
        with patch.object(impression.config_file, 'read_variable') as mock_read:
            mock_read.return_value = "task"

            # Assert impression.object_type() == "task"
            result = impression.object_type()
            mock_read.assert_called_once_with("object_type", "")
            self.assertEqual(result, "task")

    def test_vimpression_object_type_empty(self):
        """Test object_type() method returns empty string when not set."""
        # Create mock impression without object_type in config
        impression = VImpression("test-uuid")

        # Mock config_file.read_variable to return empty string (default)
        with patch.object(impression.config_file, 'read_variable') as mock_read:
            mock_read.return_value = ""

            # Assert impression.object_type() == ""
            result = impression.object_type()
            mock_read.assert_called_once_with("object_type", "")
            self.assertEqual(result, "")


if __name__ == '__main__':
    unittest.main()