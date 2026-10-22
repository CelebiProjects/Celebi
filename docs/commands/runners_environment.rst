Runners & Environment
======================

Commands for configuring execution backends and environments.

* ``runners`` – List available runners
* ``register-runner`` – Register a new runner
* ``update-runner`` – Update an existing runner
* ``remove-runner`` – Remove a runner
* ``test-runner`` – Probe runner capabilities (including native agent liveness)
* ``install-environment RUNNER NAME`` – Install or update a project environment
  on an SSH/IHEP/native runner from ``.celebi-env/NAME.yaml``
* ``runner-environments RUNNER`` – List the current project's environments on
  an SSH/IHEP/native runner (outside a project, list global environments for compatibility)
* ``yuki-overview`` – Summarize runner state, capacity and current usage
* ``hosts`` / ``add-host`` – Inspect and configure communicator hosts
* ``refresh-distribution`` – Rebuild the project's data-location registry
* ``set-environment`` – Configure execution environment
* ``set-memory-limit`` – Set task memory limits
* ``request-runner`` – Select the current task's runner
* ``auto-download on|off`` – Configure automatic result download
* ``cache-on-runner on|off`` – Configure runner-side result retention
* ``config`` – Edit the current task or algorithm's ``celebi.yaml``
* ``user-config`` – Create and edit your user settings (``~/.celebi/config.yaml``);
  ``--list`` shows the settings in force without opening an editor
* ``cache-policy [auto|mtime|off]`` – Inspect or select the project's local
  cache invalidation policy

Project environments
--------------------

Place a standard Conda environment file in the project, for example:

.. code-block:: yaml

   # .celebi-env/analysis.yaml
   name: ignored-by-celebi
   channels:
     - conda-forge
   dependencies:
     - python=3.12
     - numpy

``celebi-cli init`` creates the ``.celebi-env/`` directory automatically.

Install it on a registered SSH, IHEP, or native runner:

.. code-block:: console

   celebi-cli install-environment ihep analysis

Use ``--file PATH`` to read a different YAML file. Celebi always installs the
environment under
``<runner-workdir>/environments/<project_uuid>/<environment_name>``; therefore
two projects using the same logical name do not share a prefix. The YAML
``name`` field does not select the prefix. Repeating the command runs
``conda env update --prune`` and is the supported way to update the trusted,
mutable environment.

After installation, use the logical name in the task or algorithm:

.. code-block:: console

   celebi-cli set-environment analysis
   celebi-cli runner-environments ihep

Explicit legacy mappings in Yuki's ``conda_env_map`` remain valid. The reserved
environments ``script``, ``rawdata``, ``datalist``, and ``lhcb_ap_datalist``
retain their existing behavior. REANA installation is not supported by this command.

For native runners, ``<runner-workdir>`` defaults to ``~/.Yuki/LocalWorkflows``.
Native workflow workspaces live separately below
``<runner-workdir>/workflows/<project_uuid>/<workflow_uuid>``. Submission checks
that a referenced managed environment is installed before the native workflow is
queued and reports the corresponding ``install-environment`` command when missing.

Native execution and Yuki Storage are one storage domain: successful stage-out is
collected directly into Yuki Storage. Consequently native has no separate managed
runner cache, is not a ``transfer`` endpoint (use ``yuki``), and
``cache-on-runner`` has no additional effect for native execution.
