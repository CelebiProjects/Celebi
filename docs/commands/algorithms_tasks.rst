Algorithms and tasks
====================

Create objects
--------------

* ``create-algorithm PATH`` creates a reusable algorithm directory.
* ``create-task PATH`` creates one task; ``create-multi-tasks BASE STOP``
  creates a half-open numbered range and sets each ``index`` parameter.
* ``mkdir PATH`` creates an organizational Celebi directory.
* ``create-data NAME`` creates a raw-data object.
* ``create-data-list NAME`` creates a frozen/manual datalist task.
* ``create-lhcb-ap-list NAME`` creates a list populated through LHCb Analysis
  Productions at runtime.
* ``create-multi-data PATH`` creates and uploads a data object for every child
  directory.

Configure execution
-------------------

* ``add-algorithm ALGORITHM`` links an algorithm to the current task. It is
  valid only in a task context.
* ``add-input PATH ALIAS`` and ``remove-input ALIAS`` manage dependencies.
* ``add-multi-inputs`` and ``remove-multi-inputs`` manage numbered,
  half-open ranges of aliases.
* ``set-parameter NAME VALUE`` and ``remove-parameter NAME`` edit task
  parameters; ``add-parameter-subtask`` targets a specific descendant.
* ``set-environment ENVIRONMENT``, ``set-memory-limit LIMIT`` and
  ``set-descriptor TEXT`` update the corresponding ``celebi.yaml`` fields.
* ``request-runner RUNNER`` chooses the task's default runner.
* ``auto-download on|off`` and ``cache-on-runner on|off`` control result
  placement for future submissions.
* ``config`` opens the current task or algorithm's ``celebi.yaml``.

Tasks may run commands from a linked algorithm or define ``commands`` and
source files directly as an inline-code task. Use ``celebi-cli COMMAND --help``
for the exact range syntax and context restrictions.

An ``lb_run`` mapping wraps effective commands in an LHCb release. It accepts
required ``project`` and ``version`` fields plus optional ``platform`` and
``nightly`` fields. The task and its effective command source must both use
``environment: lb-run``; an inline-code task is its own command source and
does not need an algorithm. See :doc:`../configuration_files`.

Repeated execution of one task is configured with ``subtasks: N`` in its YAML.
This retains one Task/impression and supplies ``${index}``; it does not create
the independent objects produced by ``create-multi-tasks``. Write repeated
outputs to literal ``stageout/index/``. See :doc:`../subtasks`.

APD on SSH runners
------------------

An ``environment: lhcb_ap_datalist`` task automatically uses CVMFS
``lb-conda default`` on SSH runners. No linked algorithm or local APD Conda
installation is required. REANA continues to use the existing APD image.
To pin a CVMFS release, set ``ap_config.lb_conda: default/2026-09-17``.
The optional value accepts a package or package/date, without the ``lb-conda/``
prefix. Existing APD queries and ``stageout/dataList.txt`` are unchanged.
Use ``celebi-cli add-apd-token`` for authentication; the token stays outside
versioned configuration and is injected as ``APD_USER_TOKEN_FILE``.


Per-submission core budget
~~~~~~~~~~~~~~~~~~~~~~~~~~

Use ``celebi-cli submit --runner pkufarm212 --cores 16`` (or
``submit --runner pkufarm212 --cores 16`` in the interactive shell) to set
this workflow's Snakemake core budget. ``--cores`` accepts a positive integer.
It overrides the runner default for this submission only; omission preserves
the runner setting. Native, SSH and IHEP backends support it; REANA rejects it.
This is a workflow scheduling budget, not a thread count for each command.
It does not resize an already active workflow or force completed work to rerun.
