from threading import Thread
import time

from solution_checker.models import BuildResult
import solution_checker.constants as c

import config


class DockerBuildThread(Thread):
    result = None

    def __init__(self, client, container, source_path: str):
        super().__init__()
        self.client = client
        self.container = container
        self.source_path = source_path

    def run(self):
        # when timeout is too short exec_run could raise error
        try:
            build_command = 'make build'
            build_result = self.container.exec_run(build_command, workdir=self.source_path)
            self.result = build_result
        except Exception:
            pass

    def terminate(self):
        self.container.kill()


def build_solution(client, container, build_timeout: float) -> BuildResult:
    build_thread = DockerBuildThread(client, container, '/root/source')
    start_time = time.time()
    build_thread.start()
    build_thread.join(build_timeout)
    build_time = round(time.time() - start_time, 4)
    result = build_thread.result

    if result is None:
        build_thread.terminate()
        # waiting for container to stop and then thread will exit
        build_thread.join()
        return BuildResult(
            status=c.STATUS_BUILD_TIMEOUT,
            time=build_time,
            message=''
        )

    if result.exit_code != 0:
        msg = result.output.decode()
        return BuildResult(
            status=c.STATUS_BUILD_ERROR,
            time=build_time,
            message=msg
        )

    return BuildResult(
        status=c.STATUS_OK,
        time=build_time,
        message=''
    )
