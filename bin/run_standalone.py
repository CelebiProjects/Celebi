"""Run standalone."""
import sys
import os
import imp  # pylint: disable=import-error,deprecated-module  # imp removed in py3.12; script legacy

def run_standalone(filepath):
    """ This function is designed to run a standalone python program
    """
    # while task.has_super_task():
    # parameters_file_list.append(task.path + "/.parameters.py")
    parameters_file = filepath + "/parameters.py"
    input_output_file = filepath + "/inputs_outputs.py"
    main_file = filepath + "/main.py"
    if os.path.exists(parameters_file):
        imp.load_source("run", parameters_file)
    if os.path.exists(input_output_file):
        imp.load_source("run", input_output_file)
    if os.path.exists(main_file):
        imp.load_source("run", main_file)

if __name__ == "__main__":
    path = sys.argv[1]
    run_standalone(path)
