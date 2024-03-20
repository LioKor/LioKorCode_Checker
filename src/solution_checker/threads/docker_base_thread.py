from threading import Thread

from docker.client import DockerClient
from docker.models.containers import Container


class DockerBaseThread(Thread):
    result: tuple[int, str] | None = None

    def __init__(self, client: DockerClient, container: Container) -> None:
        super().__init__()
        self.client = client
        self.container = container

    def terminate(self) -> None:
        self.container = self.client.containers.get(self.container.id)
        if self.container.status == "running":  # type: ignore
            self.container.kill()  # type: ignore
