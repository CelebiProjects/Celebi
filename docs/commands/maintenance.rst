Maintenance and recovery
========================

Start with inspection or dry-run modes. Commands that delete data state their
scope and request confirmation unless ``--yes`` is used.

Local objects and impressions
-----------------------------

* ``doctor`` checks and repairs impression consistency for the current object.
* ``purge`` removes temporary data associated with the current object.
* ``purge-old-impressions`` and ``purge-impressions`` remove selected local
  impression data.
* ``impression-stats`` reports legacy and CAS-backed storage and deduplication.
* ``migrate-impressions --dry-run`` previews migration of legacy storage to
  CAS. Execution keeps legacy storage unless ``--prune-legacy`` is supplied.
* ``pack-impressions`` packs eligible CAS objects; ``--force`` bypasses normal
  packing thresholds.
* ``gc-impressions`` is a dry-run by default. ``--execute`` deletes unreachable
  CAS objects older than the grace period.

Runner cleanup
--------------

* ``sync-live`` sends the project's live impression set to Yuki. If syncing
  fails, the cleanup rules conservatively treat unknown impressions as live.
* ``purge-ssh-runner-cache RUNNER --dry-run`` previews removal of managed SSH
  cache entries.
* ``purge-stale-cache RUNNER --dry-run`` selects superseded cache entries.
* ``purge-stale-workflows RUNNER --dry-run`` selects non-live, non-running
  workflow workspaces.
* ``stop-orphaned-workflows RUNNER --dry-run`` identifies recorded-running
  workflows no longer referenced by the project.
* ``stop-workflow UUID`` force-stops a specific workflow, including a zombie
  run, while retaining its workspace.
* ``tidyup`` is an interactive front end that previews local CAS, stale
  workspace and SSH-cache cleanup before deletion.

Advanced commands
-----------------

``workaround-vre``, ``danger``, ``preshell`` and ``postshell`` are advanced or
developer operations. Read their live ``--help`` output before use; they are
not part of the normal analysis workflow.
