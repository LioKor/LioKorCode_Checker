import docker
import os
import shutil
import time
from threading import Thread

from uuid import uuid1

# todo: receive check timeout from backend
TESTS_TIMEOUT = 4

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
            execute_result = self.container.exec_run('/bin/bash -c "cd /root && cat solution/input.txt | ./a.out"')

            self.container = self.client.containers.get(self.container.id)
            if self.container.status == 'exited':
                self.result = {
                    'checkResult': 4,
                    'checkMessage': '',
                    'testsPassed': tests_passed,
                    'testsTotal': len(self.tests)
                }
                return

            if execute_result.exit_code != 0:
                msg = execute_result.output.decode()
                self.result = {
                    'checkResult': 3,
                    'checkMessage': msg,
                    'testsPassed': 0,
                    'testsTotal': len(self.tests)
                }
                return

            stdout = execute_result.output.decode()
            if stdout != test[1]:
                msg = 'For {} expected {}, but got {}'.format(test[0], test[1], stdout)
                self.result = {
                    'checkResult': 3,
                    'checkMessage': msg,
                    'testsPassed': tests_passed,
                    'testsTotal': len(self.tests)
                }
                return

            tests_passed += 1

        self.result = {
            'checkResult': 0,
            'checkMessage': '',
            'testsPassed': tests_passed,
            'testsTotal': len(self.tests)
        }

    def terminate(self):
        self.container.kill()


def create_file(path, content):
    f = open(path, 'w')
    f.write(content)
    f.close()


def check_solution(client, container, stdin_file_path, tests):
    # todo: compile in separate thread?
    compile_result = container.exec_run('/bin/bash -c "cd /root/solution && cp main.c ../ && cd .. && gcc main.c"')
    if compile_result.exit_code != 0:
        msg = compile_result.output.decode()
        return {
            'checkTime': 0,
            'checkResult': 2,
            'checkMessage': msg,
            'testsPassed': 0,
            'testsTotal': len(tests)
        }

    start_time = time.time()
    test_thread = DockerTestThread(client, container, stdin_file_path, tests)
    test_thread.start()
    test_thread.join(TESTS_TIMEOUT)
    test_time = round(time.time() - start_time, 4)

    if test_thread.result is None:
        test_thread.terminate()
        # waiting for container to stop and then thread will exit
        test_thread.join()

    result = test_thread.result
    result['checkTime'] = test_time
    return result


def check_task(source_code, tests):
    solution_dir = str(uuid1())
    solution_path = os.path.join(os.getcwd(), 'solutions', solution_dir)
    os.makedirs(solution_path)

    source_file_path = os.path.join(solution_path, 'main.c')
    create_file(source_file_path, source_code)

    stdin_file_path = os.path.join(solution_path, 'input.txt')

    client = docker.from_env()

    container = client.containers.run('gcc', detach=True, tty=True, volumes={
            solution_path: {
                'bind': '/root/solution',
                'mode': 'ro'
            },
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
