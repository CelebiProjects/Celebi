"""Tests for the object-level impression history list."""
import os
import unittest
from datetime import datetime
from colored import Fore, Style
import prepare
import CelebiChrono.kernel.vobject as vobj
from CelebiChrono.kernel.chern_cache import ChernCache
from CelebiChrono.utils import metadata

CHERN_CACHE = ChernCache.instance()


class TestImpressionHistory(unittest.TestCase):
    """Test object-level impressions history recording."""

    def setUp(self):
        """Set Up."""
        self.cwd = os.getcwd()

    def tearDown(self):
        """Tear Down."""
        os.chdir(self.cwd)

    def test_impress_records_history_entry(self):
        """A successful impress appends one entry to the local impressions list."""
        print(Fore.BLUE + "Testing impression history recording..." + Style.RESET)
        prepare.create_chern_project("demo_genfit_new")
        os.chdir("demo_genfit_new")
        try:
            obj_fit_task = vobj.VObject("FitTask")
            obj_fit_task.impress()

            local_config = metadata.ConfigFile(
                os.path.join(obj_fit_task.path, ".celebi", "config.local.json")
            )
            history = local_config.read_variable("impressions", [])
            self.assertEqual(len(history), 1)
            self.assertEqual(history[0]["uuid"], str(obj_fit_task.impression()))

            # Timestamp is ISO-8601 with timezone offset and is parseable.
            ts = history[0]["timestamp"]
            parsed = datetime.fromisoformat(ts)
            self.assertIsNotNone(parsed.tzinfo)

            # Descriptor is non-empty (demo project falls back to object name).
            self.assertTrue(history[0]["descriptor"])
        finally:
            os.chdir("..")
            prepare.remove_chern_project("demo_genfit_new")
            CHERN_CACHE.__init__()  # pylint: disable=unnecessary-dunder-call

    def test_multiple_impresses_append_chronologically(self):
        """Each impress appends a new entry; entries are ordered oldest-first."""
        print(Fore.BLUE + "Testing multiple impression history entries..." + Style.RESET)
        prepare.create_chern_project("demo_genfit_new")
        os.chdir("demo_genfit_new")
        try:
            obj_fit_task = vobj.VObject("FitTask")
            obj_fit_task.impress()
            first_uuid = str(obj_fit_task.impression())

            # Change the task so the next impress produces a different UUID.
            celebi_yaml = os.path.join(obj_fit_task.path, "celebi.yaml")
            with open(celebi_yaml, "a", encoding="utf-8") as f:
                f.write("# touch\n")

            # Invalidate cache so the file change is noticed.
            CHERN_CACHE.impression_consult_table.clear()
            CHERN_CACHE.project_modification_time = (None, 0)

            obj_fit_task.impress()
            second_uuid = str(obj_fit_task.impression())
            self.assertNotEqual(first_uuid, second_uuid)

            local_config = metadata.ConfigFile(
                os.path.join(obj_fit_task.path, ".celebi", "config.local.json")
            )
            history = local_config.read_variable("impressions", [])
            self.assertEqual(len(history), 2)
            self.assertEqual(history[0]["uuid"], first_uuid)
            self.assertEqual(history[1]["uuid"], second_uuid)

            self.assertLessEqual(
                datetime.fromisoformat(history[0]["timestamp"]),
                datetime.fromisoformat(history[1]["timestamp"]),
            )
        finally:
            os.chdir("..")
            prepare.remove_chern_project("demo_genfit_new")
            CHERN_CACHE.__init__()  # pylint: disable=unnecessary-dunder-call

    def test_clean_impressions_clears_history(self):
        """clean_impressions resets the object-level impressions list."""
        print(Fore.BLUE + "Testing clean impressions clears history..." + Style.RESET)
        prepare.create_chern_project("demo_genfit_new")
        os.chdir("demo_genfit_new")
        try:
            obj_fit_task = vobj.VObject("FitTask")
            obj_fit_task.impress()
            obj_fit_task.clean_impressions()

            local_config = metadata.ConfigFile(
                os.path.join(obj_fit_task.path, ".celebi", "config.local.json")
            )
            history = local_config.read_variable("impressions", [])
            self.assertEqual(history, [])
        finally:
            os.chdir("..")
            prepare.remove_chern_project("demo_genfit_new")
            CHERN_CACHE.__init__()  # pylint: disable=unnecessary-dunder-call

    def test_corrupt_history_list_is_reset(self):
        """A non-list value in impressions is replaced before appending."""
        print(Fore.BLUE + "Testing corrupt history list recovery..." + Style.RESET)
        prepare.create_chern_project("demo_genfit_new")
        os.chdir("demo_genfit_new")
        try:
            obj_fit_task = vobj.VObject("FitTask")
            local_config = metadata.ConfigFile(
                os.path.join(obj_fit_task.path, ".celebi", "config.local.json")
            )
            local_config.write_variable("impressions", "not-a-list")

            obj_fit_task.impress()
            history = local_config.read_variable("impressions", [])
            self.assertIsInstance(history, list)
            self.assertEqual(len(history), 1)
            self.assertEqual(history[0]["uuid"], str(obj_fit_task.impression()))
        finally:
            os.chdir("..")
            prepare.remove_chern_project("demo_genfit_new")
            CHERN_CACHE.__init__()  # pylint: disable=unnecessary-dunder-call
