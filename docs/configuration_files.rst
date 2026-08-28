Configuration File Formats
==========================

Celebi uses YAML files for configuration. This section documents the typical
file formats you'll encounter when working with Celebi projects.

Global Configuration (``~/.celebi/config.yaml``)
-----------------------------------------------

The global configuration file stores user preferences and is located in
the user's home directory under ``~/.celebi/``.

Run ``user-config`` to create it. The file is generated from a documented
template listing every available setting at its default value, then opened in
your editor. An existing file is never rewritten, so your edits and comments
always survive. ``user-config --list`` prints the settings in force, marking
each as ``set`` or ``default``, without opening an editor.

Any setting omitted from the file falls back to its built-in default, so it is
safe to delete a line rather than guess a value.

**Example:**

.. code-block:: yaml

    editor: code
    browser: firefox
    default_runner: farm

**Fields:**

*Programs*

* ``editor`` – Editor used by ``config``, ``edit-script``, ``readme`` and
  merge-conflict resolution (e.g., ``code``, ``vim``, ``nano``). Default: ``vi``
* ``file_opener`` – Program used to open a local file, e.g. by
  ``view local:...``. Default: ``open`` on macOS, ``xdg-open`` elsewhere
* ``browser`` – Command used to open a URL. Leave empty to use the system
  default browser. Default: empty

*Defaults for newly created tasks*

These are applied when a task is created and recorded on that task. Existing
tasks keep whatever they were created with — changing a setting never rewrites
a task that already exists.

* ``default_runner`` – Runner assigned to new tasks. Default: ``local``
* ``auto_download`` – Whether new tasks download outputs automatically.
  Default: ``true``
* ``cache_on_runner`` – Whether new tasks cache results on the runner.
  Default: ``false``
* ``task_environment`` – Environment written into a new task's ``celebi.yaml``.
  Default: ``reanahub/reana-env-root6:6.18.04``
* ``algorithm_environment`` – Environment written into a new algorithm's
  ``celebi.yaml``. Default: ``script``

*Output*

* ``dag_output_dir`` – Directory where ``draw-dag`` writes its output.
  Default: ``~/Downloads``

.. warning::

   ``task_environment`` and ``algorithm_environment`` are written **into**
   ``celebi.yaml``, which is hashed into the object's impression. Two people
   with different settings will therefore create tasks with different
   impressions. That difference is visible in the committed ``celebi.yaml``,
   so it is reviewable — but for a shared project, agree on a value.

   Deliberately, these settings are consulted only when a file is *written*.
   Reading an ``environment`` never falls back to them: if it did, two users
   could share an impression id while executing in different environments.

.. note::

   ``user-config`` edits your own user-level settings. The similarly named
   ``config`` command edits the *current task or algorithm's* ``celebi.yaml``,
   documented below.


Task Configuration (``celebi.yaml``)
------------------------------------

Each task directory contains a ``celebi.yaml`` file that defines the task's
execution environment, parameters, and input aliases.

**Minimal example (task with defaults):**

.. code-block:: yaml

    alias: []
    environment: reanahub/reana-env-root6:6.18.04
    kubernetes_memory_limit: 256Mi

**Example with parameters:**

.. code-block:: yaml

    alias: []
    environment: reanahub/reana-env-root6:6.18.04
    kubernetes_memory_limit: 256Mi
    parameters:
      events: '20000'

**Example with input aliases:**

.. code-block:: yaml

    alias:
    - gen
    environment: reanahub/reana-env-root6:6.18.04
    kubernetes_memory_limit: 256Mi
    parameters: {}

**Field descriptions:**

* ``alias`` – List of short names for input dependencies (empty list if none)
* ``environment`` – Docker image or execution environment identifier
* ``kubernetes_memory_limit`` – Memory limit for Kubernetes execution (e.g., ``256Mi``, ``1Gi``)
* ``parameters`` – Dictionary of parameter names and their values (empty ``{}`` if none)


Algorithm Configuration (``celebi.yaml``)
-----------------------------------------

Algorithm directories also use ``celebi.yaml`` but with a different structure
focused on execution commands rather than parameters.

**Example (algorithm with script environment):**

.. code-block:: yaml

    environment: script
    commands:
      - root -b -q 'code/gendata.C(${events},"outputs/data.root")'

**Example (algorithm with Docker environment):**

.. code-block:: yaml

    environment: reanahub/reana-env-root6:6.18.04
    commands:
      - root -b -q 'code/analysis.C("inputs/data.root","outputs/plot.png")'

**Field descriptions:**

* ``environment`` – Execution environment: ``script`` for local execution or Docker image name
* ``commands`` – List of shell commands to execute; use ``${parameter}`` syntax for parameter substitution


Project Configuration (``.celebi/config.json``)
-----------------------------------------------

Each project contains a ``config.json`` file (note: JSON format, not YAML)
in the ``.celebi/`` directory at the project root.

**Example:**

.. code-block:: json

    {
        "object_type": "project",
        "chern_version": "4.0.0",
        "project_uuid": "b50a736ddde44f8cbbcc773b9a075adb"
    }

**Field descriptions:**

* ``object_type`` – Always ``"project"`` for project configuration
* ``chern_version`` – Version of Celebi that created the project
* ``project_uuid`` – Unique identifier for the project


Task/Directory Configuration (``.celebi/config.json``)
------------------------------------------------------

Each task and directory also contains a ``config.json`` file in its
``.celebi/`` subdirectory.

**Example (task):**

.. code-block:: json

    {
        "object_type": "task",
        "auto_download": true,
        "default_runner": "local"
    }

**Example (directory):**

.. code-block:: json

    {
        "object_type": "directory"
    }

**Common fields:**

* ``object_type`` – Type of object: ``"task"``, ``"directory"``, or ``"algorithm"``
* ``auto_download`` – Whether to automatically download outputs (tasks only)
* ``default_runner`` – Default execution runner (e.g., ``"local"``, ``"reana``")


README Files (``README.md``)
----------------------------

While not YAML, each object (project, directory, task, algorithm) contains
a ``README.md`` file for documentation.

**Example:**

.. code-block:: markdown

    # Fit Task

    This task performs a crystal ball fit on the generated J/psi data.

    ## Inputs

    - gen: Generated MC data

    ## Outputs

    - fit_result.png: Fit visualization
    - fit_params.json: Fit parameters


Complete Project Example
------------------------

A typical Celebi project structure with configuration files:

.. code-block:: text

    my_project/
    ├── README.md
    ├── celebi.yaml              # (if project-level config needed)
    ├── .celebi/
    │   └── config.json          # Project metadata
    ├── algorithms/
    │   ├── gen_data/
    │   │   ├── README.md
    │   │   ├── celebi.yaml      # Algorithm config with commands
    │   │   └── code/
    │   └── fit_data/
    │       ├── README.md
    │       ├── celebi.yaml
    │       └── code/
    └── tasks/
        ├── generate/
        │   ├── README.md
        │   ├── celebi.yaml      # Task config with parameters
        │   └── .celebi/
        │       └── config.json
        └── fit/
            ├── README.md
            ├── celebi.yaml
            └── .celebi/
                └── config.json
