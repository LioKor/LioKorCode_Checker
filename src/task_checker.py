import docker
import os
import shutil
import time
import subprocess

from threading import Thread

from uuid import uuid1

from utils import create_file, create_files, get_ext

STATUS_OK = 0
STATUS_CHECKING = 1
STATUS_COMPILE_ERROR = 2
STATUS_RUNTIME_ERROR = 3
STATUS_CHECK_ERROR = 4
STATUS_RUNTIME_TIMEOUT = 6
STATUS_COMPILE_TIMEOUT = 7
STATUS_LINT_ERROR = 8
STATUS_DRAFT = 9

# todo: receive check timeout from backend
RUNTIME_TIMEOUT = 4  # in seconds

# todo: replace dict, that is returned, with object
# class CheckResult:
#     check_result = 0
#     check_message = ''
#     tests_passed = 0
#     tests_total = 0
#
#     def __init__(self, check_result, check_message, tests_passed, tests_total):
#         self.check_result = check_result
#         self.check_message = check_message
#         self.tests_passed = tests_passed
#         self.tests_total = tests_total


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
            create_file(self.stdin_file_path, '{}\n'.format(test[0]))
            execute_result = self.container.exec_run('/bin/bash -c "cd /root/source_w && cat /root/input/input.txt | make -s run"')

            self.container = self.client.containers.get(self.container.id)
            if self.container.status == 'exited':
                self.result = {
                    'checkResult': STATUS_RUNTIME_TIMEOUT,
                    'checkMessage': '',
                    'testsPassed': tests_passed,
                    'testsTotal': len(self.tests)
                }
                return

            if execute_result.exit_code != 0:
                msg = execute_result.output.decode()
                self.result = {
                    'checkResult': STATUS_RUNTIME_ERROR,
                    'checkMessage': msg,
                    'testsPassed': 0,
                    'testsTotal': len(self.tests)
                }
                return

            stdout = execute_result.output.decode()
            if stdout != test[1]:
                msg = 'For {} expected {}, but got {}'.format(test[0], test[1], stdout)
                self.result = {
                    'checkResult': STATUS_CHECK_ERROR,
                    'checkMessage': msg,
                    'testsPassed': tests_passed,
                    'testsTotal': len(self.tests)
                }
                return

            tests_passed += 1

        self.result = {
            'checkResult': STATUS_OK,
            'checkMessage': '',
            'testsPassed': tests_passed,
            'testsTotal': len(self.tests)
        }

    def terminate(self):
        self.container.kill()


def check_solution(client, container, stdin_file_path, tests):
    # todo: compile in separate thread to limit compile time?
    start_time = time.time()
    compile_result = container.exec_run('/bin/bash -c "cd /root && cp -r source source_w && cd source_w && make"')
    compile_time = round(time.time() - start_time, 4)

    if compile_result.exit_code != 0:
        msg = compile_result.output.decode()
        return {
            'checkTime': 0,
            'compileTime': compile_time,
            'checkResult': STATUS_COMPILE_ERROR,
            'checkMessage': msg,
            'testsPassed': 0,
            'testsTotal': len(tests)
        }

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
    result['checkTime'] = test_time
    result['compileTime'] = compile_time
    return result


def lint_code(source_path: str, py_files: list) -> str:
    result = subprocess.run(
        ['python', '-m', 'cpplint', '--filter=-legal,-build/include_subdir', '--recursive', '--repository={}'.format(source_path), '.'],
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


def check_task_multiple_files(source_code, tests):
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
        return {
            'checkTime': 0,
            'compileTime': 0,
            'checkResult': STATUS_LINT_ERROR,
            'checkMessage': lint_message,
            'testsPassed': 0,
            'testsTotal': len(tests)
        }

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

    result = check_solution(client, container, stdin_file_path, tests)

    shutil.rmtree(solution_path)

    container = client.containers.get(container.id)
    if container.status == 'running':
        container.kill()
    container.remove()

    return result
