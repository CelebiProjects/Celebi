Release notes
=============

1.1.3b1 — 2026-11-25
--------------------

This beta adds :doc:`secrets` for importing Kerberos keytabs into Yuki and binding
REANA/SSH runners, plus SSH ticket lifecycle settings. Credentials stay outside
projects and impressions; native and IHEP credential injection is not supported.

Collect EOS stageout with ``collect outputs --from eos:RUNNER`` or transfer
selected files directly to SSH runners. EOS imports to SSH are not treated as
complete caches for automatic workflow reuse.

``submit [OBJECT ...] --runner RUNNER`` selects multiple tasks/directories and
their dependencies. ``--cores N`` sets a per-workflow scheduling budget on native,
SSH and IHEP backends; REANA rejects it. SSH APD tasks use CVMFS ``lb-conda``.
Celebi follows the port published by a local Yuki service, falling back to the
project endpoint when no valid local port exists.

Upgrade both packages to ``1.1.3b1`` and restart the Yuki HTTP service and workers.
Yuki's Docker image separates REANA dependencies from native Snakemake and adds
Kerberos/XRootD clients. Python 3.9 resource traversal and CI/lint fixes are also
included. Source preparation does not imply package publication or deployment.

1.1.2b1 — 2026-11-19
--------------------

This beta adds :doc:`eos_cache` with REANA-based usage measurement and confirmed
cleanup, including an independent verification job. Upgrade Celebi and Yuki
together for these commands.

Submission now propagates runner-cache preferences across the dependency graph.
Impression comparison, content hashing and file diffs ignore generated Python
bytecode (``__pycache__``, ``.pyc``, ``.pyo``), including historical tree entries.

Matching Yuki also supports direct native-runner output previews without collect,
including nested paths and HTTP range requests. The VS Code plugin is a separate
package; Python package upgrades do not update it automatically.

The source version is a prerelease; this page does not imply PyPI publication.
