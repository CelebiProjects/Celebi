""" The helper class that is used to "operate" the project
    It is only used to "operate" things since all the information are stored in disk
    The core part may move to c language in the future
"""
import os
from ..utils import metadata
from ..utils import csys
from ..utils.message import Message
from .vdirectory import VDirectory
from .vobject import VObject
from . import helpme


class VProject(VDirectory):
    """ operate the project
    """

    def helpme(self, command):
        """ get the help message"""
        message = Message()
        message.add(helpme.project_helpme.get(command, "No such command, try ``helpme'' alone."))
        return message

    def clean_impressions(self):
        """ Clean all the impressions of the project"""
        clean_confirmed = input("Are you sure to clean all the impressions? [y/n]")
        if clean_confirmed != "y":
            return
        sub_objects = self.sub_objects()
        for sub_object in sub_objects:
            VObject(sub_object.path).clean_impressions()
        csys.rm_tree(self.path+"/.chern/impressions")

######################################
# Helper functions
def create_readme(project_path):
    """ Create the README.md and project.json file"""
    with open(project_path+"/.chern/project.json", "w", encoding="utf-8"):
        pass
    with open(project_path + "/.chern/README.md", "w", encoding="utf-8") as f:
        f.write("")


def create_configfile(project_path, uuid):
    """ Create the config file"""
    config_file = metadata.ConfigFile(project_path+"/.chern/config.json")
    config_file.write_variable("object_type", "project")
    config_file.write_variable("chern_version", "0.0.0")
    config_file.write_variable("project_uuid", uuid)


def create_hostsfile(project_path):
    """ Create the hosts file"""
    config_file = metadata.ConfigFile(project_path+"/.chern/hosts.json")
    config_file.write_variable("serverurl", "127.0.0.1:3315")


######################################
# Functions:
def init_project():
    """ Create a new project from the existing folder
    """
    pwd = os.getcwd()
    if os.listdir(pwd) != []:
        raise Exception(f"[ERROR] Initialize on a unempty directory is not allowed {pwd}")
    project_name = pwd[pwd.rfind("/")+1:]
    print(f"The project name is ``{project_name}'', would you like to change it? [y/n]")
    change = input()
    if change == "y":
        project_name = input("Please input the project name: ")

    # Check the forbidden name
    forbidden_names = ["config", "new", "projects", "start", "", "."]

    def check_project_failed(forbidden_names):
        message = "The following project names are forbidden:"
        message += "\n    "
        for name in forbidden_names:
            message += name + ", "
        raise Exception(message)

    if project_name in forbidden_names:
        check_project_failed(forbidden_names)

    project_path = pwd
    uuid = csys.generate_uuid()
    os.mkdir(project_path+"/.chern")
    create_readme(project_path)
    create_configfile(project_path, uuid)
    create_hostsfile(project_path)
    global_config_file = metadata.ConfigFile(csys.local_config_path())
    projects_path = global_config_file.read_variable("projects_path")
    if projects_path is None:
        projects_path = {}
    projects_path[project_name] = project_path
    global_config_file.write_variable("projects_path", projects_path)
    global_config_file.write_variable("current_project", project_name)
    os.chdir(project_path)


def use_project(path):
    """ Use an exsiting project
    """
    path = os.path.abspath(path)
    print(path)
    project_name = path[path.rfind("/")+1:]
    print("The project name is ``{project_name}'', would you like to change it? [y/n]")
    change = input()
    if change == "y":
        project_name = input("Please input the project name")

    # Check the forbidden name
    forbidden_names = ["config", "new", "projects", "start", "", "."]
    def check_project_failed(forbidden_names):
        message = "The following project names are forbidden:"
        message += "\n    "
        for name in forbidden_names:
            message += name + ", "
        raise Exception(message)
    if project_name in forbidden_names:
        check_project_failed(forbidden_names)

    project_path = path
    config_file = metadata.ConfigFile(project_path+"/.chern/config.json")
    object_type = config_file.read_variable("object_type", "")
    if object_type != "project":
        print("The path is not a project")
        return
    print("The project type is ", object_type)
    os.chdir(path)
    global_config_file = metadata.ConfigFile(csys.local_config_path())
    projects_path = global_config_file.read_variable("projects_path", {})
    projects_path[project_name] = project_path
    global_config_file.write_variable("projects_path", projects_path)
    global_config_file.write_variable("current_project", project_name)
    os.chdir(project_path)
