Quick start
===========

Create an empty directory and initialize it as a project:

.. code-block:: console

   mkdir my-analysis
   cd my-analysis
   celebi-cli init

Initialization creates ``.celebi/``, ``.celebi-env/`` and ``README.md``, then
registers and selects the project. The directory must be empty.

Create a simple workflow
------------------------

.. code-block:: console

   celebi-cli create-algorithm algorithms/hello
   celebi-cli create-task tasks/hello
   cd tasks/hello
   celebi-cli add-algorithm @/algorithms/hello
   celebi-cli set-environment script

Edit ``algorithms/hello/celebi.yaml`` and add a command:

.. code-block:: yaml

   descriptor: hello
   environment: script
   commands:
     - mkdir -p stageout && echo "hello" > stageout/message.txt

Run and inspect it
------------------

.. code-block:: console

   celebi-cli test
   celebi-cli submit --runner RUNNER
   celebi-cli status --wait
   celebi-cli collect all
   celebi-cli export message.txt

The interactive ``celebi`` shell provides the same object-aware operations.
Use ``helpme`` inside it, or ``celebi-cli COMMAND --help`` for complete command
syntax.

