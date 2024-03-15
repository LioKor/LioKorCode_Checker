import time

from docker.client import DockerClient
from docker.models.containers import Container

from src.solution_checker.models import BuildResult
from src.solution_checker.models import CheckStatus
from src.solution_checker.threads.docker_build_thread import DockerBuildThread


def build_solution(
    client: DockerClient, container: Container, build_timeout: float
) -> BuildResult:
    build_thread = DockerBuildThread(client, container, "/root/source")
    start_time = time.time()
    build_thread.start()
    build_thread.join(build_timeout)
    build_time = time.time() - start_time
    result = build_thread.result

    if result is None:
        build_thread.terminate()
        # waiting for container to stop and then thread will exit
        build_thread.join()
        return BuildResult(
            status=CheckStatus.BUILD_TIMEOUT, time=build_time, message=""
        )

    exit_code, msg = result

    if exit_code != 0:
        return BuildResult(status=CheckStatus.BUILD_ERROR, time=build_time, message=msg)

    return BuildResult(status=CheckStatus.OK, time=build_time, message="")
