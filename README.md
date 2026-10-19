[![Ask DeepWiki](https://deepwiki.com/badge.svg)](https://deepwiki.com/CelebiProjects/Celebi)

# Celebi

Celebi is a data analysis management toolkit designed for high-energy physics research.  
It provides a structured environment for organizing **projects, tasks, algorithms, and data**, enabling **reproducible, traceable, and collaborative scientific workflows**.

Celebi is particularly suited for complex analysis chains common in HEP, where dependency tracking, provenance, and re-execution are critical.

---

## Key Features and Benefits

- **Structured Organization**  
  Clear separation of projects, data, algorithms, and tasks with a well-defined hierarchy.

- **Dependency Tracking**  
  Automatic tracking of relationships between data, algorithms, and tasks, forming a directed acyclic graph (DAG).

- **Impressions (Versioning)**  
  Built-in *impressions* system to snapshot important results, configurations, and object states over time.

- **Reproducibility**  
  Complete capture of workflow structure, parameters, inputs, and execution environments.

- **Adaptability**  
  Modify algorithms or parameters and re-run only affected downstream tasks.

- **Collaboration**  
  Share projects and workflows consistently across users and environments.

---

## Core Concepts

- **Project** – A self-contained analysis workspace.  
- **Data** – Raw or derived datasets registered and managed by Celebi.  
- **Algorithm** – A reusable, self-contained piece of code or script.  
- **Task** – A concrete execution instance of an algorithm with specific inputs and parameters.  
- **Runner** – An execution backend (local, batch system, remote, etc.).  
- **Impression** – A recorded snapshot of key outputs or analysis states.

---

## Installation

```sh
git clone https://github.com/CelebiProjects/Celebi.git
cd Celebi
pip install .
```

---

## Getting Started

### Immutable, single-pass impressions

For a fixed Git checkout or another input tree that will not be edited while
the command runs, use:

```sh
celebi-cli impress --immutable
# Share the same project's impressions across disposable checkouts:
celebi-cli impress --immutable --cache-dir /path/outside-checkout/impression-cache
```

`--immutable` implies offline execution. It evaluates each task/algorithm once
in topological order, using resolved upstream UUIDs instead of recursive
freshness checks. It does not scan project mtimes or repeatedly enumerate
ancestor directories for case checks. UUID rules and CAS payloads are compatible
with normal `impress`; existing complete payloads are reused without rewriting
them. Missing cached payloads are rebuilt. Graph work is O(V+E), excluding
canonical sorting and input-file hashing/storage costs.

The caller must prevent concurrent input edits. Leave this option off in an
actively edited project. `--cache-dir` is optional, requires `--immutable`, and
belongs to one project only. Without it, existing `.celebi` impressions are
reused in place. With it, generated stores are linked into the external cache;
conflicting nonempty local/cache stores are refused rather than overwritten.
Do not commit these links or generated runtime files to Git. Bookkeeping's
server invokes this same local CLI mode against its exact checked-out commit.

### Publish analysis bookkeeping

Initialize and push the Celebi repository first, then create an analysis on the
password-protected `celebi_server` website and save its one-time analysis token.
The website reads the project UUID directly from the committed
`.celebi/config.json`; users do not enter or generate a UUID there.

Configure a GitLab upstream, collect the task results into the updated Yuki
server, and run inside the project:

```sh
celebi-cli register-celebi-server --server http://bookkeeping-host:3320 \
  --token <analysis-token> --yuki http://yuki-host:3315
celebi-cli bookkeep --commit "Publish fit results" --tag "v1"
```

The command commits shareable changes, atomically pushes the branch and tag,
then asks the server to impress that exact commit and compute missing result
archives. Yuki packages only small collected images/text and uploads them
using a scoped grant. Local credentials, impression stores, and stageout data
are excluded from Git. Environment definitions in `.celebi-env/` are shareable
and are included in bookkeeping commits (normal credential/result exclusions
still apply inside that directory). Existing tags and behind/diverged branches are rejected.
Before making any Git change, the CLI checks the locally saved analysis token
against its server-side hash. An invalid token cannot create a commit or tag and
cannot push. GitLab still applies the user's normal SSH/HTTPS push permission;
the bookkeeping server itself only needs read access to fetch the repository.
Use `--allow-partial` to tolerate results not collected yet, then run
`celebi-cli bookkeep` again without `--tag` after they arrive. Saved website
credentials live in `.celebi/bookkeeping.local.json` with mode 0600.

### Initialize a local project

```sh
celebi-cli init
celebi
```

Celebi provides three deliberately separate command interfaces:

- `celebi` starts the stateful interactive shell.
- `celebi-cli` runs one command for scripts and automation; its flat command
  list is organized into functional sections in `celebi-cli --help`.
- `celebi-git` contains Celebi-aware Git integration commands.

Select a registered project before starting the shell with
`celebi-cli use-project PROJECT`, or start the shell for a project directly
with `celebi --project PROJECT`.

To register a copied project as a distinct project, generate a fresh project
UUID while selecting it:

```sh
celebi use . --new-project
# Equivalent one-shot command:
celebi-cli register-project . --new-project
```

Inside the interactive shell, help is available in three complementary forms:

```text
helpme                 # Object-aware guidance for the current context
help status            # Detailed help for one command
status --help          # The same command help, inline with the command
```

`helpme COMMAND`, `help COMMAND`, and `COMMAND --help` share the same command
documentation. Run `help` without an argument for the categorized shell index;
run `celebi-cli --help` for the categorized one-shot CLI index.

---

## Documentation

For slow remote data operations, set a positive HTTP timeout in seconds:

```sh
celebi-cli register-ssh-data pkufarm212 /remote/data/2018 --timeout 120
celebi-cli transfer yuki runner:pkufarm212 --timeout 120
celebi-cli verify-data --timeout 7200
```

The interactive shell accepts the same options without the `celebi-cli` prefix.
The timeout applies to each HTTP request, including registration and transfer status
polls; it does not limit the total job duration. Defaults remain 10 seconds for
registration and transfer requests, and 3600 seconds for verification. Registration
polling retries connection failures and stops after 10 consecutive failures; the
server job may continue after polling stops.

- Online Docs: http://celebi.readthedocs.io/en/latest/
- Ask DeepWiki: https://deepwiki.com/CelebiProjects/Celebi

---

## License

Apache License, Version 2.0

---

## Author

**Mingrui Zhao**

- 2013–2017 — Center of High Energy Physics, Tsinghua University  
- 2017–2025 — Department of Nuclear Physics, China Institute of Atomic Energy  
- 2020–2025 — Niels Bohr Institute, University of Copenhagen  
- 2025–now — Peking University

### Submission timeout

For a slow server response, increase the submission request timeout (in seconds):

```bash
celebi-cli submit --runner my_runner --timeout 300
```

In the interactive Celebi shell, use:

```text
submit --runner my_runner --timeout 3000
```

The HTTP response timeout defaults to 10 seconds. An explicit timeout also
extends Yuki SSH command, connection, and startup-confirmation limits for the
submitted workflow, preserving any longer existing limits. Yuki saves this
setting for later workflow operations. It does not limit workflow runtime.
A timed-out request may still be processed by the server; check task status before submitting again.

### Live status

Wait for terminal state while querying the runner rather than repeatedly
reading the saved workflow status:

```bash
celebi-cli status --wait
```

The interactive shell uses the same syntax. Use `-i 5` or
`--poll-interval 5` to change the default two-second polling interval.
