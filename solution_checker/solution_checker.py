import docker
import time

import config

from threading import Thread

from solution_checker.models import CheckResult
from solution_checker.utils import files_to_tar
from solution_checker.docker_utils import remove_container, get_file_from_container, put_file_to_container

from linter.linter import lint_dict, lint_errors_to_str


STATUS_OK = 0
STATUS_CHECKING = 1
STATUS_BUILD_ERROR = 2
STATUS_RUNTIME_ERROR = 3
STATUS_TEST_ERROR = 4
STATUS_RUNTIME_TIMEOUT = 6
STATUS_BUILD_TIMEOUT = 7
STATUS_LINT_ERROR = 8
STATUS_DRAFT = 9

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
            self.result = (STATUS_RUNTIME_TIMEOUT, '')
            return

        stdout = execute_result.output.decode()
        if execute_result.exit_code != 0:
            self.result = (STATUS_RUNTIME_ERROR, stdout)
            return

        fout = get_file_from_container(self.container, output_file_path)
        answer = fout if fout is not None else stdout

        # it's a practice to add \n at the end of output, but usually tests don't have it
        if len(answer) > 0 and answer[-1] == '\n' and expected[-1] != '\n':
            answer = answer[0:-1]

        if answer != expected:
            msg = 'For "{}" expected "{}", but got "{}"'.format(self.test[0], self.test[1], answer)
            self.result = (STATUS_TEST_ERROR, msg)
            return

        self.result = (STATUS_OK, '')

    def terminate(self):
        self.container = self.client.containers.get(self.container.id)
        self.container.kill()


def build_solution(client, container):
    build_thread = DockerBuildThread(client, container, '/root/source')
    start_time = time.time()
    build_thread.start()
    build_thread.join(BUILD_TIMEOUT)
    build_time = round(time.time() - start_time, 4)

    compile_result = build_thread.result
    if compile_result is None:
        build_thread.terminate()
        # waiting for container to stop and then thread will exit
        build_thread.join()

    return compile_result, build_time


def test_solution(client, container, tests):
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
            result = (STATUS_RUNTIME_TIMEOUT, '')
            test_thread.terminate()
            # waiting for container to stop and then thread will exit
            test_thread.join()

        status, msg = result
        if status != STATUS_OK:
            break

        tests_passed += 1
        tests_time += test_time

    result = CheckResult(
        check_result=status,
        check_time=tests_time,
        check_message=msg,
        tests_passed=tests_passed,
        tests_total=len(tests)

    )

    return result


def check_solution(client, container, tests, need_to_build=True):
    build_time = .0
    if need_to_build:
        build_result, build_time = build_solution(client, container)

        if build_result is None:
            return CheckResult(
                build_time=build_time,
                check_result=STATUS_BUILD_TIMEOUT,
                tests_total=len(tests)
            )

        if build_result.exit_code != 0:
            msg = build_result.output.decode()
            return CheckResult(
                build_time=build_time,
                check_result=STATUS_BUILD_ERROR,
                check_message=msg,
                tests_total=len(tests)
            )

    result = test_solution(client, container, tests)
    result.build_time = build_time

    return result


def check_task_multiple_files(source_code: dict, tests: list) -> CheckResult:
    makefile = source_code.get('Makefile', None)
    if makefile is None:
        return CheckResult(check_result=STATUS_BUILD_ERROR, check_message='No Makefile found!')
    if makefile.find('run:') == -1:
        return CheckResult(check_result=STATUS_BUILD_ERROR, check_message='Makefile must at least contain "run:"')

    need_to_build = makefile.find('build:') != -1

    try:
        tar_source = files_to_tar(source_code, 'source/')
    except Exception:
        raise Exception('Unable to parse source code!')

    client = docker.from_env()

    container = client.containers.run(
        'liokorcode_checker',
        detach=True,
        tty=True,
        network_disabled=True,
        mem_limit='128m',
    )

    try:
        container.put_archive('/root', tar_source.read())
    except Exception:
        remove_container(client, container.id)
        raise Exception('Unable to create requested filesystem!')

    result = check_solution(client, container, tests, need_to_build)

    if result.check_result == STATUS_OK:
        lint_errors = lint_dict(source_code)
        str_lint = lint_errors_to_str(lint_errors)

        result.lint_success = len(str_lint) == 0
        if not result.lint_success:
            result.check_message += '\n{}'.format(str_lint)

    remove_container(client, container.id)

    return result
