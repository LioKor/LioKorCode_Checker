import docker
import os
import shutil
import time
import subprocess
import json

from threading import Thread

from uuid import uuid1

from utils import create_file, create_files, get_ext

STATUS_OK = 0
STATUS_CHECKING = 1
STATUS_BUILD_ERROR = 2
STATUS_RUNTIME_ERROR = 3
STATUS_CHECK_ERROR = 4
STATUS_RUNTIME_TIMEOUT = 6
STATUS_COMPILE_TIMEOUT = 7
STATUS_LINT_ERROR = 8
STATUS_DRAFT = 9

# todo: receive check timeout from backend
COMPILE_TIMEOUT = 6  # in seconds
RUNTIME_TIMEOUT = 4  # in seconds


class CheckResult:
    def __init__(self,
                 check_time: float = 0.0,
                 compile_time: float = 0.0,
                 check_result: int = -1,
                 check_message: str = '',
                 tests_passed: int = 0,
                 tests_total: int = 0
                 ):
        self.check_time = check_time  # todo: rename to test_time
        self.build_time = compile_time
        self.check_result = check_result  # todo: rename to status
        self.check_message = check_message  # todo: rename to message
        self.tests_passed = tests_passed
        self.tests_total = tests_total

    def json(self) -> str:
        json_data = {}
        for key, value in self.__dict__.items():
            key_split = key.split('_')
            new_key = key_split[0] + ''.join(word.capitalize() for word in key_split[1:])
            json_data[new_key] = value
        return json.dumps(json_data)


class DockerTestThread(Thread):
    result = None

    def __init__(self, client, container, stdin_file_path, tests):
        super().__init__()
        self.client = client
        self.container = container
        self.stdin_file_path = stdin_file_path
        self.tests = tests

    def run(self):
        tests_passed = 0
        for test in self.tests:
            stdin, expected = test[0], test[1]

            create_file(self.stdin_file_path, '{}\n'.format(stdin))
            execute_result = self.container.exec_run('/bin/bash -c "cd /root/source_w && cat /root/input/input.txt | make -s run"')

            self.container = self.client.containers.get(self.container.id)
            if self.container.status == 'exited':
                self.result = CheckResult(
                    check_result=STATUS_RUNTIME_TIMEOUT,
                    check_message='',
                    tests_passed=tests_passed,
                    tests_total=len(self.tests)
                )
                return

            if execute_result.exit_code != 0:
                msg = execute_result.output.decode()
                self.result = CheckResult(
                    check_result=STATUS_RUNTIME_ERROR,
                    check_message=msg,
                    tests_passed=0,
                    tests_total=len(self.tests)
                )
                return

            stdout = execute_result.output.decode()
            # it's a practice to add \n on the end of output, but tests don't have it
            if stdout[len(stdout) - 1] == '\n':
                stdout = stdout[0:len(stdout) - 1]
            if stdout != expected:
                msg = 'For "{}" expected "{}", but got "{}"'.format(test[0], test[1], stdout)
                self.result = CheckResult(
                    check_result=STATUS_CHECK_ERROR,
                    check_message=msg,
                    tests_passed=tests_passed,
                    tests_total=len(self.tests)
                )
                return

            tests_passed += 1

        self.result = CheckResult(
            check_result=STATUS_OK,
            check_message='',
            tests_passed=tests_passed,
            tests_total=len(self.tests)
        )

    def terminate(self):
        self.container.kill()


def check_solution(client, container, stdin_file_path, tests, need_to_build=True):
    container.exec_run('/bin/bash -c "cp -r /root/source /root/source_w"')

    # todo: compile in separate thread to limit compile time?
    build_time = 0
    if need_to_build:
        start_time = time.time()
        compile_result = container.exec_run('/bin/bash -c "cd /root/source_w && make build"')
        build_time = round(time.time() - start_time, 4)

        if compile_result.exit_code != 0:
            msg = compile_result.output.decode()
            return CheckResult(
                compile_time=build_time,
                check_result=STATUS_BUILD_ERROR,
                check_message=msg,
                tests_total=len(tests)
            )

    start_time = time.time()
    test_thread = DockerTestThread(client, container, stdin_file_path, tests)
    test_thread.start()
    test_thread.join(RUNTIME_TIMEOUT)
    test_time = round(time.time() - start_time, 4)

    if test_thread.result is None:
        test_thread.terminate()
        # waiting for container to stop and then thread will exit
        test_thread.join()

    result = test_thread.result
    result.check_time = test_time
    result.build_time = build_time
    return result


def lint_code(source_path: str, py_files: list) -> str:
    result = subprocess.run(
        ['python', '-m', 'cpplint', '--filter=-legal,-build/include_subdir,-whitespace/tab', '--recursive', '--repository={}'.format(source_path), '.'],
        cwd=source_path,
        stdout=subprocess.PIPE, stderr=subprocess.PIPE
    )
    if result.returncode != 0:
        return result.stderr.decode()

    if len(py_files) > 0:
        cmd = ['python', '-m', 'pylint', '--disable=missing-docstring']
        cmd.extend(py_files)
        result = subprocess.run(
            cmd, cwd=source_path,
            stdout=subprocess.PIPE, stderr=subprocess.PIPE
        )
        if result.returncode != 0:
            return result.stdout.decode()

    return ''


def check_task_multiple_files(source_code: dict, tests: list) -> CheckResult:
    makefile = source_code.get('Makefile', None)
    if makefile is None:
        return CheckResult(check_result=STATUS_BUILD_ERROR, check_message='No Makefile found!')
    if makefile.find('run:') == -1:
        return CheckResult(check_result=STATUS_BUILD_ERROR, check_message='Makefile must contain "run:"')

    need_to_build = makefile.find('build:') != -1

    solution_dir = str(uuid1())
    solution_path = os.path.join(os.getcwd(), 'solutions', solution_dir)
    solution_path_input = os.path.join(solution_path, 'input')
    solution_path_source = os.path.join(solution_path, 'source')

    os.makedirs(solution_path_input)
    os.makedirs(solution_path_source)

    stdin_file_path = os.path.join(solution_path_input, 'input.txt')

    # todo: move this procedure to container for security reasons (e.g. escape root)
    create_files(source_code, solution_path_source)
    py_files = []
    for file in source_code:
        if get_ext(file) == 'py':
            py_files.append(file)

    lint_message = lint_code(solution_path_source, py_files)
    if lint_message:
        shutil.rmtree(solution_path)
        return CheckResult(check_result=STATUS_LINT_ERROR, check_message=lint_message, tests_total=len(tests))

    client = docker.from_env()

    container = client.containers.run('gcc', detach=True, tty=True, volumes={
            solution_path_input: {
                'bind': '/root/input',
                'mode': 'ro'
            },
            solution_path_source: {
                'bind': '/root/source',
                'mode': 'ro'
            }
        },
        network_disabled=True,
        mem_limit='64m',
    )

    result = check_solution(client, container, stdin_file_path, tests, need_to_build)

    shutil.rmtree(solution_path)

    container = client.containers.get(container.id)
    if container.status == 'running':
        container.kill()
    container.remove()

    return result
