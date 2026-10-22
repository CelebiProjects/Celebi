Configuration files
===================

Celebi uses YAML for user-editable workflow configuration and JSON for its
internal metadata. Share the YAML and ``.celebi/config.json`` files in version
control. Files named ``config.local.json`` contain machine-local settings or
credentials and must remain uncommitted.

User configuration
------------------

User preferences live in ``~/.celebi/config.yaml``. Create or edit the file
with ``celebi-cli user-config``; inspect effective values with
``celebi-cli user-config --list``. Missing settings use built-in defaults.

.. code-block:: yaml

   editor: code
   browser: firefox
   default_runner: local
   auto_download: true
   cache_on_runner: false
   task_environment: reanahub/reana-env-root6:6.18.04
   algorithm_environment: script
   dag_output_dir: ~/Downloads

``editor``, ``file_opener`` and ``browser`` control external programs.
``default_runner``, ``auto_download``, ``cache_on_runner`` and
``task_environment`` are copied into newly created tasks; changing them does
not rewrite existing tasks. ``algorithm_environment`` is the default written
when an algorithm environment is needed. ``dag_output_dir`` controls where
``draw-dag`` writes output.

Task configuration
------------------

A newly created task has this ``celebi.yaml`` shape:

.. code-block:: yaml

   descriptor: fit
   environment: reanahub/reana-env-root6:6.18.04
   memory_limit: 256Mi

Tasks may also contain parameters, inline commands and their input alias list:

.. code-block:: yaml

   descriptor: fit
   environment: analysis
   memory_limit: 2Gi
   alias:
     - data
   parameters:
     events: "20000"
   commands:
     - python fit.py inputdata/data/result.root stageout/fit.png

``memory_limit`` is the current field. ``kubernetes_memory_limit`` is accepted
only for compatibility with older projects. Input paths themselves are stored
in ``.celebi/config.json``; ``alias`` records the stable names that contribute
to the impression.

An inline-code task has its own ``commands`` and source files. Otherwise use
``add-algorithm`` to link reusable algorithm code.

Algorithm configuration
-----------------------

Algorithm source files live directly in the algorithm directory. At runtime
that directory is exposed as ``code/``, which is why commands refer to paths
such as ``code/analysis.py``.

.. code-block:: yaml

   descriptor: fit-code
   environment: analysis
   commands:
     - python code/analysis.py inputdata/data/result.root stageout/fit.png

``commands`` is a list of shell commands. ``${parameter}`` expands a task
parameter. An algorithm can also contain build configuration used by the
execution backend.

Data-list configuration
-----------------------

A normal or XRootD-backed datalist uses the reserved ``datalist`` environment:

.. code-block:: yaml

   descriptor: collision-data
   environment: datalist
   datalist:
     - root://xrootd.example/path/file-001.root
     - root://xrootd.example/path/file-002.root
   data_source:
     type: xrootd
     url: root://xrootd.example/path
   manifest:
     checksum_policy: auto

For registered XRootD data, Celebi/Yuki writes the frozen file inventory and
manifest. Do not regenerate it manually. When the datalist task runs, Yuki
creates both ``stageout/filelist.txt`` and the compatibility name
``stageout/dataList.txt``.

Project metadata
----------------

``.celebi/config.json`` contains shared project metadata:

.. code-block:: json

   {
     "object_type": "project",
     "chern_version": "1.0.0b4",
     "project_uuid": "b50a736ddde44f8cbbcc773b9a075adb"
   }

The version is written from the installed Celebi package; do not copy the
example value into a project. Tasks, algorithms and directories have their own
``.celebi/config.json`` files with object type and relationship metadata.
Machine-local task settings such as the requested runner are written through
the two-tier configuration and are not a substitute for ``celebi.yaml``.

Project layout
--------------

.. code-block:: text

   my-project/
   ├── .celebi/
   │   ├── config.json
   │   └── hosts.json
   ├── .celebi-env/
   │   └── analysis.yaml
   ├── README.md
   ├── algorithms/
   │   └── fit/
   │       ├── .celebi/config.json
   │       ├── README.md
   │       ├── celebi.yaml
   │       └── analysis.py
   └── tasks/
       └── fit/
           ├── .celebi/config.json
           ├── README.md
           └── celebi.yaml

``celebi-cli init`` creates ``.celebi/``, ``.celebi-env/`` and the project
README. There is no project-level ``celebi.yaml`` and no required ``code/``
subdirectory inside algorithms.
