# Inline-Code Tasks — Design Spec

Date: 2026-08-29
Branch: `inline-code-tasks` (Celebi), same-name branch in Yuki
Status: approved in design chat; awaiting final spec review

## 1. Motivation

Today a Celebi task is only runnable when it is linked to an algorithm
object: the task's commands come from the algorithm's `celebi.yaml`, and
the algorithm's directory holds the code. Users want tasks that carry their
own code directly in the task directory, with the task's own `celebi.yaml`
declaring `commands` — no algorithm object required.

## 2. The shared rule

A task's runnable commands resolve as:

1. `commands` from the **task's own** `celebi.yaml`, if non-empty;
2. otherwise `commands` from the **linked algorithm's** `celebi.yaml`, if an
   algorithm is linked;
3. otherwise none.

The same rule is implemented on the Celebi client and the Yuki server, so
both sides agree on what runs.

Consequences:

- Inline-code tasks (code in the task dir, no algorithm) run entirely from
  their own yaml.
- A task with **both** an algorithm and its own commands runs its own
  commands; the algorithm stays linked but its commands are shadowed. The
  client shows a notice when an algorithm is added to such a task.
- Tasks with neither (rawdata/datalist data nodes) behave exactly as today.

## 3. Celebi client changes

### 3.1 `CelebiChrono/kernel/vtask_setting.py`

- New `commands()` — reads the task yaml `commands`, default `[]`
  (mirrors `VAlgorithm.commands()`).
- `env_validated()` (currently line 132) becomes:

  1. `environment` in `("rawdata", "datalist", "lhcb_ap_datalist")` → valid
     (unchanged);
  2. task-level `commands` non-empty → valid iff `environment` is non-empty;
  3. an algorithm is linked → existing algorithm-environment matching rules
     (including `environment == "script"`), unchanged;
  4. otherwise → invalid.

  `validated()` is unchanged (it is just `env_validated()`).

### 3.2 `CelebiChrono/kernel/vtask.py`

- `VTask.commands()` overrides the SettingManager method as the effective
  resolver: task-level if non-empty → else `algorithm().commands()` if an
  algorithm is linked → else `[]`.
- New `VTask.code_path()` — the editable/runtime code root:
  - `self.path` when task-level commands are non-empty;
  - else `algorithm.path` if an algorithm is linked;
  - else `None`.
- `create_task`, `create_rawdata_task`, `create_data`, `create_data_list`,
  `create_lhcb_ap_data_list` unchanged — `commands` simply defaults to
  absent/empty.

### 3.3 `CelebiChrono/kernel/vtask_job.py`

- `_test_commands()` (line 93): use effective `self.commands()` instead of
  `self.algorithm().commands()`.
- `_prepare_algorithm_code()` (line 690): when the task is inline
  (task-level commands non-empty), copy `tree_excluded(self.path)` into the
  workaround `code/` tree and symlink it; skip algorithm-input linking
  (an algorithm-only concept).
- `workaround_preshell()` (line 778): build `exec.sh` from effective
  commands with the existing `${param}` substitution; keep the conda
  preamble logic driven by the task's own `environment`.
- `workaround_postshell()` (line 982): sync origin = `code_path()` instead
  of hardcoded `algorithm.path`. Safety: `tree_excluded` keeps `celebi.yaml`
  in the filelist (synced back, never deleted) and excludes `README.md` and
  `.celebi` from both the copy and the delete scan.
- `_prepare_mounting_algorithm_code()` (line 921, docker-test mounts): when
  the task is inline, copy the task's own tree
  (`tree_excluded(self.path)`) and mount it at `/workspace/code`; otherwise
  unchanged. Task commands referencing `code/...` therefore work
  identically in docker tests.

### 3.4 `CelebiChrono/kernel/vtask_core.py`

- `ls()` (line 34): keep the "Algorithm files" section when an algorithm is
  linked; add a "Commands" section printing effective commands with
  `${param}` substitution whenever non-empty. Inline tasks' code files
  already appear under "Task files".

### 3.5 `CelebiChrono/kernel/vtask_input.py`

- `add_algorithm()` (line 45): print a notice when the task already has its
  own commands — task commands take precedence.

### 3.6 `CelebiChrono/interface/shell_modules/task_configuration.py`

