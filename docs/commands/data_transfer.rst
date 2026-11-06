Data registration and transfer
==============================

Local and SSH data
------------------

* ``upload-data PATH`` uploads a local file or directory into Yuki as data for
  the current object.
* ``register-ssh-data RUNNER REMOTE_PATH`` registers a directory already on an
  SSH runner. Yuki copies it into the runner's managed impressions area,
  computes its MD5 and creates a local rawdata pointer task.
* ``attach-data IMPRESSION_UUID`` attaches an existing Yuki rawdata impression
  to the current project. ``--path`` overrides the local task path.
* ``verify-data`` recomputes the registered checksum. For remote-hosted data,
  hashing happens on the runner that holds it.

Register XRootD without copying payloads
----------------------------------------

``register-xrootd-data`` inventories XRootD files through a registered SSH
runner and stores a frozen datalist impression. Run it while the selected
Celebi object is a project or directory:

.. code-block:: console

   celebi-cli register-xrootd-data ssh-cluster \
     root://xrootd.example//store/sample \
     --descriptor collision-data \
     --checksum auto

It can also update the current task when that task is already an XRootD-backed
datalist. It refuses an unrelated task to avoid overwriting it.

The command asks Yuki to start a registration job. The SSH runner executes the
XRootD listing and server-side checksum queries, while the client polls and
shows progress. File payloads are not copied into Celebi or Yuki during
registration.

Checksum policy
~~~~~~~~~~~~~~~

``--checksum auto`` records a server checksum where available and continues
when the server does not provide one. ``required`` fails registration if any
file lacks a checksum. ``none`` skips checksum queries and is fastest, but the
frozen identity then relies on path and metadata rather than file content.

The resulting task uses ``environment: datalist`` and contains the frozen URL
list, source description and manifest. When it runs, Yuki writes both
``stageout/filelist.txt`` and the legacy-compatible
``stageout/dataList.txt``. A downstream task can add this task as an input and
read ``inputdata/<alias>/filelist.txt``. Actual XRootD access and authentication
therefore happen in the consuming job's runtime environment.

Locations and transfers
-----------------------

* ``whereabouts`` shows whether the current impression exists in Yuki Storage
  or a managed runner cache.
* ``cache-results RUNNER`` moves stageout into an SSH runner's managed cache.
* ``transfer SOURCE DESTINATION`` transfers stageout between ``yuki`` and
  ``runner:<name>``. ``--pattern`` filters files and ``--force`` overwrites.
* ``purge-data`` removes collected stageout, logs and watermarks from Yuki.
  Without ``--force``, Yuki protects the last recoverable copy.
* ``add-apd-token TOKEN`` stores an LHCb AP token in git-excluded local
  configuration for an ``lhcb_ap_datalist`` task.

Registration and collection are separate: registering SSH or XRootD data
creates a reproducible input object, while ``collect`` retrieves outputs of a
completed workflow.

Share complete impressions through SSH
--------------------------------------

``share-ssh-impressions`` uses the current Celebi object as its scope. Run it
from a task to select that task, or from a directory to select every task below
that directory. The project root behaves like the top-level directory and
selects every task in the project. Algorithms are rejected.

Export the selected impressions from Yuki into the runner's managed shared
store:

.. code-block:: console

   celebi-cli share-ssh-impressions --export ssh-cluster

Import from that shared store into Yuki:

.. code-block:: console

   celebi-cli share-ssh-impressions --import ssh-cluster

Import first impresses the current task or directory. The resulting current
task UUIDs form a strict allow-list: historical or unrelated shared
impressions are not imported. Downloads land in staging before their files are
merged into Yuki Storage. Existing files are protected unless ``--force`` is
given.

The runner must use an SSH backend. Its shared store lives below
``<remote_workdir>/shared-impressions/<project_uuid>/`` and uses in-progress
and complete markers plus read-only publication. ``--timeout`` controls each
client-to-Yuki status request, not the total background transfer duration.
