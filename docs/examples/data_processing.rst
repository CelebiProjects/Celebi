Data processing example
========================

This example registers a remote XRootD directory as a frozen sample and passes
its file list to a processing task. Registration inventories URLs and metadata;
it does not stage the ROOT payload into Celebi or Yuki.

Prerequisites
-------------

* Yuki is running and configured with ``set-dite``.
* ``ssh-cluster`` is a registered SSH runner whose host can run the XRootD
  client and reach the target service.
* The processing runtime has the XRootD client and any required authentication.

Register the sample
-------------------

Run this from a project or Celebi directory, not from an unrelated task:

.. code-block:: console

   celebi-cli register-xrootd-data ssh-cluster \
     root://xrootd.example//store/experiment/run-42 \
     --descriptor run-42 \
     --checksum auto

Celebi creates a ``run-42`` datalist task. The frozen ``celebi.yaml`` records
the file URLs, source and manifest. Choose ``--checksum required`` when every
file must have a server-provided checksum, or ``none`` when path/metadata
identity is sufficient and listing speed matters most.

Create a consumer
-----------------

.. code-block:: console

   celebi-cli create-algorithm algorithms/process
   celebi-cli create-task tasks/process-run-42
   cd tasks/process-run-42
   celebi-cli add-algorithm @/algorithms/process
   celebi-cli add-input @/run-42 sample
   celebi-cli request-runner ssh-cluster

The datalist job emits both ``filelist.txt`` and ``dataList.txt``. In the
consumer they are available as ``inputdata/sample/filelist.txt`` and
``inputdata/sample/dataList.txt``. A typical algorithm command is:

.. code-block:: yaml

   descriptor: process-xrootd
   environment: analysis
   commands:
     - python code/process.py inputdata/sample/filelist.txt stageout

Install ``.celebi-env/analysis.yaml`` when ``analysis`` is a project-managed
Conda environment:

.. code-block:: console

   celebi-cli install-environment ssh-cluster analysis

Run and retrieve selected results
---------------------------------

.. code-block:: console

   celebi-cli submit --runner ssh-cluster
   celebi-cli status --wait
   celebi-cli collect plots
   celebi-cli collect '*.json'
   celebi-cli whereabouts

Use ``collect all`` only when the full data output is needed in Yuki Storage.
The XRootD input payload remains remote and is read by the processing job.
