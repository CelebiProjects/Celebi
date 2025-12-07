"""
Unit tests for kernel/valgorithm.py module
Tests for VAlgorithm class and create_algorithm function
"""
import os
import unittest
from unittest.mock import patch, MagicMock, mock_open
from colored import Fore, Style
import CelebiChrono.kernel.valgorithm as valg
from CelebiChrono.kernel.chern_cache import ChernCache
from CelebiChrono.kernel.chern_communicator import ChernCommunicator
from CelebiChrono.utils.message import Message
import prepare

CHERN_CACHE = ChernCache.instance()


class TestVAlgorithm(unittest.TestCase):
    """Test class for VAlgorithm"""

    def setUp(self):
        """Set up test environment"""
        self.cwd = os.getcwd()

    def tearDown(self):
        """Clean up test environment"""
        os.chdir(self.cwd)

    def test_helpme(self):
        """Test helpme method"""
        print(Fore.BLUE + "Testing VAlgorithm helpme..." + Style.RESET)

        prepare.create_chern_project("demo_complex")
        os.chdir("demo_complex")

        try:
            # Create algorithm object
            algorithm = valg.VAlgorithm(
                os.getcwd() + "/algorithms/algAna1"
            )

            # Test helpme with empty command
            help_msg = algorithm.helpme("")
            self.assertIsInstance(help_msg, Message)
            self.assertIsNotNone(str(help_msg))

            # Test helpme with existing command
            help_msg = algorithm.helpme("cd")
            self.assertIsInstance(help_msg, Message)
            self.assertIsNotNone(str(help_msg))

            # Test helpme with non-existing command
            help_msg = algorithm.helpme("nonexistent")
            self.assertIsInstance(help_msg, Message)
            help_str = str(help_msg)
            self.assertIn("No such command", help_str)

        finally:
            os.chdir("..")
            prepare.remove_chern_project("demo_complex")
            CHERN_CACHE.__init__()

    def test_run_status(self):
        """Test run_status method"""
        print(Fore.BLUE + "Testing VAlgorithm run_status..." + Style.RESET)

        prepare.create_chern_project("demo_complex")
        os.chdir("demo_complex")

        try:
            algorithm = valg.VAlgorithm(
                os.getcwd() + "/algorithms/algAna1"
            )

            # Mock ChernCommunicator
            with patch.object(ChernCommunicator, 'instance') as mock_instance:
                mock_communicator = MagicMock()
                mock_instance.return_value = mock_communicator
                mock_communicator.status.return_value = "running"

                status = algorithm.run_status()
                self.assertEqual(status, "running")
                mock_communicator.status.assert_called_once()

        finally:
            os.chdir("..")
            prepare.remove_chern_project("demo_complex")
            CHERN_CACHE.__init__()

    def test_is_submitted(self):
        """Test is_submitted method"""
        print(Fore.BLUE + "Testing VAlgorithm is_submitted..." + Style.RESET)

        prepare.create_chern_project("demo_complex")
        os.chdir("demo_complex")

        try:
            algorithm = valg.VAlgorithm(os.getcwd() + "/algorithms/algAna1")

            # Mock is_impressed_fast to return False
            with patch.object(algorithm, 'is_impressed_fast',
                              return_value=False):
                result = algorithm.is_submitted()
                self.assertFalse(result)

            # Mock is_impressed_fast to return True
            with patch.object(algorithm, 'is_impressed_fast',
                              return_value=True):
                result = algorithm.is_submitted()
                # Current implementation always returns False
                self.assertFalse(result)

        finally:
            os.chdir("..")
            prepare.remove_chern_project("demo_complex")
            CHERN_CACHE.__init__()

    def test_ls(self):
        """Test ls method"""
        print(Fore.BLUE + "Testing VAlgorithm ls..." + Style.RESET)

        prepare.create_chern_project("demo_complex")
        os.chdir("demo_complex")

        try:
            algorithm = valg.VAlgorithm(os.getcwd() + "/algorithms/algAna1")

            # Mock the path property and other methods
            test_path = os.getcwd() + "/algorithms/algAna1"
            with patch.object(algorithm, 'path', test_path), \
                 patch.object(algorithm, 'environment',
                              return_value='test_env'), \
                 patch.object(algorithm, 'commands',
                              return_value=['echo test']), \
                 patch.object(algorithm, 'build_commands',
                              return_value=['make build']), \
                 patch.object(algorithm, 'status',
                              return_value='ready'), \
                 patch('os.listdir',
                       return_value=['script.py', 'config.txt',
                                     '.chern', 'chern.yaml']), \
                 patch('shutil.get_terminal_size') as mock_terminal, \
                 patch('CelebiChrono.kernel.vobject.VObject.ls') as mock_super_ls:

                mock_terminal.return_value.columns = 80
                mock_super_ls.return_value = Message()

                from CelebiChrono.kernel.vobj_file import LsParameters
                ls_params = LsParameters()
                ls_params.status = True

                result = algorithm.ls(ls_params)
                self.assertIsInstance(result, Message)

                result_str = str(result)
                self.assertIn("test_env", result_str)
                self.assertIn("echo test", result_str)
                self.assertIn("make build", result_str)
                self.assertIn("ready", result_str)

        finally:
            os.chdir("..")
            prepare.remove_chern_project("demo_complex")
            CHERN_CACHE.__init__()

    def test_print_files(self):
        """Test print_files method"""
        print(Fore.BLUE + "Testing VAlgorithm print_files..." + Style.RESET)

        prepare.create_chern_project("demo_complex")
        os.chdir("demo_complex")

        try:
            algorithm = valg.VAlgorithm(os.getcwd() + "/algorithms/algAna1")
            test_path = os.getcwd() + "/algorithms/algAna1"

            # Test with files
            with patch('os.listdir',
                       return_value=['script.py', 'config.txt',
                                     '.hidden', 'chern.yaml']), \
                 patch('shutil.get_terminal_size') as mock_terminal:

                mock_terminal.return_value.columns = 80

                result = algorithm.print_files(
                    test_path, excluded=('chern.yaml',)
                )
                self.assertIsInstance(result, Message)

                result_str = str(result)
                self.assertIn("Files:", result_str)
                self.assertIn("script.py", result_str)
                self.assertIn("config.txt", result_str)
                self.assertNotIn(".hidden", result_str)
                self.assertNotIn("chern.yaml", result_str)

            # Test with no files
            with patch('os.listdir', return_value=[]):
                result = algorithm.print_files(test_path)
                result_str = str(result)
                self.assertIn("No files found", result_str)

        finally:
            os.chdir("..")
            prepare.remove_chern_project("demo_complex")
            CHERN_CACHE.__init__()

    def test_commands(self):
        """Test commands method"""
        print(Fore.BLUE + "Testing VAlgorithm commands..." + Style.RESET)

        prepare.create_chern_project("demo_complex")
        os.chdir("demo_complex")

        try:
            algorithm = valg.VAlgorithm(os.getcwd() + "/algorithms/algAna1")
            test_path = os.getcwd() + "/algorithms/algAna1"

            # Mock YamlFile
            with patch('CelebiChrono.utils.metadata.YamlFile') as mock_yaml, \
                 patch.object(algorithm, 'path', test_path):
                mock_yaml_instance = MagicMock()
                mock_yaml.return_value = mock_yaml_instance
                mock_yaml_instance.read_variable.return_value = [
                    'python script.py', 'echo done'
                ]

                commands = algorithm.commands()
                self.assertEqual(commands, ['python script.py', 'echo done'])
                mock_yaml_instance.read_variable.assert_called_with(
                    "commands", []
                )

        finally:
            os.chdir("..")
            prepare.remove_chern_project("demo_complex")
            CHERN_CACHE.__init__()

    def test_build_commands(self):
        """Test build_commands method"""
        print(Fore.BLUE + "Testing VAlgorithm build_commands..." + Style.RESET)

        prepare.create_chern_project("demo_complex")
        os.chdir("demo_complex")

        try:
            algorithm = valg.VAlgorithm(os.getcwd() + "/algorithms/algAna1")
            test_path = os.getcwd() + "/algorithms/algAna1"

            # Mock YamlFile
            with patch('CelebiChrono.utils.metadata.YamlFile') as mock_yaml, \
                 patch.object(algorithm, 'path', test_path):
                mock_yaml_instance = MagicMock()
                mock_yaml.return_value = mock_yaml_instance
                mock_yaml_instance.read_variable.return_value = [
                    'make', 'cmake ..'
                ]

                build_commands = algorithm.build_commands()
                self.assertEqual(build_commands, ['make', 'cmake ..'])
                mock_yaml_instance.read_variable.assert_called_with(
                    "build", []
                )

        finally:
            os.chdir("..")
            prepare.remove_chern_project("demo_complex")
            CHERN_CACHE.__init__()

    def test_environment(self):
        """Test environment method"""
        print(Fore.BLUE + "Testing VAlgorithm environment..." + Style.RESET)

        prepare.create_chern_project("demo_complex")
        os.chdir("demo_complex")

        try:
            algorithm = valg.VAlgorithm(os.getcwd() + "/algorithms/algAna1")
            test_path = os.getcwd() + "/algorithms/algAna1"

            # Mock YamlFile
            with patch('CelebiChrono.utils.metadata.YamlFile') as mock_yaml, \
                 patch.object(algorithm, 'path', test_path):
                mock_yaml_instance = MagicMock()
                mock_yaml.return_value = mock_yaml_instance
                mock_yaml_instance.read_variable.return_value = "ubuntu:20.04"

                environment = algorithm.environment()
                self.assertEqual(environment, "ubuntu:20.04")
                mock_yaml_instance.read_variable.assert_called_with(
                    "environment", ""
                )

        finally:
            os.chdir("..")
            prepare.remove_chern_project("demo_complex")
            CHERN_CACHE.__init__()

    def test_printed_status(self):
        """Test printed_status method"""
        print(Fore.BLUE + "Testing VAlgorithm printed_status..." + Style.RESET)

        prepare.create_chern_project("demo_complex")
        os.chdir("demo_complex")

        try:
            algorithm = valg.VAlgorithm(os.getcwd() + "/algorithms/algAna1")

            # Test when dite is connected and workflow is undefined
            with patch.object(ChernCommunicator, 'instance') as mock_instance, \
                 patch('CelebiChrono.kernel.vobject.VObject.printed_status') as mock_super:

                mock_communicator = MagicMock()
                mock_instance.return_value = mock_communicator
                mock_communicator.dite_status.return_value = "connected"  # Set to connected
                mock_communicator.workflow.return_value = "UNDEFINED"

                mock_message = MagicMock()
                mock_super.return_value = mock_message

                result = algorithm.printed_status()

                # Verify dite_status was checked
                mock_communicator.dite_status.assert_called_once()
                # Verify workflow was called since dite is connected
                mock_communicator.workflow.assert_called_once()
                # Verify the "Workflow not defined" message was added
                mock_message.add.assert_called_with("Workflow not defined\n")

            # Test when dite is not connected
            with patch.object(ChernCommunicator, 'instance') as mock_instance, \
                 patch('CelebiChrono.kernel.vobject.VObject.printed_status') as mock_super:

                mock_communicator = MagicMock()
                mock_instance.return_value = mock_communicator
                mock_communicator.dite_status.return_value = "disconnected"

                mock_message = MagicMock()
                mock_super.return_value = mock_message

                result = algorithm.printed_status()

                # Should return early without calling workflow
                mock_communicator.dite_status.assert_called_once()
                mock_communicator.workflow.assert_not_called()
                self.assertEqual(result, mock_message)

            # Test when dite is connected and workflow is defined
            with patch.object(ChernCommunicator, 'instance') as mock_instance, \
                 patch('CelebiChrono.kernel.vobject.VObject.printed_status') as mock_super:

                mock_communicator = MagicMock()
                mock_instance.return_value = mock_communicator
                mock_communicator.dite_status.return_value = "connected"
                mock_communicator.workflow.return_value = "defined_workflow"

                mock_message = MagicMock()
                mock_super.return_value = mock_message

                result = algorithm.printed_status()

                # Should call workflow and not add the undefined message
                mock_communicator.dite_status.assert_called_once()
                mock_communicator.workflow.assert_called_once()
                # Should not add "Workflow not defined" message since workflow is defined
                mock_message.add.assert_not_called()

        finally:
            os.chdir("..")
            prepare.remove_chern_project("demo_complex")
            CHERN_CACHE.__init__()

    @patch('subprocess.call')
    @patch('builtins.input')
    def test_create_algorithm(self, mock_input, mock_subprocess):
        """Test create_algorithm function"""
        print(Fore.BLUE + "Testing create_algorithm..." + Style.RESET)

        test_path = "test_algorithm"
        mock_input.return_value = "ubuntu"

        # Test creating algorithm without template
        with patch('os.mkdir') as mock_mkdir, \
             patch('CelebiChrono.utils.metadata.ConfigFile') as mock_config, \
             patch('builtins.open', mock_open()) as mock_file:

            valg.create_algorithm(test_path)

            # Verify directories were created
            mock_mkdir.assert_any_call(test_path)
            mock_mkdir.assert_any_call(f"{test_path}/.chern")

            # Verify config file was created
            mock_config.assert_called_once()
            mock_config.return_value.write_variable.assert_called_with(
                "object_type", "algorithm"
            )

            # Verify README file was created
            mock_file.assert_called_with(
                f"{test_path}/.chern/README.md", "w", encoding="utf-8"
            )

    @patch('subprocess.call')
    @patch('builtins.input')
    def test_create_algorithm_with_template(self, mock_input,
                                            mock_subprocess):
        """Test create_algorithm function with template"""
        print(Fore.BLUE + "Testing create_algorithm with template..." +
              Style.RESET)

        test_path = "test_algorithm_template"
        mock_input.return_value = "docker_template"

        # Test creating algorithm with template
        with patch('os.mkdir') as mock_mkdir, \
             patch('CelebiChrono.utils.metadata.ConfigFile'), \
             patch('builtins.open', mock_open()), \
             patch('builtins.print') as mock_print:

            valg.create_algorithm(test_path, use_template=True)

            # Verify directories were created
            mock_mkdir.assert_any_call(test_path)
            mock_mkdir.assert_any_call(f"{test_path}/.chern")

            # Verify template-related prints were called
            mock_print.assert_any_call("Creating template, but ...")
            mock_print.assert_any_call("Not implemented yet.")
            mock_print.assert_any_call("Template name: docker_template")

    def test_resubmit(self):
        """Test resubmit method (currently incomplete)"""
        print(Fore.BLUE + "Testing VAlgorithm resubmit..." + Style.RESET)

        prepare.create_chern_project("demo_complex")
        os.chdir("demo_complex")

        try:
            algorithm = valg.VAlgorithm(os.getcwd() + "/algorithms/algAna1")

            # Test that resubmit doesn't crash (it's not implemented yet)
            try:
                algorithm.resubmit()
            except Exception as e:
                self.fail(f"resubmit raised {e} unexpectedly!")

        finally:
            os.chdir("..")
            prepare.remove_chern_project("demo_complex")
            CHERN_CACHE.__init__()


if __name__ == '__main__':
    unittest.main(verbosity=2)