- `code:`/`code/` path resolution (line ~580): when the task is inline (no
  algorithm), resolve to the task directory itself.

### 3.7 Untouched on Celebi

`VAlgorithm`, `create_algorithm`, impressions/deposit/submit, `doctor`,
`VProject`, and the DITE protocol. The impression of a task already
snapshots the task's full file tree including `celebi.yaml`
(`VImpression.create`), so inline code and commands reach the server with
no impression-format change.

## 4. Yuki server changes

### 4.1 `Yuki/kernel/container_job.py`

A task job's `yaml_file` is the task impression's own
`contents/celebi.yaml`. User commands are currently read from the algorithm
predecessor's yaml in two places:

- `_process_user_commands_for_reana()` (line 122) — REANA path;
- `_process_user_commands()` (line 285) — native path.

In both methods, apply the shared rule using the task's own yaml first:

```python
raw_commands = self.yaml_file.read_variable("commands", [])   # task's own
if not raw_commands:
    img = self.image()
    if img is not None:
        raw_commands = img.yaml_file.read_variable("commands", [])
```

Parameter/input/path substitution afterwards is unchanged — it already
operates on the task's own `parameters()` from the task yaml, which is
correct for inline commands.

### 4.2 Verified to need no change on Yuki

- `VJob.environment()` (`vjob.py:129`) reads the task's own yaml
  `environment` — inline tasks get their runtime environment for free.
- Job factory (`vjob.py:__new__`): a task impression becomes a
  `ContainerJob` regardless of algorithms; no algorithm requirement exists.
- `ImpressionStorage.get_info()` (`impression_storage.py:339`) only reports
  runner context; workflow creation goes through `ContainerJob.step()`,
  which is the code changed above.
- Data-flavor handling in `step()` keys off the task's own `environment()`.
- `reana_booker.py` and `upload.py:436` already read each impression's own
  `celebi.yaml`; inline tasks' yaml flows through untouched.

## 5. Testing

### Celebi (`UnitTest/`, unittest style)

- `commands()` precedence: task-level wins over a linked algorithm; falls
  back to the algorithm when the task yaml has none; `[]` when neither.
- `env_validated()`: inline task with commands + environment → valid;
  commands but empty environment → invalid; no commands, no algorithm,
  non-data environment → invalid; data flavors unchanged;
  algorithm-backed rules unchanged.
- Workaround for an inline task: `code/` tree contains the task's files;
  `workaround_postshell` syncs back to the task dir and leaves
  `celebi.yaml`, `README.md`, `.celebi` intact.
- `ls` shows effective commands for inline tasks.
- `add_algorithm` prints the precedence notice when the task has its own
  commands.
- The full existing suite stays green.

### Yuki (`UnitTest/`, unittest style)

- `ContainerJob` command resolution in both
  `_process_user_commands_for_reana` and `_process_user_commands`: inline
  commands used when present; algorithm fallback when the task yaml has
  none; empty when neither. Follow existing mock style.
- The full existing suite stays green.

## 6. Out of scope

- No task-level `build` field (build stays algorithm-only).
- No `create-task` flag or default `commands` key in new-task YAML.
- No client/server feature detection for version skew — both sides ship in
  lockstep.
- No changes to `VAlgorithm`, impressions, deposit/submit, `doctor`,
  `VProject`, or the DITE protocol.

## 7. Risks

- **Both-sources tasks**: workaround/docker-test mount only the task dir
  (the winning source); algorithm files are not mounted in that case.
  Accepted.
- **Legacy yamls**: a hand-edited task yaml that already contains a
  `commands` key would switch behavior. Celebi never writes `commands` for
  tasks today, so exposure is limited to hand edits; the `add_algorithm`
  notice covers discoverability.
- **Workaround deletion scan**: for inline tasks the postshell deletes
  origin files not in the filelist. `tree_excluded` keeps `celebi.yaml` in
  the filelist and excludes `README.md`/`.celebi` on both sides, so
  bookkeeping files are safe.

## 8. Delivery

- Celebi branch `inline-code-tasks` (created from clean `master`).
- Yuki branch of the same name, created at implementation time.
- Flow: spec review (this document) → implementation plan
  (writing-plans) → TDD implementation with review checkpoints.
