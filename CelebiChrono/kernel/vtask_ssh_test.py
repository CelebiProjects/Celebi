""" SshTestMixin for VTask: run the task's algorithm commands on an ssh runner.

The connection details (host/user/key) are fetched from the DITE server, then
the client connects directly over SSH and streams the output. No impression
is created.
"""
import os
import shlex
import shutil
import tarfile
from datetime import datetime

from ..utils.message import Message
from ..utils.ssh_runner import SshRunner, sanitized_env_prefix
from .chern_communicator import ChernCommunicator
from .vtask_core import Core


class SshTestMixin(Core):
    """SSH test execution for tasks."""

    def ssh_test(self, runner: str = "") -> Message:  # pylint: disable=too-many-locals,too-many-statements,too-many-branches,too-many-return-statements
        """Run the task's algorithm commands on a registered ssh runner."""
        cherncc = ChernCommunicator.instance()
        if cherncc.dite_status() != "connected":
            msg = Message()
            msg.add("DITE is not connected. Please check the connection.", "warning")
            return msg

        ssh_config = cherncc.runner_ssh_config(runner,
                                               environment=self.environment())
        if ssh_config is None:
            msg = Message()
            msg.add(f"Runner '{runner}' not found on the DITE server.", "warning")
            return msg
        if not ssh_config.get("host") or not ssh_config.get("user"):
            msg = Message()
            msg.add(f"Runner '{runner}' has no ssh host or user configured.",
                    "warning")
            return msg

        remote_workdir = ssh_config.get("remote_workdir", "/tmp/yuki-workflows")
        timestamp = datetime.now().strftime("%Y%m%d-%H%M%S")
        remote_test_dir = f"{remote_workdir}/tests/{timestamp}"

        commands = " && ".join(self._test_commands())
        command = f"mkdir -p stageout && {commands}"
        conda_env = ssh_config.get("conda_env", "")
        if conda_env:
            print(f"Activating conda environment '{conda_env}' on the runner...")
            command = (f"conda run --no-capture-output -n {shlex.quote(conda_env)} "
                       f"-- bash -c {shlex.quote(command)}")
        print(f"Final command to execute on remote: {command}")

        ssh = SshRunner(host=ssh_config["host"], user=ssh_config["user"],
                        port=ssh_config.get("port", 22),
                        key_content=ssh_config.get("key", ""),
                        key_path=ssh_config.get("key_path", ""))
        msg = Message()
        uploaded = False
        try:
            ssh.connect()
            # Inputs already cached on the runner (runner-side impressions)
            # are symlinked there instead of being downloaded and packed.
            cached_impressions = set()
            for pre in self.inputs():
                impression = pre.impression()
                if impression and self._impression_cached_on_runner(
                        ssh, ssh_config, self.project_uuid(), impression.uuid):
                    cached_impressions.add(impression.uuid)
                    print(f"Using runner cache for {pre}")

            print("Preparing test workdir...")
            success, mount_config = self.pre_docker_test(
                skip_impressions=cached_impressions)
            if not success:
                msg = Message()
                msg.add(f"Pre-test preparation failed: {mount_config}", "warning")
                return msg

            cached_mounts = [mount for mount in mount_config["mounts"]
                             if mount.get("impression") in cached_impressions]
            skip_sources = {mount["source"] for mount in cached_mounts}

            stage_dir = self._create_workaround_dir(prefix="chernsshtest_")
            tar_path = self._package_test_workdir(mount_config, stage_dir,
                                                  skip_sources=skip_sources)

            print("Uploading test workdir to the runner...")
            ssh.put_tar(tar_path, remote_test_dir)
            uploaded = True
            if cached_mounts:
                print("Linking cached inputs on the runner...")
                code = ssh.exec_stream(
                    self._cached_input_link_command(
                        cached_mounts, ssh_config, self.project_uuid(),
                        remote_test_dir))
                if code:
                    msg.add("Failed to link cached inputs on the runner.",
                            "error")
                    return msg
            # Deterministic remote environment: ignore the submitter's shell
            # configuration so the run never inherits it.
            conda_base = ssh.conda_base_dir()
            prefix = sanitized_env_prefix(conda_base)
            if conda_env and conda_base:
                ok, resolved = self._verify_conda_env(ssh, conda_env, conda_base)
                if not ok:
                    msg.add(
                        f"conda environment '{conda_env}' is not usable on the "
                        f"runner (no python found at {resolved}). Recreate it, "
                        f"e.g.: conda create -n {conda_env} "
                        f"-c conda-forge root python",
                        "error")
                    return msg
            command = prefix + command
            code = ssh.exec_stream(command, cwd=remote_test_dir, on_line=print)
            msg.add(f"Remote test exited with code {code}.",
                    "info" if not code else "error")
        except (OSError, RuntimeError, ValueError) as e:
            msg.add(f"SSH test failed: {e}", "error")
        finally:
            ssh.close()
        if uploaded:
            msg.add(f"Remote workdir kept at {ssh_config['host']}:{remote_test_dir}",
                    "info")
        return msg

    def check_results(self, runner: str = "") -> Message:  # pylint: disable=too-many-return-statements
        """Mount the impression's cached results into a check dir on an ssh
        runner.

        Each cache entry is symlinked individually into a fresh timestamped
        check dir under ``<remote_workdir>/tests/check/``, so diagnosing the
        results never modifies the cache itself.
        """
        impression = self.impression()
        if impression is None:
            msg = Message()
            msg.add("Current object has no impression — impress it first.",
                    "error")
            return msg

        cherncc = ChernCommunicator.instance()
        if cherncc.dite_status() != "connected":
            msg = Message()
            msg.add("DITE is not connected. Please check the connection.",
                    "warning")
            return msg

        ssh_config = cherncc.runner_ssh_config(runner,
                                               environment=self.environment())
        if ssh_config is None:
            msg = Message()
            msg.add(f"Runner '{runner}' not found on the DITE server.",
                    "warning")
            return msg
        if not ssh_config.get("host") or not ssh_config.get("user"):
            msg = Message()
            msg.add(f"Runner '{runner}' has no ssh host or user configured.",
                    "warning")
            return msg

        base = ssh_config.get("remote_workdir", "/tmp/yuki-workflows")
        cache_dir = f"{base}/impressions/{self.project_uuid()}/{impression.uuid}"

        ssh = SshRunner(host=ssh_config["host"], user=ssh_config["user"],
                        port=ssh_config.get("port", 22),
                        key_content=ssh_config.get("key", ""),
                        key_path=ssh_config.get("key_path", ""))
        msg = Message()
        try:
            ssh.connect()
            timestamp = datetime.now().strftime("%Y%m%d-%H%M%S")
            check_dir = f"{base}/tests/check/{timestamp}"
            # One round trip covers both the cached check and the linking:
            # each remote exec costs seconds of shell startup overhead.
            # Exit code 3 means the impression is not cached on the runner.
            command = (
                f"test -d {shlex.quote(cache_dir)} || exit 3; "
                f"mkdir -p {shlex.quote(check_dir)} && "
                f"for f in {shlex.quote(cache_dir)}/*; do "
                f"[ -e \"$f\" ] || [ -L \"$f\" ] || continue; "
                f"ln -s \"$f\" {shlex.quote(check_dir)}/; done")
            print(f"Final command to execute on remote: {command}")
            code = ssh.exec_stream(command)
            if code == 3:
                msg.add(f"Impression '{impression.uuid}' is not cached on "
                        f"runner '{runner}' — run cache-results {runner} "
                        f"first.", "error")
                return msg
            if code:
                msg.add(f"Remote link exited with code {code}.", "error")
                return msg
            msg.add(f"Results mounted at {ssh_config['host']}:{check_dir}\n",
                    "success")
            msg.add("Each entry is a symlink into the runner cache.\n",
                    "info")
        except (OSError, RuntimeError, ValueError) as e:
            msg.add(f"Check results failed: {e}", "error")
        finally:
            ssh.close()
        return msg

    @staticmethod
    def _impression_cached_on_runner(ssh, ssh_config, project_uuid, impression):
        """True when the impression lives in the runner-side cache."""
        base = ssh_config.get("remote_workdir", "/tmp/yuki-workflows")
        cache_dir = f"{base}/impressions/{project_uuid}/{impression}"
        code = ssh.exec_stream(f"test -d {shlex.quote(cache_dir)}")
        return not code

    @staticmethod
    def _cached_input_link_command(cached_mounts, ssh_config, project_uuid,
                                   remote_test_dir):
        """Build one remote command linking cached impressions into the test dir.

        The runner cache holds files directly under
        ``<remote_workdir>/impressions/<project>/<impression>/``, while the
        docker layout exposes them at ``<alias>/stageout/`` — hence the
        stageout symlink.
        """
        base = ssh_config.get("remote_workdir", "/tmp/yuki-workflows")
        parts = []
        for mount in cached_mounts:
            target = mount["target"]
            rel = target[len("/workspace/"):] if target.startswith("/workspace/") \
                else target.lstrip("/")
            cache_dir = (f"{base}/impressions/{project_uuid}/"
                         f"{mount['impression']}")
            parts.append(
                f"mkdir -p {shlex.quote(f'{remote_test_dir}/{rel}')} && "
                f"ln -s {shlex.quote(cache_dir)} "
                f"{shlex.quote(f'{remote_test_dir}/{rel}/stageout')}")
        return " && ".join(parts)

    @staticmethod
    def _verify_conda_env(ssh, conda_env, conda_base):
        """Check that the conda env actually provides python.

        ``conda run`` strips the calling conda's base from the child PATH,
        so a broken env (no bin/python) silently falls back to the system
        python. A cheap existence check of the env's own python catches
        exactly that.

        Returns (ok, resolved_python_path).
        """
        resolved = f"{conda_base}/envs/{conda_env}/bin/python"
        code = ssh.exec_stream(f"test -x {shlex.quote(resolved)}")
        return not code, resolved

    @staticmethod
    def _package_test_workdir(mount_config, stage_dir, skip_sources=()):
        """Copy the docker mount sources into one tree and tar it.

        Sources listed in ``skip_sources`` are left out (they are linked
        remotely instead). Returns the path of the created tar.gz.
        """
        skip_sources = set(skip_sources)
        shutil.copytree(mount_config["base_dir"], stage_dir, dirs_exist_ok=True)
        for mount in mount_config["mounts"]:
            if mount["source"] in skip_sources:
                continue
            target = mount["target"]
            rel = target[len("/workspace/"):] if target.startswith("/workspace/") \
                else target.lstrip("/")
            shutil.copytree(mount["source"],
                            os.path.join(stage_dir, rel),
                            dirs_exist_ok=True)
        tar_path = stage_dir + ".tar.gz"
        with tarfile.open(tar_path, "w:gz") as tar:
            for entry in sorted(os.listdir(stage_dir)):
                tar.add(os.path.join(stage_dir, entry), arcname=entry)
        return tar_path
