# pylint: disable=broad-exception-caught
# pylint: disable=too-many-public-methods
# pylint: disable=consider-using-with
"""
Chern class for communicate to local and remote server.

HTTP API Endpoints Summary:
==========================

Job Submission & Management:
- POST /upload - Upload impression tar.gz and config files
- GET /run/{uuid}/{machine_id} - Execute impression on specified machine
- POST /execute - Execute multiple impressions with machine specification
- GET /kill/{uuid} - Kill running impression
- GET /resubmit/{uuid}/{machine_id} - Resubmit failed impression

Status & Monitoring:
- GET /status/{uuid} - Get job status of impression
- GET /run-status/{uuid}/{machine} - Get run status on specific machine
- GET /deposited/{uuid} - Check if impression is deposited
- GET /sample-status/{uuid} - Get sample processing status
- GET /workflow/{uuid} - Get workflow information
- GET /dite-status - Check DITE server connection status

Machine & Runner Management:
- GET /runners - List available compute runners
- GET /runners-url - List runner URLs
- GET /machine-id/{machine} - Get machine ID for runner name
- POST /register-runner - Register new compute runner
- GET /remove-runner/{runner} - Remove compute runner
- GET /runner-connection/{runner} - Check runner connection status

File Operations:
- GET /collect/{uuid} - Collect impression results
- GET /export/{uuid}/{filename} - Download specific file from impression
- GET /outputs/{impression}/{machine_id} - List output files
- GET /get-file/{impression}/{filename} - Get file path from impression
- GET /imp-view/{uuid} - View impression in browser interface
- GET /set-job-status/{uuid}/archived - Set job status to archived

All requests use configurable timeout (default: 10s) and support both local and remote execution.

Method Usage Status:
===================
✓ Used methods: submit, deposit, execute, kill, runners, register_runner,
  remove_runner, status, run_status, collect, export, dite_status, dite_info,
  output_files, get_file, deposit_with_data, add_host, serverurl, is_deposited,
  workflow, sample_status, job_status, runner_connection, impview, display

✗ UNUSED methods: resubmit, runners_url
"""

from os.path import join
import json
from logging import getLogger
import subprocess
import tarfile
import requests

from ..utils import csys
from ..utils import metadata
from ..utils.pretty import colorize
logger = getLogger("ChernLogger")


