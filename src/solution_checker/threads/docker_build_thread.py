from docker.client import DockerClient
from docker.models.containers import Container

from src.solution_checker.threads.docker_base_thread import DockerBaseThread


class DockerBuildThread(DockerBaseThread):
    def __init__(self, client: DockerClient, container: Container, source_path: str):
        super().__init__(client, container)
        self.source_path = source_path

    def run(self) -> None:
        # when timeout is too short exec_run could raise error
        try:
            build_command = "make build"
            execute_result = self.container.exec_run(
                build_command, workdir=self.source_path
            )
        except Exception:
            return

        exit_code, stdout = execute_result.exit_code, execute_result.output.decode()
        self.result = (exit_code, stdout)
