""" The helper class that is used to "operate" the project
    It is only used to "operate" things since all the information are stored in disk
    The core part may move to c language in the future
"""
import os
from ..utils import metadata
from ..utils import csys
from ..utils.message import Message
from .vdirectory import VDirectory
from .vobject import VObject
from . import helpme
from .chern_communicator import ChernCommunicator
from .impression_gc import ImpressionGC
from .impression_pack import ImpressionPack
from .impression_store import ImpressionStore
from .vimpression import VImpression


class VProject(VDirectory):
    """ operate the project
    """

    def helpme(self, command):
        """ get the help message"""
        message = Message()
        message.add(helpme.project_helpme.get(command, "No such command, try ``helpme'' alone."))
        return message

    def clean_impressions(self):
        """ Clean all the impressions of the project"""
        clean_confirmed = input("Are you sure to clean all the impressions? [y/n]")
        if clean_confirmed != "y":
            return
        sub_objects = self.sub_objects()
        for sub_object in sub_objects:
            VObject(sub_object.path).clean_impressions()
        csys.rm_tree(self.path+"/.celebi/impressions")

    def bookkeep(self):
        """
        Bookkeep files to the server
        Organizes the project structure and collects README.md
        and .celebi/config.json files for transmission.
        """
        all_objs = self.sub_objects_recursively()
        manifest = {"project_path": self.path, "objects": []}
        file_payload = {}

        for obj in all_objs:
            rel_path = os.path.relpath(obj.path, self.path)
            obj_record = {"path": rel_path, "files": []}

            # Paths to the specific files we want to pack
            target_files = {
                "readme": os.path.join(obj.path, "README.md"),
                "config": os.path.join(obj.path, ".celebi", "config.json")
            }

            for _, full_path in target_files.items():
                if os.path.exists(full_path):
                    # Create a unique key
                    storage_key = os.path.join(rel_path, os.path.basename(full_path))

                    # FIX: Use a context manager to read and CLOSE the file immediately
                    with open(full_path, "rb") as f:
                        file_payload[storage_key] = f.read()  # Store content, not the file object

                    obj_record["files"].append(storage_key)

            manifest["objects"].append(obj_record)

        # Check the size of file_payload
        total_size = sum(len(content) for content in file_payload.values())
        print(f"Total size of files to be sent: {total_size} bytes")

        # No need for the 'finally' loop to close files anymore
        cherncc = ChernCommunicator.instance()
        return cherncc.send_to_bookkeeping(manifest, file_payload)

    def bookkeep_url(self):
        """ Get the bookkeeping url"""
        cherncc = ChernCommunicator.instance()
        return cherncc.bkkview()

    def gc_impressions(self, grace_days: int = 14, dry_run: bool = True) -> Message:
        """Run CAS impression garbage collection."""
        message = Message()
        result = ImpressionGC(self.path).run(grace_days=grace_days, dry_run=dry_run)
        mode = "dry-run" if dry_run else "delete"
        message.add(f"Impression GC ({mode}) completed\n", "title0")
        message.add(
            f"Live hashes: {result['live_hashes']}, "
            f"unreachable: {result['unreachable_objects']}, "
            f"deleted: {result['deleted_objects']}, "
            f"freed bytes: {result['deleted_bytes']}",
            "info",
        )
        message.data.update(result)
        return message

    def pack_impressions(self, force: bool = False) -> Message:
        """Evaluate loose object packing thresholds for CAS impressions."""
        message = Message()
        result = ImpressionPack(self.path).maybe_pack(force=force)
        if result["should_pack"]:
            message.add(
                "Packing threshold reached. Packfile writing is not implemented yet.",
                "warning",
            )
        else:
            message.add("Loose object counts are below pack thresholds.", "info")
        message.data.update(result)
        return message

    @staticmethod
    def _prune_legacy_impression_payload(
        imp_path: str, dry_run: bool = False
    ) -> tuple[int, int]:
        """Remove legacy payload under an impression directory.

        Returns:
            Tuple[removed_contents_dirs, removed_packed_files]
        """
        removed_contents = 0
        removed_packed = 0

        contents_path = os.path.join(imp_path, "contents")
        if os.path.isdir(contents_path):
            removed_contents += 1
            if not dry_run:
                csys.rm_tree(contents_path)

        for name in os.listdir(imp_path):
            full_path = os.path.join(imp_path, name)
            if not os.path.isfile(full_path):
                continue
            if name.startswith("packed") and name.endswith(".tar.gz"):
                removed_packed += 1
                if not dry_run:
                    os.remove(full_path)

        return removed_contents, removed_packed

    def migrate_impressions(
        self, dry_run: bool = False, prune_legacy: bool = False
    ) -> Message:
        """Migrate legacy impression contents into CAS refs immediately."""
        message = Message()
        impressions_dir = os.path.join(self.path, ".celebi", "impressions")
        if not os.path.isdir(impressions_dir):
            message.add("No legacy .celebi/impressions directory found.", "warning")
            message.data.update({
                "processed": 0,
                "migrated": 0,
                "already_migrated": 0,
                "missing_contents": 0,
                "prune_legacy": prune_legacy,
                "pruned_contents_dirs": 0,
                "pruned_packed_files": 0,
                "dry_run": dry_run,
            })
            return message

        processed = 0
        migrated = 0
        already_migrated = 0
        missing_contents = 0
        pruned_contents_dirs = 0
        pruned_packed_files = 0

        cwd = os.getcwd()
        try:
            os.chdir(self.path)
            for uuid in sorted(os.listdir(impressions_dir)):
                imp_path = os.path.join(impressions_dir, uuid)
                if not os.path.isdir(imp_path):
                    continue
                processed += 1

                impression = VImpression(uuid)
                had_ref = impression.store.has_impression_ref(uuid)
                has_contents = os.path.isdir(os.path.join(imp_path, "contents"))

                if had_ref:
                    already_migrated += 1
                    if prune_legacy:
                        cleaned_contents, cleaned_packed = self._prune_legacy_impression_payload(
                            imp_path, dry_run=dry_run
                        )
                        pruned_contents_dirs += cleaned_contents
                        pruned_packed_files += cleaned_packed
                    continue
                if not has_contents:
                    missing_contents += 1
                    if prune_legacy:
                        cleaned_contents, cleaned_packed = self._prune_legacy_impression_payload(
                            imp_path, dry_run=dry_run
                        )
                        pruned_contents_dirs += cleaned_contents
                        pruned_packed_files += cleaned_packed
                    continue

                if not dry_run:
                    impression.is_zombie()  # Triggers lazy import for legacy contents
                migration_success = impression.store.has_impression_ref(uuid) or dry_run
                if migration_success:
                    migrated += 1
                    if prune_legacy:
                        cleaned_contents, cleaned_packed = self._prune_legacy_impression_payload(
                            imp_path, dry_run=dry_run
                        )
                        pruned_contents_dirs += cleaned_contents
                        pruned_packed_files += cleaned_packed
        finally:
            os.chdir(cwd)

        mode = "dry-run" if dry_run else "execute"
        message.add(f"Impression migration ({mode}) completed\n", "title0")
        message.add(
            f"Processed: {processed}, migrated: {migrated}, "
            f"already migrated: {already_migrated}, missing contents: {missing_contents}, "
            f"pruned contents dirs: {pruned_contents_dirs}, pruned packed files: "
            f"{pruned_packed_files}",
            "info",
        )
        message.data.update({
            "processed": processed,
            "migrated": migrated,
            "already_migrated": already_migrated,
            "missing_contents": missing_contents,
            "prune_legacy": prune_legacy,
            "pruned_contents_dirs": pruned_contents_dirs,
            "pruned_packed_files": pruned_packed_files,
            "dry_run": dry_run,
        })
        return message

    @staticmethod
    def _dir_size_bytes(path: str) -> int:
        """Return recursive file size in bytes for an existing directory."""
        if not os.path.isdir(path):
            return 0
        total = 0
        for root, _, files in os.walk(path):
            for name in files:
                full_path = os.path.join(root, name)
                if not os.path.isfile(full_path):
                    continue
                total += os.path.getsize(full_path)
        return total

    def stats_impressions(self) -> Message:
        """Report legacy/CAS impression storage usage and dedup indicators."""
        message = Message()
        legacy_root = os.path.join(self.path, ".celebi", "impressions")
        cas_root = os.path.join(self.path, ".celebi", "impressions_store")
        cas_ref_root = os.path.join(cas_root, "refs", "impressions")

        legacy_total_bytes = self._dir_size_bytes(legacy_root)
        legacy_payload_bytes = 0
        legacy_config_bytes = 0
        legacy_contents_dirs = 0
        legacy_packed_files = 0
        legacy_impression_dirs = 0

        if os.path.isdir(legacy_root):
            for uuid in os.listdir(legacy_root):
                imp_path = os.path.join(legacy_root, uuid)
                if not os.path.isdir(imp_path):
                    continue
                legacy_impression_dirs += 1
                contents_path = os.path.join(imp_path, "contents")
                if os.path.isdir(contents_path):
                    legacy_contents_dirs += 1
                    legacy_payload_bytes += self._dir_size_bytes(contents_path)
                for name in os.listdir(imp_path):
                    full_path = os.path.join(imp_path, name)
                    if not os.path.isfile(full_path):
                        continue
                    if name == "config.json":
                        legacy_config_bytes += os.path.getsize(full_path)
                    if name.startswith("packed") and name.endswith(".tar.gz"):
                        legacy_packed_files += 1
                        legacy_payload_bytes += os.path.getsize(full_path)

        cas_total_bytes = self._dir_size_bytes(cas_root)
        cas_stats = ImpressionStore(self.path).loose_object_stats()
        cas_ref_count = 0
        if os.path.isdir(cas_ref_root):
            cas_ref_count = len([n for n in os.listdir(cas_ref_root) if n.endswith(".json")])

        # Approximate dedup ratio: legacy payload bytes vs CAS object bytes.
        cas_object_bytes = cas_stats["total_size_bytes"]
        if legacy_payload_bytes > 0 and cas_object_bytes > 0:
            dedup_ratio = legacy_payload_bytes / cas_object_bytes
        else:
            dedup_ratio = 0.0

        message.add("Impression Storage Stats\n", "title0")
        message.add(
            f"Legacy impressions: dirs={legacy_impression_dirs}, "
            f"contents_dirs={legacy_contents_dirs}, packed_files={legacy_packed_files}\n",
            "info",
        )
        message.add(
            f"Legacy size: total={legacy_total_bytes} B, payload={legacy_payload_bytes} B, "
            f"config={legacy_config_bytes} B\n",
            "info",
        )
        message.add(
            f"CAS refs: {cas_ref_count}, objects: {cas_stats['total_count']} "
            f"(blobs={cas_stats['blob_count']}, trees={cas_stats['tree_count']})\n",
            "info",
        )
        message.add(
            f"CAS size: total={cas_total_bytes} B, objects={cas_object_bytes} B\n",
            "info",
        )
        message.add(f"Approx dedup ratio (legacy_payload/cas_objects): {dedup_ratio:.3f}\n", "info")

        message.data.update({
            "legacy_impression_dirs": legacy_impression_dirs,
            "legacy_contents_dirs": legacy_contents_dirs,
            "legacy_packed_files": legacy_packed_files,
            "legacy_total_bytes": legacy_total_bytes,
            "legacy_payload_bytes": legacy_payload_bytes,
            "legacy_config_bytes": legacy_config_bytes,
            "cas_ref_count": cas_ref_count,
            "cas_total_bytes": cas_total_bytes,
            "cas_object_bytes": cas_object_bytes,
            "cas_blob_count": cas_stats["blob_count"],
            "cas_tree_count": cas_stats["tree_count"],
            "cas_object_count": cas_stats["total_count"],
            "dedup_ratio": dedup_ratio,
        })
        return message

