Installation
============

Celebi is the project and command-line client. Yuki is the service that stores
impressions and coordinates execution. At least one runner is needed to execute
workflows; supported runner types include REANA, SSH, IHEP and native runners.

Install Celebi
--------------

The recommended installation is an editable install from the GitHub repository.
This keeps the checkout available for updates and makes local source changes take
effect without reinstalling the package:

.. code-block:: bash

   git clone https://github.com/CelebiProjects/Celebi.git
   cd Celebi
   python -m pip install -e .

Verify both command-line entry points:

.. code-block:: bash

   celebi-cli --help
   celebi --help

To update this installation, pull the repository. Re-run the editable install
when dependencies or package metadata change:

.. code-block:: bash

   git pull
   python -m pip install -e .

The packaged release is also available from PyPI when a source checkout is not
desired:

.. code-block:: bash

   python -m pip install celebichrono

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

Celebi first uses the port published by a local Yuki instance started with
``yuki-service start --auto-ports``. It reads ``run/yuki.port`` from
``YUKIDIR`` (default ``~/.Yuki``) on each connection so it can follow a port
change after restart. Set the same ``YUKIDIR`` for both tools if you are using
a custom state directory.

Without a valid local port, Celebi uses the project address saved with
``set-dite``, or ``127.0.0.1:3315`` when none is configured.
``celebi-cli dite`` displays the address in use.

.. code-block:: console

   celebi-cli dite
   celebi-cli set-dite yuki.example.org:3315

Yuki registers the native ``local`` runner on first server start. Start its
host agent, install the new project's bundled environment, and test it:

.. code-block:: console

   yuki native-runner start
   celebi-cli install-environment local default
   celebi-cli test-runner local

``celebi-cli init`` creates ``.celebi-env/default.yaml`` with ROOT 6.38.04,
NumPy and Python 3.10, and new tasks use the logical environment name
``default``. Use ``celebi-cli register-runner`` only to add another backend.

Runner-specific credentials are stored by Yuki, not committed to the Celebi
project. Use ``register-booking-server`` for REANA booking credentials and the
runner registration command for SSH or REANA execution credentials.
