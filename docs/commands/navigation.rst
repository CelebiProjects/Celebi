Navigation and file management
==============================

Project registry
----------------

* ``init`` initializes the current empty directory, creates ``.celebi/`` and
  ``.celebi-env/``, registers the project and selects it.
* ``list-projects`` lists registered projects; ``use-project PROJECT`` selects
  one for subsequent sessions.
* ``register-project PATH`` registers an existing project and
  ``remove-project PROJECT`` removes only its registry entry.
* ``project-path`` and ``project-uuid`` print the selected project's path and
  stable identifier.

The interactive-shell equivalents ``ls-projects`` and ``cd-project`` remain
available. ``cd`` is intentionally shell-only because a child
``celebi-cli`` process cannot change its parent's directory.

Browse and inspect
------------------

* ``ls`` and ``short-ls`` describe the current object.
* ``tree`` displays the project hierarchy.
* ``status [--wait]`` shows execution status and optionally waits for a
  terminal state.
* ``predecessors`` and ``successors`` inspect dependency edges.
* ``draw-dag`` renders the dependency graph with Graphviz.

Files and content
-----------------

* ``cat FILE`` prints text and ``display FILE`` opens a result file.
* ``edit`` edits a script; ``edit-readme`` edits object documentation.
* ``comment`` appends a comment to the current object.
* ``import`` and ``add-source`` bring files or source trees into an object.
* ``cp``, ``mv`` and ``rm`` operate on project objects.
* ``move-file`` and ``remove-file`` operate within a task or algorithm.
* ``replace A B`` replaces names, inputs and parameter references across the
  selected scope. Review the proposed changes carefully.
