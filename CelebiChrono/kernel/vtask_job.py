""" JobManager class for managing tasks
"""
import os
from logging import getLogger

from ..utils.container_manager import ContainerManager
from .chern_communicator import ChernCommunicator
from ..utils import csys
from ..utils.message import Message
from .vtask_core import Core

logger = getLogger("ChernLogger")


class JobManager(Core):
    """Job management for task execution and Docker container orchestration."""

    def docker_test(self) -> Message:
        """
        Executes the `docker_test` workflow by orchestrating Docker containers.

        Args:
            self.environment() (str): The Docker image to use.
            self.commands() (list[str]): Command list to execute inside the container.

        Returns:
            tuple[bool, str]: Execution result status and message.
        """
        print("Starting docker test...")
        success, mount_config = self.pre_docker_test()
        print(f"Pre-docker test preparation result: success={success}, "
              f"mount_config={mount_config}")
        if not success:
            return False, f"Pre-docker test preparation failed: {mount_config}"

        memory_limit = self.memory_limit()
        # Change the format of memory limit to be compatible with Docker
        # (e.g., "1g" instead of "1024Mi")
        if memory_limit.endswith("Mi"):
            memory_limit = str(int(memory_limit[:-2]) // 1024) + "g"
        elif memory_limit.endswith("Gi"):
            memory_limit = str(int(memory_limit[:-2])) + "g"
        print(f"Using memory limit for Docker: {memory_limit}")

        # Initialize the ContainerManager with the prepared mount configuration
        # Mount the base as /workspace
        volumes = {mount_config["base_dir"]: {'bind': '/workspace', 'mode': 'rw'}}
        # Add the additional mounts for preceding jobs and algorithm code
        for entry in mount_config["mounts"]:
            volumes[entry["source"]] = {'bind': entry["target"],
                                         'mode': 'ro' if entry["readonly"] else 'rw'}
        container_manager = ContainerManager(
            image=self.environment(),
            volumes=volumes,
            memory_limit=memory_limit,
            # name=f"container_{self.impression()}"
        )

        try:
            commands = self.algorithm().commands()
            # Parse the commands, and replace any placeholders with actual values if needed
            parameters = self.parameters()
            if parameters:
                # Example: Parameters for command execution:
                # (['events'], {'events': '20000'})
                # Here you can implement any logic to replace placeholders
                # in commands with actual parameter values
                # For example, if your command has a placeholder like {param1},
                # you can replace it with parameters['param1']
                for key, value in parameters[1].items():
                    commands = [cmd.replace(f"${{{key}}}", str(value)) for cmd in commands]
                # Commands after parameter substitution:
                # ['root -b -q \'code/gendata.C(20000,"stageout/data.root")\'']
            commands = " && ".join(commands)  # Join commands with '&&' to execute them sequentially
            # Insert a mkdir -p /workspace/stageout command to ensure the stageout directory exists
            commands = f"mkdir -p /workspace/stageout && {commands}"
            print(f"Final command to execute in container: {commands}")
            commands = ["/bin/bash", "-c", commands]  # Execute the commands in a bash shell
            container_manager.start_container(commands=commands)
            for log in container_manager.logs():
                print(log)  # Stream logs to the console
            container_manager.stop_container()
            return True, "Docker test executed successfully."
        except RuntimeError as e:
            return False, f"Docker test failed: {e}"

    def kill(self):
        """ Kill the task
        """
        cherncc = ChernCommunicator.instance()
        cherncc.kill(self.impression())

    def run_status(self, runner="none"): # pylint: disable=unused-argument
        """ Get the run status of the job"""
        # FIXME duplicated code
        cherncc = ChernCommunicator.instance()
        environment = self.environment()
        if environment == "rawdata":
            md5 = self.input_md5()
            dite_md5 = cherncc.sample_status(self.impression())
            if dite_md5 == md5:
                return "finished"
            return "unsubmitted"
        return cherncc.status(self.impression())

    # Communicator Interaction Methods
    def collect(self, contents="all"):
        """ Collect the results of the job"""
        msg = Message()
        if contents not in ("all", "outputs", "logs"):
            raise ValueError(f"Invalid contents parameter: {contents}")
        cherncc = ChernCommunicator.instance()
        if contents == "all":
            cherncc.collect(self.impression())
        elif contents == "outputs":
            cherncc.collect_outputs(self.impression())
        elif contents == "logs":
            cherncc.collect_logs(self.impression())
        msg.add(f"Collected {contents} of impression {self.impression()}")
        return msg

    def error_log(self, error_index=0):
        """ Collect the error logs of the job"""
        cherncc = ChernCommunicator.instance()
        cherncc.collect_logs(self.impression())
        msg = Message()
        msg.add(cherncc.error_log(self.impression(), error_index))
        return msg

    def watermark(self):
        """ Set the watermark to png files """
        cherncc = ChernCommunicator.instance()
        cherncc.watermark(self.impression())

    def display(self, filename):
        """ Display the file"""
        cherncc = ChernCommunicator.instance()
        # Open the browser to display the file
        cherncc.display(self.impression(), filename)

    def impview(self):
        """ Open browser to view the impression"""
        cherncc = ChernCommunicator.instance()
        return cherncc.impview(self.impression())

    def export(self, filename, output_file):
        """ Export the file"""
        cherncc = ChernCommunicator.instance()
        output_file_path = cherncc.export(
            self.impression(), filename, output_file
            )
        if output_file_path == "NOTFOUND":
            logger.error(
                "File %s not found in the job %s",
                filename, self.impression()
            )

    def send_data(self, path):
        """ Send data to the job"""
        cherncc = ChernCommunicator.instance()
        cherncc.deposit_with_data(self.impression(), path)

    def _check_preceding_jobs(self, cherncc) -> tuple[bool, str]:
        """Check whether all the preceding jobs are finished"""
        for pre in self.inputs():
            if not pre.is_impressed_fast():
                return False, f"Preceding job {pre} is not impressed"
            pre_status = pre.job_status()
            if pre_status not in ("finished", "archived"):
                return False, f"Preceding job {pre} is not finished"
            cherncc.collect(pre.impression())
        return True, ""

    def _prepare_data_dir(self, temp_dir):
        """copy the data to the temporal directory"""
        file_list = csys.tree_excluded(self.path)
        print(file_list)
        for dirpath, _, filenames in file_list:
            for f in filenames:
                full_path = os.path.join(self.project_path(), self.invariant_path(), dirpath, f)
                rel_path = os.path.relpath(full_path, self.path)
                dest_path = os.path.join(temp_dir, rel_path)
                csys.copy(full_path, dest_path)

    def _link_preceding_jobs(self, cherncc, temp_dir):
        """Create the temporal directory and copy the data there"""
        for pre in self.inputs():
            if not os.path.exists(
                csys.temp_dir(
                    name=pre.impression().uuid,
                    prefix="chernimp_"
                )):
                pre_temp_dir = csys.create_temp_dir(name=pre.impression().uuid, prefix="chernimp_")
                outputs = cherncc.output_files(pre.impression())
                csys.mkdir(os.path.join(pre_temp_dir, "stageout"))
                for f in outputs:
                    output_path = os.path.join(pre_temp_dir, "stageout", f)
                    cherncc.export(pre.impression(), f"{f}", output_path)
                    if pre.environment() != "rawdata":
                        print(f"Exported {f} to {output_path}")
            else:
                pre_temp_dir = csys.temp_dir(name=pre.impression().uuid, prefix="chernimp_")
            alias = self.path_to_alias(pre.invariant_path())
            print(f"Linking preceding job {pre} to {alias}")
            # Make a symlink
            csys.symlink(
                os.path.join(pre_temp_dir),
                os.path.join(temp_dir, alias),
            )

    def _prepare_algorithm_code(self, temp_dir): # pylint: disable=too-many-locals
        """Prepare the algorithm code and its inputs"""
        algorithm = self.algorithm()
        if not algorithm:
            return

        alg_temp_dir = csys.create_temp_dir(prefix="chernws_")
        file_list = csys.tree_excluded(algorithm.path)
        for dirpath, _, filenames in file_list:
            for f in filenames:
                full_path = os.path.join(
                        self.project_path(),
                        algorithm.invariant_path(),
                        dirpath, f
                )
                rel_path = os.path.relpath(full_path, algorithm.path)
                dest_path = os.path.join(alg_temp_dir, rel_path)
                csys.copy(full_path, dest_path)
        csys.symlink(
            os.path.join(alg_temp_dir),
            os.path.join(temp_dir, "code"),
        )

        # if the algorithm have inputs, link them too
        alg_inputs = filter(
            lambda x: (x.object_type() == "algorithm"), algorithm.predecessors()
            )
        for alg_in in list(map(lambda x: self.get_task(x.path), alg_inputs)):
            if not os.path.exists(
                csys.temp_dir(
                    name=alg_in.impression().uuid,
                    prefix="chernimp_"
                )):
                alg_in_temp_dir = csys.create_temp_dir(
                    name=alg_in.impression().uuid,
                    prefix="chernimp_"
                )
                alg_in_file_list = csys.tree_excluded(alg_in.path)
                for dirpath, _, filenames in alg_in_file_list:
                    for f in filenames:
                        full_path = os.path.join(
                                self.project_path(),
                                alg_in.invariant_path(),
                                dirpath, f
                        )
                        rel_path = os.path.relpath(full_path, alg_in.path)
                        dest_path = os.path.join(alg_in_temp_dir, rel_path)
                        csys.copy(full_path, dest_path)
            else:
                alg_in_temp_dir = csys.temp_dir(
                    name=alg_in.impression().uuid,
                    prefix="chernimp_"
                )
            alias = algorithm.path_to_alias(alg_in.invariant_path())
            # Link it under code
            csys.symlink(
                os.path.join(alg_in_temp_dir),
                os.path.join(temp_dir, "code", alias),
            )

    # pylint: disable=too-many-locals
    def workaround_preshell(self) -> tuple[bool, str]:
        """ Pre-shell workaround"""
        print("Start constructing workaround environment...")
        cherncc = ChernCommunicator.instance()
        status = cherncc.dite_status()
        if status != "connected":
            return False, ""

        success, message = self._check_preceding_jobs(cherncc)
        if not success:
            return False, message

        print("All preceding jobs are finished. Preparing data...")
        temp_dir = csys.create_temp_dir(prefix="chernws_")
        self._prepare_data_dir(temp_dir)

        print("Linking preceding jobs...")
        self._link_preceding_jobs(cherncc, temp_dir)

        self._prepare_algorithm_code(temp_dir)

        return True, temp_dir

    def pre_docker_test(self) -> tuple[bool, str | dict]:
        """ Pre-docker workaround - returns mounting guidance for Docker"""
        cherncc = ChernCommunicator.instance()
        status = cherncc.dite_status()
        if status != "connected":
            return False, ""

        success, message = self._check_preceding_jobs(cherncc)
        if not success:
            return False, message

        temp_dir = csys.create_temp_dir(prefix="chernwd_")
        self._prepare_data_dir(temp_dir)

        # The temp_dir will be mounted to the container as the workspace, and the preceding jobs
        # and algorithm code will be mounted to the corresponding paths under the workspace.
        # The container can access the data through these mounts, without needing to know
        # the details of how they are prepared.
        mount_config = {
            "base_dir": temp_dir,
            "mounts": []
        }

        self._prepare_mounting_preceding_jobs(cherncc, temp_dir, mount_config)
        self._prepare_mounting_algorithm_code(temp_dir, mount_config)

        return True, mount_config

    def _prepare_mounting_preceding_jobs(self, cherncc, _temp_dir, mount_config):
        """Prepare the preceding jobs for mounting - generates mount guidance"""
        for pre in self.inputs():
            pre_temp_dir = csys.temp_dir(name=pre.impression().uuid, prefix="chernimp_")
            if not os.path.exists(pre_temp_dir):
                pre_temp_dir = csys.create_temp_dir(name=pre.impression().uuid, prefix="chernimp_")
                outputs = cherncc.output_files(pre.impression())
                csys.mkdir(os.path.join(pre_temp_dir, "stageout"))
                for f in outputs:
                    output_path = os.path.join(pre_temp_dir, "stageout", f)
                    cherncc.export(pre.impression(), f"{f}", output_path)
                    if pre.environment() != "rawdata":
                        print(f"Exported {f} to {output_path}")

            alias = self.path_to_alias(pre.invariant_path())
            print(f"Mounting preceding job {pre} to {alias}")

            # Add mount configuration instead of creating symlink
            mount_config["mounts"].append({
                "source": pre_temp_dir,
                "target": f"/workspace/{alias}",
                "type": "bind",
                "readonly": True,
                "description": f"Preceding job {pre}"
            })

    def _prepare_mounting_algorithm_code(self, _temp_dir, mount_config):
        """Prepare the algorithm code for mounting - generates mount guidance"""
        algorithm = self.algorithm()
        if not algorithm:
            return

        alg_temp_dir = csys.create_temp_dir(prefix="chernws_")
        file_list = csys.tree_excluded(algorithm.path)
        for dirpath, _, filenames in file_list:
            for f in filenames:
                full_path = os.path.join(
                        self.project_path(),
                        algorithm.invariant_path(),
                        dirpath, f
                )
                rel_path = os.path.relpath(full_path, algorithm.path)
                dest_path = os.path.join(alg_temp_dir, rel_path)
                csys.copy(full_path, dest_path)

        # Add mount configuration instead of creating symlink (moved outside the loop)
        mount_config["mounts"].append({
            "source": alg_temp_dir,
            "target": "/workspace/code",
            "type": "bind",
            "readonly": False,
            "description": "Algorithm code"
        })

        # if the algorithm have inputs, link them too
        alg_inputs = filter(
            lambda x: (x.object_type() == "algorithm"), algorithm.predecessors()
            )
        for alg_in in list(map(lambda x: self.get_task(x.path), alg_inputs)):
            alg_in_temp_dir = csys.temp_dir(
                name=alg_in.impression().uuid, prefix="chernimp_")
            if not os.path.exists(alg_in_temp_dir):
                alg_in_temp_dir = csys.create_temp_dir(
                    name=alg_in.impression().uuid, prefix="chernimp_")
                alg_in_file_list = csys.tree_excluded(alg_in.path)
                for dirpath, _, filenames in alg_in_file_list:
                    for f in filenames:
                        full_path = os.path.join(
                                self.project_path(),
                                alg_in.invariant_path(),
                                dirpath, f
                        )
                        rel_path = os.path.relpath(full_path, alg_in.path)
                        dest_path = os.path.join(alg_in_temp_dir, rel_path)
                        csys.copy(full_path, dest_path)

            alias = algorithm.path_to_alias(alg_in.invariant_path())

            # Add mount configuration instead of creating symlink
            mount_config["mounts"].append({
                "source": alg_in_temp_dir,
                "target": f"/workspace/code/{alias}",
                "type": "bind",
                "readonly": True,
                "description": f"Algorithm input {alg_in}"
            })

    def workaround_postshell(self, path) -> bool:
        """ Post-shell workaround"""
        algorithm = self.algorithm()
        print("Post shell DEBUG")
        if algorithm:
            alg_temp_dir = os.path.join(path, "code")
            print(alg_temp_dir)
            file_list = csys.tree_excluded(algorithm.path)
            for dirpath, _, filenames in file_list:
                for f in filenames:
                    full_path = os.path.join(
                            self.project_path(),
                            algorithm.invariant_path(),
                            dirpath, f
                    )
                    rel_path = os.path.relpath(full_path, algorithm.path)
                    dest_path = os.path.join(alg_temp_dir, rel_path)
                    csys.copy(dest_path, full_path)
        return True
