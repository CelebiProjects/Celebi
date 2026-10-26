100 Gaussian toys with subtasks
========================================

This example has exactly three inline-code Tasks and three Task impressions:

.. code-block:: text

   GenerateTask -> FitTask (subtasks: 100) -> SummaryTask

GenerateTask produces 100 Gaussian pseudoexperiments, each with 1,000 events,
true mean 5 and sigma 1.5. FitTask repeats an exact unbinned Gaussian
maximum-likelihood fit 100 times. SummaryTask checks completeness and produces
parameter and pull distributions. The fit uses the analytic ML solution;
errors use asymptotic likelihood curvature. All scripts use Python's standard
library, without ROOT or a numerical optimizer.

The local Demo checkout contains the runnable project at
``Demo/demo-subtasks-01-gaussian-toys/``. Its ``run_local.py`` validates the
production Yuki-generated Snakefile using the current Python environment,
without contacting a Yuki service. The scripts are also downloadable here:

* :download:`GenerateTask/generate.py <gaussian-toys/GenerateTask/generate.py>`
* :download:`FitTask/fit.py <gaussian-toys/FitTask/fit.py>`
* :download:`SummaryTask/summarize.py <gaussian-toys/SummaryTask/summarize.py>`

Create and connect the tasks
----------------------------------------

From an existing Celebi project root:

.. code-block:: bash

   celebi-cli create-task GenerateTask
   celebi-cli create-task FitTask
   celebi-cli create-task SummaryTask
   cd FitTask
   celebi-cli add-input ../GenerateTask toys
   cd ../SummaryTask
   celebi-cli add-input ../FitTask fits
   cd ..

Place each downloaded script in its corresponding Task directory. Use the
following ``celebi.yaml`` files; configure dependencies with the commands
above, rather than writing dependency metadata manually.

GenerateTask
------------

.. code-block:: yaml

   descriptor: GenerateTask
   environment: python3.12
   memory_limit: 128Mi
   parameters:
     toys: 100
     events: 1000
     mean: 5.0
     sigma: 1.5
     seed: 20261025
   commands:
     - python generate.py --toys ${toys} --events ${events} --mean ${mean} --sigma ${sigma} --seed ${seed} --output stageout

This task runs once and writes ``stageout/0/toy.json`` through
``stageout/99/toy.json``, plus a root-level ``manifest.json``. Random streams
use ``seed + index``. Numbered output directories are valid even for a normal
Task: the producer explicitly creates these partitions.

FitTask
-------

.. code-block:: yaml

   descriptor: FitTask
   environment: python3.12
   memory_limit: 128Mi
   subtasks: 100
   alias:
     - toys
   commands:
     - python code/fit.py --index ${index} --input toys/stageout/${index}/*.json --output stageout/index

The shell expands ``*.json`` in the selected upstream partition; each
partition contains exactly one toy dataset. ``${index}`` supplies the numeric
input partition, while ``stageout/index/`` is the fixed output path for the
current instance. For index 7:

.. code-block:: text

   input:         toys/stageout/7/toy.json
   code writes:   stageout/index/fit.json
   Task output:   stageout/7/fit.json

Repeated inline tasks expose their shared task source as ``code/``. Each
instance also has a separate working directory and log directory. There are
no per-index Task objects or impressions.

SummaryTask
-----------

.. code-block:: yaml

   descriptor: SummaryTask
   environment: python3.12
   memory_limit: 128Mi
   parameters:
     expected: 100
   alias:
     - fits
   commands:
     - python summarize.py --fits fits/stageout --expected ${expected} --output stageout

The ``fits`` alias references the whole FitTask. SummaryTask waits until all
100 instances complete, verifies indices 0 through 99, and fails if results
are missing, failed or inconsistent. Outputs are ``fits.csv``, ``summary.json``,
``summary.svg`` and ``report.md`` under ``stageout/``.

Run and inspect
---------------

Create ``.celebi-env/python3.12.yaml`` at the project root:

.. code-block:: yaml

   channels:
     - conda-forge
   dependencies:
     - python=3.12

With an updated Yuki server and a configured local native runner, install
the environment and ensure all three tasks request that runner:

.. code-block:: bash

   celebi-cli install-environment local python3.12
   cd GenerateTask
   celebi-cli request-runner local
   cd ../FitTask
   celebi-cli request-runner local
   cd ../SummaryTask
   celebi-cli request-runner local
   celebi-cli submit --runner local
   celebi-cli status --wait
   celebi-cli collect all
   celebi-cli view-url

From FitTask, inspect a specific instance's first command log:

.. code-block:: bash

   celebi-cli log 0 --subtask 7

The local Demo project's independent validation is:

.. code-block:: bash

   python run_local.py --cores 4

It writes ``.local-run/results/<Task>/stageout/`` and records the three
impression IDs in ``.local-run/validation.json``. Choose another
``--workdir`` to preserve previous validation results.

The validated 100-toy ensemble gave average fitted mean 4.995186 and average
fitted sigma 1.496423. These are a reproducible reference for the supplied
seed and configuration, not acceptance thresholds. Pull means and widths
fluctuate around zero and one; sigma ML estimates have a small finite-sample
bias. This local run validates Yuki's rule generation, not a live service
deployment.

Change GenerateTask's ``parameters.toys``, FitTask's ``subtasks`` and
SummaryTask's ``parameters.expected`` together when changing the ensemble
size. See :doc:`../subtasks` for cache publication and retry limitations.
