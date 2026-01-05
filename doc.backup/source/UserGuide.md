# Chern User Guide

## Introduction

Chern is a data analysis management toolkit designed for high energy physics research. This guide will help you get started with organizing and managing your analysis workflows.

## Installation and Setup

After installing Chern, you can create a new project by running:

```bash
chern init
```

To start from an existing Chern project:

```bash
chern init --from-existing /path/to/existing/project
```

This will launch an interactive IPython environment that serves as your analysis shell.

## Core Concepts

### VTask
Tasks represent individual analysis steps or computations. Each task can have inputs, outputs, and an associated algorithm.

### VAlgorithm
Algorithms define the computational logic for tasks. They contain the actual code and parameters needed to process data.

### VData
Data objects represent datasets, whether raw experimental data or processed results from previous analysis steps.

### VDirectory
Directories organize and group related objects, providing a hierarchical structure for your analysis.

## Essential Commands

### Navigation
- `cd [object]` - Navigate to a specific object or directory
- `ls` - List contents of current location
- `cd_project [name]` - Switch between projects
- `ls_projects` - List all available projects

### Object Management
- `mkdir [name]` - Create new directories or objects
- `mv [source] [destination]` - Move or rename objects
- `cp [source] [destination]` - Copy objects with full directory structure
- `rm [object]` - Remove objects
- `mv_file` / `rm_file` - File-level operations

### Task Configuration
- `add_input [data_object] [nickname]` - Add input data to current task
- `remove_input [nickname]` - Remove input from current task
- `add_algorithm [algorithm]` - Associate an algorithm with current task
- `add_parameter [name] [value]` - Add parameters to current task
- `remove_parameter [name]` - Remove parameters from current task

### Algorithm and Data Creation
- `create_task [name]` - Create a new task
- `create_algorithm [name]` - Create a new algorithm
- `create_data [path]` - Import raw data from external location

### Execution and Job Management
- `status` - Check status of tasks and dependencies
- `submit` - Submit task for execution
- `kill` - Kill running jobs
- `register_runner [name]` - Register compute resources
- `runners` - List available runners

### Documentation and Configuration
- `edit_readme` - Edit documentation for any object
- `edit_script` - Edit algorithm scripts
- `comment [text]` - Add comments to objects
- `config` - Configure object settings

### Data Transfer and Import/Export
- `send [object] [destination]` - Send data to remote locations
- `auto_download` - Automatically download required data
- `import [object]` - Import objects
- `export [object]` - Export objects
- `import_file` / `export` - File-level import/export operations

### Impression System (Version Control)
- `impress` - Create an impression (snapshot) of current state
- `impression [name]` - Create named impression
- `impview` - View impression history
- `clean_impressions` - Clean old impressions

### Utilities
- `help` - Show available commands
- `helpme [command]` - Get detailed help for specific commands
- `cat [file]` - Display file contents
- `display [object]` - Display object information
- `collect` - Collect and organize objects

## Getting Help

- `help` - Show all available commands
- `helpme [command]` - Get detailed help for specific commands
- Visit the full documentation at [chern.readthedocs.io](http://chern.readthedocs.io/en/latest/)

## Best Practices

1. **Document Everything**: Use `edit_readme` and `comment` to document your objects and workflows
2. **Organize Hierarchically**: Use directories to group related tasks and data
3. **Track Dependencies**: Properly configure inputs and outputs for reproducible workflows
4. **Use Impressions**: Leverage Chern's impression system for version control and tracking changes
5. **Configure Runners**: Set up appropriate compute resources for your analysis tasks

## Warning

This is an early version of Chern. The software will evolve significantly during development, and backward compatibility is not guaranteed in future versions.
