# Inline-Code Tasks Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** Let a Celebi task carry its own code and `commands` in its `celebi.yaml` (no algorithm object required), with the same rule implemented on the Yuki server.

**Architecture:** A task's runnable commands resolve as: task-level `commands` if non-empty → else the linked algorithm's `commands` → else none. The Celebi client exposes this as `VTask.commands()` (effective) and `VTask.code_path()` (code root), which the job workaround/docker-test code and the shell use instead of assuming an algorithm. Yuki's `ContainerJob` reads the task impression's own `celebi.yaml` first in both command-processing paths.

**Tech Stack:** Python, unittest + pytest (both repos use pytest for newer tests), `metadata.YamlFile`/`TwoTierConfigFile` from CelebiChrono (Yuki imports CelebiChrono.utils too).

**Spec:** `docs/superpowers/specs/2026-08-29-inline-code-tasks-design.md` — the plan argues from the spec; read both.

## Global Constraints

- **The shared rule** (spec §2): task-level `commands` from the task's own `celebi.yaml` if non-empty → else linked algorithm's `commands` → else none. Implemented identically on Celebi and Yuki.
- Task commands **win** over the algorithm's when both exist (user decision); the algorithm stays linked.
- No task-level `build` field (spec §6).
- `env_validated()` order (spec §3.1): data flavors valid → task-level commands valid iff `environment` non-empty → algorithm-backed rules unchanged → else invalid.
- Workaround/docker-test code tree = `code_path()`: task dir when inline, else algorithm dir (spec §3.3).
- Existing test suites must stay green in both repos; no changes to `VAlgorithm`, impressions, deposit/submit, `doctor`, `VProject`, or the DITE protocol.
- **Naming deviation from spec §3.1:** the raw yaml reader is named `task_commands()` (not `commands()` overridden). Reason: `env_validated()` must test *task-level* commands; if `commands()` were the SettingManager method, `self.commands()` inside `env_validated()` would dispatch to the `VTask.commands()` override and return *effective* commands — wrongly validating algorithm-backed tasks with mismatched environments (and breaking the existing "non-matching algorithm environment" test). External API is unchanged.
- **Repos:**
  - Celebi: `/Users/wave/workdir/Celebi/Celebi`, branch `inline-code-tasks` (already checked out).
  - Yuki: `/Users/wave/workdir/Celebi/Yuki`, create branch `inline-code-tasks` in Task 8.
- Celebi tests run from the `UnitTest/` directory (fixtures `os.chdir` relative to cwd): `cd UnitTest && python -m pytest -v`. Yuki tests run from the Yuki repo root.
- Commits: conventional-commit messages, end each with the `Co-Authored-By: Claude Code <noreply@anthropic.com>` trailer.

---

### Task 1: Task-level commands reader and effective resolver (Celebi)

**Files:**
- Modify: `CelebiChrono/kernel/vtask_setting.py` (add `task_commands()`)
- Modify: `CelebiChrono/kernel/vtask.py` (add `VTask.commands()`, `VTask.code_path()`, typing imports)
- Test: `UnitTest/test_vtask.py` (add 3 test methods; add `metadata` import)

