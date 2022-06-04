import time

import config

from threading import Thread

from solution_checker.models import CheckResult, BuildResult, TestResult, TestsResult, LintResult
from solution_checker.utils import files_to_tar
from solution_checker.docker_utils import create_container, remove_container, get_file_from_container, put_file_to_container
import solution_checker.constants as c

from linter.linter import lint_dict, lint_errors_to_str


class DockerBuildThread(Thread):
    result = None

    def __init__(self, client, container, source_path):
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


class DockerTestThread(Thread):
    result = None

    def __init__(self, client, container, source_path, input_path, output_path):
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


def build_solution(client, container, build_timeout: float = config.DEFAULT_BUILD_TIMEOUT) -> BuildResult:
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


def run_test(client, container, test, io_path, test_timeout) -> TestResult:
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


def lint_solution(source_code: dict) -> LintResult:
    lint_errors = lint_dict(source_code)
    str_lint = lint_errors_to_str(lint_errors)

    lint_status = c.STATUS_OK if len(str_lint) == 0 else c.STATUS_LINT_ERROR
    return LintResult(
        status=lint_status,
        message=str_lint
    )


def check_solution(source_code: dict, tests: list, build_timeout: float, test_timeout: float) -> CheckResult:
    makefile = source_code.get('Makefile', None)
    if makefile is None:
        return CheckResult(check_result=c.STATUS_BUILD_ERROR, check_message='No Makefile found!')
    if makefile.find('run:') == -1:
        return CheckResult(check_result=c.STATUS_BUILD_ERROR, check_message='Makefile must at least contain "run:"')

    need_to_build = makefile.find('build:') != -1

    try:
        tar_source = files_to_tar(source_code, 'source/')
    except Exception:
        raise Exception('Unable to parse source code!')

    client, container = create_container()

    try:
        container.put_archive('/root', tar_source.read())
    except Exception:
        remove_container(client, container.id)
        raise Exception('Unable to create requested filesystem!')

    message = ''

    build_result = BuildResult(status=c.STATUS_OK)
    if need_to_build:
        build_result = build_solution(client, container, build_timeout)
        message += build_result.message + '\n' if len(build_result.message) > 0 else ''

    tests_result = TestsResult()
    if build_result.status == c.STATUS_OK:
        tests_result = test_solution(client, container, tests, test_timeout)
        message += tests_result.message + '\n' if len(tests_result.message) > 0 else ''

    lint_result = LintResult(status=c.STATUS_LINT_ERROR)
    if build_result.status == c.STATUS_OK and tests_result.status == c.STATUS_OK:
        lint_result = lint_solution(source_code)
        message += lint_result.message + '\n' if len(lint_result.message) > 0 else ''

    remove_container(client, container.id)

    check_result = build_result.status if build_result.status != c.STATUS_OK else tests_result.status
    return CheckResult(
        check_time=tests_result.time,  # todo: rename to test_time
        build_time=build_result.time,
        check_result=check_result,  # todo: rename to status
        check_message=message,
        tests_passed=tests_result.tests_passed,
        tests_total=tests_result.tests_total,
        lint_success=lint_result.status == c.STATUS_OK
    )
