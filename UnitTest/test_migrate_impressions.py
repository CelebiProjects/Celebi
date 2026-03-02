import json
import os
import shutil
import tempfile
import unittest

from CelebiChrono.kernel.vproject import VProject
from CelebiChrono.kernel.impression_store import ImpressionStore


class TestMigrateImpressions(unittest.TestCase):
    def setUp(self):
        self.project_dir = tempfile.mkdtemp(prefix="celebi_migrate_test_")
        os.makedirs(os.path.join(self.project_dir, ".celebi"), exist_ok=True)
        with open(os.path.join(self.project_dir, ".celebi", "project.json"), "w", encoding="utf-8"):
            pass
        with open(os.path.join(self.project_dir, ".celebi", "config.json"), "w", encoding="utf-8") as f:
            json.dump({"object_type": "project", "project_uuid": "test-project"}, f)

        self.uuid = "aaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaa"
        self.imp_dir = os.path.join(self.project_dir, ".celebi", "impressions", self.uuid)
        os.makedirs(os.path.join(self.imp_dir, "contents"), exist_ok=True)

        with open(os.path.join(self.imp_dir, "contents", "celebi.yaml"), "w", encoding="utf-8") as f:
            f.write("descriptor: demo\n")
        with open(os.path.join(self.imp_dir, "config.json"), "w", encoding="utf-8") as f:
            json.dump({
                "object_type": "algorithm",
                "tree": [[".", [], ["celebi.yaml"]]],
                "dependencies": [],
                "parents": [],
                "current_path": "Fit",
            }, f)
        with open(os.path.join(self.imp_dir, f"packed{self.uuid}.tar.gz"), "wb") as f:
            f.write(b"legacy")

    def tearDown(self):
        shutil.rmtree(self.project_dir)

    def test_migrate_with_prune_legacy(self):
        project = VProject(self.project_dir)

        dry_result = project.migrate_impressions(dry_run=True, prune_legacy=True)
        self.assertEqual(dry_result.data["processed"], 1)
        self.assertEqual(dry_result.data["migrated"], 1)
        self.assertEqual(dry_result.data["pruned_contents_dirs"], 1)
        self.assertEqual(dry_result.data["pruned_packed_files"], 1)
        self.assertTrue(os.path.isdir(os.path.join(self.imp_dir, "contents")))
        self.assertTrue(os.path.exists(os.path.join(self.imp_dir, f"packed{self.uuid}.tar.gz")))

        exec_result = project.migrate_impressions(dry_run=False, prune_legacy=True)
        self.assertEqual(exec_result.data["processed"], 1)
        self.assertEqual(exec_result.data["migrated"], 1)
        self.assertEqual(exec_result.data["pruned_contents_dirs"], 1)
        self.assertEqual(exec_result.data["pruned_packed_files"], 1)

        self.assertFalse(os.path.isdir(os.path.join(self.imp_dir, "contents")))
        self.assertFalse(os.path.exists(os.path.join(self.imp_dir, f"packed{self.uuid}.tar.gz")))

        store = ImpressionStore(self.project_dir)
        self.assertTrue(store.has_impression_ref(self.uuid))


if __name__ == "__main__":
    unittest.main()
