# pylint: disable=invalid-name
"""
This is the top class for project manager
"""
import os
from typing import TYPE_CHECKING, Optional, List
from ..utils import metadata
from ..utils import csys
from ..kernel import valgorithm as valg  # as _VAlgorithm
from ..kernel import vtask as vtsk  # as _VTask
from ..kernel import vdirectory as vdir
from ..kernel import vproject as vproj

if TYPE_CHECKING:
    from ..kernel.vobject import VObject

def create_object_instance(path: str) -> 'VObject':
    """ Create an object instance
    """
    path = csys.strip_path_string(path)
    object_config_file = metadata.ConfigFile(path+"/.chern/config.json")
    object_type = object_config_file.read_variable("object_type")
    vobject_class = {"algorithm":valg.VAlgorithm,
                     "task":vtsk.VTask,
                     "directory":vdir.VDirectory,
                     "project":vproj.VProject}
    return vobject_class[object_type](path)

class ChernProjectManager:
    """ ChernManager class
    """
    instance = None
    c = None

    @classmethod
    def get_manager(cls) -> 'ChernProjectManager':
        """ Return the manager itself
        """
        if cls.instance is None:
            cls.instance = ChernProjectManager()
        return cls.instance

    def __init__(self) -> None:
        self.init_global_config()

    def init_global_config(self) -> None:
        """Initialize global configuration directory and paths."""
        chern_config_path = os.environ.get("HOME") +"/.Chern"
        if not os.path.exists(chern_config_path):
            os.mkdir(chern_config_path)
        self.global_config_path = csys.strip_path_string(chern_config_path) + "/config.json"

    def get_current_project(self) -> Optional[str]:
        """ Get the name of the current working project.
        If there isn't a working project, return None
        """
        global_config_file = metadata.ConfigFile(self.global_config_path)
        current_project = global_config_file.read_variable("current_project")
        if current_project is None:
            return None

        projects_path = global_config_file.read_variable("projects_path")
        path = projects_path.get(current_project, "no_place|")
        if path == "no_place|":
            projects_path[current_project] = "no_place|"
        if not os.path.exists(path):
            projects_path.pop(current_project)
            if projects_path != {}:
                current_project = list(projects_path.keys())[0]
            else:
                current_project = None
            global_config_file.write_variable("current_project", current_project)
            global_config_file.write_variable("projects_path", projects_path)
            return self.get_current_project()

        return current_project

    def get_all_projects(self) -> List[str]:
        """ Get the list of all the projects.
        If there is not a list create one.
        """
        global_config_file = metadata.ConfigFile(self.global_config_path)
        projects_path = global_config_file.read_variable("projects_path")
        return list(projects_path.keys())

    def ls_projects(self) -> None:
        """
        ls projects
        """
        projects_list = self.get_all_projects()
        for project_name in projects_list:
            print(project_name)

    def get_project_path(self, project_name: str) -> str:
        """ Get The path of a specific project.
        You must be sure that the project exists.
        This function don't check it.
        """
        global_config_file = metadata.ConfigFile(self.global_config_path)
        projects_path = global_config_file.read_variable("projects_path")
        return projects_path[project_name]

    def switch_project(self, project_name: str) -> None:
        """ Switch the current project

        """
        projects_list = self.get_all_projects()
        if project_name not in projects_list:
            print("No such a project")
            return
        global_config_file = metadata.ConfigFile(self.global_config_path)
        global_config_file.write_variable("current_project", project_name)
        path = self.get_project_path(project_name)
        if not os.path.exists(path):
            print("Project deleted")
            return
        self.c = create_object_instance(path)

    def switch_current_object(self, path: str) -> None:
        """Switch the current object to the one at the given path."""
        self.c = create_object_instance(path)

    def current_object(self) -> 'VObject':
        """Get the current object instance from the current working directory."""
        path = os.getcwd()
        return create_object_instance(path)

    def sub_object(self, dirname) -> 'VObject':
        """Get the sub object instance from the current working directory."""
        path = os.path.join(os.getcwd(), dirname)
        return create_object_instance(path)



def get_manager() -> ChernProjectManager:
    """Get the singleton ChernProjectManager instance."""
    return ChernProjectManager.get_manager()
