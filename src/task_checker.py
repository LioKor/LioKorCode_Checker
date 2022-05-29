import docker
import os
import shutil
import time
import subprocess
import json

import tarfile
from io import BytesIO

from threading import Thread

from uuid import uuid1

from utils import create_file, create_files, get_ext

STATUS_OK = 0
STATUS_CHECKING = 1
STATUS_BUILD_ERROR = 2
STATUS_RUNTIME_ERROR = 3
STATUS_CHECK_ERROR = 4
STATUS_RUNTIME_TIMEOUT = 6
STATUS_BUILD_TIMEOUT = 7
STATUS_LINT_ERROR = 8
STATUS_DRAFT = 9

# todo: receive check timeout from backend
BUILD_TIMEOUT = 4  # in seconds
RUNTIME_TIMEOUT = 4  # in seconds


def get_file_from_container(container, fname):
    try:
        bits, stats = container.get_archive(fname)
        bio = BytesIO()
        for chunk in bits:
            bio.write(chunk)
        bio.seek(0)
        tar = tarfile.open(fileobj=bio)
        content = tar.extractfile(tar.getmembers()[0]).read().decode()
        tar.close()

        return content
    except Exception:
        return None


class CheckResult:
    def __init__(self,
                 check_time: float = 0.0,
                 build_time: float = 0.0,
                 check_result: int = -1,
                 check_message: str = '',
                 tests_passed: int = 0,
                 tests_total: int = 0
                 ):
        self.check_time = check_time  # todo: rename to test_time
        self.build_time = build_time
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


class DockerBuildThread(Thread):
    result = None

    def __init__(self, client, container):
        super().__init__()
        self.client = client
        self.container = container

    def run(self):
        build_command = '/bin/bash -c "cd /root/source_w && make build"'
        build_result = self.container.exec_run(build_command)
        self.result = build_result

    def terminate(self):
        self.container.kill()


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
            source_path = '/root/source_w'
            input_file_path = '/root/input/input.txt'
            output_file_path = source_path + '/output.txt'

            run_command = '/bin/bash -c "rm -f {output_fpath} && cat {input_fpath} | make -s ARGS=\'{input_fpath} {output_fpath}\' run"'.format(
                input_fpath=input_file_path,
                output_fpath=output_file_path
            )
            execute_result = self.container.exec_run(run_command, workdir=source_path, environment={
                'ARGS': '{} {}'.format(input_file_path, output_file_path)
            })

            self.container = self.client.containers.get(self.container.id)
            if self.container.status == 'exited':
                self.result = CheckResult(
                    check_result=STATUS_RUNTIME_TIMEOUT,
                    check_message='',
                    tests_passed=tests_passed,
                    tests_total=len(self.tests)
                )
                return

            stdout = execute_result.output.decode()
            if execute_result.exit_code != 0:
                self.result = CheckResult(
                    check_result=STATUS_RUNTIME_ERROR,
                    check_message=stdout,
                    tests_passed=0,
                    tests_total=len(self.tests)
                )
                return

            fout = get_file_from_container(self.container, output_file_path)
            answer = fout if fout is not None else stdout

            # it's a practice to add \n at the end of output, but usually tests don't have it
            if len(answer) > 0 and answer[-1] == '\n' and expected[-1] != '\n':
                answer = answer[0:-1]

            if answer != expected:
                msg = 'For "{}" expected "{}", but got "{}"'.format(test[0], test[1], answer)
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


def build_solution(client, container):
    build_thread = DockerBuildThread(client, container)
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


def test_solution(client, container, stdin_file_path, tests):
    test_thread = DockerTestThread(client, container, stdin_file_path, tests)
    start_time = time.time()
    test_thread.start()
    test_thread.join(RUNTIME_TIMEOUT)
    test_time = round(time.time() - start_time, 4)

    if test_thread.result is None:
        test_thread.terminate()
        # waiting for container to stop and then thread will exit
        test_thread.join()

    return test_thread.result, test_time


def check_solution(client, container, stdin_file_path, tests, need_to_build=True):
    container.exec_run('/bin/bash -c "cp -r /root/source /root/source_w"')

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

    test_result, test_time = test_solution(client, container, stdin_file_path, tests)

    if test_result is None:
        test_result = CheckResult(check_result=STATUS_RUNTIME_TIMEOUT)

    result = test_result
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
    solution_path_input = os.path.join(solution_path, 'io')
    solution_path_source = os.path.join(solution_path, 'source')

    os.makedirs(solution_path_input)
    os.makedirs(solution_path_source)

    stdin_file_path = os.path.join(solution_path_input, 'input.txt')

    # todo: move this procedure to container for security reasons (e.g. escape root)
    create_files(source_code, solution_path_source)
    # py_files = []
    # for file in source_code:
    #     if get_ext(file) == 'py':
    #         py_files.append(file)

    # lint_message = lint_code(solution_path_source, py_files)
    # if lint_message:
    #     shutil.rmtree(solution_path)
    #     return CheckResult(check_result=STATUS_LINT_ERROR, check_message=lint_message, tests_total=len(tests))

    client = docker.from_env()

    container = client.containers.run('liokorcode_checker', detach=True, tty=True, volumes={
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
