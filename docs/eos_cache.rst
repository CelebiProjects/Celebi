EOS cache usage and cleanup
===========================

Available in CelebiChrono and Yuki ``1.1.2b1``. Both components must be updated;
reload the Yuki HTTP service after upgrading. The REANA runner must provide EOS
mount access and Kerberos credentials. Celebi and Yuki do not access EOS directly.

Measure and preview
-------------------

.. code-block:: bash

   celebi-cli eos-usage cern --all-projects
   celebi-cli eos-usage --scan-id SCAN_ID --json
   celebi-cli eos-cleanup cern --all-projects --include-unknown

Usage reports distinguish ``live``, ``non_live`` and ``unknown``. A stale or missing
live set is unknown, not proof that files are unused. Byte totals measure logical
file sizes, not replication or disk allocation. Incomplete scans are lower bounds.
The current-project usage command synchronizes its live set; for all-project usage,
run ``sync-live`` in other projects that need an updated classification.

Cleanup defaults to a preview and selects only non-live caches. The cleanup CLI
refreshes live sets for matching local checkouts. ``--include-unknown`` also selects
unknown impression caches with a unique project owner; unassigned entries remain
excluded. A new scan is needed for current file measurements.

Execute the reviewed plan
-------------------------

.. code-block:: bash

   celebi-cli eos-cleanup --plan-id PLAN_ID --execute
   celebi-cli eos-cleanup --plan-id PLAN_ID

The execution command confirms the exact plan. ``--yes`` skips that prompt only
with ``--execute``. ``--clear-project PROJECT_UUID`` on a new preview explicitly
selects all cache in that project, including live data. ``tidyup`` exposes the same
REANA cleanup workflow interactively. Removing a REANA workflow does not remove
its EOS cache.

A plan needs a complete scan less than 24 hours old with metadata fingerprints.
Changes to liveness, ownership, runner configuration or selected files cause the
operation to refuse or stop. Active project workflows block submission. Avoid
starting new analysis workflows until cleanup and verification finish.

Deletion is checked by a separate read-only REANA job. Residuals or verification
errors are reported as partial completion. A timeout does not cancel deletion:
query the existing plan ID. Never start a replacement deletion merely because a
submission response was lost. Neither partial nor uncertain deletions are retried
automatically. Independent verification is still a point-in-time observation.
