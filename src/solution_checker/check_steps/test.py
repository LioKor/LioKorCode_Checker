import time

from docker.client import DockerClient
from docker.models.containers import Container

from src.solution_checker.models import TestsResult, TestResult
from src.solution_checker.docker_utils import (
    put_file_to_container,
    get_file_from_container,
)
from src.solution_checker.models import CheckStatus
from src.solution_checker.threads.docker_test_thread import DockerTestThread


def run_test(
    client: DockerClient,
    container: Container,
    test: list[str],
    io_path: str,
    test_timeout: float,
) -> TestResult:
    input_file_path = io_path + "/input.txt"
    output_file_path = io_path + "/output.txt"

    test_input, expected_output = test
    put_file_to_container(container, input_file_path, test_input)

    test_thread = DockerTestThread(
        client, container, "/root/source", input_file_path, output_file_path
    )
    start_time = time.time()
    test_thread.start()
    test_thread.join(test_timeout)
    test_time = time.time() - start_time
    result = test_thread.result

    if result is None:
        test_thread.terminate()
        # waiting for container to stop and then thread will exit
        test_thread.join()
        return TestResult(
            status=CheckStatus.EXECUTION_TIMEOUT, time=test_time, message=""
        )

    exit_code, stdout = result
    if exit_code != 0:
        return TestResult(
            status=CheckStatus.RUNTIME_ERROR, time=test_time, message=stdout
        )

    fout = get_file_from_container(container, output_file_path)
    answer = fout if fout is not None else stdout

    # it's a practice to add \n at the end of output, but usually tests don't have it
    answer_has_end_newline = len(answer) > 0 and answer[-1] == "\n"
    expected_has_not_end_newline = (
        len(expected_output) > 0 and expected_output[-1] != "\n"
    )
    if answer_has_end_newline and expected_has_not_end_newline:
        answer = answer[0:-1]

    if answer != expected_output:
        msg = 'For "{}" expected "{}", but got "{}"'.format(
            test_input, expected_output, answer
        )
        return TestResult(status=CheckStatus.TEST_ERROR, time=test_time, message=msg)

    return TestResult(status=CheckStatus.OK, time=test_time, message="")


def test_solution(
    client: DockerClient,
    container: Container,
    tests: list[list[str]],
    test_timeout: float,
) -> TestsResult:
    io_directory_path = "/root/io"
    container.exec_run("mkdir -p {}".format(io_directory_path))

    tests_result = TestsResult(
        tests_total=len(tests),
        tests_passed=0,
        status=CheckStatus.OK,
        time=0.0,
        message="",
    )

    for test in tests:
        test_result = run_test(client, container, test, io_directory_path, test_timeout)

        tests_result.time += test_result.time
        if test_result.status != CheckStatus.OK:
            tests_result.status = test_result.status
            tests_result.message = test_result.message
            return tests_result

        tests_result.tests_passed += 1

    return tests_result
