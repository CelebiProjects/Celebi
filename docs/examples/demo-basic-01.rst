==================
Basic Example: 01
==================

This repository is a demonstration project that includes two main components:

* **Generation (Gen)**: Initial data production.
* **Fitting (Fit)**: Statistical analysis and modeling.

The workflow is executed using **REANA** as the runner backend.
Follow these steps to clone the repository and execute the workflow within the Celebi environment.

1. Clone the Repository
-----------------------

.. code-block:: bash

   git clone https://github.com/CelebiProjects/demo-basic-01.git
   cd demo-basic-01

2. Enter the Celebi Environment
-------------------------------

Initialize and enter the **Celebi shell**:

.. code-block:: bash

   celebi-cli register-project .
   celebi

3. Verify the Yuki Connection
-----------------------------

Inspect the configured Yuki/DITE endpoint:

.. code-block:: bash

   celebi-cli dite

*Note: If this is your first time, configure the DITE endpoint:*, for example:

.. code-block:: bash

   celebi-cli set-dite localhost:3315

4. Check Available Runners
--------------------------

List the registered runners to confirm availability:

.. code-block:: bash

   celebi-cli runners

If no runner is registered, you can add one by running:

.. code-block:: bash

   celebi-cli register-runner

And you should also help change the requested runner for running the workflow:

.. code-block:: bash

   celebi-cli request-runner RUNNER_NAME

5. Submit the Workflow
----------------------

Finally, submit the workflow to the runner for execution:

.. code-block:: bash

   celebi-cli submit --runner RUNNER_NAME

This command will make the objects impressed, and then submit the workflow to the selected runner (REANA in this case).

6. Monitor the Workflow
-----------------------
You can monitor the status of your work with

.. code-block:: bash

   celebi-cli status --wait

7. Retrieve Results
--------------------
Once the workflow is complete, retrieve the results using:

.. code-block:: bash

   celebi-cli collect

The default collects plots and logs into Yuki Storage. Use
``celebi-cli collect all`` when all stageout data is required.

8. View the Output
--------------------
You can now view the output files.

.. code-block:: bash

   celebi-cli view

This will display the results in your browser like this:

.. figure:: ../images/demo-basic-01-output.png
   :alt: demo-basic-01 output
   :width: 600px
   :align: center

Congratulations!
You have now successfully executed the basic workflow using Celebi!


.. note::

   The example is adapted from the REANA demo example.
