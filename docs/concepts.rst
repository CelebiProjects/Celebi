Concepts
========

Project and objects
-------------------

A project is a filesystem tree with metadata in ``.celebi/``. Directories
organize the tree, algorithms contain reusable code and commands, and tasks
bind algorithms, inputs, parameters and an execution environment. A data
object is represented by a specialized task, such as ``rawdata``, ``datalist``
or ``lhcb_ap_datalist``.

Inputs and aliases
------------------

Tasks form a directed acyclic graph. ``add-input`` records a predecessor and
an alias. During execution the predecessor's staged output is available below
``<alias>/stageout/``. ``predecessors``, ``successors`` and ``draw-dag`` show
the resulting graph.

Repeated tasks
--------------

A Task may declare ``subtasks: N`` to repeat its computation with integer
``index`` values from zero to N - 1. It remains one Task and one impression;
Yuki expands it into a Snakemake wildcard rule. Each instance writes through
the literal path ``stageout/index/``, which maps to ``stageout/<number>/`` in
caches, collected results and downstream aliases. See :doc:`subtasks`.

Impressions
-----------

An impression is the content-addressed snapshot used for reproducibility. It
includes relevant object files, configuration, dependencies and environment.
Changing any of those inputs can create a new impression. Local impression
objects use content-addressed storage (CAS), allowing identical content to be
deduplicated.

Yuki, runners and storage
-------------------------

Yuki records impressions, constructs workflows and coordinates runners.
Runners execute the workflow and may retain a cache. Collected results live in
Yuki Storage; ``whereabouts`` reports which copies exist. ``transfer`` moves
stageout files between Yuki and managed runner caches.

Project environments
--------------------

Shareable Conda specifications live in ``.celebi-env/``. The directory is
created automatically by ``celebi-cli init``. Installing
``.celebi-env/analysis.yaml`` with ``install-environment RUNNER analysis``
creates a project-scoped environment on SSH, IHEP or native runners.
