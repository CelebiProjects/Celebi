Commands
==========

Celebi has three command entry points:

* ``celebi`` enters the persistent interactive shell. Commands such as ``cd``
  and ``cd-project`` belong here because their effect must survive the command.
* ``celebi-cli COMMAND`` runs one operation and is suitable for scripts.
* ``celebi-git COMMAND`` contains Git integration commands.

Inside the interactive shell, ``helpme`` explains the current object and suggests
the next operations. These three forms share the same detailed command help:

.. code-block:: text

   help status
   helpme status
   status --help

Bare ``help`` lists commands by workflow category. ``celebi-cli --help`` uses the
same categories and shows old spellings separately under compatibility aliases.

.. toctree::
   :maxdepth: 2
   :caption: Commands

   commands/navigation
   commands/algorithms_tasks
   commands/execution
   commands/runners_environment
   commands/visualization_provenance
