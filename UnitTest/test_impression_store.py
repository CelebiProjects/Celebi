import os
import shutil
import tempfile
import unittest

from CelebiChrono.kernel.impression_materializer import ImpressionMaterializer
from CelebiChrono.kernel.impression_store import ImpressionStore


class TestImpressionStore(unittest.TestCase):
    def setUp(self):
        self.temp_dir = tempfile.mkdtemp(prefix="celebi_store_test_")
        os.makedirs(os.path.join(self.temp_dir, ".celebi"), exist_ok=True)
        self.store = ImpressionStore(self.temp_dir)

    def tearDown(self):
        shutil.rmtree(self.temp_dir)

    def test_blob_dedup(self):
        h1 = self.store.put_blob(b"same-data")
        h2 = self.store.put_blob(b"same-data")
        self.assertEqual(h1, h2)
        self.assertEqual(self.store.get_blob(h1), b"same-data")

    def test_tree_deterministic_hash(self):
        tree1 = [
            {"path": "b.txt", "type": "blob", "hash": "2", "size": 1},
            {"path": "a.txt", "type": "blob", "hash": "1", "size": 1},
        ]
        tree2 = [
            {"path": "b.txt", "type": "blob", "hash": "2", "size": 1},
            {"path": "a.txt", "type": "blob", "hash": "1", "size": 1},
        ]
        t1 = self.store.put_tree(tree1)
        t2 = self.store.put_tree(tree2)
        self.assertEqual(t1, t2)

    def test_ref_write_read_and_materialize(self):
        blob_hash = self.store.put_blob(b"hello")
        root_tree = self.store.put_tree([
            {"path": "dir/file.txt", "type": "blob", "hash": blob_hash, "size": 5}
        ])
        self.store.write_impression_ref("imp1", {"root_tree": root_tree})

        ref = self.store.read_impression_ref("imp1")
        self.assertEqual(ref["root_tree"], root_tree)

        out_dir = os.path.join(self.temp_dir, "materialized")
        mat = ImpressionMaterializer(self.temp_dir)
        mat.materialize_impression("imp1", out_dir)
        with open(os.path.join(out_dir, "dir", "file.txt"), "rb") as f:
            self.assertEqual(f.read(), b"hello")


if __name__ == "__main__":
    unittest.main()
