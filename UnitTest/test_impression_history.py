"""Tests for the object-level impression history list."""
import os
import unittest
from datetime import datetime
from colored import Fore, Style
import CelebiChrono.kernel.vobject as vobj
from CelebiChrono.kernel.chern_cache import ChernCache
from CelebiChrono.utils import metadata
import prepare

CHERN_CACHE = ChernCache.instance()


class TestImpressionHistory(unittest.TestCase):
    """Test object-level impressions history recording."""

    def setUp(self):
        self.cwd = os.getcwd()

    def tearDown(self):
        os.chdir(self.cwd)

    def test_impress_records_history_entry(self):
        """A successful impress appends one entry to the local impressions list."""
        print(Fore.BLUE + "Testing impression history recording..." + Style.RESET)
        prepare.create_chern_project("demo_genfit_new")
        os.chdir("demo_genfit_new")
        try:
            obj_fitTask = vobj.VObject("FitTask")
            obj_fitTask.impress()

            local_config = metadata.ConfigFile(
                os.path.join(obj_fitTask.path, ".celebi", "config.local.json")
            )
            history = local_config.read_variable("impressions", [])
            self.assertEqual(len(history), 1)
            self.assertEqual(history[0]["uuid"], str(obj_fitTask.impression()))

            # Timestamp is ISO-8601 with timezone offset and is parseable.
            ts = history[0]["timestamp"]
            parsed = datetime.fromisoformat(ts)
            self.assertIsNotNone(parsed.tzinfo)

            # Descriptor is non-empty (demo project falls back to object name).
            self.assertTrue(history[0]["descriptor"])
        finally:
            os.chdir("..")
            prepare.remove_chern_project("demo_genfit_new")
            CHERN_CACHE.__init__()
