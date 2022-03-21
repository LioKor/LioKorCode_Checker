import docker
import os
import shutil

from uuid import uuid1


def create_file(path, content):
    f = open(path, 'w')
    f.write(content)
    f.close()


def check_solution(container, stdin_file_path, tests):
    compile_result = container.exec_run('/bin/bash -c "cd /root/solution && cp main.c ../ && cd .. && gcc main.c"')
    if compile_result.exit_code != 0:
        msg = compile_result.output.decode()
        return {
            'checkResult': 2,
            'checkMessage': msg,
            'testsPassed': 0,
            'testsTotal': len(tests)
        }

    tests_passed = 0
    for test in tests:
        create_file(stdin_file_path, '{}\n'.format(test[0]))
        execute_result = container.exec_run('/bin/bash -c "cd /root && cat solution/input.txt | ./a.out"')
        if execute_result.exit_code != 0:
            msg = compile_result.output.decode()
            return {
                'checkResult': 3,
                'checkMessage': msg,
                'testsPassed': 0,
                'testsTotal': len(tests)
            }

        stdout = execute_result.output.decode()
        if stdout != test[1]:
            msg = 'For {} expected {}, but got {}'.format(test[0], test[1], stdout)
            return {
                'checkResult': 3,
                'checkMessage': msg,
                'testsPassed': tests_passed,
                'testsTotal': len(tests)
            }

        tests_passed += 1

    return {
        'checkResult': 0,
        'checkMessage': '',
        'testsPassed': tests_passed,
        'testsTotal': len(tests)
    }


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
        }
    })

    result = check_solution(container, stdin_file_path, tests)

    shutil.rmtree(solution_path)
    container.kill()
    container.remove()

    return result
