Installation
============

Celebi is the project and command-line client. Yuki is the service that stores
impressions and coordinates execution. At least one runner is needed to execute
workflows; supported runner types include REANA, SSH, IHEP and native runners.

Install Celebi
--------------

Install the released package:

.. code-block:: bash

   pip install celebichrono

For development from a checkout, use an editable install:

.. code-block:: bash

   pip install -e .
   celebi-cli --help

Run Yuki
--------

If the Yuki package is installed, its Docker helper starts an all-in-one server
and persists storage under the host's ``~/.Yuki`` directory:

.. code-block:: bash

   yuki docker run

For Yuki development, run the Compose configuration from the Yuki checkout:

.. code-block:: bash

   docker compose up

The production image can also be started directly:

.. code-block:: bash

   docker run -d -p 3315:3315 yuki:latest

Production containers run as the non-root ``yuki`` user and store data at
``/home/yuki/.Yuki``. Prefer ``yuki docker run`` when mounting host storage,
because it handles the normal and rootless-Docker ownership cases.

Connect Celebi to Yuki
----------------------

The default endpoint is ``127.0.0.1:3315``. Inspect or change it with:

.. code-block:: console

   celebi-cli dite
   celebi-cli set-dite localhost:3315

Then register and test an execution backend:

.. code-block:: console

   celebi-cli register-runner
   celebi-cli runners
   celebi-cli test-runner RUNNER

Runner-specific credentials are stored by Yuki, not committed to the Celebi
project. Use ``register-booking-server`` for REANA booking credentials and the
runner registration command for SSH or REANA execution credentials.
