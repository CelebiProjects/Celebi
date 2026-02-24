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

    def test_vimpression_get_descriptor_from_yaml(self):
        """Test get_descriptor() reads descriptor from impression celebi.yaml."""
        impression = VImpression("test-uuid")

        with patch('CelebiChrono.kernel.vimpression.csys.exists',
                   return_value=True), \
             patch('CelebiChrono.kernel.vimpression.metadata.YamlFile') as mock_yaml:
            mock_yaml_instance = MagicMock()
            mock_yaml.return_value = mock_yaml_instance
            mock_yaml_instance.read_variable.return_value = "Impression Descriptor"

            result = impression.get_descriptor()
            self.assertEqual(result, "Impression Descriptor")
            mock_yaml_instance.read_variable.assert_called_once_with(
                "descriptor", ""
            )

    def test_vimpression_get_descriptor_fallback(self):
        """Test get_descriptor() falls back to current_path basename."""
        impression = VImpression("test-uuid")

        with patch('CelebiChrono.kernel.vimpression.csys.exists',
                   return_value=False), \
             patch.object(impression.config_file, 'read_variable') as mock_read:
            mock_read.return_value = "tasks/taskAna1"

            result = impression.get_descriptor()
            self.assertEqual(result, "taskAna1")
            mock_read.assert_called_once_with("current_path", "")


if __name__ == '__main__':
    unittest.main()
