"""
    main function
    The purpose is to start: Celebi

    Functions:
        cli:
            default entrance, to start chern command line
        ipython: [deprecated]
            start the ipython shell of chern
        * start_chern_ipython:
            function for cli:ipython
        * start_chern_command_line:
            function for default cli

        machine:
            start or stop the chernmachine

        config:
            set the configurations: inavailable yet
        prologue:
            print the prologue
"""

# pylint: disable=broad-exception-caught,import-outside-toplevel
import os
import logging
from os.path import join
from logging import getLogger

import click

from .kernel import vproject
from .utils import csys
from .utils import metadata
from .interface.ChernShell import ChernShell


def is_first_time():
    """ Check if it is the first time to use the software """
    return not os.path.exists(csys.local_config_dir())


def start_first_time():
    """ Start the first time """
    print("Starting the first time")
    print("Creating the config directory $HOME/.Chern")
    csys.mkdir(csys.local_config_dir())


def start_chern_command_line():
    """Start the Chern command line interface."""
    logger = getLogger("ChernLogger")
    handler = logging.StreamHandler()
    formatter = logging.Formatter('[%(asctime)s][%(levelname)s] %(message)s')
    handler.setFormatter(formatter)
    logger.addHandler(handler)
    logger.setLevel(logging.ERROR)

    logger.debug("def start_chern_command_line")
    print("Welcome to the CELEBI Shell environment")
    print("Please type: 'helpme' to get more information")
    chern_shell = ChernShell()
    chern_shell.init()
    chern_shell.cmdloop()
    logger.debug("end start_chern_command_line")


@click.group(invoke_without_command=True)
@click.pass_context
def cli(ctx):
    """ Chern command only is equal to `Chern ipython`
    """
    if is_first_time():
        start_first_time()
    if ctx.invoked_subcommand is None:
        try:
            config_file = metadata.ConfigFile(
                csys.local_config_dir() + "/config.json"
            )
            current_project = config_file.read_variable("current_project", "")
            print("Current project: ", current_project)
            if (
                current_project is None or current_project == "" or
                current_project not in config_file.read_variable(
                    "projects_path"
                ).keys()
            ):

                print("No project is selected as the current project")
                msg = "Please use ``chern workon PROJECT''' to select"
                print(msg + " a project")
                print("Please use ``chern projects'' to list all the projects")
            else:
                start_chern_command_line()
        except Exception as e:
            print(e)
            print("Chern shell ended")


@cli.command()
def config():
    """ Configure the software"""
    print("Configuration is not supported yet")


@cli.command()
def chern_command_line():
    """ Start Chern command line with cmd """
    try:
        start_chern_command_line()
    except Exception as e:
        print("Fail to start Chern command line:", e)


@cli.command()
def init():
    """ Add the current directory to project """
    try:
        vproject.init_project()
        start_chern_command_line()
    except Exception as e:
        print(e)
        print("Chern Shell Ended")


@cli.command()
@click.argument("path", type=str)
def use(path):
    """ Use a directory as the project"""
    try:
        vproject.use_project(path)
        start_chern_command_line()
    except Exception as e:
        print("Fail to start ipython:", e)


@cli.command()
def projects():
    """ List all the projects """
    try:
        config_path = csys.local_config_dir() + "/config.json"
        config_file = metadata.ConfigFile(config_path)
        projects_list = config_file.read_variable("projects_path")
        current_project = config_file.read_variable("current_project")
        for project in projects_list.keys():
            if project == current_project:
                print("*", project, ":", projects_list[project])
            else:
                print(project, ":", projects_list[project])
    except Exception as e:
        print("Fail to list all the projects:", e)


@cli.command()
@click.argument("project", type=str)
def workon(project):
    """ Switch to the project ``PROJECT' """
    try:
        config_file = metadata.ConfigFile(
            join(csys.local_config_dir(), "config.json")
        )
        projects_list = config_file.read_variable("projects_path")
        if project in projects_list.keys():
            config_file.write_variable("current_project", project)
            print("Switch to project: ", project)
        else:
            print(f"Project ``{project}'' not found")
    except Exception as e:
        print("Fail to switch to the project:", e)


@cli.command()
@click.argument("project", type=str)
def remove(project):
    """ Remove the project ``PROJECT' """
    try:
        config_file = metadata.ConfigFile(
            join(csys.local_config_dir, "config.json")
        )
        projects_list = config_file.read_variable("projects_path")
        current_project = config_file.read_variable("current_project")
        if project == current_project:
            config_file.write_variable("current_project", "")

        if project in projects_list:
            projects_list.pop(project)
            config_file.write_variable("projects_path", projects_list)
            print("Remove project: ", project)
        else:
            print(f"Project ``{project}'' not found")
    except Exception:
        print("Fail to remove the project")


@cli.command()
def prologue():
    """ A prologue from the author """
    print("""
    Celebi: A data analysis management toolkit
    Author: Mingrui Zhao
            2013 - 2017
          @ Center of High Energy Physics, Tsinghua University
            2017 - 2025
          @ Department of Nuclear Physics, China Institute of Atomic Energy
            2020 - 2024
          @ Niels Bohr Institute, Copenhagen University
            2025 - now
          @ Peking University
    Email: mingrui.zhao@mail.labz0.org


    """)


@click.group()
def cli_sh():
    """ celebi command line command
    """

@cli_sh.command()
@click.argument("project", type=str)
def cd_project(project):
    """Switch to the project ``PROJECT'."""
    from CelebiChrono.interface import shell
    shell.cd_project(project)


def sh():
    """Entry point for shell commands."""
    cli_sh()


def main():
    """Main entry point for the Celebi CLI."""
    cli()  # pylint: disable=no-value-for-parameter
