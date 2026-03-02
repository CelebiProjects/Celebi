"""Helper class for impression operations."""
import hashlib
import os
import tempfile
from logging import getLogger
from os.path import join
from typing import TYPE_CHECKING, Any, List, Optional

from ..utils import csys
from ..utils import metadata
from .impression_materializer import ImpressionMaterializer
from .impression_store import ImpressionStore

if TYPE_CHECKING:
    from .vobject import VObject

logger = getLogger("ChernLogger")


class VImpression:
    """A class to represent an impression."""

    uuid: Optional[str] = None

    def __init__(self, uuid: Optional[str] = None) -> None:
        if uuid is None:
            self.uuid = ""
        else:
            self.uuid = str(uuid)

        self.project_root = csys.project_path()
        base_path = self.project_root if self.project_root else "."
        self.path = base_path + "/.celebi/impressions/" + self.uuid
        self.config_file = metadata.ConfigFile(self.path + "/config.json")
        self.tarfile = self.path + "/packed" + self.uuid + ".tar.gz"
        self.store = ImpressionStore(self.project_root or os.getcwd())
        self._materializer = ImpressionMaterializer(self.project_root or os.getcwd())
        self._materialized_contents: Optional[str] = None

    def __str__(self) -> str:
        return self.uuid

    def short_uuid(self) -> str:
        return self.uuid[:7]

    def is_cas_backed(self) -> bool:
        backend = self.config_file.read_variable("storage_backend", "")
        if backend == "cas":
            return True
        ref = self.store.read_impression_ref(self.uuid)
        return ref is not None

    def has_contents_dir(self) -> bool:
        return csys.exists(os.path.join(self.path, "contents"))

    def _import_legacy_contents_to_cas(self) -> None:
        """Lazy migration: import legacy contents into CAS and write impression ref."""
        if self.store.has_impression_ref(self.uuid):
            return
        legacy_contents = os.path.join(self.path, "contents")
        if not csys.exists(legacy_contents):
            return

        entries = []
        for rel_path in sorted(csys.get_files_in_directory(legacy_contents)):
            abs_path = os.path.join(legacy_contents, rel_path)
            with open(abs_path, "rb") as f:
                content = f.read()
            blob_hash = self.store.put_blob(content)
            entries.append({
                "path": rel_path,
                "type": "blob",
                "hash": blob_hash,
                "size": len(content),
            })
        root_tree = self.store.put_tree(entries)

        self.config_file.write_variable("storage_backend", "cas")
        self.config_file.write_variable("root_tree", root_tree)
        self.store.write_impression_ref(
            self.uuid,
            {
                "object_type": self.config_file.read_variable("object_type", ""),
                "tree": self.config_file.read_variable("tree", []),
                "dependencies": self.config_file.read_variable("dependencies", []),
                "current_path": self.config_file.read_variable("current_path", ""),
                "alias_to_impression": self.config_file.read_variable("alias_to_impression", {}),
                "parents": self.config_file.read_variable("parents", []),
                "storage_backend": "cas",
                "root_tree": root_tree,
            },
        )

    def is_zombie(self) -> bool:
        if not self.uuid:
            return True
        self._import_legacy_contents_to_cas()
        if self.store.has_impression_ref(self.uuid):
            return False
        if csys.exists(os.path.join(self.path, "contents")):
            return False
        return True

    def is_packed(self) -> bool:
        return csys.exists(self.tarfile)

    def materialize_contents(self, target_dir: Optional[str] = None) -> str:
        """Return a local directory that contains this impression's content tree."""
        legacy_contents = os.path.join(self.path, "contents")
        if csys.exists(legacy_contents):
            self._import_legacy_contents_to_cas()
            return legacy_contents

        if target_dir:
            self._materializer.materialize_impression(self.uuid, target_dir)
            return target_dir

        if self._materialized_contents and csys.exists(self._materialized_contents):
            return self._materialized_contents

        self._materialized_contents = tempfile.mkdtemp(prefix=f"celebi_imp_{self.uuid[:8]}_")
        self._materializer.materialize_impression(self.uuid, self._materialized_contents)
        return self._materialized_contents

    def ensure_tarfile(self) -> str:
        """Make sure tarfile exists and return path."""
        self.pack()
        return self.tarfile

    def pack(self) -> None:
        if self.is_packed():
            return
        csys.mkdir(self.path)
        source_dir = self.materialize_contents()
        output_name = os.path.join(self.path, "packed" + self.uuid)
        csys.make_archive(output_name, source_dir)

    def clean(self) -> None:
        contents_path = os.path.join(self.path, "contents")
        if csys.exists(contents_path):
            csys.rm_tree(contents_path)
        if self._materialized_contents and csys.exists(self._materialized_contents):
            csys.rm_tree(self._materialized_contents)
            self._materialized_contents = None

    def upack(self) -> None:
        # FIXME: to be implemented
        return

    def difference(self) -> Any:
        # FIXME: to be implemented
        return None

    def _read_ref_metadata(self) -> dict:
        ref = self.store.read_impression_ref(self.uuid)
        if ref is None:
            return {}
        return ref

    def read_metadata(self, key: str, default: Any = None) -> Any:
        value = self.config_file.read_variable(key, default)
        if value != default:
            return value
        ref = self._read_ref_metadata()
        if key in ref:
            return ref[key]
        return value

    def tree(self) -> Any:
        return self.read_metadata("tree", [])

    def parents(self) -> List[str]:
        return self.read_metadata("parents", [])

    def parent(self) -> Optional[str]:
        parents = self.parents()
        if parents:
            return parents[-1]
        return None

    def pred_impressions(self) -> List["VImpression"]:
        dependencies_uuid = self.read_metadata("dependencies", [])
        dependencies = [VImpression(uuid) for uuid in dependencies_uuid]
        return dependencies

    def object_type(self) -> str:
        return self.read_metadata("object_type", "")

    def get_descriptor(self) -> str:
        yaml_paths = [
            os.path.join(self.path, "contents", "celebi.yaml"),
            os.path.join(self.path, "contents", ".", "celebi.yaml"),
        ]
        for yaml_path in yaml_paths:
            if not csys.exists(yaml_path):
                continue
            yaml_file = metadata.YamlFile(yaml_path)
            descriptor = yaml_file.read_variable("descriptor", "")
            if descriptor:
                return descriptor

        if self.store.has_impression_ref(self.uuid):
            try:
                contents_root = self.materialize_contents()
                cas_yaml = os.path.join(contents_root, "celebi.yaml")
                if csys.exists(cas_yaml):
                    yaml_file = metadata.YamlFile(cas_yaml)
                    descriptor = yaml_file.read_variable("descriptor", "")
                    if descriptor:
                        return descriptor
            except FileNotFoundError:
                pass

        current_path = self.read_metadata("current_path", "")
        if current_path:
            return os.path.basename(os.path.normpath(current_path))
        return self.short_uuid()

    def has_alias(self, alias: str) -> bool:
        alias_to_imp = self.read_metadata("alias_to_impression", {})
        return alias in alias_to_imp

    def alias_to_impression_uuid(self, alias: str) -> str:
        alias_to_imp = self.read_metadata("alias_to_impression", {})
        return alias_to_imp.get(alias, "")

    def _build_cas_tree(self, obj: "VObject", file_list: List[List[Any]]) -> str:
        entries = []
        for dirpath, _, filenames in file_list:
            for filename in filenames:
                rel_path = filename if dirpath == "." else os.path.join(dirpath, filename)
                file_path = os.path.join(obj.path, rel_path)
                with open(file_path, "rb") as f:
                    content = f.read()
                blob_hash = self.store.put_blob(content)
                entries.append({
                    "path": rel_path,
                    "type": "blob",
                    "hash": blob_hash,
                    "size": len(content),
                })
        entries = sorted(entries, key=lambda x: x["path"])
        return self.store.put_tree(entries)

    def create(self, obj: "VObject") -> None:
        """Create this impression from a VObject file tree."""
        file_list = csys.tree_excluded(obj.path)
        dependencies = obj.pred_impressions()
        dependencies_uuid = [dep.uuid for dep in dependencies]

        self.config_file.write_variable("object_type", obj.object_type())
        self.config_file.write_variable("tree", file_list)
        self.config_file.write_variable("dependencies", dependencies_uuid)
        self.config_file.write_variable("current_path", obj.invariant_path())

        alias_to_imp = {}
        if obj.is_task_or_algorithm():
            alias_to_path = obj.config_file.read_variable("alias_to_path", {})
            for alias, path in alias_to_path.items():  # pylint: disable=unused-variable
                alias_to_imp[alias] = obj.alias_to_impression(alias).uuid
            self.config_file.write_variable("alias_to_impression", alias_to_imp)

        parent_impression = obj.impression()
        if parent_impression is None:
            parents = []
        else:
            parents = list(parent_impression.parents())
            if parent_impression.uuid and parent_impression.uuid != self.uuid:
                parents.append(parent_impression.uuid)
            # Keep order, remove duplicates to avoid repeated history entries.
            parents = list(dict.fromkeys(parents))
            if parent_impression.is_zombie():
                parent_impression.clean()
        self.config_file.write_variable("parents", parents)

        root_tree = self._build_cas_tree(obj, file_list)
        self.config_file.write_variable("storage_backend", "cas")
        self.config_file.write_variable("root_tree", root_tree)

        self.store.write_impression_ref(
            self.uuid,
            {
                "object_type": obj.object_type(),
                "tree": file_list,
                "dependencies": dependencies_uuid,
                "current_path": obj.invariant_path(),
                "alias_to_impression": alias_to_imp,
                "parents": parents,
                "storage_backend": "cas",
                "root_tree": root_tree,
            },
        )

    def update_uuid(self, obj: "VObject") -> str:
        dependencies = obj.pred_impressions()
        dependencies_uuid = [dep.uuid for dep in dependencies]
        new_uuid = self.generate_imp_uuid(obj.project_uuid(), obj.path, dependencies_uuid)
        self.uuid = new_uuid
        self.project_root = csys.project_path()
        base_path = self.project_root if self.project_root else "."
        self.path = base_path + "/.celebi/impressions/" + self.uuid
        self.config_file = metadata.ConfigFile(self.path + "/config.json")
        self.tarfile = self.path + "/packed" + self.uuid + ".tar.gz"
        self.store = ImpressionStore(self.project_root or os.getcwd())
        self._materializer = ImpressionMaterializer(self.project_root or os.getcwd())
        self._materialized_contents = None
        return new_uuid

    def generate_imp_uuid(
        self,
        project_uuid: str,
        directory_path: str,
        dependency_uuids: List[str],
    ) -> str:
        hasher = hashlib.md5()
        hasher.update(project_uuid.encode("utf-8"))
        for dep_uuid in sorted(dependency_uuids):
            hasher.update(dep_uuid.encode("utf-8"))

        for root, dirs, files in os.walk(directory_path):
            dirs.sort()
            files.sort()
            dirs[:] = [d for d in dirs if not (d.startswith(".") or d.startswith("__"))]

            for file_name in files:
                if file_name == "README.md":
                    continue
                if file_name.startswith(".") or file_name.startswith("__"):
                    continue

                file_path = os.path.join(root, file_name)
                rel_path = os.path.relpath(file_path, directory_path)
                hasher.update(rel_path.encode("utf-8"))
                try:
                    with open(file_path, "rb") as f:
                        while chunk := f.read(8192):
                            hasher.update(chunk)
                except (IOError, OSError):
                    pass

        return hasher.hexdigest()