######################################
# Helper functions
def create_readme(project_path):
    """ Create the README.md and project.json file"""
    with open(project_path+"/.celebi/project.json", "w", encoding="utf-8"):
        pass
    with open(project_path + "/README.md", "w", encoding="utf-8") as f:
        f.write("")


def create_configfile(project_path, uuid):
    """ Create the config file"""
    config_file = metadata.ConfigFile(project_path+"/.celebi/config.json")
    config_file.write_variable("object_type", "project")
    config_file.write_variable("chern_version", "0.0.0")
    config_file.write_variable("project_uuid", uuid)


def create_hostsfile(project_path):
    """ Create the hosts file"""
    config_file = metadata.ConfigFile(project_path+"/.celebi/hosts.json")
    config_file.write_variable("serverurl", "127.0.0.1:3315")


######################################
# Functions:
def init_project():
    """ Create a new project from the existing folder
    """
    pwd = os.getcwd()
    if os.listdir(pwd) != []:
        raise Exception(f"[ERROR] Initialize on a unempty directory is not allowed {pwd}")
    project_name = pwd[pwd.rfind("/")+1:]
    print(f"The project name is ``{project_name}'', would you like to change it? [y/n]")
    change = input()
    if change == "y":
        project_name = input("Please input the project name: ")

    # Check the forbidden name
    forbidden_names = ["config", "new", "projects", "start", "", "."]

    def check_project_failed(forbidden_names):
        message = "The following project names are forbidden:"
        message += "\n    "
        for name in forbidden_names:
            message += name + ", "
        raise Exception(message)

    if project_name in forbidden_names:
        check_project_failed(forbidden_names)

    project_path = pwd
    uuid = csys.generate_uuid()
    os.mkdir(project_path+"/.celebi")
    create_readme(project_path)
    create_configfile(project_path, uuid)
    create_hostsfile(project_path)
    global_config_file = metadata.ConfigFile(csys.local_config_path())
    projects_path = global_config_file.read_variable("projects_path")
    if projects_path is None:
        projects_path = {}
    projects_path[project_name] = project_path
    global_config_file.write_variable("projects_path", projects_path)
    global_config_file.write_variable("current_project", project_name)
    os.chdir(project_path)


def use_project(path):
    """ Use an exsiting project
    """
    path = os.path.abspath(path)
    print(path)
    project_name = path[path.rfind("/")+1:]
    print(f"The project name is ``{project_name}'', would you like to change it? [y/n]")
    change = input()
    if change == "y":
        project_name = input("Please input the project name ")

    # Check the forbidden name
    forbidden_names = ["config", "new", "projects", "start", "", "."]
    def check_project_failed(forbidden_names):
        message = "The following project names are forbidden:"
        message += "\n    "
        for name in forbidden_names:
            message += name + ", "
        raise Exception(message)
    if project_name in forbidden_names:
        check_project_failed(forbidden_names)

    project_path = path
    config_file = metadata.ConfigFile(project_path+"/.celebi/config.json")
    object_type = config_file.read_variable("object_type", "")
    if object_type != "project":
        print("The path is not a project")
        return
    print("The project type is ", object_type)
    os.chdir(path)
    global_config_file = metadata.ConfigFile(csys.local_config_path())
    projects_path = global_config_file.read_variable("projects_path", {})
    projects_path[project_name] = project_path
    global_config_file.write_variable("projects_path", projects_path)
    global_config_file.write_variable("current_project", project_name)
    os.chdir(project_path)
