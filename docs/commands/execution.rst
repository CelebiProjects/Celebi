Execution and results
=====================

Run workflows
-------------

* ``submit --runner RUNNER`` submits the current task and its dependencies.
* ``test [docker|ssh] [RUNNER]`` tests the current task without creating an
  official impression. SSH tests stream output from the chosen SSH runner.
* ``cancel`` cancels running impressions selected by the current task or
  directory.
* ``status --wait`` waits until the relevant workflows reach a terminal state.

Logs and file listings
----------------------

* ``log [INDEX]`` reads a user-command log; ``--follow`` polls for new output.
* ``engine-logs`` reads workflow-engine diagnostics.
* ``refresh-filelists`` forces Yuki to re-list stageout and log files on the
  runner. This is useful after a terminal workflow's saved listing has frozen.

Selective collection
--------------------

``collect`` copies results from the runner into Yuki Storage. Its selector is:

* no argument: plots plus logs (the lightweight default);
* ``all``: all stageout files plus logs;
* ``plots``, ``data`` or ``logs``: the named class;
* a filename or glob: matching stageout files.

For example:

.. code-block:: console

   celebi-cli collect
   celebi-cli collect plots
   celebi-cli collect '*.root'
   celebi-cli collect all

``collect --allow-failed`` permits diagnostic stageout from a failed workflow;
those files are not official results. ``collect-outputs`` and ``collect-logs``
provide compatibility shortcuts for full stageout or logs.

Inspect and export
------------------

* ``check-results RUNNER`` mounts an SSH runner's managed cache in a temporary
  remote directory for manual inspection.
* ``export [GLOB]`` copies matching collected results into the project's export
  directory.
* ``imgcat FILE`` displays a collected image in a compatible terminal.
