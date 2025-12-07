""" Module containing all README information
"""


project_helpme = { "": """
Hello, you are in a ``project''. What would you like to do?
You can consult http://chern.readthedocs.io/en/latest/ for a complete document.

The following commands can be used, and type ``helpme [COMMAND]'' or ``[COMMAND] --help'' to see the help in detail:
    cd           : Change to directory/object.
    ls           : List the containings.
    mv           : Move a directory/object to another place.
    rm           : Remove a directory/object.
    mkdir        : Create a directory.
    mk_task      : Create a task.
    mk_algorithm : Create an algorithm.
    --------------------------------
    status       : Show the status of the objects.
    --------------------------------
    ls_project   : List the projects.
    cd_project   : Switch to another project.
""",

"cd": """The usage of cd:
    cd [object] """,

"cd test": """Test for cd"""
                  }

task_helpme = {"": """
Hello, you are now operating a ``task''. What would you like to do?

The following commands can be used, and type ``helpme [COMMAND]'' or ``[COMMAND] --help'' to see the help in detail:
    ls               : List the containings
    la               : A short
    add_source       : Add source to a task. The source should be a directory and it will be regarded the output of the current task.
    add_input        : Add input to a task. The input should also be a task.
    add_algorithm    : Add algorithm to the current task. The input should also be a task.
    add_parameter    : Add a parameter to the
    remove_source    : This command does not exists.
    remove_input     : Add input to a task. The input should also be a task.
    remove_algorithm : Add algorithm to the current task. The input should also be a task.
    remove_parameter : Add a parameter to the
    --------------------------------
    status           : Get the status of the objects.
    impress          : Create a new impression for the task.
    submit           : Submit the impression to the backend.
    jobs             : Consult the jobs.
    stdout           : Get the stdout.
    readme           : Read or write the readme.
""",
"status": """The status of a task may be one of the following:
    new: The task is edited and not impressed yet.
    impressed: The task is impressed, however, there is not a job link to the impression.
    submitted: The task is impressed and .
    failed: The task is failed for some reason.
    finished:
    missing: """
}

algorithm_helpme = { "": """Hello, you are operating an ``algorithm'', what would you like to do?
The commands to use:
    cd [object]
    ls : list the containings
    importfile : import the files
""",

"cd": """The usage of cd:
    cd [object] """,

"cd test": """Test for cd"""
                  }

directory_helpme = { "": """Hello, you are in the ``directory'' object, what would you like to do?
The commands to use:
    cd : change directory
    ls : list the containings
    mktask :
    mkalgorithm : """,

"cd": """The usage of cd:
    cd [object] """,

"cd test": """Test for cd"""
                  }
