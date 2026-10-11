Runners & Environment
======================

Commands for configuring execution backends and environments.

* ``runners`` – List available runners
* ``register-runner`` – Register a new runner
* ``update-runner`` – Update an existing runner
* ``remove-runner`` – Remove a runner
* ``test-runner`` – Probe runner capabilities
* ``install-environment RUNNER NAME`` – Install or update a project environment
  on an SSH/IHEP runner from ``.celebi-env/NAME.yaml``
* ``runner-environments RUNNER`` – List the current project's environments on
  an SSH/IHEP runner (outside a project, list global environments for compatibility)
* ``set-environment`` – Configure execution environment
* ``set-memory-limit`` – Set task memory limits
* ``request-runner`` – Select the current task's runner
* ``auto-download on|off`` – Configure automatic result download
* ``cache-on-runner on|off`` – Configure runner-side result retention
* ``config`` – Edit the current task or algorithm's ``celebi.yaml``
* ``user-config`` – Create and edit your user settings (``~/.celebi/config.yaml``);
  ``--list`` shows the settings in force without opening an editor

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

Install it on a registered SSH or IHEP runner:

.. code-block:: console

   celebi-cli install-environment ihep analysis

Use ``--file PATH`` to read a different YAML file. Celebi always installs the
environment under
``<remote_workdir>/environments/<project_uuid>/<environment_name>``; therefore
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
retain their existing behavior. REANA and native runner installation are not
supported by this command.
