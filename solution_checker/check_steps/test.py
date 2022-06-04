from threading import Thread
import time

from solution_checker.models import TestsResult, TestResult
from solution_checker.docker_utils import put_file_to_container, get_file_from_container
import solution_checker.constants as c


class DockerTestThread(Thread):
    result = None

    def __init__(self, client, container, source_path: str, input_path: str, output_path: str):
        super().__init__()
        self.client = client
        self.container = container
        self.source_path = source_path
        self.input_path = input_path
        self.output_path = output_path

    def run(self):
        # when timeout is too short exec_run could raise error
        try:
            run_command = '/bin/bash -c "rm -f {output_fpath} && cat {input_fpath} | make -s ARGS=\'{input_fpath} {output_fpath}\' run"'.format(
                input_fpath=self.input_path,
                output_fpath=self.output_path
            )
            execute_result = self.container.exec_run(
                run_command,
                workdir=self.source_path,
                environment={
                    'ARGS': '{} {}'.format(self.input_path, self.output_path),
                    'input_path': self.input_path,
                    'output_path': self.output_path
                }
            )

            self.container = self.client.containers.get(self.container.id)
            if self.container.status == 'exited':
                return
        except Exception:
            return

        exit_code, stdout = execute_result.exit_code, execute_result.output.decode()
        self.result = (exit_code, stdout)

    def terminate(self):
        self.container = self.client.containers.get(self.container.id)
        if self.container.status == 'running':
            self.container.kill()


def run_test(client, container, test: list, io_path: str, test_timeout: float) -> TestResult:
    input_file_path = io_path + '/input.txt'
    output_file_path = io_path + '/output.txt'

    test_input, expected_output = test
    put_file_to_container(container, input_file_path, test_input)

    test_thread = DockerTestThread(client, container, '/root/source', input_file_path, output_file_path)
    start_time = time.time()
    test_thread.start()
    test_thread.join(test_timeout)
    test_time = round(time.time() - start_time, 4)
    result = test_thread.result

    if result is None:
        test_thread.terminate()
        # waiting for container to stop and then thread will exit
        test_thread.join()
        return TestResult(
            status=c.STATUS_RUNTIME_TIMEOUT,
            time=test_time
        )

    exit_code, stdout = result
    if exit_code != 0:
        return TestResult(
            status=c.STATUS_RUNTIME_ERROR,
            time=test_time,
            message=stdout
        )

    fout = get_file_from_container(container, output_file_path)
    answer = fout if fout is not None else stdout

    # it's a practice to add \n at the end of output, but usually tests don't have it
    if len(answer) > 0 and answer[-1] == '\n' and expected_output[-1] != '\n':
        answer = answer[0:-1]

    if answer != expected_output:
        msg = 'For "{}" expected "{}", but got "{}"'.format(test_input, expected_output, answer)
        return TestResult(
            status=c.STATUS_TEST_ERROR,
            time=test_time,
            message=msg
        )

    return TestResult(
        status=c.STATUS_OK,
        time=test_time
    )


def test_solution(client, container, tests: list, test_timeout: float) -> TestsResult:
    io_directory_path = '/root/io'
    container.exec_run('mkdir -p {}'.format(io_directory_path))

    tests_result = TestsResult(tests_total=len(tests))

    for test in tests:
        test_result = run_test(client, container, test, io_directory_path, test_timeout)

        tests_result.time += test_result.time
        if test_result.status != c.STATUS_OK:
            tests_result.status = test_result.status
            tests_result.message = test_result.message
            break

        tests_result.tests_passed += 1

    return tests_result
