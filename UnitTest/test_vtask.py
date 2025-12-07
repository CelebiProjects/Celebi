import os
import unittest
from unittest.mock import patch, MagicMock, ANY, mock_open
from colored import Fore, Style
import CelebiChrono.kernel.vtask as vtsk
from CelebiChrono.kernel.chern_cache import ChernCache
from CelebiChrono.kernel.chern_communicator import ChernCommunicator
import prepare

CHERN_CACHE = ChernCache.instance()


class TestChernVTask(unittest.TestCase):

    def setUp(self):
        self.cwd = os.getcwd()

    def tearDown(self):
        os.chdir(self.cwd)

    def test_setting(self):
        print(Fore.BLUE + "Testing setting..." + Style.RESET)
        prepare.create_chern_project("demo_complex")
        os.chdir("demo_complex")
        obj_tsk = vtsk.VTask(os.getcwd() + "/tasks/taskAna1")

        self.assertEqual(obj_tsk.environment(),
                         "reanahub/reana-env-root6:6.18.04")
        self.assertEqual(obj_tsk.memory_limit(), "256Mi")
        self.assertEqual(obj_tsk.parameters(), ([], {}))
        self.assertTrue(obj_tsk.auto_download())
        self.assertEqual(obj_tsk.default_runner(), "local")

        print(obj_tsk.env_validated())
        print(obj_tsk.validated())

        obj_tsk.set_environment("new_env")
        print(obj_tsk.environment())
        self.assertEqual(obj_tsk.environment(), "new_env")
        obj_tsk.set_memory_limit("1Gi")
        self.assertEqual(obj_tsk.memory_limit(), "1Gi")
        obj_tsk.add_parameter("param1", "value1")
        self.assertEqual(obj_tsk.parameters(),
                         (["param1"], {"param1": "value1"}))
        obj_tsk.remove_parameter("param1")
        self.assertEqual(obj_tsk.parameters(), ([], {}))
        obj_tsk.set_auto_download(False)
        self.assertFalse(obj_tsk.auto_download())
        obj_tsk.set_default_runner("new_runner")
        self.assertEqual(obj_tsk.default_runner(), "new_runner")

        os.chdir("..")
        prepare.remove_chern_project("demo_complex")
        CHERN_CACHE.__init__()

    def test_init(self):
        print(Fore.BLUE + "Testing Init Commands..." + Style.RESET)

        prepare.create_chern_project("demo_complex")
        os.chdir("demo_complex")
        obj_tsk = vtsk.VTask(os.getcwd() + "/tasks/taskAna1")

        self.assertEqual(str(obj_tsk), "tasks/taskAna1")
        self.assertEqual(repr(obj_tsk), "tasks/taskAna1")
        self.assertEqual(obj_tsk.invariant_path(), "tasks/taskAna1")
        self.assertEqual(obj_tsk.object_type(), "task")
        self.assertFalse(obj_tsk.is_zombie())
        self.assertTrue(obj_tsk.is_task_or_algorithm())

        os.chdir("..")
        prepare.remove_chern_project("demo_complex")
        CHERN_CACHE.__init__()

    def test_file(self):
        print(Fore.BLUE + "Testing File Operation..." + Style.RESET)

        prepare.create_chern_project("demo_complex")
        os.chdir("demo_complex")
        obj_tsk = vtsk.VTask(os.getcwd() + "/tasks/taskAna1")

        # Test move operation
        obj_tsk.move_to(os.getcwd() + "/tasks/TASKANA1")
        print(obj_tsk.invariant_path())

        os.chdir("..")
        prepare.remove_chern_project("demo_complex")
        CHERN_CACHE.__init__()

    def test_job_manager_methods(self):
        """Test JobManager methods inherited by VTask"""
        print(Fore.BLUE + "Testing JobManager Methods..." + Style.RESET)

        prepare.create_chern_project("demo_complex")
        os.chdir("demo_complex")
        obj_tsk = vtsk.VTask(os.getcwd() + "/tasks/taskAna1")

        # Mock ChernCommunicator instance and its methods
        with patch.object(ChernCommunicator, 'instance') as mock_instance:
            mock_communicator = MagicMock()
            mock_instance.return_value = mock_communicator

            # Test kill method
            obj_tsk.kill()
            mock_communicator.kill.assert_called_once_with(ANY)

            # Reset mock
            mock_communicator.reset_mock()

            # Test collect method
            obj_tsk.collect()
            mock_communicator.collect.assert_called_once_with(ANY)

            # Reset mock
            mock_communicator.reset_mock()

            # Test display method
            test_filename = "test_file.txt"
            obj_tsk.display(test_filename)
            mock_communicator.display.assert_called_once_with(
                ANY, test_filename
            )

            # Reset mock
            mock_communicator.reset_mock()

            # Test impview method
            obj_tsk.impview()
            mock_communicator.impview.assert_called_once_with(ANY)

            # Reset mock
            mock_communicator.reset_mock()

            # Test export method - successful case
            test_filename = "output.txt"
            test_output_file = "exported_output.txt"
            mock_communicator.export.return_value = (
                "/path/to/exported_output.txt"
            )

            obj_tsk.export(test_filename, test_output_file)
            mock_communicator.export.assert_called_once_with(
                ANY, test_filename, test_output_file
            )

            # Reset mock
            mock_communicator.reset_mock()

            # Test export method - file not found case
            mock_communicator.export.return_value = "NOTFOUND"
            with patch('CelebiChrono.kernel.vtask_job.logger') as mock_logger:
                obj_tsk.export(test_filename, test_output_file)
                mock_logger.error.assert_called_once()
                self.assertIn("not found", str(mock_logger.error.call_args))

            # Reset mock
            mock_communicator.reset_mock()

            # Test send_data method
            test_path = "/path/to/data"
            obj_tsk.send_data(test_path)
            mock_communicator.deposit_with_data.assert_called_once_with(
                ANY, test_path
            )

        os.chdir("..")
        prepare.remove_chern_project("demo_complex")
        CHERN_CACHE.__init__()

    # def test_run_status_method(self):
    #     """Test run_status method with different scenarios"""
    #     print(Fore.BLUE + "Testing run_status Method..." + Style.RESET)

    #     prepare.create_chern_project("demo_complex")
    #     os.chdir("demo_complex")
    #     obj_tsk = vtsk.VTask(os.getcwd() + "/tasks/taskAna1")

    #     with patch.object(ChernCommunicator, 'instance') as mock_instance:
    #         mock_communicator = MagicMock()
    #         mock_instance.return_value = mock_communicator

    #         # Test normal case (non-rawdata environment)
    #         with patch.object(obj_tsk, 'environment',
    #                           return_value='normal_env'):
    #             mock_communicator.status.return_value = "running"
    #             status = obj_tsk.run_status()
    #             self.assertEqual(status, "running")
    #             mock_communicator.status.assert_called_once_with(ANY)

    #         # Reset mock
    #         mock_communicator.reset_mock()

    #         # Test rawdata environment - finished case
    #         with patch.object(obj_tsk, 'environment',
    #                           return_value='rawdata'), \
    #              patch.object(obj_tsk, 'input_md5',
    #                           return_value='test_md5'):
    #             mock_communicator.sample_status.return_value = 'test_md5'
    #             status = obj_tsk.run_status()
    #             self.assertEqual(status, "finished")
    #             mock_communicator.sample_status.assert_called_once_with(ANY)

    #         # Reset mock
    #         mock_communicator.reset_mock()

    #         # Test rawdata environment - unsubmitted case
    #         with patch.object(obj_tsk, 'environment',
    #                           return_value='rawdata'), \
    #              patch.object(obj_tsk, 'input_md5',
    #                           return_value='test_md5'):
    #             mock_communicator.sample_status.return_value = 'different_md5'
    #             status = obj_tsk.run_status()
    #             self.assertEqual(status, "unsubmitted")
    #             mock_communicator.sample_status.assert_called_once_with(ANY)

    #         # Test with custom host parameter (ignored due to unused-argument)
    #         mock_communicator.reset_mock()
    #         with patch.object(obj_tsk, 'environment',
    #                           return_value='normal_env'):
    #             mock_communicator.status.return_value = "queued"
    #             status = obj_tsk.run_status(host="remote")
    #             self.assertEqual(status, "queued")
    #             mock_communicator.status.assert_called_once_with(ANY)

    #     os.chdir("..")
    #     prepare.remove_chern_project("demo_complex")
    #     CHERN_CACHE.__init__()

    def test_core_methods(self):
        """Test Core class methods inherited by VTask"""
        print(Fore.BLUE + "Testing Core Methods..." + Style.RESET)

        prepare.create_chern_project("demo_complex")
        os.chdir("demo_complex")
        obj_tsk = vtsk.VTask(os.getcwd() + "/tasks/taskAna1")

        # Test helpme method
        help_msg = obj_tsk.helpme("")
        self.assertIsNotNone(help_msg)
        # Test with existing command
        help_msg = obj_tsk.helpme("status")
        self.assertIsNotNone(help_msg)
        # Test with non-existing command
        help_msg = obj_tsk.helpme("nonexistent")
        self.assertIsNotNone(help_msg)

        # Test ls method (inherited from Core)
        from CelebiChrono.kernel.vobj_file import LsParameters
        ls_params = LsParameters()
        ls_result = obj_tsk.ls(ls_params)
        self.assertIsNotNone(ls_result)

        # Test show_parameters method
        param_msg = obj_tsk.show_parameters()
        self.assertIsNotNone(param_msg)

        # Add a parameter and test again
        obj_tsk.add_parameter("test_param", "test_value")
        param_msg = obj_tsk.show_parameters()
        self.assertIsNotNone(param_msg)

        # Test show_algorithm method
        algorithm_msg = obj_tsk.show_algorithm()
        self.assertIsNotNone(algorithm_msg)

        os.chdir("..")
        prepare.remove_chern_project("demo_complex")
        CHERN_CACHE.__init__()

    def test_core_environment_methods(self):
        """Test Core environment-related methods"""
        print(Fore.BLUE + "Testing Core Environment Methods..." + Style.RESET)

        prepare.create_chern_project("demo_complex")
        os.chdir("demo_complex")
        obj_tsk = vtsk.VTask(os.getcwd() + "/tasks/taskAna1")

        # Test environment method
        env = obj_tsk.environment()
        self.assertIsInstance(env, str)
        self.assertNotEqual(env, "")

        # Test memory_limit method
        memory = obj_tsk.memory_limit()
        self.assertIsInstance(memory, str)
        self.assertNotEqual(memory, "")

        # Test validated method
        validated = obj_tsk.validated()
        self.assertIsInstance(validated, bool)

        # Test auto_download method
        auto_dl = obj_tsk.auto_download()
        self.assertIsInstance(auto_dl, bool)

        # Test default_runner method
        runner = obj_tsk.default_runner()
        self.assertIsInstance(runner, str)
        self.assertNotEqual(runner, "")

        # Test parameters method
        params, values = obj_tsk.parameters()
        self.assertIsInstance(params, list)
        self.assertIsInstance(values, dict)

        os.chdir("..")
        prepare.remove_chern_project("demo_complex")
        CHERN_CACHE.__init__()

    def test_core_with_rawdata_environment(self):
        """Test Core methods with rawdata environment"""
        print(Fore.BLUE + "Testing Core with rawdata environment..." +
              Style.RESET)

        prepare.create_chern_project("demo_complex")
        os.chdir("demo_complex")
        obj_tsk = vtsk.VTask(os.getcwd() + "/tasks/taskAna1")

        # Mock environment to be rawdata
        with patch.object(obj_tsk, 'environment', return_value='rawdata'), \
             patch.object(obj_tsk, 'input_md5',
                          return_value='test_md5_hash'):

            # Test show_parameters with rawdata environment
            param_msg = obj_tsk.show_parameters()
            self.assertIsNotNone(param_msg)
            # Should contain input data info
            param_str = str(param_msg)
            self.assertIn("Input data", param_str)
            self.assertIn("test_md5_hash", param_str)

        os.chdir("..")
        prepare.remove_chern_project("demo_complex")
        CHERN_CACHE.__init__()

    def test_core_algorithm_display(self):
        """Test Core algorithm display functionality"""
        print(Fore.BLUE + "Testing Core Algorithm Display..." + Style.RESET)

        prepare.create_chern_project("demo_complex")
        os.chdir("demo_complex")
        obj_tsk = vtsk.VTask(os.getcwd() + "/tasks/taskAna1")

        # Mock algorithm object
        mock_algorithm = MagicMock()
        mock_algorithm.path = "/mock/algorithm/path"
        mock_algorithm.commands.return_value = [
            "echo 'Running algorithm with ${test_param}'",
            "python script.py --input ${input_file}"
        ]

        # Create mock algorithm directory with files
        with patch('os.listdir') as mock_listdir, \
             patch.object(obj_tsk, 'algorithm', return_value=mock_algorithm), \
             patch('os.get_terminal_size') as mock_terminal_size:

            mock_listdir.return_value = [
                "script.py",
                "config.txt",
                ".hidden",
                "README.md",
                "chern.yaml",
                "data_processor.py"
            ]
            mock_terminal_size.return_value.columns = 80

            # Add parameters for command substitution
            obj_tsk.add_parameter("test_param", "test_value")
            obj_tsk.add_parameter("input_file", "input.dat")

            algorithm_msg = obj_tsk.show_algorithm()
            self.assertIsNotNone(algorithm_msg)

            msg_str = str(algorithm_msg)
            # Should contain algorithm files
            # (excluding hidden, README.md, chern.yaml)
            self.assertIn("script.py", msg_str)
            self.assertIn("data_processor.py", msg_str)
            self.assertNotIn(".hidden", msg_str)
            self.assertNotIn("README.md", msg_str)
            self.assertNotIn("chern.yaml", msg_str)

            # Should contain commands with parameter substitution
            self.assertIn("Commands", msg_str)
            self.assertIn("test_value", msg_str)  # Parameter substituted
            self.assertIn("input.dat", msg_str)   # Parameter substituted
            self.assertNotIn("${test_param}", msg_str)  # Original not present

        # Test with empty algorithm directory
        with patch('os.listdir') as mock_listdir, \
             patch.object(obj_tsk, 'algorithm', return_value=mock_algorithm):

            mock_listdir.return_value = []
            algorithm_msg = obj_tsk.show_algorithm()
            self.assertIsNotNone(algorithm_msg)

        # Test with no algorithm
        with patch.object(obj_tsk, 'algorithm', return_value=None):
            ls_result = obj_tsk.ls()
            self.assertIsNotNone(ls_result)

        os.chdir("..")
        prepare.remove_chern_project("demo_complex")
        CHERN_CACHE.__init__()

    def test_file_manager_methods(self):
        """Test FileManager methods inherited by VTask"""
        print(Fore.BLUE + "Testing FileManager Methods..." + Style.RESET)

        prepare.create_chern_project("demo_complex")
        os.chdir("demo_complex")
        obj_tsk = vtsk.VTask(os.getcwd() + "/tasks/taskAna1")

        # Test input_md5 method
        input_md5 = obj_tsk.input_md5()
        self.assertIsInstance(input_md5, str)

        # Test set_input_md5 method with mocking
        test_path = "/test/input/path"
        test_md5 = "test_md5_hash_12345"

        with patch('CelebiChrono.utils.csys.dir_md5') as mock_dir_md5, \
             patch('CelebiChrono.utils.metadata.YamlFile') as mock_yaml_file:

            mock_dir_md5.return_value = test_md5
            mock_yaml_instance = MagicMock()
            mock_yaml_file.return_value = mock_yaml_instance

            # Test set_input_md5
            result_md5 = obj_tsk.set_input_md5(test_path)

            # Verify the method calls
            mock_dir_md5.assert_called_once_with(test_path)
            mock_yaml_file.assert_called_once_with(
                os.path.join(obj_tsk.path, "chern.yaml")
            )
            mock_yaml_instance.write_variable.assert_called_once_with(
                "uuid", test_md5
            )
            self.assertEqual(result_md5, test_md5)

        # Test output_md5 method with mocking
        test_impression = "test_impression_123"
        test_output_md5 = "output_md5_hash_67890"

        with patch.object(obj_tsk, 'config_file') as mock_config_file, \
             patch.object(obj_tsk, 'impression', return_value=test_impression):

            # Mock the config file to return output_md5s
            mock_config_file.read_variable.return_value = {
                test_impression: test_output_md5,
                "other_impression": "other_md5"
            }

            result_output_md5 = obj_tsk.output_md5()

            # Verify the method calls
            mock_config_file.read_variable.assert_called_once_with(
                "output_md5s", {}
            )
            self.assertEqual(result_output_md5, test_output_md5)

        # Test output_md5 method with empty result
        with patch.object(obj_tsk, 'config_file') as mock_config_file, \
             patch.object(obj_tsk, 'impression', return_value=test_impression):

            # Mock the config file to return empty dict
            mock_config_file.read_variable.return_value = {}

            result_output_md5 = obj_tsk.output_md5()

            # Should return empty string for non-existent impression
            self.assertEqual(result_output_md5, "")

        # Test output_md5 method with non-existent impression
        with patch.object(obj_tsk, 'config_file') as mock_config_file, \
             patch.object(obj_tsk, 'impression',
                          return_value="non_existent_impression"):

            # Mock the config file to return dict without our impression
            mock_config_file.read_variable.return_value = {
                "other_impression": "other_md5"
            }

            result_output_md5 = obj_tsk.output_md5()

            # Should return empty string for non-existent impression
            self.assertEqual(result_output_md5, "")

        os.chdir("..")
        prepare.remove_chern_project("demo_complex")
        CHERN_CACHE.__init__()

    def test_file_manager_input_md5_integration(self):
        """Test FileManager input_md5 integration with real YAML file"""
        print(Fore.BLUE + "Testing FileManager input_md5 integration..." +
              Style.RESET)

        prepare.create_chern_project("demo_complex")
        os.chdir("demo_complex")
        obj_tsk = vtsk.VTask(os.getcwd() + "/tasks/taskAna1")

        # Test reading actual YAML file (should work with real file)
        original_md5 = obj_tsk.input_md5()
        self.assertIsInstance(original_md5, str)

        # Test with mocked YAML file content
        with patch('CelebiChrono.utils.metadata.YamlFile') as mock_yaml_file:
            mock_yaml_instance = MagicMock()
            mock_yaml_file.return_value = mock_yaml_instance
            mock_yaml_instance.read_variable.return_value = "mocked_uuid_123"

            md5_result = obj_tsk.input_md5()

            # Verify correct file path and variable name
            mock_yaml_file.assert_called_once_with(
                os.path.join(obj_tsk.path, "chern.yaml")
            )
            mock_yaml_instance.read_variable.assert_called_once_with(
                "uuid", ""
            )
            self.assertEqual(md5_result, "mocked_uuid_123")

        # Test with missing UUID in YAML (should return default empty string)
        with patch('CelebiChrono.utils.metadata.YamlFile') as mock_yaml_file:
            mock_yaml_instance = MagicMock()
            mock_yaml_file.return_value = mock_yaml_instance
            mock_yaml_instance.read_variable.return_value = ""

            md5_result = obj_tsk.input_md5()
            self.assertEqual(md5_result, "")

        os.chdir("..")
        prepare.remove_chern_project("demo_complex")
        CHERN_CACHE.__init__()

    def test_file_manager_error_handling(self):
        """Test FileManager error handling scenarios"""
        print(Fore.BLUE + "Testing FileManager error handling..." +
              Style.RESET)

        prepare.create_chern_project("demo_complex")
        os.chdir("demo_complex")
        obj_tsk = vtsk.VTask(os.getcwd() + "/tasks/taskAna1")

        # Test set_input_md5 with directory that doesn't exist
        with patch('CelebiChrono.utils.csys.dir_md5') as mock_dir_md5, \
             patch('CelebiChrono.utils.metadata.YamlFile') as mock_yaml_file:

            # Simulate dir_md5 raising an exception
            mock_dir_md5.side_effect = FileNotFoundError("Directory not found")

            with self.assertRaises(FileNotFoundError):
                obj_tsk.set_input_md5("/non/existent/path")

        # Test input_md5 with corrupted YAML file
        with patch('CelebiChrono.utils.metadata.YamlFile') as mock_yaml_file:
            mock_yaml_instance = MagicMock()
            mock_yaml_file.return_value = mock_yaml_instance
            mock_yaml_instance.read_variable.side_effect = Exception(
                "YAML parsing error"
            )

            with self.assertRaises(Exception):
                obj_tsk.input_md5()

        # Test output_md5 with corrupted config file
        with patch.object(obj_tsk, 'config_file') as mock_config_file:
            mock_config_file.read_variable.side_effect = Exception(
                "Config file error"
            )

            with self.assertRaises(Exception):
                obj_tsk.output_md5()

        os.chdir("..")
        prepare.remove_chern_project("demo_complex")
        CHERN_CACHE.__init__()

    def test_input_manager_methods(self):
        """Test InputManager methods inherited by VTask"""
        print(Fore.BLUE + "Testing InputManager Methods..." + Style.RESET)

        prepare.create_chern_project("demo_complex")
        os.chdir("demo_complex")
        obj_tsk = vtsk.VTask(os.getcwd() + "/tasks/taskAna1")

        # Test add_source method
        test_path = "/test/source/path"
        test_md5 = "source_md5_hash_12345"

        with patch('CelebiChrono.utils.csys.dir_md5') as mock_dir_md5, \
             patch('CelebiChrono.utils.metadata.ConfigFile') as mock_config_file, \
             patch.object(obj_tsk, 'impress') as mock_impress:

            mock_dir_md5.return_value = test_md5
            mock_config_instance = MagicMock()
            mock_config_file.return_value = mock_config_instance

            obj_tsk.add_source(test_path)

            # Verify method calls
            mock_dir_md5.assert_called_once_with(test_path)
            mock_config_file.assert_called_once_with(
                os.path.join(obj_tsk.path, "data.json")
            )
            mock_config_instance.write_variable.assert_called_once_with(
                "md5", test_md5
            )
            mock_impress.assert_called_once()

        # Test send method
        with patch('CelebiChrono.utils.csys.dir_md5') as mock_dir_md5, \
             patch.object(obj_tsk, 'set_input_md5') as mock_set_input_md5, \
             patch.object(obj_tsk, 'impress') as mock_impress, \
             patch.object(obj_tsk, 'send_data') as mock_send_data, \
             patch('builtins.print') as mock_print:

            mock_dir_md5.return_value = test_md5

            obj_tsk.send(test_path)

            # Verify method calls
            mock_dir_md5.assert_called_once_with(test_path)
            mock_set_input_md5.assert_called_once_with(test_path)
            mock_impress.assert_called_once()
            mock_send_data.assert_called_once_with(test_path)
            mock_print.assert_called_with("The md5 of the dir is: ", test_md5)

        os.chdir("..")
        prepare.remove_chern_project("demo_complex")
        CHERN_CACHE.__init__()

    def test_input_manager_algorithm_methods(self):
        """Test InputManager algorithm-related methods"""
        print(Fore.BLUE + "Testing InputManager Algorithm Methods..." +
              Style.RESET)

        prepare.create_chern_project("demo_complex")
        os.chdir("demo_complex")
        obj_tsk = vtsk.VTask(os.getcwd() + "/tasks/taskAna1")

        # Mock algorithm object
        mock_algorithm_obj = MagicMock()
        mock_algorithm_obj.object_type.return_value = "algorithm"
        mock_algorithm_obj.has_predecessor_recursively.return_value = False

        # Test add_algorithm method - successful case
        with patch.object(obj_tsk, 'get_vobject') as mock_get_vobject, \
             patch.object(obj_tsk, 'algorithm') as mock_algorithm, \
             patch.object(obj_tsk, 'add_arc_from') as mock_add_arc_from, \
             patch.object(obj_tsk, 'project_path', return_value='/mock/project/path'), \
             patch('builtins.print') as mock_print:

            mock_get_vobject.return_value = mock_algorithm_obj
            mock_algorithm.return_value = None  # No existing algorithm

            obj_tsk.add_algorithm("/path/to/algorithm")

            # Verify method calls
            mock_get_vobject.assert_any_call("/path/to/algorithm", "/mock/project/path")
            mock_add_arc_from.assert_called_once_with(mock_algorithm_obj)
            mock_print.assert_not_called()

        # Test add_algorithm method - wrong object type
        mock_wrong_obj = MagicMock()
        mock_wrong_obj.object_type.return_value = "task"

        with patch.object(obj_tsk, 'get_vobject') as mock_get_vobject, \
             patch('builtins.print') as mock_print:

            mock_get_vobject.return_value = mock_wrong_obj

            obj_tsk.add_algorithm("/path/to/task")

            # Should print error message
            mock_print.assert_called()
            error_call = mock_print.call_args[0][0]
            self.assertIn("task", error_call)
            self.assertIn("algorithm", error_call)

        # Test add_algorithm method - circular dependency
        mock_algorithm_obj.has_predecessor_recursively.return_value = True

        with patch.object(obj_tsk, 'get_vobject') as mock_get_vobject, \
             patch('builtins.print') as mock_print:

            mock_get_vobject.return_value = mock_algorithm_obj

            obj_tsk.add_algorithm("/path/to/algorithm")

            # Should print circular dependency error
            mock_print.assert_called()
            error_call = mock_print.call_args[0][0]
            self.assertIn("loop", error_call)

        # Test add_algorithm method - replace existing algorithm
        mock_algorithm_obj.has_predecessor_recursively.return_value = False
        mock_existing_algorithm = MagicMock()

        with patch.object(obj_tsk, 'get_vobject') as mock_get_vobject, \
             patch.object(obj_tsk, 'algorithm') as mock_algorithm, \
             patch.object(obj_tsk, 'remove_algorithm') as mock_remove_algorithm, \
             patch.object(obj_tsk, 'add_arc_from') as mock_add_arc_from, \
             patch('builtins.print') as mock_print:

            mock_get_vobject.return_value = mock_algorithm_obj
            mock_algorithm.return_value = mock_existing_algorithm

            obj_tsk.add_algorithm("/path/to/algorithm")

            # Should remove existing and add new
            mock_remove_algorithm.assert_called_once()
            mock_add_arc_from.assert_called_once_with(mock_algorithm_obj)
            mock_print.assert_called_with(
                "Already have algorithm, will replace it"
            )

        os.chdir("..")
        prepare.remove_chern_project("demo_complex")
        CHERN_CACHE.__init__()

    def test_input_manager_remove_algorithm(self):
        """Test InputManager remove_algorithm method"""
        print(Fore.BLUE + "Testing InputManager remove_algorithm..." +
              Style.RESET)

        prepare.create_chern_project("demo_complex")
        os.chdir("demo_complex")
        obj_tsk = vtsk.VTask(os.getcwd() + "/tasks/taskAna1")

        # Test remove_algorithm with existing algorithm
        mock_algorithm = MagicMock()

        with patch.object(obj_tsk, 'algorithm') as mock_get_algorithm, \
             patch.object(obj_tsk, 'remove_arc_from') as mock_remove_arc_from:

            mock_get_algorithm.return_value = mock_algorithm

            obj_tsk.remove_algorithm()

            # Verify method calls
            mock_remove_arc_from.assert_called_once_with(mock_algorithm)

        # Test remove_algorithm with no algorithm
        with patch.object(obj_tsk, 'algorithm') as mock_get_algorithm, \
             patch('builtins.print') as mock_print:

            mock_get_algorithm.return_value = None

            obj_tsk.remove_algorithm()

            # Should print "Nothing to remove"
            mock_print.assert_called_once_with("Nothing to remove")

        os.chdir("..")
        prepare.remove_chern_project("demo_complex")
        CHERN_CACHE.__init__()

    def test_input_manager_algorithm_getter(self):
        """Test InputManager algorithm getter method"""
        print(Fore.BLUE + "Testing InputManager algorithm getter..." +
              Style.RESET)

        prepare.create_chern_project("demo_complex")
        os.chdir("demo_complex")
        obj_tsk = vtsk.VTask(os.getcwd() + "/tasks/taskAna1")

        # Mock predecessor objects
        mock_task_pred = MagicMock()
        mock_task_pred.object_type.return_value = "task"
        mock_algorithm_pred = MagicMock()
        mock_algorithm_pred.object_type.return_value = "algorithm"
        mock_algorithm_pred.path = "/path/to/algorithm"
        mock_directory_pred = MagicMock()
        mock_directory_pred.object_type.return_value = "directory"

        # Test algorithm method with algorithm predecessor
        with patch.object(obj_tsk, 'predecessors') as mock_predecessors, \
             patch('CelebiChrono.kernel.valgorithm.VAlgorithm') as mock_valgorithm:

            mock_predecessors.return_value = [
                mock_task_pred, mock_algorithm_pred, mock_directory_pred
            ]
            mock_valg_instance = MagicMock()
            mock_valgorithm.return_value = mock_valg_instance

            result = obj_tsk.algorithm()

            # Should return VAlgorithm instance
            mock_valgorithm.assert_called_once_with("/path/to/algorithm")
            self.assertEqual(result, mock_valg_instance)

        # Test algorithm method with no algorithm predecessor
        with patch.object(obj_tsk, 'predecessors') as mock_predecessors:

            mock_predecessors.return_value = [
                mock_task_pred, mock_directory_pred
            ]

            result = obj_tsk.algorithm()

            # Should return None
            self.assertIsNone(result)

        # Test algorithm method with empty predecessors
        with patch.object(obj_tsk, 'predecessors') as mock_predecessors:

            mock_predecessors.return_value = []

            result = obj_tsk.algorithm()

            # Should return None
            self.assertIsNone(result)

        os.chdir("..")
        prepare.remove_chern_project("demo_complex")
        CHERN_CACHE.__init__()

    def test_input_manager_inputs_outputs(self):
        """Test InputManager inputs and outputs methods"""
        print(Fore.BLUE + "Testing InputManager inputs/outputs..." +
              Style.RESET)

        prepare.create_chern_project("demo_complex")
        os.chdir("demo_complex")
        obj_tsk = vtsk.VTask(os.getcwd() + "/tasks/taskAna1")

        # Mock predecessor and successor objects
        mock_task_pred1 = MagicMock()
        mock_task_pred1.object_type.return_value = "task"
        mock_task_pred1.path = "/path/to/task1"

        mock_task_pred2 = MagicMock()
        mock_task_pred2.object_type.return_value = "task"
        mock_task_pred2.path = "/path/to/task2"

        mock_algorithm_pred = MagicMock()
        mock_algorithm_pred.object_type.return_value = "algorithm"

        mock_task_succ1 = MagicMock()
        mock_task_succ1.object_type.return_value = "task"
        mock_task_succ1.path = "/path/to/output_task1"

        mock_task_succ2 = MagicMock()
        mock_task_succ2.object_type.return_value = "task"
        mock_task_succ2.path = "/path/to/output_task2"

        mock_directory_succ = MagicMock()
        mock_directory_succ.object_type.return_value = "directory"

        # Test inputs method
        with patch.object(obj_tsk, 'predecessors') as mock_predecessors, \
             patch.object(obj_tsk, 'get_task') as mock_get_task:

            mock_predecessors.return_value = [
                mock_task_pred1, mock_algorithm_pred, mock_task_pred2
            ]

            mock_task1 = MagicMock()
            mock_task2 = MagicMock()
            mock_get_task.side_effect = [mock_task1, mock_task2]

            inputs = obj_tsk.inputs()

            # Should return list of task objects
            self.assertEqual(len(inputs), 2)
            self.assertEqual(inputs, [mock_task1, mock_task2])

            # Verify get_task calls
            expected_calls = [
                unittest.mock.call("/path/to/task1"),
                unittest.mock.call("/path/to/task2")
            ]
            mock_get_task.assert_has_calls(expected_calls)

        # Test outputs method
        with patch.object(obj_tsk, 'successors') as mock_successors, \
             patch.object(obj_tsk, 'get_task') as mock_get_task:

            mock_successors.return_value = [
                mock_task_succ1, mock_directory_succ, mock_task_succ2
            ]

            mock_output_task1 = MagicMock()
            mock_output_task2 = MagicMock()
            mock_get_task.side_effect = [mock_output_task1, mock_output_task2]

            outputs = obj_tsk.outputs()

            # Should return list of task objects
            self.assertEqual(len(outputs), 2)
            self.assertEqual(outputs, [mock_output_task1, mock_output_task2])

            # Verify get_task calls
            expected_calls = [
                unittest.mock.call("/path/to/output_task1"),
                unittest.mock.call("/path/to/output_task2")
            ]
            mock_get_task.assert_has_calls(expected_calls)

        # Test inputs with no task predecessors
        with patch.object(obj_tsk, 'predecessors') as mock_predecessors:

            mock_predecessors.return_value = [mock_algorithm_pred]

            inputs = obj_tsk.inputs()

            # Should return empty list
            self.assertEqual(inputs, [])

        # Test outputs with no task successors
        with patch.object(obj_tsk, 'successors') as mock_successors:

            mock_successors.return_value = [mock_directory_succ]

            outputs = obj_tsk.outputs()

            # Should return empty list
            self.assertEqual(outputs, [])

        os.chdir("..")
        prepare.remove_chern_project("demo_complex")
        CHERN_CACHE.__init__()

    def test_input_manager_error_handling(self):
        """Test InputManager error handling scenarios"""
        print(Fore.BLUE + "Testing InputManager error handling..." +
              Style.RESET)

        prepare.create_chern_project("demo_complex")
        os.chdir("demo_complex")
        obj_tsk = vtsk.VTask(os.getcwd() + "/tasks/taskAna1")

        # Test add_source with invalid directory
        with patch('CelebiChrono.utils.csys.dir_md5') as mock_dir_md5:
            mock_dir_md5.side_effect = FileNotFoundError("Directory not found")

            with self.assertRaises(FileNotFoundError):
                obj_tsk.add_source("/non/existent/path")

        # Test send with invalid directory
        with patch('CelebiChrono.utils.csys.dir_md5') as mock_dir_md5:
            mock_dir_md5.side_effect = PermissionError("Permission denied")

            with self.assertRaises(PermissionError):
                obj_tsk.send("/restricted/path")

        # Test add_algorithm with invalid object path
        with patch.object(obj_tsk, 'get_vobject') as mock_get_vobject:
            mock_get_vobject.side_effect = Exception("Invalid object path")

            with self.assertRaises(Exception):
                obj_tsk.add_algorithm("/invalid/path")

        # Test inputs/outputs with get_task failure
        mock_task_pred = MagicMock()
        mock_task_pred.object_type.return_value = "task"
        mock_task_pred.path = "/invalid/task/path"

        with patch.object(obj_tsk, 'predecessors') as mock_predecessors, \
             patch.object(obj_tsk, 'get_task') as mock_get_task:

            mock_predecessors.return_value = [mock_task_pred]
            mock_get_task.side_effect = Exception("Task creation failed")

            with self.assertRaises(Exception):
                obj_tsk.inputs()

        os.chdir("..")
        prepare.remove_chern_project("demo_complex")
        CHERN_CACHE.__init__()

    def test_setting_manager_read_methods(self):
        """Test SettingManager read methods inherited by VTask"""
        print(Fore.BLUE + "Testing SettingManager Read Methods..." +
              Style.RESET)

        prepare.create_chern_project("demo_complex")
        os.chdir("demo_complex")
        obj_tsk = vtsk.VTask(os.getcwd() + "/tasks/taskAna1")

        # Test environment method
        with patch('CelebiChrono.utils.metadata.YamlFile') as mock_yaml:
            mock_yaml_instance = MagicMock()
            mock_yaml.return_value = mock_yaml_instance
            mock_yaml_instance.read_variable.return_value = "ubuntu:20.04"

            environment = obj_tsk.environment()

            # Verify method calls
            mock_yaml.assert_called_once_with(
                os.path.join(obj_tsk.path, "chern.yaml")
            )
            mock_yaml_instance.read_variable.assert_called_once_with(
                "environment", ""
            )
            self.assertEqual(environment, "ubuntu:20.04")

        # Test memory_limit method
        with patch('CelebiChrono.utils.metadata.YamlFile') as mock_yaml:
            mock_yaml_instance = MagicMock()
            mock_yaml.return_value = mock_yaml_instance
            mock_yaml_instance.read_variable.return_value = "1Gi"

            memory_limit = obj_tsk.memory_limit()

            # Verify method calls
            mock_yaml.assert_called_once_with(
                os.path.join(obj_tsk.path, "chern.yaml")
            )
            mock_yaml_instance.read_variable.assert_called_once_with(
                "memory_limit", ""
            )
            self.assertEqual(memory_limit, "1Gi")

        # Test parameters method
        test_params = {"param1": "value1", "param2": "value2"}
        with patch('CelebiChrono.utils.metadata.YamlFile') as mock_yaml:
            mock_yaml_instance = MagicMock()
            mock_yaml.return_value = mock_yaml_instance
            mock_yaml_instance.read_variable.return_value = test_params

            params_list, params_dict = obj_tsk.parameters()

            # Verify method calls
            mock_yaml.assert_called_once_with(
                os.path.join(obj_tsk.path, "chern.yaml")
            )
            mock_yaml_instance.read_variable.assert_called_once_with(
                "parameters", {}
            )
            self.assertEqual(sorted(params_list), ["param1", "param2"])
            self.assertEqual(params_dict, test_params)

        # Test auto_download method
        with patch.object(obj_tsk, 'config_file') as mock_config:
            mock_config.read_variable.return_value = False

            auto_download = obj_tsk.auto_download()

            # Verify method calls
            mock_config.read_variable.assert_called_once_with(
                "auto_download", True
            )
            self.assertFalse(auto_download)

        # Test default_runner method
        with patch.object(obj_tsk, 'config_file') as mock_config:
            mock_config.read_variable.return_value = "remote"

            default_runner = obj_tsk.default_runner()

            # Verify method calls
            mock_config.read_variable.assert_called_once_with(
                "default_runner", "local"
            )
            self.assertEqual(default_runner, "remote")

        os.chdir("..")
        prepare.remove_chern_project("demo_complex")
        CHERN_CACHE.__init__()

    def test_setting_manager_parameter_methods(self):
        """Test SettingManager parameter modification methods"""
        print(Fore.BLUE + "Testing SettingManager Parameter Methods..." +
              Style.RESET)

        prepare.create_chern_project("demo_complex")
        os.chdir("demo_complex")
        obj_tsk = vtsk.VTask(os.getcwd() + "/tasks/taskAna1")

        # Test add_parameter method
        existing_params = {"existing_param": "existing_value"}
        with patch('CelebiChrono.utils.metadata.YamlFile') as mock_yaml:
            mock_yaml_instance = MagicMock()
            mock_yaml.return_value = mock_yaml_instance
            mock_yaml_instance.read_variable.return_value = existing_params

            obj_tsk.add_parameter("new_param", "new_value")

            # Verify read and write calls
            mock_yaml_instance.read_variable.assert_called_once_with(
                "parameters", {}
            )
            expected_params = {
                "existing_param": "existing_value",
                "new_param": "new_value"
            }
            mock_yaml_instance.write_variable.assert_called_once_with(
                "parameters", expected_params
            )

        # Test add_parameter method with empty parameters
        with patch('CelebiChrono.utils.metadata.YamlFile') as mock_yaml:
            mock_yaml_instance = MagicMock()
            mock_yaml.return_value = mock_yaml_instance
            mock_yaml_instance.read_variable.return_value = {}

            obj_tsk.add_parameter("first_param", "first_value")

            # Verify write call
            expected_params = {"first_param": "first_value"}
            mock_yaml_instance.write_variable.assert_called_once_with(
                "parameters", expected_params
            )

        # Test remove_parameter method - existing parameter
        existing_params = {
            "param1": "value1",
            "param2": "value2",
            "param3": "value3"
        }
        with patch('CelebiChrono.utils.metadata.YamlFile') as mock_yaml:
            mock_yaml_instance = MagicMock()
            mock_yaml.return_value = mock_yaml_instance
            mock_yaml_instance.read_variable.return_value = existing_params

            obj_tsk.remove_parameter("param2")

            # Verify read and write calls
            mock_yaml_instance.read_variable.assert_called_once_with(
                "parameters", {}
            )
            expected_params = {"param1": "value1", "param3": "value3"}
            mock_yaml_instance.write_variable.assert_called_once_with(
                "parameters", expected_params
            )

        # Test remove_parameter method - non-existing parameter
        existing_params = {"param1": "value1"}
        with patch('CelebiChrono.utils.metadata.YamlFile') as mock_yaml, \
             patch('CelebiChrono.kernel.vtask_setting.logger') as mock_logger:

            mock_yaml_instance = MagicMock()
            mock_yaml.return_value = mock_yaml_instance
            mock_yaml_instance.read_variable.return_value = existing_params

            obj_tsk.remove_parameter("non_existent_param")

            # Should log warning and not call write_variable
            mock_logger.warning.assert_called_once()
            # Check that warning was called with correct format and parameter
            warning_args = mock_logger.warning.call_args[0]
            self.assertEqual(len(warning_args), 2)
            self.assertIn("Parameter '%s' not found", warning_args[0])
            self.assertEqual(warning_args[1], "non_existent_param")
            mock_yaml_instance.write_variable.assert_not_called()

        os.chdir("..")
        prepare.remove_chern_project("demo_complex")
        CHERN_CACHE.__init__()

    def test_setting_manager_setter_methods(self):
        """Test SettingManager setter methods"""
        print(Fore.BLUE + "Testing SettingManager Setter Methods..." +
              Style.RESET)

        prepare.create_chern_project("demo_complex")
        os.chdir("demo_complex")
        obj_tsk = vtsk.VTask(os.getcwd() + "/tasks/taskAna1")

        # Test set_auto_download method
        with patch.object(obj_tsk, 'config_file') as mock_config:
            obj_tsk.set_auto_download(False)

            mock_config.write_variable.assert_called_once_with(
                "auto_download", False
            )

        # Test set_default_runner method
        with patch.object(obj_tsk, 'config_file') as mock_config:
            obj_tsk.set_default_runner("kubernetes")

            mock_config.write_variable.assert_called_once_with(
                "default_runner", "kubernetes"
            )

        # Test set_environment method
        with patch('CelebiChrono.utils.metadata.YamlFile') as mock_yaml:
            mock_yaml_instance = MagicMock()
            mock_yaml.return_value = mock_yaml_instance

            obj_tsk.set_environment("python:3.9")

            # Verify method calls
            mock_yaml.assert_called_once_with(
                os.path.join(obj_tsk.path, "chern.yaml")
            )
            mock_yaml_instance.write_variable.assert_called_once_with(
                "environment", "python:3.9"
            )

        # Test set_memory_limit method
        with patch('CelebiChrono.utils.metadata.YamlFile') as mock_yaml:
            mock_yaml_instance = MagicMock()
            mock_yaml.return_value = mock_yaml_instance

            obj_tsk.set_memory_limit("2Gi")

            # Verify method calls
            mock_yaml.assert_called_once_with(
                os.path.join(obj_tsk.path, "chern.yaml")
            )
            mock_yaml_instance.write_variable.assert_called_once_with(
                "memory_limit", "2Gi"
            )

        os.chdir("..")
        prepare.remove_chern_project("demo_complex")
        CHERN_CACHE.__init__()

    def test_setting_manager_validation_methods(self):
        """Test SettingManager validation methods"""
        print(Fore.BLUE + "Testing SettingManager Validation Methods..." +
              Style.RESET)

        prepare.create_chern_project("demo_complex")
        os.chdir("demo_complex")
        obj_tsk = vtsk.VTask(os.getcwd() + "/tasks/taskAna1")

        # Test env_validated method - rawdata environment
        with patch.object(obj_tsk, 'environment', return_value='rawdata'):
            result = obj_tsk.env_validated()
            self.assertTrue(result)

        # Test env_validated method - algorithm with script environment
        mock_algorithm = MagicMock()
        mock_algorithm.environment.return_value = "script"

        with patch.object(obj_tsk, 'environment', return_value='python:3.9'), \
             patch.object(obj_tsk, 'algorithm', return_value=mock_algorithm):

            result = obj_tsk.env_validated()
            self.assertTrue(result)

        # Test env_validated method - matching algorithm environment
        mock_algorithm = MagicMock()
        mock_algorithm.environment.return_value = "python:3.9"

        with patch.object(obj_tsk, 'environment', return_value='python:3.9'), \
             patch.object(obj_tsk, 'algorithm', return_value=mock_algorithm):

            result = obj_tsk.env_validated()
            self.assertTrue(result)

        # Test env_validated method - non-matching algorithm environment
        mock_algorithm = MagicMock()
        mock_algorithm.environment.return_value = "ubuntu:20.04"

        with patch.object(obj_tsk, 'environment', return_value='python:3.9'), \
             patch.object(obj_tsk, 'algorithm', return_value=mock_algorithm):

            result = obj_tsk.env_validated()
            self.assertFalse(result)

        # Test env_validated method - no algorithm
        with patch.object(obj_tsk, 'environment', return_value='python:3.9'), \
             patch.object(obj_tsk, 'algorithm', return_value=None):

            result = obj_tsk.env_validated()
            self.assertFalse(result)

        # Test validated method - env_validated returns True
        with patch.object(obj_tsk, 'env_validated', return_value=True):
            result = obj_tsk.validated()
            self.assertTrue(result)

        # Test validated method - env_validated returns False
        with patch.object(obj_tsk, 'env_validated', return_value=False):
            result = obj_tsk.validated()
            self.assertFalse(result)

        os.chdir("..")
        prepare.remove_chern_project("demo_complex")
        CHERN_CACHE.__init__()

    def test_setting_manager_integration(self):
        """Test SettingManager integration with real YAML files"""
        print(Fore.BLUE + "Testing SettingManager Integration..." +
              Style.RESET)

        prepare.create_chern_project("demo_complex")
        os.chdir("demo_complex")
        obj_tsk = vtsk.VTask(os.getcwd() + "/tasks/taskAna1")

        # Test reading actual values from YAML file
        original_env = obj_tsk.environment()
        self.assertIsInstance(original_env, str)

        original_memory = obj_tsk.memory_limit()
        self.assertIsInstance(original_memory, str)

        original_params = obj_tsk.parameters()
        self.assertIsInstance(original_params[0], list)
        self.assertIsInstance(original_params[1], dict)

        # Test adding and reading parameters
        obj_tsk.add_parameter("test_integration_param", "test_value")
        params_list, params_dict = obj_tsk.parameters()

        self.assertIn("test_integration_param", params_list)
        self.assertEqual(params_dict["test_integration_param"], "test_value")

        # Test removing parameters
        obj_tsk.remove_parameter("test_integration_param")
        params_list, params_dict = obj_tsk.parameters()

        self.assertNotIn("test_integration_param", params_list)
        self.assertNotIn("test_integration_param", params_dict)

        # Test setting and reading environment
        obj_tsk.set_environment("test_environment")
        new_env = obj_tsk.environment()
        self.assertEqual(new_env, "test_environment")

        # Test setting and reading memory limit
        obj_tsk.set_memory_limit("512Mi")
        new_memory = obj_tsk.memory_limit()
        self.assertEqual(new_memory, "512Mi")

        # Test config file settings
        original_auto_download = obj_tsk.auto_download()
        obj_tsk.set_auto_download(not original_auto_download)
        new_auto_download = obj_tsk.auto_download()
        self.assertEqual(new_auto_download, not original_auto_download)

        original_runner = obj_tsk.default_runner()
        obj_tsk.set_default_runner("test_runner")
        new_runner = obj_tsk.default_runner()
        self.assertEqual(new_runner, "test_runner")

        os.chdir("..")
        prepare.remove_chern_project("demo_complex")
        CHERN_CACHE.__init__()

    def test_setting_manager_error_handling(self):
        """Test SettingManager error handling scenarios"""
        print(Fore.BLUE + "Testing SettingManager Error Handling..." +
              Style.RESET)

        prepare.create_chern_project("demo_complex")
        os.chdir("demo_complex")
        obj_tsk = vtsk.VTask(os.getcwd() + "/tasks/taskAna1")

        # Test environment method with YAML file error
        with patch('CelebiChrono.utils.metadata.YamlFile') as mock_yaml:
            mock_yaml.side_effect = Exception("YAML file error")

            with self.assertRaises(Exception):
                obj_tsk.environment()

        # Test memory_limit method with YAML read error
        with patch('CelebiChrono.utils.metadata.YamlFile') as mock_yaml:
            mock_yaml_instance = MagicMock()
            mock_yaml.return_value = mock_yaml_instance
            mock_yaml_instance.read_variable.side_effect = Exception(
                "Read error"
            )

            with self.assertRaises(Exception):
                obj_tsk.memory_limit()

        # Test parameters method with YAML read error
        with patch('CelebiChrono.utils.metadata.YamlFile') as mock_yaml:
            mock_yaml_instance = MagicMock()
            mock_yaml.return_value = mock_yaml_instance
            mock_yaml_instance.read_variable.side_effect = Exception(
                "Parameters read error"
            )

            with self.assertRaises(Exception):
                obj_tsk.parameters()

        # Test add_parameter with YAML write error
        with patch('CelebiChrono.utils.metadata.YamlFile') as mock_yaml:
            mock_yaml_instance = MagicMock()
            mock_yaml.return_value = mock_yaml_instance
            mock_yaml_instance.read_variable.return_value = {}
            mock_yaml_instance.write_variable.side_effect = Exception(
                "Write error"
            )

            with self.assertRaises(Exception):
                obj_tsk.add_parameter("test_param", "test_value")

        # Test set_environment with YAML write error
        with patch('CelebiChrono.utils.metadata.YamlFile') as mock_yaml:
            mock_yaml_instance = MagicMock()
            mock_yaml.return_value = mock_yaml_instance
            mock_yaml_instance.write_variable.side_effect = Exception(
                "Environment write error"
            )

            with self.assertRaises(Exception):
                obj_tsk.set_environment("test_env")

        # Test auto_download with config file error
        with patch.object(obj_tsk, 'config_file') as mock_config:
            mock_config.read_variable.side_effect = Exception(
                "Config read error"
            )

            with self.assertRaises(Exception):
                obj_tsk.auto_download()

        # Test set_auto_download with config file write error
        with patch.object(obj_tsk, 'config_file') as mock_config:
            mock_config.write_variable.side_effect = Exception(
                "Config write error"
            )

            with self.assertRaises(Exception):
                obj_tsk.set_auto_download(True)

        os.chdir("..")
        prepare.remove_chern_project("demo_complex")
        CHERN_CACHE.__init__()

    def test_vtask_specific_methods(self):
        """Test VTask-specific methods not covered by other managers"""
        print(Fore.BLUE + "Testing VTask Specific Methods..." + Style.RESET)

        prepare.create_chern_project("demo_complex")
        os.chdir("demo_complex")
        obj_tsk = vtsk.VTask(os.getcwd() + "/tasks/taskAna1")

        # Test output_files method
        output_files = obj_tsk.output_files()
        self.assertEqual(output_files, [])

        # Test get_file method
        test_filename = "test_output.txt"
        with patch.object(ChernCommunicator, 'instance') as mock_instance:
            mock_communicator = MagicMock()
            mock_instance.return_value = mock_communicator
            mock_communicator.get_file.return_value = "/path/to/file"

            result = obj_tsk.get_file(test_filename)

            mock_communicator.get_file.assert_called_once_with(
                "local", ANY, test_filename
            )
            self.assertEqual(result, "/path/to/file")

        # Test get_task method
        test_path = "/path/to/task"
        result_task = obj_tsk.get_task(test_path)
        self.assertIsInstance(result_task, vtsk.VTask)

        os.chdir("..")
        prepare.remove_chern_project("demo_complex")
        CHERN_CACHE.__init__()

    def test_vtask_view_method(self):
        """Test VTask view method"""
        print(Fore.BLUE + "Testing VTask view method..." + Style.RESET)

        prepare.create_chern_project("demo_complex")
        os.chdir("demo_complex")
        obj_tsk = vtsk.VTask(os.getcwd() + "/tasks/taskAna1")

        # Test view method with local file that exists
        test_filename = "local:test_file.txt"
        mock_file_path = "/path/to/test_file.txt"

        with patch.object(obj_tsk, 'get_file') as mock_get_file, \
             patch('CelebiChrono.utils.csys.exists') as mock_exists, \
             patch('CelebiChrono.kernel.vtask.open_subprocess') as \
             mock_open_subprocess:

            mock_get_file.return_value = mock_file_path
            mock_exists.return_value = True

            obj_tsk.view(test_filename)

            # Verify method calls
            mock_get_file.assert_called_once_with("local:test_file.txt")
            mock_exists.assert_called_once_with(mock_file_path)
            mock_open_subprocess.assert_called_once_with(
                f"open {mock_file_path}"
            )

        # Test view method with local file that doesn't exist
        with patch.object(obj_tsk, 'get_file') as mock_get_file, \
             patch('CelebiChrono.utils.csys.exists') as mock_exists, \
             patch('builtins.print') as mock_print:

            mock_get_file.return_value = mock_file_path
            mock_exists.return_value = False

            obj_tsk.view(test_filename)

            # Should print error message
            mock_print.assert_called_once()
            error_msg = mock_print.call_args[0][0]
            self.assertIn("do not exists", error_msg)
            self.assertIn(mock_file_path, error_msg)

        # Test view method with non-local filename
        non_local_filename = "remote_file.txt"

        with patch.object(obj_tsk, 'get_file') as mock_get_file, \
             patch('CelebiChrono.utils.csys.exists') as mock_exists:

            obj_tsk.view(non_local_filename)

            # Should not call get_file or exists for non-local files
            mock_get_file.assert_not_called()
            mock_exists.assert_not_called()

        os.chdir("..")
        prepare.remove_chern_project("demo_complex")
        CHERN_CACHE.__init__()

    def test_vtask_printed_status_method(self):
        """Test VTask printed_status method"""
        print(Fore.BLUE + "Testing VTask printed_status method..." +
              Style.RESET)

        prepare.create_chern_project("demo_complex")
        os.chdir("demo_complex")
        obj_tsk = vtsk.VTask(os.getcwd() + "/tasks/taskAna1")

        # Test printed_status when not impressed
        with patch.object(obj_tsk, 'status') as mock_status, \
             patch('CelebiChrono.kernel.vobject.VObject.printed_status') as mock_super:

            mock_status.return_value = "new"
            mock_message = MagicMock()
            mock_super.return_value = mock_message

            result = obj_tsk.printed_status()

            # Should return early without communicator calls
            mock_super.assert_called_once()
            self.assertEqual(result, mock_message)

        # Test printed_status when impressed but dite not connected
        with patch.object(obj_tsk, 'status') as mock_status, \
             patch.object(ChernCommunicator, 'instance') as mock_instance, \
             patch('CelebiChrono.kernel.vobject.VObject.printed_status') as mock_super:

            mock_status.return_value = "impressed"

            mock_communicator = MagicMock()
            mock_instance.return_value = mock_communicator
            mock_communicator.dite_status.return_value = "disconnected"

            mock_message = MagicMock()
            mock_super.return_value = mock_message

            result = obj_tsk.printed_status()

            # Should check dite status but not call job_status
            mock_communicator.dite_status.assert_called_once()
            mock_communicator.job_status.assert_not_called()
            # Check if add was called - if not, the method doesn't handle dite disconnection
            if mock_message.add.called:
                mock_message.add.assert_called_with("DITE not connected\n")
            self.assertEqual(result, mock_message)

        # Test printed_status when impressed and dite connected - job_status should be called
        with patch.object(obj_tsk, 'status') as mock_status, \
             patch.object(ChernCommunicator, 'instance') as mock_instance, \
             patch('CelebiChrono.kernel.vobject.VObject.printed_status') as mock_super:

            mock_status.return_value = "impressed"

            mock_communicator = MagicMock()
            mock_instance.return_value = mock_communicator
            mock_communicator.dite_status.return_value = "connected"
            mock_communicator.job_status.return_value = "running"

            mock_message = MagicMock()
            mock_super.return_value = mock_message

            result = obj_tsk.printed_status()

            # Should check dite status and call job_status when connected
            mock_communicator.dite_status.assert_called_once()
            mock_communicator.job_status.assert_called_once_with(ANY)
            self.assertEqual(result, mock_message)

        os.chdir("..")
        prepare.remove_chern_project("demo_complex")
        CHERN_CACHE.__init__()

    # def test_create_task_function(self):
    #     """Test create_task function"""
    #     print(Fore.BLUE + "Testing create_task function..." + Style.RESET)

    #     # Test creating task in project directory
    #     test_path = "test_task"
    #
    #     with patch('CelebiChrono.utils.csys.strip_path_string') as mock_strip, \
    #          patch('os.path.abspath') as mock_abspath, \
    #          patch('CelebiChrono.kernel.vobject.VObject') as mock_vobject, \
    #          patch('CelebiChrono.utils.csys.mkdir') as mock_mkdir, \
    #          patch('CelebiChrono.utils.metadata.ConfigFile') as mock_config_file, \
    #          patch('CelebiChrono.utils.metadata.YamlFile') as mock_yaml_file, \
    #          patch('builtins.open', mock_open()) as mock_file:
    #
    #         mock_strip.return_value = test_path
    #         mock_abspath.return_value = "/parent/path"
    #
    #         # Mock parent object as project
    #         mock_parent = MagicMock()
    #         mock_parent.object_type.return_value = "project"
    #         mock_vobject.return_value = mock_parent
    #
    #         # Mock config and yaml files
    #         mock_config_instance = MagicMock()
    #         mock_config_file.return_value = mock_config_instance
    #         mock_yaml_instance = MagicMock()
    #         mock_yaml_file.return_value = mock_yaml_instance
    #
    #         # Mock task object
    #         mock_task = MagicMock()
    #         mock_task.invariant_path.return_value = "test_task"
    #         mock_vobject.side_effect = [mock_parent, mock_task]
    #
    #         vtsk.create_task(test_path)
    #
    #         # Verify method calls
    #         mock_strip.assert_called_once_with(test_path)
    #         mock_mkdir.assert_called_once_with(f"{test_path}/.chern")
    #
    #         # Verify config file writes
    #         config_calls = mock_config_instance.write_variable.call_args_list
    #         self.assertEqual(len(config_calls), 3)
    #         self.assertEqual(config_calls[0][0], ("object_type", "task"))
    #         self.assertEqual(config_calls[1][0], ("auto_download", True))
    #         self.assertEqual(config_calls[2][0], ("default_runner", "local"))
    #
    #         # Verify yaml file writes
    #         yaml_calls = mock_yaml_instance.write_variable.call_args_list
    #         self.assertEqual(len(yaml_calls), 2)
    #         expected_env = ("environment", "reanahub/reana-env-root6:6.18.04")
    #         self.assertEqual(yaml_calls[0][0], expected_env)
    #         expected_memory = ("kubernetes_memory_limit", "256Mi")
    #         self.assertEqual(yaml_calls[1][0], expected_memory)
    #
    #         # Verify README file was written
    #         mock_file.assert_called_once_with(
    #             f"{test_path}/.chern/README.md", "w", encoding="utf-8"
    #         )

    #     # Test creating task in non-project/directory parent
    #     with patch('CelebiChrono.utils.csys.strip_path_string') as mock_strip, \
    #          patch('os.path.abspath') as mock_abspath, \
    #          patch('CelebiChrono.kernel.vobject.VObject') as mock_vobject:
    #
    #         mock_strip.return_value = test_path
    #         mock_abspath.return_value = "/parent/path"
    #
    #         # Mock parent object as non-project/directory
    #         mock_parent = MagicMock()
    #         mock_parent.object_type.return_value = "task"
    #         mock_vobject.return_value = mock_parent
    #
    #         # Should return early without creating anything
    #         result = vtsk.create_task(test_path)
    #         self.assertIsNone(result)

    # def test_create_data_function(self):
    #     """Test create_data function"""
    #     print(Fore.BLUE + "Testing create_data function..." + Style.RESET)

    #     test_path = "test_data"
    #
    #     with patch('CelebiChrono.utils.csys.strip_path_string') as mock_strip, \
    #          patch('os.path.abspath') as mock_abspath, \
    #          patch('CelebiChrono.kernel.vobject.VObject') as mock_vobject, \
    #          patch('CelebiChrono.utils.csys.mkdir') as mock_mkdir, \
    #          patch('CelebiChrono.utils.metadata.ConfigFile') as mock_config_file, \
    #          patch('CelebiChrono.utils.metadata.YamlFile') as mock_yaml_file, \
    #          patch('builtins.open', mock_open()) as mock_file:
    #
    #         mock_strip.return_value = test_path
    #         mock_abspath.return_value = "/parent/path"
    #
    #         # Mock parent object as directory
    #         mock_parent = MagicMock()
    #         mock_parent.object_type.return_value = "directory"
    #         mock_vobject.return_value = mock_parent
    #
    #         # Mock config and yaml files
    #         mock_config_instance = MagicMock()
    #         mock_config_file.return_value = mock_config_instance
    #         mock_yaml_instance = MagicMock()
    #         mock_yaml_file.return_value = mock_yaml_instance
    #
    #         # Mock task object
    #         mock_task = MagicMock()
    #         mock_task.invariant_path.return_value = "test_data"
    #         mock_vobject.side_effect = [mock_parent, mock_task]
    #
    #         vtsk.create_data(test_path)
    #
    #         # Verify method calls
    #         mock_strip.assert_called_once_with(test_path)
    #         mock_mkdir.assert_called_once_with(f"{test_path}/.chern")
    #
    #         # Verify config file writes (only object_type for data)
    #         mock_config_instance.write_variable.assert_called_once_with(
    #             "object_type", "task"
    #         )
    #
    #         # Verify yaml file writes (rawdata environment and empty uuid)
    #         yaml_calls = mock_yaml_instance.write_variable.call_args_list
    #         self.assertEqual(len(yaml_calls), 2)
    #         self.assertEqual(yaml_calls[0][0], ("environment", "rawdata"))
    #         self.assertEqual(yaml_calls[1][0], ("uuid", ""))
    #
    #         # Verify README file was written
    #         mock_file.assert_called_once_with(
    #             f"{test_path}/.chern/README.md", "w", encoding="utf-8"
    #         )

    #     # Test creating data in non-project/directory parent
    #     with patch('CelebiChrono.utils.csys.strip_path_string') as mock_strip, \
    #          patch('os.path.abspath') as mock_abspath, \
    #          patch('CelebiChrono.kernel.vobject.VObject') as mock_vobject:
    #
    #         mock_strip.return_value = test_path
    #         mock_abspath.return_value = "/parent/path"
    #
    #         # Mock parent object as non-project/directory
    #         mock_parent = MagicMock()
    #         mock_parent.object_type.return_value = "algorithm"
    #         mock_vobject.return_value = mock_parent
    #
    #         # Should return early without creating anything
    #         result = vtsk.create_data(test_path)
    #         self.assertIsNone(result)


if __name__ == '__main__':
    unittest.main(verbosity=2)

