Algorithms & Tasks
====================

Commands for defining algorithms and creating task instances.

* ``create-algorithm`` – Define a reusable algorithm
* ``add-algorithm`` – Attach an algorithm to a project or task
* ``add-input`` – Add a single input dependency
* ``add-multi-inputs PATH_BASE ALIAS_BASE STOP [--start START]`` – Add a numbered,
  half-open range of dependencies
* ``remove-multi-inputs ALIAS_BASE STOP [--start START]`` – Remove a numbered range
  of dependency aliases
* ``set-parameter`` – Define or replace a configurable task parameter
* ``remove-input`` – Remove an input dependency
* ``remove-parameter`` – Remove a parameter
* ``create-task`` – Create a single task
* ``create-multi-tasks BASE_NAME STOP [--start START]`` – Create numbered tasks and
  set each task's ``index`` parameter
* ``create-data`` – Register a data object
* ``create-multi-data PATH`` – Create and upload one data object per child directory
* ``edit`` – Edit an algorithm script
* ``edit-readme`` – Edit the current object's README
