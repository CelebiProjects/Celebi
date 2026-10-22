Python API
==========

Celebi's supported public interface is the ``celebi-cli`` command line and the
interactive ``celebi`` shell. The modules below ``CelebiChrono.kernel`` and
``CelebiChrono.interface`` are implementation details and may change between
releases without a Python-level compatibility guarantee.

For automation, prefer commands such as:

.. code-block:: console

   celebi-cli project-path
   celebi-cli impression
   celebi-cli status
   celebi-cli view-url

Commands return a non-zero exit status on errors, making them suitable for
shell scripts and continuous-integration jobs. Run ``celebi-cli --help`` for
the categorized command list and ``celebi-cli COMMAND --help`` for arguments
and options.
