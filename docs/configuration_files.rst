Configuration File Formats
==========================

Celebi uses YAML files for configuration. This section documents the typical
file formats you'll encounter when working with Celebi projects.

Global Configuration (``~/.celebi/config.yaml``)
-----------------------------------------------

The global configuration file stores user preferences and is located in
the user's home directory under ``~/.celebi/``.

**Example:**

.. code-block:: yaml

    editor: code

**Common fields:**

* ``editor`` – Default editor for editing files (e.g., ``code``, ``vim``, ``nano``)


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
