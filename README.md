[![Ask DeepWiki](https://deepwiki.com/badge.svg)](https://deepwiki.com/CelebiProjects/Celebi)
# Celebi

Celebi is a data analysis management toolkit designed for high energy physics research. It provides a structured environment for organizing projects, tasks, algorithms, and data, enabling reproducible and collaborative scientific workflows.

## Key Features and Benefits

Celebi provides several advantages for scientific data analysis:

- **Structured Organization:** Clear separation of data, algorithms, and tasks
- **Dependency Tracking:** Automatic monitoring of relationships between objects
- **Version Control:** Impressions system for tracking object states over time
- **Reproducibility:** Complete capture of workflow and parameters
- **Adaptability:** Easy modification and re-execution of analysis components
- **Collaboration:** Project sharing and management capabilities

## Features

- **Project Management:** Create, organize, and switch between multiple analysis projects.
- **Task & Algorithm Handling:** Define tasks and algorithms with configuration files and documentation.
- **Data Organization:** Manage raw and processed data with clear directory structures.
- **Interactive Shell:** Launch an IPython shell for interactive exploration and command execution.
- **Extensible:** Easily add new commands, algorithms, and data types.

## Installation

Clone the repository and install dependencies:

```sh
git clone https://github.com/CelebiProjects/Celebi.git
cd Celebi
pip install .
```

## Getting Started

Initialize a new project:

```sh
chern init
```

Start the interactive shell:

```sh
chern
```

## Common Commands

| Command       | Description                                                     |
| ------------- | --------------------------------------------------------------- |
| `ls`          | Lists the contents of the current directory or specified path.  |
| `cd`          | Changes the current working directory.                          |
| `mkdir`       | Creates a new directory.                                        |
| `cp`          | Copies files or directories.                                    |
| `mv`          | Moves or renames files or directories.                          |
| `rm`          | Removes (deletes) files or directories.                         |
| `cat`         | Concatenates files and prints their content to standard output. |
| `ls-projects` | Lists all available projects within the system environment.     |
| `cd-project`  | Changes the active project context (project-level `cd`).        |


| Command              | Description                                                             |
| -------------------- | ----------------------------------------------------------------------- |
| `create-algorithm`   | Defines a new reusable algorithm (self-contained script or code block). |
| `add-algorithm`      | Adds an existing algorithm to a project or task configuration.          |
| `add-input`          | Specifies a single input dependency for an algorithm or task.           |
| `add-multi-inputs`   | Specifies multiple inputs at once (batch / parameter sweep).            |
| `add-parameter`      | Defines a configurable parameter for a task or algorithm.               |
| `remove-input`       | Removes a specified input dependency.                                   |
| `remove-parameter`   | Removes a specified parameter.                                          |
| `create-task`        | Defines a single task instance of an algorithm.                         |
| `create-multi-tasks` | Defines multiple tasks simultaneously.                                  |
| `create-data`        | Registers a new data object or artifact.                                |
| `edit-script`        | Opens the script associated with an algorithm for editing.              |
| `edit-readme`        | Opens and edits the README documentation.                               |

| Command           | Description                                                    |
| ----------------- | -------------------------------------------------------------- |
| `submit`          | Submits tasks or workflows for execution.                      |
| `status`          | Checks execution status (pending, running, failed, completed). |
| `kill`            | Cancels a running or pending job.                              |
| `collect`         | Retrieves outputs or artifacts from completed tasks.           |
| `trace`           | Displays detailed execution logs or history.                   |
| `display`         | Prints output or results to the console.                       |
| `runners`         | Lists available execution environments.                        |
| `register-runner` | Adds a new execution environment (runner).                     |
| `remove-runner`   | Deletes an existing runner configuration.                      |


| Command         | Description                                                         |
| --------------- | ------------------------------------------------------------------- |
| `import`        | Imports data, tasks, or definitions from another project or source. |
| `export`        | Exports data or definitions to an external location.                |
| `import-file`   | Imports a specific external file into the managed file system.      |
| `rm-file`       | Removes a managed file.                                             |
| `mv-file`       | Moves or renames a managed file.                                    |
| `auto-download` | Automatically retrieves required inputs or dependencies.            |


| Command            | Description                                     |
| ------------------ | ----------------------------------------------- |
| `config`           | Displays or modifies configuration settings.    |
| `setenv`           | Sets an environment variable.                   |
| `set-environment`  | Configures the execution environment for tasks. |
| `set-memory-limit` | Defines the maximum memory allowed for a task.  |

| Command             | Description                                                      |
| ------------------- | ---------------------------------------------------------------- |
| `draw-dag-graphviz` | Generates a static DAG visualization using Graphviz.             |
| `draw-live-dag`     | Generates a live (dynamic) DAG visualization with task statuses. |
| `impress`           | Records a key result or output for reporting.                    |
| `impression`        | Lists or retrieves recorded impressions.                         |
| `clean-impressions` | Deletes old or unwanted impressions.                             |
| `view`              | Opens a file or component in the default viewer/editor.          |


See the [User Guide](doc/source/UserGuide.md) for more details.

## Documentation

Full documentation is available at [chern.readthedocs.io](http://chern.readthedocs.io/en/latest/).

## License

Apache License, Version 2.0

## Author

Mingrui Zhao  
2013–2025
2013--2017 Center of High Energy Physics, Tsinghua University  
2017--2025 Department of Nuclear Physics, China Institute of Atomic Energy  
2020--2025 Niels Bohr Institute, University of Copenhagen
2025--now  Peking University