**Interfaces:**
- Consumes: nothing new (`self.algorithm()` from `InputManager`, `self.path` from `Core`).
- Produces (used by later tasks):
  - `SettingManager.task_commands() -> List[str]` — task yaml `commands`, default `[]`.
  - `VTask.commands() -> List[str]` — effective commands (task-level if non-empty, else algorithm's, else `[]`).
  - `VTask.code_path() -> Optional[str]` — task dir when inline, else `algorithm.path`, else `None`.

- [ ] **Step 1: Add the failing tests to `UnitTest/test_vtask.py`**

Add `from CelebiChrono.utils import metadata` to the import block (after line 12), then add these methods to `TestChernVTask` (place after `test_set_descriptor`, ~line 141):

```python
    def test_task_commands_reads_yaml(self):
        """task_commands reads the task's own commands from celebi.yaml."""
        prepare.create_chern_project("demo_complex")
        os.chdir("demo_complex")
        obj_tsk = vtsk.VTask(os.getcwd() + "/tasks/taskAna1")

        # Default: no commands field
        self.assertEqual(obj_tsk.task_commands(), [])

        yaml_file = metadata.YamlFile(os.path.join(obj_tsk.path, "celebi.yaml"))
        yaml_file.write_variable("commands", ["echo hi", "echo bye"])
        self.assertEqual(obj_tsk.task_commands(), ["echo hi", "echo bye"])

        os.chdir("..")
        prepare.remove_chern_project("demo_complex")
        CHERN_CACHE.__init__()  # pylint: disable=unnecessary-dunder-call

    def test_effective_commands_precedence(self):
        """Task-level commands win; algorithm commands are the fallback."""
        prepare.create_chern_project("demo_complex")
        os.chdir("demo_complex")
        obj_tsk = vtsk.VTask(os.getcwd() + "/tasks/taskAna1")

        mock_algorithm = MagicMock()
        mock_algorithm.commands.return_value = ["echo algorithm"]

        # No task-level commands: fall back to the algorithm
        with patch.object(obj_tsk, 'algorithm', return_value=mock_algorithm):
            self.assertEqual(obj_tsk.commands(), ["echo algorithm"])

        # No task-level commands and no algorithm: empty
        with patch.object(obj_tsk, 'algorithm', return_value=None):
            self.assertEqual(obj_tsk.commands(), [])

        # Task-level commands win over the algorithm
        yaml_file = metadata.YamlFile(os.path.join(obj_tsk.path, "celebi.yaml"))
        yaml_file.write_variable("commands", ["echo inline"])
        with patch.object(obj_tsk, 'algorithm', return_value=mock_algorithm):
            self.assertEqual(obj_tsk.commands(), ["echo inline"])
        with patch.object(obj_tsk, 'algorithm', return_value=None):
            self.assertEqual(obj_tsk.commands(), ["echo inline"])

        os.chdir("..")
        prepare.remove_chern_project("demo_complex")
        CHERN_CACHE.__init__()  # pylint: disable=unnecessary-dunder-call

    def test_code_path(self):
        """code_path is the task dir when inline, else the algorithm dir."""
        prepare.create_chern_project("demo_complex")
        os.chdir("demo_complex")
        obj_tsk = vtsk.VTask(os.getcwd() + "/tasks/taskAna1")

        mock_algorithm = MagicMock()
        mock_algorithm.path = "/mock/algorithm/path"

        with patch.object(obj_tsk, 'algorithm', return_value=None):
            self.assertIsNone(obj_tsk.code_path())

        with patch.object(obj_tsk, 'algorithm', return_value=mock_algorithm):
            self.assertEqual(obj_tsk.code_path(), "/mock/algorithm/path")

        yaml_file = metadata.YamlFile(os.path.join(obj_tsk.path, "celebi.yaml"))
        yaml_file.write_variable("commands", ["echo inline"])
        with patch.object(obj_tsk, 'algorithm', return_value=mock_algorithm):
            self.assertEqual(obj_tsk.code_path(), obj_tsk.path)
        with patch.object(obj_tsk, 'algorithm', return_value=None):
            self.assertEqual(obj_tsk.code_path(), obj_tsk.path)

        os.chdir("..")
        prepare.remove_chern_project("demo_complex")
        CHERN_CACHE.__init__()  # pylint: disable=unnecessary-dunder-call
```

- [ ] **Step 2: Run the tests to verify they fail**

Run: `cd UnitTest && python -m pytest test_vtask.py::TestChernVTask::test_task_commands_reads_yaml test_vtask.py::TestChernVTask::test_effective_commands_precedence test_vtask.py::TestChernVTask::test_code_path -v`
Expected: FAIL — `AttributeError: 'VTask' object has no attribute 'task_commands'` (first test).

- [ ] **Step 3: Implement `task_commands()` in `CelebiChrono/kernel/vtask_setting.py`**

Add after `memory_limit()` (after line 48):

```python
    def task_commands(self):
        """
        Read the task's own commands from celebi.yaml.
        """
        parameters_file = metadata.YamlFile(join(self.path, "celebi.yaml"))
        return parameters_file.read_variable("commands", [])
```

- [ ] **Step 4: Implement `commands()` and `code_path()` in `CelebiChrono/kernel/vtask.py`**

Add `from typing import List, Optional` to the imports (after line 87), then add after `set_descriptor` (after line 267):

```python
    def commands(self) -> List[str]:
        """Effective commands: task-level if non-empty, else the algorithm's."""
        task_commands = self.task_commands()
        if task_commands:
            return task_commands
        algorithm = self.algorithm()
        if algorithm is not None:
            return algorithm.commands()
        return []

    def code_path(self) -> Optional[str]:
        """The code root: task dir when inline, else the algorithm dir."""
        if self.task_commands():
            return self.path
        algorithm = self.algorithm()
        if algorithm is not None:
            return algorithm.path
        return None
```

- [ ] **Step 5: Run the tests to verify they pass**

Run: same command as Step 2.
Expected: PASS (3 passed).

- [ ] **Step 6: Commit**

```bash
git add CelebiChrono/kernel/vtask_setting.py CelebiChrono/kernel/vtask.py UnitTest/test_vtask.py
git commit -m "feat(task): add task-level commands reader and effective resolver

Co-Authored-By: Claude Code <noreply@anthropic.com>"
```

---

### Task 2: Validation for inline-code tasks (Celebi)

**Files:**
- Modify: `CelebiChrono/kernel/vtask_setting.py` (`env_validated()`, lines 132-143)
- Test: `UnitTest/test_vtask.py` (add `test_env_validated_inline_commands`)

**Interfaces:**
- Consumes: `SettingManager.task_commands()` from Task 1.
- Produces: nothing new.

- [ ] **Step 1: Add the failing test to `UnitTest/test_vtask.py`**

Add after `test_setting_manager_validation_methods` (~line 1371):

```python
    def test_env_validated_inline_commands(self):
        """Inline-code tasks validate on their own commands and environment."""
        prepare.create_chern_project("demo_complex")
        os.chdir("demo_complex")
        obj_tsk = vtsk.VTask(os.getcwd() + "/tasks/taskAna1")
        yaml_file = metadata.YamlFile(os.path.join(obj_tsk.path, "celebi.yaml"))
        yaml_file.write_variable("commands", ["echo hi"])

        # Inline commands with an environment: valid
        with patch.object(obj_tsk, 'environment', return_value='python:3.9'), \
             patch.object(obj_tsk, 'algorithm', return_value=None):
            self.assertTrue(obj_tsk.env_validated())

        # Inline commands without an environment: invalid
        with patch.object(obj_tsk, 'environment', return_value=''), \
             patch.object(obj_tsk, 'algorithm', return_value=None):
            self.assertFalse(obj_tsk.env_validated())

        # Inline commands win: algorithm environment mismatch is irrelevant
        mock_algorithm = MagicMock()
        mock_algorithm.environment.return_value = "ubuntu:20.04"
        with patch.object(obj_tsk, 'environment', return_value='python:3.9'), \
             patch.object(obj_tsk, 'algorithm', return_value=mock_algorithm):
            self.assertTrue(obj_tsk.env_validated())

        os.chdir("..")
        prepare.remove_chern_project("demo_complex")
        CHERN_CACHE.__init__()  # pylint: disable=unnecessary-dunder-call
```

- [ ] **Step 2: Run the test to verify it fails**

Run: `cd UnitTest && python -m pytest test_vtask.py::TestChernVTask::test_env_validated_inline_commands -v`
Expected: FAIL — "inline commands without an environment" returns True (old code falls into algorithm rules with `algorithm=None` → the assert in the "with environment" case passes already; the empty-environment case asserts False but old code returns False via the no-algorithm path... verify: old code, algorithm None → `if self.algorithm() is not None` False → return False. So the empty-env case passes and the first case FAILS: algorithm None → False, expected True). Expect at least one failure: `assertTrue` failing on the first block.

- [ ] **Step 3: Rewrite `env_validated()` in `CelebiChrono/kernel/vtask_setting.py`**

Replace lines 132-143 with:

```python
    def env_validated(self):
        """
        Check whether the environment is validated or not
        """
        if self.environment() in ("rawdata", "datalist", "lhcb_ap_datalist"):
            return True
        if self.task_commands():
            return bool(self.environment())
        if self.algorithm() is not None:
            if self.algorithm().environment() == "script":
                return True
            if self.environment() == self.algorithm().environment():
                return True
        return False
```

- [ ] **Step 4: Run the new test AND the existing validation tests**

Run: `cd UnitTest && python -m pytest test_vtask.py::TestChernVTask::test_env_validated_inline_commands test_vtask.py::TestChernVTask::test_setting_manager_validation_methods test_vtask.py::TestChernVTask::test_setting_manager_integration -v`
Expected: PASS (all three).

- [ ] **Step 5: Commit**

```bash
git add CelebiChrono/kernel/vtask_setting.py UnitTest/test_vtask.py
git commit -m "feat(task): validate inline-code tasks without an algorithm

Co-Authored-By: Claude Code <noreply@anthropic.com>"
```

---

### Task 3: Job workaround and docker-test use the code root (Celebi)

**Files:**
- Modify: `CelebiChrono/kernel/vtask_job.py` (`_test_commands` :93-108, `_prepare_algorithm_code` :690-748, `workaround_preshell` :778-828, `workaround_postshell` :982-1031, `_prepare_mounting_algorithm_code` :921-948)
- Test: `UnitTest/test_vtask_job_workaround.py` (extend `FakeJobManager`, add 5 tests)

**Interfaces:**
- Consumes: `VTask.commands()` / `VTask.code_path()` from Task 1 (via `self` on real tasks; via stubs on `FakeJobManager`).
- Produces: nothing new (existing method signatures unchanged).

- [ ] **Step 1: Extend `FakeJobManager` in `UnitTest/test_vtask_job_workaround.py`**

Change `FakeJobManager.__init__` (line 18-22) to:

```python
    def __init__(self, project_path, inputs=None, commands=None, code_path=None):
        # pylint: disable=super-init-not-called
        """Init."""
        self._project_path = project_path
        self._inputs = inputs or []
        self._commands = commands if commands is not None else []
        self._code_path = code_path
```

And add stubs next to the other stubs (after `cache_on_runner`):

```python
    def commands(self):
        """Effective commands."""
        return self._commands

    def code_path(self):
        """Code root."""
        return self._code_path
```

Existing tests construct `FakeJobManager(tmpdir, inputs=[pre])` — defaults keep them green.

- [ ] **Step 2: Add the failing tests to `UnitTest/test_vtask_job_workaround.py`**

Append at the end of the file:

```python
def _write(path, text):
    """Write a text file, creating parent directories."""
    os.makedirs(os.path.dirname(path), exist_ok=True)
    with open(path, "w", encoding="utf-8") as f:
        f.write(text)


def test_test_commands_uses_effective_commands():
    """_test_commands substitutes parameters into the effective commands."""
    with tempfile.TemporaryDirectory() as tmpdir:
        jm = FakeJobManager(tmpdir, commands=["echo ${n}"])
        jm.parameters = mock.Mock(return_value=(["n"], {"n": "5"}))
        assert jm._test_commands() == ["echo 5"]


def test_prepare_algorithm_code_copies_inline_task_tree():
    """Inline tasks copy their own directory as the workaround code tree."""
    with tempfile.TemporaryDirectory() as tmpdir:
        task_dir = os.path.join(tmpdir, "task")
        os.makedirs(task_dir)
        _write(os.path.join(task_dir, "main.py"), "print('hi')")
        _write(os.path.join(task_dir, "celebi.yaml"), "descriptor: t\n")

        jm = FakeJobManager(tmpdir, code_path=task_dir)
        workspace = os.path.join(tmpdir, "workspace")
        os.makedirs(workspace)

        with mock.patch.object(jm, "algorithm", return_value=None), \
             mock.patch("CelebiChrono.kernel.vtask_job.csys.symlink") as mock_symlink:
            jm._prepare_algorithm_code(workspace)

        assert mock_symlink.call_count == 1
        symlink_source = mock_symlink.call_args.args[0]
        assert os.path.exists(os.path.join(symlink_source, "main.py"))
        assert os.path.exists(os.path.join(symlink_source, "celebi.yaml"))


def test_prepare_algorithm_code_returns_when_no_code_root():
    """No code root means nothing to copy or link."""
    with tempfile.TemporaryDirectory() as tmpdir:
        jm = FakeJobManager(tmpdir, code_path=None)
        workspace = os.path.join(tmpdir, "workspace")
        os.makedirs(workspace)

        with mock.patch("CelebiChrono.kernel.vtask_job.csys.symlink") as mock_symlink:
            jm._prepare_algorithm_code(workspace)

        mock_symlink.assert_not_called()


def test_workaround_preshell_writes_exec_sh_for_inline_commands():
    """Inline commands become exec.sh inside the workaround workspace."""
    with tempfile.TemporaryDirectory() as tmpdir:
        jm = FakeJobManager(tmpdir, commands=["echo inline"])
        workspace = os.path.join(tmpdir, "workspace")
        os.makedirs(workspace)

        cherncc = mock.Mock()
        cherncc.dite_status.return_value = "connected"

        with mock.patch(
                "CelebiChrono.kernel.vtask_job.ChernCommunicator.instance",
                return_value=cherncc), \
             mock.patch.object(jm, "_check_preceding_jobs",
                               return_value=(True, "")), \
             mock.patch.object(jm, "_create_workaround_dir",
                               return_value=workspace), \
             mock.patch.object(jm, "_prepare_data_dir"), \
             mock.patch.object(jm, "_link_preceding_jobs"), \
             mock.patch.object(jm, "_prepare_algorithm_code"), \
             mock.patch.object(jm, "_generate_workaround_filelist"), \
             mock.patch.object(jm, "parameters", return_value=([], {})):
            success, _ = jm.workaround_preshell()

        assert success
        script_path = os.path.join(workspace, "exec.sh")
        assert os.path.exists(script_path)
        with open(script_path, encoding="utf-8") as f:
            content = f.read()
        assert "echo inline" in content


def test_workaround_postshell_syncs_back_to_inline_task_dir():
    """Postshell syncs code/ back to the task dir, deleting stray files."""
    with tempfile.TemporaryDirectory() as tmpdir:
        task_dir = os.path.join(tmpdir, "task")
        os.makedirs(task_dir)
        _write(os.path.join(task_dir, "main.py"), "old")
        _write(os.path.join(task_dir, "celebi.yaml"), "descriptor: t\n")
        _write(os.path.join(task_dir, "README.md"), "readme\n")
        _write(os.path.join(task_dir, "stale.py"), "stale\n")

        workspace = os.path.join(tmpdir, "workspace")
        code_dir = os.path.join(workspace, "code")
        os.makedirs(code_dir)
        _write(os.path.join(code_dir, "main.py"), "new")
        _write(os.path.join(code_dir, "celebi.yaml"), "descriptor: t\n")
        _write(os.path.join(workspace, "filelist.yaml"),
               "files:\n- rel_path: main.py\n- rel_path: celebi.yaml\n")

        jm = FakeJobManager(tmpdir, code_path=task_dir)
        assert jm.workaround_postshell(workspace)

        with open(os.path.join(task_dir, "main.py"), encoding="utf-8") as f:
            assert f.read() == "new"
        assert not os.path.exists(os.path.join(task_dir, "stale.py"))
        assert os.path.exists(os.path.join(task_dir, "celebi.yaml"))
        assert os.path.exists(os.path.join(task_dir, "README.md"))


def test_prepare_mounting_algorithm_code_mounts_inline_task_dir():
    """Docker-test mounts point at /workspace/code for inline tasks."""
    with tempfile.TemporaryDirectory() as tmpdir:
        task_dir = os.path.join(tmpdir, "task")
        os.makedirs(task_dir)
        _write(os.path.join(task_dir, "main.py"), "print('hi')")

        jm = FakeJobManager(tmpdir, code_path=task_dir)
        mount_config = {"base_dir": tmpdir, "mounts": []}

        with mock.patch.object(jm, "algorithm", return_value=None):
            jm._prepare_mounting_algorithm_code(tmpdir, mount_config)

        assert len(mount_config["mounts"]) == 1
        entry = mount_config["mounts"][0]
        assert entry["target"] == "/workspace/code"
        assert os.path.exists(os.path.join(entry["source"], "main.py"))
```

- [ ] **Step 3: Run the tests to verify they fail**

Run: `cd UnitTest && python -m pytest test_vtask_job_workaround.py -v`
Expected: FAIL — `AttributeError: 'FakeJobManager' object has no attribute 'commands'` (first new test); note the four pre-existing tests in this file must stay green.

- [ ] **Step 4: Change `_test_commands()` in `CelebiChrono/kernel/vtask_job.py`**

Replace lines 93-108 with:

```python
    def _test_commands(self):
        """Return the effective commands with parameters substituted.

        Shared by docker_test and ssh_test.
        """
        commands = self.commands()
        # Parse the commands, and replace any placeholders with actual values if needed
        parameters = self.parameters()
        if parameters:
            # Example: Parameters for command execution:
            # (['events'], {'events': '20000'})
            # For example, if your command has a placeholder like {param1},
            # you can replace it with parameters['param1']
            for key, value in parameters[1].items():
                commands = [cmd.replace(f"${{{key}}}", str(value)) for cmd in commands]
        return commands
```

- [ ] **Step 5: Change `_prepare_algorithm_code()` in `CelebiChrono/kernel/vtask_job.py`**

Replace the method body (lines 690-748) with:

```python
    def _prepare_algorithm_code(self, temp_dir): # pylint: disable=too-many-locals
        """Prepare the task's code tree (inline task dir or algorithm dir)"""
        code_root = self.code_path()
        if not code_root:
            return

        alg_temp_dir = self._create_workaround_dir(prefix="chernws_")
        file_list = csys.tree_excluded(code_root)
        for dirpath, _, filenames in file_list:
            for f in filenames:
                full_path = os.path.join(code_root, dirpath, f)
                rel_path = os.path.relpath(full_path, code_root)
                dest_path = os.path.join(alg_temp_dir, rel_path)
                csys.copy(full_path, dest_path)
        csys.symlink(
            os.path.join(alg_temp_dir),
            os.path.join(temp_dir, "code"),
        )

        algorithm = self.algorithm()
        if algorithm is None:
            return

        # if the algorithm have inputs, link them too
        alg_inputs = filter(
            lambda x: (x.object_type() == "algorithm"), algorithm.predecessors()
            )
        for alg_in in list(map(lambda x: self.get_task(x.path), alg_inputs)):
            if not os.path.exists(
                self._workaround_dir(
                    name=alg_in.impression().uuid,
                    prefix="chernimp_"
                )):
                alg_in_temp_dir = self._create_workaround_dir(
                    name=alg_in.impression().uuid,
                    prefix="chernimp_"
                )
                alg_in_file_list = csys.tree_excluded(alg_in.path)
                for dirpath, _, filenames in alg_in_file_list:
                    for f in filenames:
                        full_path = os.path.join(
                                self.project_path(),
                                alg_in.invariant_path(),
                                dirpath, f
                        )
                        rel_path = os.path.relpath(full_path, alg_in.path)
                        dest_path = os.path.join(alg_in_temp_dir, rel_path)
                        csys.copy(full_path, dest_path)
            else:
                alg_in_temp_dir = self._workaround_dir(
                    name=alg_in.impression().uuid,
                    prefix="chernimp_"
                )
            alias = algorithm.path_to_alias(alg_in.invariant_path())
            # Link it under code
            csys.symlink(
                os.path.join(alg_in_temp_dir),
                os.path.join(temp_dir, "code", alias),
            )
```

- [ ] **Step 6: Change the commands block of `workaround_preshell()`**

Replace this exact block (the `algorithm = self.algorithm()` block, lines 802-824):

```python
        algorithm = self.algorithm()
        if algorithm:
            commands = algorithm.commands()
            if commands:
                parameters = self.parameters()
                if parameters:
                    for key, value in parameters[1].items():
                        commands = [cmd.replace(f"${{{key}}}", str(value)) for cmd in commands]
                script = "#!/bin/bash\n\n"
                env = self.environment()
                if env and env != "rawdata" and "/" not in env:
                    conda_env = env.split("=", 1)[1] if env.startswith("conda_env=") else env
                    script += (
                        'eval "$(conda shell.bash hook)" 2>/dev/null || '
                        'source ~/miniconda3/etc/profile.d/conda.sh 2>/dev/null || '
                        'source ~/anaconda3/etc/profile.d/conda.sh 2>/dev/null || true\n'
                        f'conda activate {conda_env}\n\n'
                    )
                script += "mkdir -p stageout\n\n" + " && ".join(commands) + "\n"
                script_path = os.path.join(temp_dir, "exec.sh")
                with open(script_path, "w", encoding="utf-8") as f:
                    f.write(script)
                os.chmod(script_path, 0o755)
```

with:

```python
        commands = self.commands()
        if commands:
            parameters = self.parameters()
            if parameters:
                for key, value in parameters[1].items():
                    commands = [cmd.replace(f"${{{key}}}", str(value)) for cmd in commands]
            script = "#!/bin/bash\n\n"
            env = self.environment()
            if env and env != "rawdata" and "/" not in env:
                conda_env = env.split("=", 1)[1] if env.startswith("conda_env=") else env
                script += (
                    'eval "$(conda shell.bash hook)" 2>/dev/null || '
                    'source ~/miniconda3/etc/profile.d/conda.sh 2>/dev/null || '
                    'source ~/anaconda3/etc/profile.d/conda.sh 2>/dev/null || true\n'
                    f'conda activate {conda_env}\n\n'
                )
            script += "mkdir -p stageout\n\n" + " && ".join(commands) + "\n"
            script_path = os.path.join(temp_dir, "exec.sh")
            with open(script_path, "w", encoding="utf-8") as f:
                f.write(script)
            os.chmod(script_path, 0o755)
```

- [ ] **Step 7: Change `workaround_postshell()` to sync against `code_path()`**

Replace this exact method (lines 982-1031):

```python
    def workaround_postshell(self, path) -> bool:
        """ Post-shell workaround - sync files according to filelist

        The filelist.yaml is the authority: files listed in it are copied from
        the workaround to origin; files in origin but not in the filelist are
        deleted. The user may edit filelist.yaml during the workaround to add
        new files they want to keep or remove files they want to discard.
        """
        algorithm = self.algorithm()
        if not algorithm:
            return True

        alg_temp_dir = os.path.join(path, "code")
        if not os.path.isdir(alg_temp_dir):
            return True

        # Resolve symlink so os.walk dirpath and alg_temp_dir share the same base
        alg_temp_dir = os.path.realpath(alg_temp_dir)

        # Load the filelist (user may have edited it to add/remove entries)
        filelist_entries = set()
        filelist_path = os.path.join(path, "filelist.yaml")
        if os.path.exists(filelist_path):
            with open(filelist_path, "r", encoding="utf-8") as f:
                data = yaml.load(f, Loader=yaml.Loader)
                if data:
                    for record in data.get("files", []):
                        filelist_entries.add(record["rel_path"])

        # Copy files from workaround to origin according to filelist
        for rel_path in filelist_entries:
            workaround_path = os.path.join(alg_temp_dir, rel_path)
            origin_path = os.path.join(algorithm.path, rel_path)
            if os.path.isfile(workaround_path):
                csys.copy(workaround_path, origin_path)
                print(f"Copied: {rel_path}")
            else:
                print(f"Warning: {rel_path} listed in filelist but not found")

        # Delete files from origin that are NOT in the filelist
        origin_tree = csys.tree_excluded(algorithm.path)
        for dirpath, _, filenames in origin_tree:
            for f in filenames:
                full_path = os.path.join(algorithm.path, dirpath, f)
                rel_path = os.path.relpath(full_path, algorithm.path)
                if rel_path not in filelist_entries:
                    os.remove(full_path)
                    print(f"Deleted: {rel_path}")

        return True
```

with:

```python
    def workaround_postshell(self, path) -> bool:
        """ Post-shell workaround - sync files according to filelist

        The filelist.yaml is the authority: files listed in it are copied from
        the workaround to origin; files in origin but not in the filelist are
        deleted. The user may edit filelist.yaml during the workaround to add
        new files they want to keep or remove files they want to discard.
        """
        code_root = self.code_path()
        if not code_root:
            return True

        alg_temp_dir = os.path.join(path, "code")
        if not os.path.isdir(alg_temp_dir):
            return True

        # Resolve symlink so os.walk dirpath and alg_temp_dir share the same base
        alg_temp_dir = os.path.realpath(alg_temp_dir)

        # Load the filelist (user may have edited it to add/remove entries)
        filelist_entries = set()
        filelist_path = os.path.join(path, "filelist.yaml")
        if os.path.exists(filelist_path):
            with open(filelist_path, "r", encoding="utf-8") as f:
                data = yaml.load(f, Loader=yaml.Loader)
                if data:
                    for record in data.get("files", []):
                        filelist_entries.add(record["rel_path"])

        # Copy files from workaround to origin according to filelist
        for rel_path in filelist_entries:
            workaround_path = os.path.join(alg_temp_dir, rel_path)
            origin_path = os.path.join(code_root, rel_path)
            if os.path.isfile(workaround_path):
                csys.copy(workaround_path, origin_path)
                print(f"Copied: {rel_path}")
            else:
                print(f"Warning: {rel_path} listed in filelist but not found")

        # Delete files from origin that are NOT in the filelist
        origin_tree = csys.tree_excluded(code_root)
        for dirpath, _, filenames in origin_tree:
            for f in filenames:
                full_path = os.path.join(code_root, dirpath, f)
                rel_path = os.path.relpath(full_path, code_root)
                if rel_path not in filelist_entries:
                    os.remove(full_path)
                    print(f"Deleted: {rel_path}")

        return True
```

- [ ] **Step 8: Change `_prepare_mounting_algorithm_code()`**

Replace lines 921-948 with:

```python
    def _prepare_mounting_algorithm_code(self, _temp_dir, mount_config):
        """Prepare the code tree (inline task dir or algorithm dir) for mounting"""
        code_root = self.code_path()
        if not code_root:
            return

        alg_temp_dir = self._create_workaround_dir(prefix="chernws_")
        file_list = csys.tree_excluded(code_root)
        for dirpath, _, filenames in file_list:
            for f in filenames:
                full_path = os.path.join(code_root, dirpath, f)
                rel_path = os.path.relpath(full_path, code_root)
                dest_path = os.path.join(alg_temp_dir, rel_path)
                csys.copy(full_path, dest_path)

        # Add mount configuration instead of creating symlink (moved outside the loop)
        mount_config["mounts"].append({
            "source": alg_temp_dir,
            "target": "/workspace/code",
            "type": "bind",
            "readonly": False,
            "description": "Algorithm code"
        })

        algorithm = self.algorithm()
        if algorithm is None:
            return

        # if the algorithm have inputs, link them too
        alg_inputs = filter(
            lambda x: (x.object_type() == "algorithm"), algorithm.predecessors()
            )
        for alg_in in list(map(lambda x: self.get_task(x.path), alg_inputs)):
            alg_in_temp_dir = self._workaround_dir(
                name=alg_in.impression().uuid, prefix="chernimp_")
            if not os.path.exists(alg_in_temp_dir):
                alg_in_temp_dir = self._create_workaround_dir(
                    name=alg_in.impression().uuid, prefix="chernimp_")
                alg_in_file_list = csys.tree_excluded(alg_in.path)
                for dirpath, _, filenames in alg_in_file_list:
                    for f in filenames:
                        full_path = os.path.join(
                                self.project_path(),
                                alg_in.invariant_path(),
                                dirpath, f
                        )
                        rel_path = os.path.relpath(full_path, alg_in.path)
                        dest_path = os.path.join(alg_in_temp_dir, rel_path)
                        csys.copy(full_path, dest_path)
```

Keep the remainder of the original method (the mount entry for `alg_in` and the alias symlink block, lines 969-982) unchanged after this.

- [ ] **Step 9: Run the tests to verify they pass**

Run: `cd UnitTest && python -m pytest test_vtask_job_workaround.py -v`
Expected: PASS — all 10 tests (4 pre-existing + 6 new).

- [ ] **Step 10: Run the broader job/task tests**

Run: `cd UnitTest && python -m pytest test_vtask.py test_vtask_job_workaround.py test_ssh_test_task.py -v`
Expected: PASS — no regressions in `_test_commands` consumers (`ssh_test` uses it).

- [ ] **Step 11: Commit**

```bash
git add CelebiChrono/kernel/vtask_job.py UnitTest/test_vtask_job_workaround.py
git commit -m "feat(task): run workaround and docker tests from inline task code

Co-Authored-By: Claude Code <noreply@anthropic.com>"
```

---

### Task 4: `ls` shows effective commands (Celebi)

**Files:**
- Modify: `CelebiChrono/kernel/vtask_core.py` (`ls()` :34-62, `show_algorithm()` :160-197)
- Test: `UnitTest/test_vtask.py` (add `test_ls_shows_effective_commands_for_inline_task`)

**Interfaces:**
- Consumes: `VTask.commands()` from Task 1.
- Produces: nothing new.

- [ ] **Step 1: Add the failing test to `UnitTest/test_vtask.py`**

Add after `test_core_algorithm_display` (~line 503):

```python
    def test_ls_shows_effective_commands_for_inline_task(self):
        """ls lists the task's own commands when the task is inline."""
        prepare.create_chern_project("demo_complex")
        os.chdir("demo_complex")
        obj_tsk = vtsk.VTask(os.getcwd() + "/tasks/taskAna1")
        yaml_file = metadata.YamlFile(os.path.join(obj_tsk.path, "celebi.yaml"))
        yaml_file.write_variable("commands", ["echo inline"])

        with patch.object(obj_tsk, 'algorithm', return_value=None), \
             patch('os.get_terminal_size') as mock_terminal_size:
            mock_terminal_size.return_value.columns = 80
            message = obj_tsk.ls()

        msg_str = str(message)
        self.assertIn("Commands", msg_str)
        self.assertIn("echo inline", msg_str)

        os.chdir("..")
        prepare.remove_chern_project("demo_complex")
        CHERN_CACHE.__init__()  # pylint: disable=unnecessary-dunder-call
```

- [ ] **Step 2: Run the test to verify it fails**

Run: `cd UnitTest && python -m pytest test_vtask.py::TestChernVTask::test_ls_shows_effective_commands_for_inline_task -v`
Expected: FAIL — "Commands" not in the ls message (show_algorithm is skipped when no algorithm).

- [ ] **Step 3: Change `ls()` in `CelebiChrono/kernel/vtask_core.py`**

Replace line 43-44:

```python
            if self.algorithm() is not None:
                message.append(self.show_algorithm())
```

with:

```python
            if self.algorithm() is not None or self.commands():
                message.append(self.show_algorithm())
```

- [ ] **Step 4: Change `show_algorithm()` in `CelebiChrono/kernel/vtask_core.py`**

Replace lines 160-197 with:

```python
    def show_algorithm(self) -> Message:
        """ Show the algorithm files (if any) and the effective commands of the task.
        """
        message = Message()

        algorithm = self.algorithm()
        if algorithm is not None:
            message.add("---- Algorithm files:\n", "title0")

            files = os.listdir(algorithm.path)
            if files:
                files = sorted(f for f in files
                    if not f.startswith(".") and f not in ["README.md", "celebi.yaml"])
                if files:
                    max_len = max(len(f) for f in files)
                    columns = shutil.get_terminal_size((80, 20)).columns
                    nfiles = max(1, columns // (max_len + 4 + 11))  # Avoid division by zero
                    line = ""

                    for i, f in enumerate(files, start=1):
                        line += f"code:{f:<{max_len+4}}"
                        if not i % nfiles:
                            message.add(line + "\n")
                            line = ""
                    if line:
                        message.add(line + "\n")

        commands = self.commands()
        if commands:
            message.add("---- Commands:\n", "title0")
            parameters, values = self.parameters()
            for command in commands:
                for parameter in parameters:
                    command = command.replace("${" + parameter + "}", values[parameter])
                message.add(command + "\n")

        return message
```

- [ ] **Step 5: Run the new test AND the existing display tests**

Run: `cd UnitTest && python -m pytest test_vtask.py::TestChernVTask::test_ls_shows_effective_commands_for_inline_task test_vtask.py::TestChernVTask::test_core_algorithm_display -v`
Expected: PASS — the existing `test_core_algorithm_display` asserts `show_algorithm()` output contains "Commands" and substituted parameters; effective `self.commands()` falls back to the mocked algorithm's commands because the real task yaml has no commands, so those assertions still hold.

- [ ] **Step 6: Commit**

```bash
git add CelebiChrono/kernel/vtask_core.py UnitTest/test_vtask.py
git commit -m "feat(task): show effective commands in task ls

Co-Authored-By: Claude Code <noreply@anthropic.com>"
```

---

### Task 5: Notice when adding an algorithm to an inline task (Celebi)

**Files:**
- Modify: `CelebiChrono/kernel/vtask_input.py` (`add_algorithm()` :45-63)
- Test: `UnitTest/test_vtask.py` (add `test_add_algorithm_notices_task_commands_precedence`)

**Interfaces:**
- Consumes: `SettingManager.task_commands()` from Task 1.
- Produces: nothing new.

- [ ] **Step 1: Add the failing test to `UnitTest/test_vtask.py`**

Add after `test_input_manager_algorithm_methods` (~line 816):

```python
    def test_add_algorithm_notices_task_commands_precedence(self):
        """add_algorithm warns when task commands will shadow the algorithm."""
        prepare.create_chern_project("demo_complex")
        os.chdir("demo_complex")
        obj_tsk = vtsk.VTask(os.getcwd() + "/tasks/taskAna1")

        mock_algo_obj = MagicMock()
        mock_algo_obj.object_type.return_value = "algorithm"
        mock_algo_obj.has_predecessor_recursively.return_value = False

        with patch.object(obj_tsk, 'get_vobject', return_value=mock_algo_obj), \
             patch.object(obj_tsk, 'algorithm', return_value=None), \
             patch.object(obj_tsk, 'task_commands', return_value=["echo hi"]), \
             patch("builtins.print") as mock_print:
            obj_tsk.add_algorithm(os.getcwd() + "/code/ana1")

        printed = " ".join(str(call.args[0]) for call in mock_print.call_args_list)
        self.assertIn("take precedence", printed)

        os.chdir("..")
        prepare.remove_chern_project("demo_complex")
        CHERN_CACHE.__init__()  # pylint: disable=unnecessary-dunder-call
```

- [ ] **Step 2: Run the test to verify it fails**

Run: `cd UnitTest && python -m pytest test_vtask.py::TestChernVTask::test_add_algorithm_notices_task_commands_precedence -v`
Expected: FAIL — "take precedence" not printed.

- [ ] **Step 3: Add the notice in `CelebiChrono/kernel/vtask_input.py`**

In `add_algorithm()`, after the existing "Already have algorithm, will replace it" block (after line 62) insert:

```python
        if self.task_commands():
            print("The task has its own commands in celebi.yaml; "
                  "they take precedence over the algorithm's commands.")
```

- [ ] **Step 4: Run the new test AND the existing algorithm tests**

Run: `cd UnitTest && python -m pytest test_vtask.py::TestChernVTask::test_add_algorithm_notices_task_commands_precedence test_vtask.py::TestChernVTask::test_input_manager_algorithm_methods test_vtask.py::TestChernVTask::test_input_manager_remove_algorithm test_vtask.py::TestChernVTask::test_input_manager_algorithm_getter -v`
Expected: PASS (all four).

- [ ] **Step 5: Commit**

```bash
git add CelebiChrono/kernel/vtask_input.py UnitTest/test_vtask.py
git commit -m "feat(task): warn when adding an algorithm to a task with inline commands

Co-Authored-By: Claude Code <noreply@anthropic.com>"
```

---

### Task 6: Shell `code:` path resolution for inline tasks (Celebi)

**Files:**
- Modify: `CelebiChrono/interface/shell_modules/task_configuration.py` (`get_script_path()` :578-590)
- Test: `UnitTest/test_task_configuration_paths.py` (add `TestGetScriptPathCodePrefix`)

**Interfaces:**
- Consumes: `VTask.code_path()` from Task 1 (on `MANAGER.current_object()`).
- Produces: nothing new.

- [ ] **Step 1: Add the failing tests to `UnitTest/test_task_configuration_paths.py`**

Append:

```python
class TestGetScriptPathCodePrefix(unittest.TestCase):
    """Tests that code:/code/ prefixes resolve via the task's code_path."""

    @patch.object(MANAGER, "current_object")
    def test_code_prefix_resolves_to_code_path(self, mock_current_object):
        """code: paths resolve against the code root (task dir when inline)."""
        mock_task = MagicMock()
        mock_task.is_task_or_algorithm.return_value = True
        mock_task.object_type.return_value = "task"
        mock_task.path = "/project/tasks/foo"
        mock_task.code_path.return_value = "/project/tasks/foo"
        mock_current_object.return_value = mock_task

        message = task_configuration.get_script_path("code/main.py")
        self.assertEqual(message.data["path"], "/project/tasks/foo/main.py")

        message = task_configuration.get_script_path("code:utils.py")
        self.assertEqual(message.data["path"], "/project/tasks/foo/utils.py")

    @patch.object(MANAGER, "current_object")
    def test_code_prefix_without_code_root_is_error(self, mock_current_object):
        """code: paths with no code root report an error instead of None."""
        mock_task = MagicMock()
        mock_task.is_task_or_algorithm.return_value = True
        mock_task.object_type.return_value = "task"
        mock_task.path = "/project/tasks/foo"
        mock_task.code_path.return_value = None
        mock_current_object.return_value = mock_task

        message = task_configuration.get_script_path("code/main.py")
        self.assertFalse(message.success)

    @patch.object(MANAGER, "current_object")
    def test_plain_filename_unaffected(self, mock_current_object):
        """Non-code: paths still resolve against the object itself."""
        mock_task = MagicMock()
        mock_task.is_task_or_algorithm.return_value = True
        mock_task.object_type.return_value = "task"
        mock_task.path = "/project/tasks/foo"
        mock_current_object.return_value = mock_task

        message = task_configuration.get_script_path("script.py")
        self.assertEqual(message.data["path"], "/project/tasks/foo/script.py")
```

- [ ] **Step 2: Run the tests to verify they fail**

Run: `cd UnitTest && python -m pytest test_task_configuration_paths.py -v`
Expected: FAIL — the two `code:` tests (current code calls `algorithm()` on the mock, producing a `MagicMock` path).

- [ ] **Step 3: Change `get_script_path()` in `CelebiChrono/interface/shell_modules/task_configuration.py`**

Replace lines 578-590 with:

```python
    if MANAGER.current_object().object_type() == "task":
        if filename.startswith("code/") or filename.startswith("code:"):
            code_root = MANAGER.current_object().code_path()
            if code_root is None:
                message.add(
                    "No code root for this task (no algorithm and no inline commands).",
                    "error")
                return message
            path = f"{code_root}/{filename[5:]}"
            message.add(path, "normal")
            message.data["path"] = path
            return message
        path = f"{MANAGER.current_object().path}/{filename}"
        message.add(path, "normal")
        message.data["path"] = path
        return message
```

- [ ] **Step 4: Run the tests to verify they pass**

Run: `cd UnitTest && python -m pytest test_task_configuration_paths.py -v`
Expected: PASS (all tests in the file).

- [ ] **Step 5: Commit**

```bash
git add CelebiChrono/interface/shell_modules/task_configuration.py UnitTest/test_task_configuration_paths.py
git commit -m "feat(shell): resolve code: paths against the task code root

Co-Authored-By: Claude Code <noreply@anthropic.com>"
```

---

### Task 7: Celebi full suite and lint verification (Celebi)

**Files:**
- None modified (verification only; fix anything that surfaces).

**Interfaces:**
- Consumes: everything from Tasks 1-6.
- Produces: green Celebi suite on branch `inline-code-tasks`.

- [ ] **Step 1: Run the full Celebi test suite**

Run: `cd UnitTest && python -m pytest -v`
Expected: PASS — all tests, including the untouched `test_valgorithm.py`, `test_vobject.py`, `test_vimpression.py`, shell and cli suites.

If any pre-existing test fails, do NOT patch it silently: run `git diff` to check whether the failure is caused by Tasks 1-6; if it is, fix the production code; if the failure is unrelated (pre-existing), report it and keep it untouched.

- [ ] **Step 2: Lint the changed files**

Run: `python -m pylint --rcfile=.pylintrc CelebiChrono/kernel/vtask.py CelebiChrono/kernel/vtask_setting.py CelebiChrono/kernel/vtask_job.py CelebiChrono/kernel/vtask_core.py CelebiChrono/kernel/vtask_input.py CelebiChrono/interface/shell_modules/task_configuration.py`
Expected: no new pylint errors in the changed files (fix line-length/import issues if any).

- [ ] **Step 3: Commit any fixes**

```bash
git add -u
git commit -m "fix(task): lint and regression fixes for inline-code tasks

Co-Authored-By: Claude Code <noreply@anthropic.com>"
```

(Only if Step 1/2 required changes; otherwise skip the commit.)

---

### Task 8: ContainerJob prefers inline task commands (Yuki)

**Files:**
- Create: branch `inline-code-tasks` in `/Users/wave/workdir/Celebi/Yuki`
- Modify: `Yuki/kernel/container_job.py` (`_process_user_commands_for_reana()` :116-140, `_process_user_commands()` :279-305)
- Test: `UnitTest/test_container_job.py` (extend with a helper and 3 tests)

**Interfaces:**
- Consumes: `self.yaml_file` (the task impression's own `contents/celebi.yaml`, set by `VJob.__init__`), `self.image()` (algorithm predecessor's `ImageJob`, may be `None`).
- Produces: processed command lists — same shape as before (list of str).

- [ ] **Step 1: Create the branch in the Yuki repo**

```bash
cd /Users/wave/workdir/Celebi/Yuki && git checkout -b inline-code-tasks
```

- [ ] **Step 2: Add the failing tests to `Yuki/UnitTest/test_container_job.py`**

Replace the top of the file (the import block and helpers, lines 1-10) with:

```python
"""Tests for ContainerJob output discovery and command resolution."""
from unittest import mock

from CelebiChrono.utils import metadata
from Yuki.kernel.container_job import ContainerJob


def _make_container(path, machine_id="runner-1"):
    c = ContainerJob.__new__(ContainerJob, str(path), machine_id)
    c.path = str(path)
    c.machine_id = machine_id
    return c


def _make_container_with_yaml(path, task_vars):
    """Build a ContainerJob whose yaml_file is a real celebi.yaml with task_vars."""
    contents = path / "contents"
    contents.mkdir(parents=True, exist_ok=True)
    yaml_file = metadata.YamlFile(str(contents / "celebi.yaml"))
    for key, value in task_vars.items():
        yaml_file.write_variable(key, value)
    c = _make_container(path)
    c.is_input = False
    c.yaml_file = yaml_file
    c._substitute_parameters = lambda cmd: cmd
    c._substitute_inputs = lambda cmd: cmd
    c._substitute_paths = lambda cmd: cmd
    return c


def _algorithm_with_commands(path, commands):
    """Build a mock ImageJob whose yaml_file declares the given commands."""
    alg_yaml = metadata.YamlFile(str(path / "alg.yaml"))
    alg_yaml.write_variable("commands", commands)
    img = mock.Mock()
    img.yaml_file = alg_yaml
    return img
```

Then append the new tests at the end of the file:

```python
def test_process_user_commands_prefers_inline_commands(tmp_path, monkeypatch):
    """Inline task commands win over the algorithm's, in both processing paths."""
    c = _make_container_with_yaml(tmp_path, {"commands": ["echo inline"]})
    img = _algorithm_with_commands(tmp_path, ["echo algorithm"])
    mock_image = mock.Mock(return_value=img)
    monkeypatch.setattr(c, "image", mock_image)

    for processed in (c._process_user_commands_for_reana(),
                      c._process_user_commands()):
        assert any("echo inline" in cmd for cmd in processed)
        assert not any("echo algorithm" in cmd for cmd in processed)

    mock_image.assert_not_called()


def test_process_user_commands_falls_back_to_algorithm(tmp_path, monkeypatch):
    """Without inline commands, the algorithm's commands are used."""
    c = _make_container_with_yaml(tmp_path, {})
    img = _algorithm_with_commands(tmp_path, ["echo algorithm"])
    monkeypatch.setattr(c, "image", lambda: img)

    for processed in (c._process_user_commands_for_reana(),
                      c._process_user_commands()):
        assert any("echo algorithm" in cmd for cmd in processed)


def test_process_user_commands_empty_when_neither(tmp_path, monkeypatch):
    """No inline commands and no algorithm means no user commands."""
    c = _make_container_with_yaml(tmp_path, {})
    monkeypatch.setattr(c, "image", lambda: None)

    assert c._process_user_commands_for_reana() == []
    assert c._process_user_commands() == []
```

- [ ] **Step 3: Run the tests to verify they fail**

Run: `cd /Users/wave/workdir/Celebi/Yuki && python -m pytest UnitTest/test_container_job.py -v`
Expected: FAIL — `test_process_user_commands_prefers_inline_commands`: "echo algorithm" appears instead of "echo inline" (algorithm preference today). The three pre-existing output-discovery tests stay green.

- [ ] **Step 4: Change `_process_user_commands_for_reana()` in `Yuki/kernel/container_job.py`**

Replace lines 121-124:

```python
        img = self.image()
        if img is not None:
            raw_commands = img.yaml_file.read_variable("commands", [])
        else:
            raw_commands = []
```

with:

```python
        raw_commands = self.yaml_file.read_variable("commands", [])
        if not raw_commands:
            img = self.image()
            if img is not None:
                raw_commands = img.yaml_file.read_variable("commands", [])
```

Also update the method docstring: change "Prepare and process user-defined commands for REANA execution." to "Prepare and process user-defined commands for REANA execution. The task's own celebi.yaml commands win over the linked algorithm's."

- [ ] **Step 5: Change `_process_user_commands()` in `Yuki/kernel/container_job.py`**

Replace lines 285-288:

```python
        img = self.image()
        if img is not None:
            raw_commands = img.yaml_file.read_variable("commands", [])
        else:
            raw_commands = []
```

with:

```python
        raw_commands = self.yaml_file.read_variable("commands", [])
        if not raw_commands:
            img = self.image()
            if img is not None:
                raw_commands = img.yaml_file.read_variable("commands", [])
```

- [ ] **Step 6: Run the tests to verify they pass**

Run: `cd /Users/wave/workdir/Celebi/Yuki && python -m pytest UnitTest/test_container_job.py -v`
Expected: PASS — all 6 tests.

- [ ] **Step 7: Commit in the Yuki repo**

```bash
cd /Users/wave/workdir/Celebi/Yuki
git add Yuki/kernel/container_job.py UnitTest/test_container_job.py
git commit -m "feat(job): prefer inline task commands in container jobs

Co-Authored-By: Claude Code <noreply@anthropic.com>"
```

---

### Task 9: Yuki full suite and final cross-check (both repos)

**Files:**
- None modified (verification only).

**Interfaces:**
- Consumes: Tasks 1-8.
- Produces: both suites green, spec coverage confirmed.

- [ ] **Step 1: Run the full Yuki suite**

Run: `cd /Users/wave/workdir/Celebi/Yuki && python -m pytest UnitTest/ -v`
Expected: PASS. If a failure is caused by Task 8, fix `container_job.py`; if unrelated, report it without touching.

- [ ] **Step 2: Re-run the Celebi suite once more (final state)**

Run: `cd /Users/wave/workdir/Celebi/Celebi/UnitTest && python -m pytest -v`
Expected: PASS.

- [ ] **Step 3: Spec coverage check**

Walk the spec (`docs/superpowers/specs/2026-08-29-inline-code-tasks-design.md`) and confirm each section maps to a completed task:

- §3.1 `task_commands()` + `env_validated()` → Tasks 1, 2
- §3.2 `VTask.commands()`, `code_path()`, untouched creators → Task 1
- §3.3 `_test_commands`, `_prepare_algorithm_code`, `workaround_preshell/postshell`, `_prepare_mounting_algorithm_code` → Task 3
- §3.4 `ls` commands section → Task 4
- §3.5 `add_algorithm` notice → Task 5
- §3.6 shell `code:` resolution → Task 6
- §4.1 Yuki `ContainerJob` precedence → Task 8
- §5 testing → Tasks 1-9

- [ ] **Step 4: Report**

Summarize per-repo commits and test results. Both branches (`inline-code-tasks` in Celebi and Yuki) are ready for review/merge.

---

## Self-Review Notes

- Spec §3.1's naming deviation (`task_commands()` vs `commands()`) is documented in Global Constraints; external behavior matches the spec.
- Task 4 keeps `show_algorithm()` printing commands so the pre-existing `test_core_algorithm_display` stays green — the spec's "add a Commands section" is realized by moving effective-command display into `show_algorithm()` and calling it for inline tasks too (same visible output).
- Task 8 helper sets instance-level lambdas for `_substitute_*` because tests construct via `__new__` (existing file pattern); `is_input` and `yaml_file` are set manually for the same reason.
