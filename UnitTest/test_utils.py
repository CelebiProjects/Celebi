"""
Unit tests for utils/csys.py module
Tests for all utility functions in the csys module
"""
import unittest
import os
import warnings
from colored import Fore, Style
import CelebiChrono.utils.csys as csys
from CelebiChrono.kernel.chern_cache import ChernCache
import prepare

CHERN_CACHE = ChernCache.instance()


class TestChernUtils(unittest.TestCase):
    """Test class for Chern utilities"""

    def setUp(self):
        """Set up test environment"""
        self.cwd = os.getcwd()

    def tearDown(self):
        """Clean up test environment"""
        os.chdir(self.cwd)

    def test_generate_uuid(self):
        """Test UUID generation"""
        print(Fore.BLUE + "Testing generate_uuid..." + Style.RESET)
        uuid = csys.generate_uuid()
        self.assertEqual(len(uuid), 32)
        self.assertIsInstance(uuid, str)
        # Test that consecutive calls return different UUIDs
        uuid2 = csys.generate_uuid()
        self.assertNotEqual(uuid, uuid2)

    def test_abspath(self):
        """Test absolute path resolution"""
        print(Fore.BLUE + "Testing abspath..." + Style.RESET)
        self.assertEqual(csys.abspath('~/'), csys.abspath('~'))

    def test_project_path(self):
        """Test project path resolution"""
        print(Fore.BLUE + "Testing project_path..." + Style.RESET)
        pwd = os.getcwd()

        prepare.create_chern_project("demo_genfit")
        try:
            self.assertEqual(
                csys.project_path("demo_genfit"),
                os.path.join(pwd, "demo_genfit")
            )
            self.assertEqual(
                csys.project_path("demo_genfit/Fit"),
                os.path.join(pwd, "demo_genfit")
            )
            self.assertIsNone(csys.project_path("demo_genfit/Dummy"))
            self.assertIsNone(csys.project_path("."))
        finally:
            prepare.remove_chern_project("demo_genfit")

    def test_dir_mtime(self):
        """Test directory modification time"""
        print(Fore.BLUE + "Testing dir_mtime..." + Style.RESET)
        prepare.create_chern_project("demo_genfit")
        try:
            mtime = csys.dir_mtime("demo_genfit")
            self.assertIsInstance(mtime, (int, float))
            self.assertGreater(mtime, 0)
        finally:
            prepare.remove_chern_project("demo_genfit")

    def test_md5sum(self):
        """Test MD5 sum calculation"""
        print(Fore.BLUE + "Testing md5sum..." + Style.RESET)
        prepare.create_chern_project("demo_genfit")
        try:
            expected_md5 = "b74a43595f1bc0d040e22a3cffc82096"
            actual_md5 = csys.md5sum("demo_genfit/Gen/gendata.C")
            self.assertEqual(actual_md5, expected_md5)
        finally:
            prepare.remove_chern_project("demo_genfit")

    def test_daemon_path(self):
        """Test daemon path (deprecated)"""
        print(Fore.BLUE + "Testing daemon_path..." + Style.RESET)
        # This function is deprecated, just verify it exists
        self.assertTrue(hasattr(csys, 'daemon_path'))

    def test_local_config_path(self):
        """Test local config path"""
        print(Fore.BLUE + "Testing local_config_path..." + Style.RESET)
        home = os.environ['HOME']
        expected_path = os.path.join(home, ".Chern", "config.json")
        self.assertEqual(csys.local_config_path(), expected_path)

    def test_local_config_dir(self):
        """Test local config directory"""
        print(Fore.BLUE + "Testing local_config_dir..." + Style.RESET)
        home = os.environ['HOME']
        expected_dir = os.path.join(home, ".Chern")
        self.assertEqual(csys.local_config_dir(), expected_dir)

    def test_mkdir(self):
        """Test directory creation"""
        print(Fore.BLUE + "Testing mkdir..." + Style.RESET)
        prepare.create_chern_project("demo_genfit")
        try:
            test_dir = "demo_genfit/test"
            csys.mkdir(test_dir)
            self.assertTrue(os.path.exists(test_dir))
        finally:
            prepare.remove_chern_project("demo_genfit")

    def test_copy(self):
        """Test file copying"""
        print(Fore.BLUE + "Testing copy..." + Style.RESET)
        prepare.create_chern_project("demo_genfit")
        try:
            src = "demo_genfit/Gen/gendata.C"
            dst = "demo_genfit/gendata.C"
            csys.copy(src, dst)
            self.assertTrue(os.path.exists(dst))
        finally:
            prepare.remove_chern_project("demo_genfit")

    def test_list_dir(self):
        """Test directory listing"""
        print(Fore.BLUE + "Testing list_dir..." + Style.RESET)
        prepare.create_chern_project("demo_genfit")
        try:
            expected_files = ["gendata.C", ".chern", "chern.yaml"]
            actual_files = csys.list_dir("demo_genfit/Gen")
            self.assertEqual(sorted(actual_files), sorted(expected_files))
        finally:
            prepare.remove_chern_project("demo_genfit")

    def test_rm_tree(self):
        """Test tree removal"""
        print(Fore.BLUE + "Testing rm_tree..." + Style.RESET)
        prepare.create_chern_project("demo_genfit")
        try:
            csys.rm_tree("demo_genfit/Gen")
            self.assertFalse(os.path.exists("demo_genfit/Gen"))
        finally:
            prepare.remove_chern_project("demo_genfit")

    def test_copy_tree(self):
        """Test tree copying"""
        print(Fore.BLUE + "Testing copy_tree..." + Style.RESET)
        prepare.create_chern_project("demo_genfit")
        try:
            src = "demo_genfit/Gen"
            dst = "demo_genfit/Gen2"
            csys.copy_tree(src, dst)
            self.assertTrue(os.path.exists(dst))
        finally:
            prepare.remove_chern_project("demo_genfit")

    def test_exists(self):
        """Test file existence check"""
        print(Fore.BLUE + "Testing exists..." + Style.RESET)
        prepare.create_chern_project("demo_genfit")
        try:
            self.assertTrue(csys.exists("demo_genfit/Gen/gendata.C"))
            self.assertFalse(csys.exists("demo_genfit/Gen/gendata.h"))
        finally:
            prepare.remove_chern_project("demo_genfit")

    def test_make_archive(self):
        """Test archive creation"""
        print(Fore.BLUE + "Testing make_archive..." + Style.RESET)
        prepare.create_chern_project("demo_genfit")
        try:
            src = "demo_genfit/Gen"
            archive = "demo_genfit/Gen.tar.gz"
            csys.make_archive(src, archive)
            self.assertTrue(os.path.exists(archive))
        finally:
            prepare.remove_chern_project("demo_genfit")

    def test_unpack_archive(self):
        """Test archive unpacking"""
        print(Fore.BLUE + "Testing unpack_archive..." + Style.RESET)
        prepare.create_chern_project("demo_genfit")
        try:
            src = "demo_genfit/Gen"
            archive = "demo_genfit/Gen"
            dst = "demo_genfit/Gen2"

            csys.make_archive(src, archive)

            # Suppress the deprecation warning for tar extraction
            with warnings.catch_warnings():
                warnings.simplefilter("ignore", DeprecationWarning)
                csys.unpack_archive(f"{archive}.tar.gz", dst)

            self.assertTrue(os.path.exists(dst))
        finally:
            prepare.remove_chern_project("demo_genfit")

    def test_strip_path_string(self):
        """Test path string stripping"""
        print(Fore.BLUE + "Testing strip_path_string..." + Style.RESET)
        result = csys.strip_path_string("demo_genfit/Gen/")
        self.assertEqual(result, "demo_genfit/Gen")

    def test_refine_path(self):
        """Test path refinement"""
        print(Fore.BLUE + "Testing refine_path..." + Style.RESET)
        home = os.environ['HOME']
        input_path = "~/demo_genfit/Gen/gendata.C"
        expected = os.path.join(home, "demo_genfit/Gen/gendata.C")
        result = csys.refine_path(input_path, home)
        self.assertEqual(result, expected)

    def test_walk(self):
        """Test directory walking"""
        print(Fore.BLUE + "Testing walk..." + Style.RESET)
        prepare.create_chern_project("demo_genfit")
        try:
            result = csys.walk("demo_genfit/Gen")
            # Convert generator to list if needed
            if hasattr(result, '__iter__') and not isinstance(result, list):
                result = list(result)
            self.assertIsInstance(result, list)
            self.assertGreater(len(result), 0)
        finally:
            prepare.remove_chern_project("demo_genfit")

    def test_tree_excluded(self):
        """Test tree exclusion"""
        print(Fore.BLUE + "Testing tree_excluded..." + Style.RESET)
        prepare.create_chern_project("demo_genfit")
        try:
            result = csys.tree_excluded("demo_genfit/Gen")
            self.assertIsInstance(result, list)
        finally:
            prepare.remove_chern_project("demo_genfit")

    def test_special_path_string(self):
        """Test special path string (deprecated)"""
        print(Fore.BLUE + "Testing special_path_string..." + Style.RESET)
        # This function is deprecated, just verify it exists
        if hasattr(csys, 'special_path_string'):
            result = csys.special_path_string("demo_genfit/Gen/gendata.C")
            # The function might modify the path, check it returns string
            self.assertIsInstance(result, str)
        else:
            self.skipTest("special_path_string function not available")

    def test_colorize(self):
        """Test text colorization"""
        print(Fore.BLUE + "Testing colorize..." + Style.RESET)
        result = csys.colorize("test", "warning")
        expected = "\033[31mtest\033[m"
        self.assertEqual(result, expected)

    def test_color_print(self):
        """Test color printing"""
        print(Fore.BLUE + "Testing color_print..." + Style.RESET)
        # This function prints to stdout, just verify it doesn't crash
        try:
            csys.color_print("test", "red")
        except Exception as e:
            self.fail(f"color_print raised {e} unexpectedly!")

    def test_debug(self):
        """Test debug printing"""
        print(Fore.BLUE + "Testing debug..." + Style.RESET)
        # This function prints debug info, just verify it doesn't crash
        try:
            csys.debug("test")
        except Exception as e:
            self.fail(f"debug raised {e} unexpectedly!")

    def test_remove_cache(self):
        """Test cache removal (deprecated)"""
        print(Fore.BLUE + "Testing remove_cache..." + Style.RESET)
        # This function is deprecated, just verify it exists
        self.assertTrue(hasattr(csys, 'remove_cache'))


if __name__ == '__main__':
    unittest.main(verbosity=2)

