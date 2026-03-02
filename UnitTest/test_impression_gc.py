import os
import shutil
import tempfile
import unittest

from CelebiChrono.kernel.impression_gc import ImpressionGC
from CelebiChrono.kernel.impression_store import ImpressionStore


class TestImpressionGC(unittest.TestCase):
    def setUp(self):
        self.temp_dir = tempfile.mkdtemp(prefix="celebi_gc_test_")
        os.makedirs(os.path.join(self.temp_dir, ".celebi"), exist_ok=True)
        self.store = ImpressionStore(self.temp_dir)

    def tearDown(self):
        shutil.rmtree(self.temp_dir)

    def test_gc_keeps_reachable_and_deletes_unreachable(self):
        reachable_blob = self.store.put_blob(b"reachable")
        unreachable_blob = self.store.put_blob(b"unreachable")

        root_tree = self.store.put_tree([
            {"path": "a.txt", "type": "blob", "hash": reachable_blob, "size": 9}
        ])
        self.store.write_impression_ref("imp-live", {"root_tree": root_tree})

        dry = ImpressionGC(self.temp_dir).run(grace_days=0, dry_run=True)
        self.assertGreaterEqual(dry["unreachable_objects"], 1)
        self.assertEqual(dry["deleted_objects"], 0)

        real = ImpressionGC(self.temp_dir).run(grace_days=0, dry_run=False)
        self.assertGreaterEqual(real["deleted_objects"], 1)

        self.assertTrue(os.path.exists(self.store._blob_path(reachable_blob)))
        self.assertFalse(os.path.exists(self.store._blob_path(unreachable_blob)))


if __name__ == "__main__":
    unittest.main()
