import docker  # Using the Docker SDK for Python

class ContainerManager:
    def __init__(self, image: str, volumes: dict, memory_limit: str = "256Mi", name: str = None):
        """
        Initialize and configure the container manager.

        Args:
            image (str): Docker image name to use for the container.
            volumes (dict): Volume mappings for the container.
            memory_limit (str): Memory limit for the container.
            name (str): Name of the container.
        """
        self.image = image
        self.volumes = volumes
        self.memory_limit = memory_limit
        self.name = name
        self.client = docker.DockerClient(base_url='unix:///Users/zhaomr/.docker/run/docker.sock')
        self.container = None

    def start_container(self, commands: list[str]) -> None:
        """Start a Docker container with the specified settings."""
        try:
            self.container = self.client.containers.run(
                self.image,
                command=commands,
                volumes=self.volumes,
                detach=True,
                mem_limit=self.memory_limit,
                working_dir="/workspace",
                # name=self.name,
            )
            print(f"Container started with ID: {self.container.id}")
        except Exception as e:
            raise RuntimeError(f"Failed to start container: {e}")

    def logs(self):
        """Stream logs from the running container."""
        if not self.container:
            raise RuntimeError("No container is running")
        for log in self.container.logs(stream=True):
            yield log.decode().strip()

    def stop_container(self) -> None:
        """Stop and remove the container."""
        if self.container:
            self.container.stop()
            self.container.remove()
            print(f"Container {self.container.id} stopped and removed.")
        else:
            print("No container to stop.")