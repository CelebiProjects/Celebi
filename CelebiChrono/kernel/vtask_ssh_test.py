""" SshTestMixin for VTask: run the task's algorithm commands on an ssh runner.

The connection details (host/user/key) are fetched from the DITE server, then
the client connects directly over SSH and streams the output. No impression
is created.
"""
import os
import shlex
import shutil
import tarfile
import time
from datetime import datetime

from ..utils.message import Message
from ..utils.ssh_runner import SshRunner, sanitized_env_prefix
from .chern_communicator import ChernCommunicator
from .vtask_core import Core


class SshTestMixin(Core):
    """SSH test execution for tasks."""

    def ssh_test(self, runner: str = "") -> Message:  # pylint: disable=too-many-locals,too-many-statements,too-many-branches,too-many-return-statements
        """Run the task's algorithm commands on a registered ssh runner."""
        def _log(label: str, t0: float = None) -> None:
            now = time.strftime("%Y-%m-%d %H:%M:%S")
            elapsed = f" [+{time.time() - t0:.2f}s]" if t0 is not None else ""
            print(f"[ssh_test:{runner or 'none'}] {now} {label}{elapsed}")

        t_start = time.time()
        _log("start")
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

        _log("ssh config fetched", t_start)

        remote_workdir = ssh_config.get("remote_workdir", "/tmp/yuki-workflows")
        timestamp = datetime.now().strftime("%Y%m%d-%H%M%S")
        remote_test_dir = f"{remote_workdir}/tests/{timestamp}"

        commands = " && ".join(self._test_commands())
        command = (f'mkdir -p stageout && '
                   f'echo -e "=== start running ===\\n" && '
                   f'{commands}')
        conda_env = ssh_config.get("conda_env", "")
        if conda_env:
            print(f"Activating conda environment '{conda_env}' on the runner...")
            command = (f"conda run --no-capture-output -n {shlex.quote(conda_env)} "
                       f"-- bash -c {shlex.quote(command)}")
        _log("command built", t_start)
        print(f"Final command to execute on remote: {command}")

        _log("initializing ssh runner", t_start)

        ssh = SshRunner(host=ssh_config["host"], user=ssh_config["user"],
                        port=ssh_config.get("port", 22),
                        key_content=ssh_config.get("key", ""),
                        key_path=ssh_config.get("key_path", ""))
        msg = Message()
        uploaded = False
        try:
            _log("connecting ssh...", t_start)
            ssh.connect()
            _log("ssh connected", t_start)
            # Inputs already cached on the runner (runner-side impressions)
            # are symlinked there instead of being downloaded and packed.
            _log("resolving inputs...", t_start)
            inputs = list(self.inputs())
            impression_uuids = [pre.impression().uuid for pre in inputs
                                if pre.impression()]
            cached_impressions = set()
            if impression_uuids:
                _log(f"checking {len(impression_uuids)} cached impressions on runner...",
                     t_start)
                cached_impressions = self._cached_impressions_on_runner(
                    ssh, ssh_config, self.project_uuid(), impression_uuids)
                _log(f"found {len(cached_impressions)} cached impressions", t_start)
            for pre in inputs:
                impression = pre.impression()
                if impression and impression.uuid in cached_impressions:
                    print(f"Using runner cache for {pre}")

            _log("preparing test workdir...", t_start)
            success, mount_config = self.pre_docker_test(
                skip_impressions=cached_impressions)
            if not success:
                msg = Message()
                msg.add(f"Pre-test preparation failed: {mount_config}", "warning")
                return msg
            _log("test workdir prepared", t_start)

            cached_mounts = [mount for mount in mount_config["mounts"]
                             if mount.get("impression") in cached_impressions]
            skip_sources = {mount["source"] for mount in cached_mounts}

            stage_dir = self._create_workaround_dir(prefix="chernsshtest_")
            _log("packaging test workdir...", t_start)
            tar_path = self._package_test_workdir(mount_config, stage_dir,
                                                  skip_sources=skip_sources)
            _log(f"test workdir packaged: {tar_path}", t_start)

            _log("uploading tar to runner...", t_start)
            ssh.put_tar(tar_path, remote_test_dir)
            uploaded = True
            _log("tar uploaded", t_start)
            if cached_mounts:
                _log("linking cached inputs on runner...", t_start)
                code = ssh.exec_stream(
                    self._cached_input_link_command(
                        cached_mounts, ssh_config, self.project_uuid(),
                        remote_test_dir))
                if code:
                    msg.add("Failed to link cached inputs on the runner.",
                            "error")
                    return msg
                _log("cached inputs linked", t_start)
            # Deterministic remote environment: ignore the submitter's shell
            # configuration so the run never inherits it. One round trip
            # resolves the conda base and verifies the env's own python.
            conda_base = ""
            if conda_env:
                _log("probing conda environment...", t_start)
                conda_base, ok, resolved = self._conda_probe(ssh, conda_env)
                if not ok:
                    msg.add(
                        f"conda environment '{conda_env}' is not usable on the "
                        f"runner (no python found at {resolved}). Recreate it, "
                        f"e.g.: conda create -n {conda_env} "
                        f"-c conda-forge root python",
                        "error")
                    return msg
                _log("conda probe ok", t_start)
            else:
                _log("resolving conda base dir...", t_start)
                conda_base = ssh.conda_base_dir()
                _log(f"conda base dir: {conda_base!r}", t_start)
            prefix = sanitized_env_prefix(conda_base)
            command = prefix + command
            _log("executing test command...", t_start)
            code = ssh.exec_stream(command, cwd=remote_test_dir, on_line=print)
            _log("test command finished", t_start)
            msg.add(f"Remote test exited with code {code}.",
                    "info" if not code else "error")
        except (OSError, RuntimeError, ValueError) as e:
            msg.add(f"SSH test failed: {e}", "error")
        finally:
            _log("closing ssh...", t_start)
            ssh.close()
            _log("ssh closed", t_start)
        if uploaded:
            msg.add(f"Remote workdir kept at {ssh_config['host']}:{remote_test_dir}",
                    "info")
        _log("finished", t_start)
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
    def _cached_impressions_on_runner(ssh, ssh_config, project_uuid,
                                      impressions):
        """Return the impressions present in the runner-side cache.

        One remote round trip checks every cache dir at once: each existing
        dir is echoed back and parsed on the client.
        """
        if not impressions:
            return set()
        base = ssh_config.get("remote_workdir", "/tmp/yuki-workflows")
        prefix = f"{base}/impressions/{project_uuid}/"
        lines = []
        command = ("for d in "
                   + " ".join(shlex.quote(prefix + imp) for imp in impressions)
                   + "; do test -d \"$d\" && echo \"$d\"; done")
        ssh.exec_stream(command, on_line=lines.append)
        return {line[len(prefix):] for line in lines
                if line.startswith(prefix)}

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
    def _conda_probe(ssh, conda_env):
        """Resolve the conda base and verify the env's own python in one exec.

        ``conda run`` strips the calling conda's base from the child PATH,
        so a broken env (no bin/python) silently falls back to the system
        python. A cheap existence check of the env's own python catches
        exactly that.

        Returns (base, ok, resolved_python_path).
        """
        lines = []
        code = ssh.exec_stream(
            "base=$(conda info --base 2>/dev/null || true); "
            "echo CBASE=$base; "
            f"test -x \"$base/envs/{shlex.quote(conda_env)}/bin/python\" "
            "&& echo CPY=ok",
            on_line=lines.append)
        base = ""
        py_ok = False
        for line in lines:
            if line.startswith("CBASE="):
                base = line[len("CBASE="):]
            elif line == "CPY=ok":
                py_ok = True
        resolved = f"{base}/envs/{conda_env}/bin/python"
        return base, (not code and py_ok), resolved

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
