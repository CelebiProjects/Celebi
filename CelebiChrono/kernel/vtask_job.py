""" JobManager class for managing tasks
"""
import os
from logging import getLogger
from typing import Tuple, Union

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

    def engine_logs(self):  # pylint: disable=too-many-locals,too-many-branches,too-many-statements
        """ Fetch and display engine logs for the task.

        Retrieves documented engine logs from the DITE server for the current
        task's impression. Engine logs provide detailed information about the
        execution environment, workflow engine operations, and runtime events.

        Returns:
            Message containing formatted engine log content or error message.
        """
        import json

        cherncc = ChernCommunicator.instance()
        # Check the connection
        dite_status = cherncc.dite_status()
        if dite_status != "connected":
            msg = Message()
            msg.add("DITE is not connected. Please check the connection.", "warning")
            return msg
        impression = self.impression()
        if not impression:
            msg = Message()
            msg.add("No impression found for current task", "error")
            return msg
        try:
            logs_raw = cherncc.engine_logs(impression)
            if logs_raw == "unconnected to DITE":
                msg = Message()
                msg.add("Failed to connect to DITE server", "error")
                return msg

            msg = Message()
            msg.add("=" * 60 + "\n", "title0")
            msg.add("ENGINE LOGS\n", "title0")
            msg.add("=" * 60 + "\n", "title0")

            # Parse outer JSON
            try:
                outer_data = json.loads(logs_raw)
            except json.JSONDecodeError:
                # If not JSON, print raw
                msg.add(logs_raw + "\n", "normal")
                return msg

            # The structure is: {"logs": {"logs": "...", "user": "...",
            # "workflow_id": "...", "workflow_name": "..."}}
            logs_container = outer_data.get("logs", {})
            if isinstance(logs_container, str):
                try:
                    logs_container = json.loads(logs_container)
                except json.JSONDecodeError:
                    logs_container = {}

            # Extract workflow info from logs_container
            workflow_name = logs_container.get("workflow_name", "N/A")
            workflow_id = logs_container.get("workflow_id", "N/A")
            user = logs_container.get("user", "N/A")

            msg.add("Workflow Name: ", "title0")
            msg.add(f"{workflow_name}\n", "normal")
            msg.add("Workflow ID: ", "title0")
            msg.add(f"{workflow_id}\n", "normal")
            msg.add("User: ", "title0")
            msg.add(f"{user}\n", "normal")
            msg.add("-" * 60 + "\n", "normal")

            # Parse inner logs (the nested "logs" field containing workflow_logs and job_logs)
            inner_logs_str = logs_container.get("logs", "{}")
            if isinstance(inner_logs_str, str):
                try:
                    inner_logs = json.loads(inner_logs_str)
                except json.JSONDecodeError:
                    inner_logs = {"workflow_logs": inner_logs_str}
            else:
                inner_logs = inner_logs_str

            # Display workflow logs with color-coded severity
            workflow_logs = inner_logs.get("workflow_logs", "")
            if workflow_logs:
                msg.add("\n", "normal")
                msg.add("WORKFLOW LOGS:\n", "title0")
                msg.add("=" * 40 + "\n", "normal")
                for line in workflow_logs.split("\n"):
                    # Determine color based on log severity
                    line_upper = line.upper()
                    if "CRITICAL" in line_upper or "ERROR" in line_upper:
                        color = "warning"  # Red for error/critical
                    elif "WARNING" in line_upper:
                        color = "running"  # Yellow for warning
                    else:
                        color = "normal"
                    msg.add(line + "\n", color)
                msg.add("\n", "normal")

            # Display job logs
            job_logs = inner_logs.get("job_logs", {})
            if job_logs:
                msg.add("\n", "normal")
                msg.add("JOB LOGS:\n", "title0")
                msg.add("=" * 40 + "\n", "normal")
                for job_id, job_info in job_logs.items():
                    msg.add("\nJob: ", "title0")
                    msg.add(f"{job_info.get('job_name', job_id)}\n", "success")
                    msg.add("  Status: ", "normal")
                    status = job_info.get("status", "unknown")
                    status_color = "success" if status == "finished" else "warning"
                    msg.add(f"{status}\n", status_color)
                    msg.add("  Backend: ", "normal")
                    msg.add(f"{job_info.get('compute_backend', 'N/A')}\n", "normal")
                    msg.add("  Docker: ", "normal")
                    msg.add(f"{job_info.get('docker_img', 'N/A')}\n", "normal")
                    msg.add("  Started: ", "normal")
                    msg.add(f"{job_info.get('started_at', 'N/A')}\n", "normal")
                    msg.add("  Finished: ", "normal")
                    msg.add(f"{job_info.get('finished_at', 'N/A')}\n", "normal")
                    msg.add("  Command: ", "normal")
                    msg.add(f"{job_info.get('cmd', 'N/A')}\n", "info")
                    job_log_content = job_info.get("logs", "")
                    if job_log_content and job_log_content.strip():
                        msg.add("  Output:\n", "normal")
                        for line in job_log_content.strip().split("\n"):
                            msg.add(f"    {line}\n", "normal")

            # Display engine-specific info if present
            engine_specific = inner_logs.get("engine_specific")
            if engine_specific:
                msg.add("\n", "normal")
                msg.add("ENGINE SPECIFIC:\n", "title0")
                msg.add("=" * 40 + "\n", "normal")
                msg.add(json.dumps(engine_specific, indent=2) + "\n", "normal")

            return msg
        except Exception as e:
            msg = Message()
            msg.add(f"Failed to fetch engine logs: {e}", "error")
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

    def imgcat(self, filename):
        """ Display image file inline in terminal using imgcat protocol.

        Fetches the image from dite and returns data for inline terminal display
        using iTerm2 imgcat escape sequences.

        Args:
            filename: Name of the image file to display from dite.

        Returns:
            tuple: (success: bool, message: str, image_output: str or None)
        """

        cherncc = ChernCommunicator.instance()
        impression = self.impression()

        if impression is None:
            return False, "No impression available for current task", None

        # Fetch image data from dite
        url = cherncc.serverurl()
        try:
            import requests
            response = requests.get(
                f"http://{url}/export/{cherncc.project_uuid}/{impression.uuid}/{filename}",
                timeout=cherncc.timeout * 1000
            )
            if response.status_code != 200:
                return False, f"Failed to fetch image: HTTP {response.status_code}", None
            image_data = response.content

            # Validate that the data is actually an image by checking magic bytes
            if not self._is_valid_image_data(image_data):
                return False, f"File not found or not a valid image: {filename}", None
        except Exception as e:
            return False, f"Failed to fetch image from dite: {e}", None

        # Generate imgcat escape sequence for inline image display
        try:
            imgcat_output = self._generate_imgcat_output(image_data, filename)
            return True, "Image ready for display", imgcat_output
        except Exception as e:
            return False, f"Failed to generate imgcat output: {e}", None

    def _is_valid_image_data(self, data):
        """Check if data is a valid image by examining magic bytes.

        Args:
            data: Raw bytes to check.

        Returns:
            bool: True if data looks like a valid image format.
        """
        if len(data) < 8:
            return False

        # Check magic bytes for common image formats
        magic_bytes = {
            b'\x89PNG\r\n\x1a\n': 'png',  # PNG
            b'\xff\xd8\xff': 'jpeg',      # JPEG
            b'GIF87a': 'gif',              # GIF87a
            b'GIF89a': 'gif',              # GIF89a
            b'BM': 'bmp',                  # BMP
            b'RIFF': 'webp',               # WebP (starts with RIFF)
        }

        for magic, _fmt in magic_bytes.items():
            if data.startswith(magic):
                return True

        return False

    def _generate_imgcat_output(self, image_data, filename):
        """Generate iTerm2 imgcat escape sequence for image data.

        Args:
            image_data: Raw bytes of the image file.
            filename: Name of the file (used to determine format).

        Returns:
            str: The imgcat escape sequence.
        """
        import base64
        # Determine format from extension
        ext = filename.lower().split('.')[-1] if '.' in filename else 'png'
        format_map = {
            'png': 'image/png',
            'jpg': 'image/jpeg',
            'jpeg': 'image/jpeg',
            'gif': 'image/gif',
            'bmp': 'image/bmp',
            'webp': 'image/webp'
        }
        mime_type = format_map.get(ext, 'image/png')

        # Base64 encode the image and filename
        b64_data = base64.b64encode(image_data).decode('utf-8')
        name_b64 = base64.b64encode(filename.encode('utf-8')).decode('utf-8')

        # Build imgcat escape sequence
        output = (
            f"\033]1337;File=name={name_b64};size={len(image_data)};inline=1;"
            f"type={mime_type}:{b64_data}\007"
        )

        return output

    def list_output_files(self):
        """List available output files from dite for current impression.

        Returns:
            tuple: (success: bool, files: list or error_message: str)
        """
        cherncc = ChernCommunicator.instance()
        impression = self.impression()

        if impression is None:
            return False, "No impression available for current task"

        try:
            files = cherncc.output_files(impression, "none")
            return True, files
        except Exception as e:
            return False, f"Failed to list output files: {e}"

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

    def pre_docker_test(self) -> Tuple[bool, Union[str, dict]]:
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
