Workflow visualization and provenance
=====================================

* ``impress`` records the current reproducible state and ``impression`` prints
  its identifier.
* ``history`` and ``changes`` inspect recorded object history.
* ``trace IMPRESSION`` compares the current graph with a stored impression.
* ``search-impression TEXT`` resolves a partial impression identifier.
* ``watermark`` prints the task or algorithm watermark.
* ``view [IMPRESSION]`` opens the Yuki view; ``view-url`` prints its URL.
* ``draw-dag`` renders the dependency graph.
* ``bookkeeping-url`` prints the project's bookkeeping URL and
  ``open-bookkeeping`` opens it.

Publishing code and selected results is covered under
:doc:`services_booking`; storage-level impression maintenance is covered under
:doc:`maintenance`.
