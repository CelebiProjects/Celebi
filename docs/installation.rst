Installation
============

To use Celebi, the following three components need to be installed or set up:

1. **Celebi package**  
   The package that manages the repository and provides the command-line interface.

2. **Yuki middleware**  
   The middleware that handles the execution of tasks.

3. **Runner backends**  
   The execution backends that run the tasks (e.g., REANA).

Installation of Celebi Package
----------------------------
The Celebi package can be installed via pip. Run the following command:

.. code-block:: bash

   pip install celebichrono


Setting Up Yuki Middleware
----------------------------
Yuki middleware can be set up using the docker image provided by the Yuki project.
Run the following command to start the Yuki middleware:

.. code-block:: bash

    docker run -d -p 3315:3315 celebi/yuki:latest

Consider configuring environment variables to point Celebi to the Yuki middleware instance.