class ChernCommunicator():
    """ Communicator for Chern """
    ins = None

    # === Core Infrastructure ===
    def __init__(self):
        """ Initialize the communicator and Singleton """
        self.local_config_dir = csys.local_config_dir()
        self.timeout = 10
        project_path = csys.project_path()
        self.config_file = metadata.ConfigFile(
            join(project_path, ".chern/hosts.json")
            )

    @classmethod
    def instance(cls):
        """ Singleton instance """
        if cls.ins is None:
            cls.ins = ChernCommunicator()
        return cls.ins

    def add_host(self, url):
        """ Add a host to the server """
        # FIXME: add host_name and url check
        self.config_file.write_variable("serverurl", url)

    def serverurl(self):
        """ Get the serverurl """
        return self.config_file.read_variable("serverurl", "localhost:5000")

    # === Server Status & Connection ===
    def dite_status(self): # UnitTest: DONE
        """ Get the status of the DITE """
        logger.debug("ChernCommunicator/dite_status")
        url = self.serverurl()
        logger.debug("url: %s", url)
        try:
            logger.debug("http://%s/dite-status", url)
            r = requests.get(f"http://{url}/dite-status", timeout=self.timeout)
            logger.debug(r)
        except Exception:
            return "unconnected"
        status = r.text
        if status == "ok":
            return "connected"
        return "unconnected"

    def dite_info(self): # UnitTest: DONE
        """ Get the information of the DITE """
        w = ""
        w += colorize("DITE URL: ", "title0")
        w += colorize(self.serverurl(), "normal")
        w += "\n"
        w += colorize("DITE Status: ", "title0")
        if self.dite_status() == "connected":
            w += colorize("[connected]", "success")
        else:
            w += colorize("[unconnected]", "warning")
        w += "\n"
        return w

    # === Job Submission & Execution ===
    def submit(self, impression, machine="local"):
        """ Submit the impression to the server """
        tarname = impression.tarfile
        files = {
            f"{impression.uuid}.tar.gz": open(tarname, "rb").read(),
            "config.json": open(impression.path + "/config.json", "rb").read()
        }
        url = self.serverurl()
        machine_id = requests.get(
            f"http://{url}/machine-id/{machine}",
            timeout=self.timeout
        ).text
        requests.post(
            f"http://{url}/upload",
            data={
                'tarname': f"{impression.uuid}.tar.gz",
                'config': "config.json"
            },
            files=files,
            timeout=self.timeout
        )
        # FIXME: here we simply assume that the upload is always correct
        requests.get(
            f"http://{url}/run/{impression.uuid}/{machine_id}",
            timeout=self.timeout
        )

    def deposit(self, impression):
        """ Deposit the impression to the server """
        tarname = impression.tarfile
        files = {
            f"{impression.uuid}.tar.gz": open(tarname, "rb").read(),
            "config.json": open(impression.path + "/config.json", "rb").read()
        }
        url = self.serverurl()
        requests.post(
            f"http://{url}/upload",
            data={
                'tarname': f"{impression.uuid}.tar.gz",
                'config': "config.json"
            },
            files=files,
            timeout=self.timeout
        )

    def deposit_with_data(self, impression, path): # UnitTest: DONE
        """ Deposit the impression with additional data """
        tmpdir = "/tmp"
        tarname = tmpdir + "/" + impression.uuid + ".tar.gz"
        impression_tar = tarfile.open(impression.tarfile, "r")
        # Add additional data to the tar file
        tar = tarfile.open(tarname, "w:gz")
        for member in impression_tar.getmembers():
            tar.addfile(member, impression_tar.extractfile(member))
        tar.add(path, arcname="rawdata")
        tar.close()
        impression_tar.close()

        files = {
            f"{impression.uuid}.tar.gz": open(tarname, "rb").read(),
            "config.json": open(impression.path + "/config.json", "rb").read()
        }
        url = self.serverurl()

        requests.post(
            f"http://{url}/upload",
            data={
                'tarname': f"{impression.uuid}.tar.gz",
                'config': "config.json"
            },
            files=files,
            timeout=self.timeout
        )
        requests.get(
                f"http://{url}/set-job-status/{impression.uuid}/archived",
                timeout=self.timeout
        )

    def execute(self, impressions, machine="local"):
        """ Execute the impressions on the server """
        files = {"impressions": " ".join(impressions)}
        url = self.serverurl()
        machine_id = requests.get(
            f"http://{url}/machine-id/{machine}",
            timeout=self.timeout
        ).text
        requests.post(
            f"http://{url}/execute",
            data={'machine': machine_id},
            files=files,
            timeout=self.timeout
        )

    def resubmit(self, impression, machine="local"):
        """ Resubmit the impression to the server

        ✗ UNUSED METHOD - No references found in codebase
        """
        # Well, I don't know how to do it.
        # Because we need to check which part has the problem, etc.
        # For testing purpose on a small project,
        # we should first remove every thing in the impression
        # and workflow directory and then to redo the submit

    # === Job Status & Monitoring ===
    def status(self, impression): # UnitTest: DONE
        """ Get the status of the impression """
        url = self.serverurl()
        try:
            r = requests.get(
                f"http://{url}/status/{impression.uuid}",
                timeout=self.timeout
            )
        except Exception as e:
            print(f"An error occurred: {e}")
            return "unconnected"
        return r.text

    def run_status(self, impression, machine="none"): # UnitTest: DONE
        """ Get the run status of the impression """
        url = self.serverurl()
        try:
            r = requests.get(
                f"http://{url}/run-status/{impression.uuid}/{machine}",
                timeout=self.timeout
            )
        except Exception as e:
            print(f"An error occurred: {e}")
            return "unconnected"
        return r.text

    def is_deposited(self, impression):
        """ Check if the impression is deposited on the server """
        url = self.serverurl()
        try:
            r = requests.get(
                f"http://{url}/deposited/{impression.uuid}",
                timeout=self.timeout
            )
        except Exception as e:
            print(f"An error occurred: {e}")
            return "FALSE"
        return r.text

    def job_status(self, impression):
        """ Get the job status of the impression """
        url = self.serverurl()
        try:
            r = requests.get(
                f"http://{url}/status/{impression.uuid}",
                timeout=self.timeout
            )
        except Exception as e:
            print(f"An error occurred: {e}")
            return "unconnected to DITE"
        return r.text

    def sample_status(self, impression):
        """ Get the sample status of the impression """
        url = self.serverurl()
        try:
            r = requests.get(
                f"http://{url}/sample-status/{impression.uuid}",
                timeout=self.timeout
            )
        except Exception as e:
            print(f"An error occurred: {e}")
            return "unconnected to DITE"
        return r.text

    def workflow(self, impression):
        """ Get the workflow of the impression """
        url = self.serverurl()
        try:
            r = requests.get(
                f"http://{url}/workflow/{impression.uuid}",
                timeout=self.timeout
            )
        except Exception as e:
            print(f"An error occurred: {e}")
            return ["unconnected to DITE"]
        return r.text.split()

    # === Job Control ===
    def kill(self, impression):
        """ Kill the impression on the server """
        url = self.serverurl()
        try:
            r = requests.get(
                f"http://{url}/kill/{impression.uuid}",
                timeout=self.timeout
            )
        except Exception as e:
            print(f"An error occurred: {e}")
            return "unconnected"
        return r.text

    def collect(self, impression): # UnitTest: DONE
        """ Collect the impression from the server """
        url = self.serverurl()
        r = requests.get(
                f"http://{url}/collect/{impression.uuid}",
                timeout=self.timeout * 1000
        )
        return r.text

    # === Runner Management ===
    def runners(self):
        """ Get the list of runners """
        url = self.serverurl()
        try:
            r = requests.get(
                    f"http://{url}/runners",
                    timeout=self.timeout
            )
        except Exception as e:
            print(f"An error occurred: {e}")
            return ["unconnected to DITE"]
        return r.text.split()

    def runners_url(self):
        """ Get the list of runner URLs

        ✗ UNUSED METHOD - No references found in codebase
        """
        url = self.serverurl()
        try:
            r = requests.get(
                    f"http://{url}/runners-url",
                    timeout=self.timeout
            )
        except Exception as e:
            print(f"An error occurred: {e}")
            return ["unconnected to DITE"]
        return r.text.split()

    def register_runner(self, runner, runner_url, token):
        """ Register a runner to the server """
        url = self.serverurl()

        requests.post(
            f"http://{url}/register-runner",
            data={'runner': runner, 'url': runner_url, 'token': token},
            timeout=self.timeout
        )

    def remove_runner(self, runner):
        """ Remove a runner from the server """
        url = self.serverurl()
        try:
            r = requests.get(
                    f"http://{url}/remove-runner/{runner}",
                    timeout=self.timeout
            )
            if r.text != "successful":
                print("Failed to remove runner")
        except Exception as e:
            print(f"An error occurred: {e}")
            return ["unconnected to DITE"]
        return r.text.split()

    def runner_connection(self, runner):
        """ Get the connection status of the runner """
        url = self.serverurl()
        try:
            r = requests.get(
                f"http://{url}/runner-connection/{runner}",
                timeout=self.timeout
            )
        except Exception as e:
            print(f"An error occurred: {e}")
            return {"status": "unconnected to DITE"}
        return json.loads(r.text)

    # === File Operations ===
    def output_files(self, impression, machine="none"): # UnitTest: DONE
        """ Get the output files of the impression """
        url = self.serverurl()
        if machine == "none":
            machine_id = "none"
        else:
            machine_id = requests.get(
                f"http://{url}/machine-id/{machine}",
                timeout=self.timeout
            ).text
        r = requests.get(
            f"http://{url}/outputs/{impression}/{machine_id}",
            timeout=self.timeout
        )
        return r.text.split()

    def get_file(self, impression, filename): # UnitTest: DONE
        """ Get the file from the server """
        url = self.serverurl()
        path = requests.get(
            f"http://{url}/get-file/{impression}/{filename}",
            timeout=self.timeout
        ).text
        return path

    def export(self, impression, filename, output): # UnitTest: DONE
        """ Export the file from the server """
        url = self.serverurl()
        r = requests.get(
                f"http://{url}/export/{impression.uuid}/{filename}",
                timeout=self.timeout
        )
        with open(output, "wb") as f:
            f.write(r.content)

    # === Browser Integration ===
    def display(self, impression, filename):
        """ Display the file in the browser """
        # Open the browser to display the file
        url = self.serverurl()
        # The browser is 'open'
        subprocess.call(["open", f"http://{url}/export/{impression.uuid}/{filename}"
            ])

    def impview(self, impression):
        """ View the impression in the browser """
        url = self.serverurl()
        return f"http://{url}/imp-view/{impression.uuid}"
