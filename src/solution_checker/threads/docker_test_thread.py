from docker.client import DockerClient
from docker.models.containers import Container

from src.solution_checker.threads.docker_base_thread import DockerBaseThread


class DockerTestThread(DockerBaseThread):
    def __init__(
        self,
        client: DockerClient,
        container: Container,
        source_path: str,
        input_path: str,
        output_path: str,
    ):
        super().__init__(client, container)
        self.source_path = source_path
        self.input_path = input_path
        self.output_path = output_path

    def run(self) -> None:
        # when timeout is too short exec_run could raise error
        try:
            run_command = (
                f'/bin/bash -c "rm -f {self.output_path} && cat {self.input_path} | '
                f"make -s ARGS='{self.input_path} {self.output_path}' run\""
            )
            execute_result = self.container.exec_run(
                run_command,
                workdir=self.source_path,
                environment={
                    "ARGS": "{} {}".format(self.input_path, self.output_path),
                    "input_path": self.input_path,
                    "output_path": self.output_path,
                },
            )

            self.container = self.client.containers.get(self.container.id)
            if self.container.status == "exited":
                return
        except Exception:
            return

        exit_code, stdout = execute_result.exit_code, execute_result.output.decode()
        self.result = (exit_code, stdout)
