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
