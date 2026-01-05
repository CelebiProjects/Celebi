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

```sh
celebi init
celebi
```

---

## Documentation

- User Guide: `doc/source/UserGuide.md`
- Online Docs: http://chern.readthedocs.io/en/latest/
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
