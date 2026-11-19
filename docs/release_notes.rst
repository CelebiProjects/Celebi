Release notes
=============

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
