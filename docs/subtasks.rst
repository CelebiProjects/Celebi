Repeated tasks
==============

Set ``subtasks`` in a task's ``celebi.yaml`` to run the same computation N times:

.. code-block:: yaml

   environment: my-environment
   memory_limit: 256Mi
   subtasks: 100
   parameters:
     events: 1000
   commands:
     - python code/simulate.py --index ${index} --events ${events} --output stageout/index/a.root

The task remains an ordinary Celebi Task with one impression and one set of
shared dependencies. Yuki generates a Snakemake wildcard rule for indices
``0`` through ``N - 1`` and a completion rule that waits for every execution.
Commands may come from the task itself or a linked algorithm. ``${index}``
is replaced with the current integer's decimal representation; when parsing
command-line arguments in Python, use ``type=int``.

``subtasks`` must be a positive YAML integer (not a string or boolean).
The parameter name ``index`` is reserved only when ``subtasks`` is present.
Data-only environments and the special ``htcondorcern`` compute backend do
not support repeats. This feature requires the corresponding Yuki update;
older servers do not expand ``subtasks``.
Use workflow ``submit`` to execute repeats; ``docker-test``, ``ssh-test`` and
``workaround`` do not expand repeated tasks and reject them explicitly.

Output paths
------------

Each execution has its own working directory. Write outputs through the
literal path ``stageout/index/``: the word ``index`` is a directory name,
not a variable to substitute. The runner links that directory directly to
the numbered output directory for the current execution:

.. code-block:: text

   execution 0: stageout/index/a.root -> Task stageout/0/a.root
   execution 1: stageout/index/a.root -> Task stageout/1/a.root

No output relocation is required. Runner caches, collected results and
downstream aliases all preserve ``stageout/<number>/...``. Even ``subtasks: 1``
uses ``stageout/0/``. Omitting ``subtasks`` retains ordinary Task behavior
and the existing ``stageout/...`` output paths.

The isolated working directories avoid accidental output collisions. They
are not a security sandbox: native/SSH commands retain the filesystem access
of the runner account. Shared code and inputs must be treated as read-only;
this feature does not introduce operating-system access controls.

Inputs and aliases
------------------

An alias always references the entire upstream Task. Connect it normally:

.. code-block:: bash

   celebi-cli add-input ../simulation input

All repeats may read a normal upstream file at ``input/stageout/a.root``.
To pair repeats by index, read ``input/stageout/${index}/a.root`` in the
command. A normal reduction task can read ``input/stageout/*/a.root``.
Parameters that represent paths remain relative to the alias root, for
example ``stageout/${index}/a.root``. Downstream tasks wait for the entire
upstream Task, not just one matching index. A shell expands ``*``; programs
receiving a quoted pattern must expand it themselves.

Logs, completion and retries
----------------------------------------

Logs are stored under ``logs/<index>/``. After log collection, inspect a
command's log with:

.. code-block:: bash

   celebi-cli log 0 --subtask 7
   celebi-cli log 0 --subtask 7 --follow

The first argument selects the command, and ``--subtask`` selects the repeat.
The interactive shell accepts the same option. Each instance also records
``running``, ``failed`` or ``finished`` in ``logs/<index>/status``; an execution
that has not started has no status file. Abrupt process termination can leave
``running`` behind, so the workflow's terminal status remains authoritative.

Each repeat has its own Snakemake completion marker. Re-running Snakemake
in the same workspace with ``--rerun-incomplete`` retries failed or missing
instances while preserving successful ones. A fresh Celebi submission may
create a new workflow workspace and run all instances again. Cross-workflow
per-index reuse and a dedicated index retry CLI are not provided.

The Task's completion marker and runner cache are published only after all
repeats succeed. Changing ``subtasks`` changes the Task impression; no
additional subtask impressions or Yuki jobs are registered.

For a complete three-Task example with partitioned inputs at
``toys/stageout/${index}/*.json``, see :doc:`examples/gaussian-toys`.
