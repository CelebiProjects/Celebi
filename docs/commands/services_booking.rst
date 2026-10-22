Services, authentication and publishing
=======================================

Yuki endpoint and hosts
-----------------------

* ``dite`` displays the configured Yuki/DITE service and ``set-dite HOST:PORT``
  changes it.
* ``hosts`` lists communicator hosts; ``add-host HOST PORT`` adds one.
* ``refresh-distribution`` rebuilds the current project's data-location
  registry without submitting work.

REANA booking
-------------

``register-booking-server`` stores REANA credentials in Yuki;
``booking-server`` checks the stored endpoint and its connectivity. Configure
them once:

.. code-block:: console

   celebi-cli register-booking-server \
     --server https://reana.example \
     --token "$REANA_ACCESS_TOKEN"
   celebi-cli booking-server

``book-reana`` publishes the current project as a REANA file catalog through
Yuki. It uses stored credentials unless ``--server`` and ``--token`` override
them. ``--upload`` accepts ``plots+logs`` (default), ``plots``, ``data``,
``all`` or a glob. ``--stageout`` is a deprecated alias for ``--upload all``.

Celebi bookkeeping
------------------

``register-celebi-server`` stores and verifies the analysis server and token in
git-excluded local configuration:

.. code-block:: console

   celebi-cli register-celebi-server \
     --server https://celebi.example \
     --token "$CELEBI_PROJECT_TOKEN"

Publish code and eligible small collected results with:

.. code-block:: console

   celebi-cli bookkeep --commit "Publish results" --tag v1

Run ``bookkeep`` again without ``--tag`` to retry missing result uploads.
``--allow-partial`` permits publication when some required results are not
collected. Analysis tokens stay on the client; Yuki receives a short-lived
upload grant rather than the long-lived website token.

Use ``bookkeeping-url`` or ``open-bookkeeping`` to locate the published page.
