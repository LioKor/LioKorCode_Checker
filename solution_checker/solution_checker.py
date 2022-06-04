import docker
import time

import config

from threading import Thread

from solution_checker.models import CheckResult, BuildResult, TestResult, LintResult
from solution_checker.utils import files_to_tar
from solution_checker.docker_utils import remove_container, get_file_from_container, put_file_to_container
import solution_checker.constants as c

from linter.linter import lint_dict, lint_errors_to_str

# todo: receive check timeout from backend
BUILD_TIMEOUT = config.DEFAULT_BUILD_TIMEOUT  # in seconds
RUNTIME_TIMEOUT = config.DEFAULT_TEST_TIMEOUT  # in seconds


class DockerBuildThread(Thread):
    result = None

    def __init__(self, client, container, source_path):
        super().__init__()
        self.client = client
        self.container = container
        self.source_path = source_path

    def run(self):
        build_command = 'make build'
        build_result = self.container.exec_run(build_command, workdir=self.source_path)
        self.result = build_result

    def terminate(self):
        self.container.kill()


class DockerTestThread(Thread):
    result = None

    def __init__(self, client, container, source_path, test):
        super().__init__()
        self.client = client
        self.container = container
        self.source_path = source_path
        self.test = test

    def run(self):
        io_directory_path = '/root/io'
        input_file_path = io_directory_path + '/input.txt'
        output_file_path = io_directory_path + '/output.txt'
        self.container.exec_run('mkdir -p {}'.format(io_directory_path))

        stdin, expected = self.test[0], self.test[1]

        put_file_to_container(self.container, input_file_path, stdin)

        run_command = '/bin/bash -c "rm -f {output_fpath} && cat {input_fpath} | make -s ARGS=\'{input_fpath} {output_fpath}\' run"'.format(
            input_fpath=input_file_path,
            output_fpath=output_file_path
        )
        execute_result = self.container.exec_run(run_command, workdir=self.source_path, environment={
            'ARGS': '{} {}'.format(input_file_path, output_file_path),
            'input_path': input_file_path,
            'output_path': output_file_path
        })

        self.container = self.client.containers.get(self.container.id)
        if self.container.status == 'exited':
            return

        stdout = execute_result.output.decode()
        if execute_result.exit_code != 0:
            self.result = (c.STATUS_RUNTIME_ERROR, stdout)
            return

        fout = get_file_from_container(self.container, output_file_path)
        answer = fout if fout is not None else stdout

        # it's a practice to add \n at the end of output, but usually tests don't have it
        if len(answer) > 0 and answer[-1] == '\n' and expected[-1] != '\n':
            answer = answer[0:-1]

        if answer != expected:
            msg = 'For "{}" expected "{}", but got "{}"'.format(self.test[0], self.test[1], answer)
            self.result = (c.STATUS_TEST_ERROR, msg)
            return

        self.result = (c.STATUS_OK, '')

    def terminate(self):
        self.container = self.client.containers.get(self.container.id)
        self.container.kill()


def build_solution(client, container) -> BuildResult:
    build_thread = DockerBuildThread(client, container, '/root/source')
    start_time = time.time()
    build_thread.start()
    build_thread.join(BUILD_TIMEOUT)
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


def test_solution(client, container, tests) -> TestResult:
    tests_passed = 0
    tests_time = .0
    status, msg = None, None

    for test in tests:
        test_thread = DockerTestThread(client, container, '/root/source', test)
        start_time = time.time()
        test_thread.start()
        test_thread.join(RUNTIME_TIMEOUT)
        test_time = round(time.time() - start_time, 4)
        result = test_thread.result

        if result is None:
            result = (c.STATUS_RUNTIME_TIMEOUT, '')
            test_thread.terminate()
            # waiting for container to stop and then thread will exit
            test_thread.join()

        status, msg = result
        if status != c.STATUS_OK:
            break

        tests_passed += 1
        tests_time += test_time

    return TestResult(
        status=status,
        time=tests_time,
        message=msg,
        tests_passed=tests_passed,
        tests_total=len(tests)
    )


def lint_solution(source_code: dict) -> LintResult:
    lint_errors = lint_dict(source_code)
    str_lint = lint_errors_to_str(lint_errors)

    lint_status = c.STATUS_OK if len(str_lint) == 0 else c.STATUS_LINT_ERROR
    return LintResult(
        status=lint_status,
        message=str_lint
    )


def create_container():
    client = docker.from_env()
    container = client.containers.run(
        'liokorcode_checker',
        detach=True,
        tty=True,

        network_disabled=True,
        mem_limit='128m',
    )
    return client, container


def check_task_multiple_files(source_code: dict, tests: list) -> CheckResult:
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
        build_result = build_solution(client, container)
        message += build_result.message + '\n'

    test_result = TestResult()
    if build_result.status == c.STATUS_OK:
        test_result = test_solution(client, container, tests)
        message += test_result.message + '\n'

    lint_result = LintResult(status=c.STATUS_LINT_ERROR)
    if build_result.status == c.STATUS_OK and test_result.status == c.STATUS_OK:
        lint_result = lint_solution(source_code)
        message += lint_result.message + '\n'

    remove_container(client, container.id)

    check_result = build_result.status if build_result.status != c.STATUS_OK else test_result.status
    return CheckResult(
        check_time=test_result.time,  # todo: rename to test_time
        build_time=build_result.time,
        check_result=check_result,  # todo: rename to status
        check_message=message,
        tests_passed=test_result.tests_passed,
        tests_total=test_result.tests_total,
        lint_success=lint_result.status == c.STATUS_OK
    )
