Basic example: 01
====================

This repository is a demonstration project that includes two main components:

* **Generation (Gen)**
* **Fitting (Fit)**

The workflow is executed using **REANA** as the runner backend.

An introduction to this example is also available on **Read the Docs**.

# Steps to Run the Example

1. Clone the Repository

---

.. code-block:: bash

git clone https://github.com/CelebiProjects/demo-basic-01.git
cd demo-basic-01

2. Enter the Celebi Environment

---

.. code-block:: bash

celebi use .   # Use this legacy project
celebi

You are now inside the **Celebi shell**.

3. Verify DITE Connection

---

List the current status:

.. code-block:: bash

ls

If DITE is connected, you should see:

.. code-block:: text

> > > > DITE: [connected]

To check or activate DITE:

.. code-block:: bash

dite

Configure the DITE endpoint (only required once):

.. code-block:: bash

set-dite [https://dite.reana.io/](https://dite.reana.io/)

4. Check Available Runners

---

List registered runners:

.. code-block:: bash

runners

If no runner is registered, register one:

.. code-block:: bash

register-runner

5. Submit the Workflow

---

Submit the workflow to the runner:

.. code-block:: bash

submit
