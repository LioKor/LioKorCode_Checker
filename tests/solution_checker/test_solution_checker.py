import unittest

import solution_checker.constants as c
import solution_checker.solution_checker as sc

source_code_py_file = {
    'Makefile': '''
run:
	python3 main.py $(ARGS)
''',
    'main.py': '''
import sys

fin_path = sys.argv[1]
fin = open(fin_path, 'r')
a, b = map(int, fin.read().split())
fin.close()
# a, b = map(int, input().split())
# print(a + b)

fout_path = sys.argv[2]
print(fout_path)
fout = open(fout_path, 'w')
fout.write(str(a + b))
fout.close()
'''
}

source_code_c_multiple_files = {
    'Makefile': '''
build: main.c sum.o
	gcc main.c sum.o -o solution
run:
	./solution
sum.o: lib/sum.h lib/sum.c
	gcc -c lib/sum.c
''',

    'main.c': '''
#include "stdio.h"

#include "lib/sum.h"

int main() {
    int a, b;
    scanf("%d %d", &a, &b);
    
    printf("%d", sum(a, b));
    
    return 0;
}
''',
    'lib/sum.c': '''
#include "sum.h"
int sum(int a, int b) {
    return a + b;
}
''',
    'lib/sum.h': '''
int sum(int, int);
'''
}

source_code_bad_build = {
    'Makefile': '''
build:
	gcc main.c
run:
	./a.out
''',

    'main.c': '''
#include "stdio.h"

int main() {
    int a, b;
    scanf("%d %d", &a, &b);
    printf("%d", a + b)
    return 0;
}
''',
}

source_code_bad_runtime = {
    'Makefile': '''
build:
	gcc main.c
run:
	./a.out
''',

    'main.c': '''
#include "stdio.h"

int main() {
    int a, b;
    scanf("%d %d", &a, &b);
    printf("%d", 1 / 0);
    return 0;
}
''',
}

source_code_build_timeout = {
    'Makefile': '''
build:
	sleep 10
run:
	echo wolf
'''
}

source_code_runtime_timeout = {
    'Makefile': '''
run:
	sleep 10
	echo 3
'''
}

source_code_py_wrong = {
    'Makefile': '''
run:
	python3 main.py
''',
    'main.py': '''
# a, b = map(int, input().split())
print(3)    
'''
}


class SolutionCheckerTest(unittest.TestCase):
    build_timeout = 2
    test_timeout = 1

    tests = [
        ['1 2', '3'],
        ['4 5', '9'],
        ['-2 2', '0'],
        ['1 2', '3'],
        ['4 5', '9'],
        ['-2 2', '0'],
        ['1 2', '3'],
        ['4 5', '9'],
        ['-2 2', '0']
    ]

    def check_solution_ok(self, result):
        self.assertEqual(result.check_result, c.STATUS_OK)
        self.assertEqual(result.tests_passed, result.tests_total)
        self.assertEqual(result.tests_passed, len(self.tests))
        self.assertLessEqual(result.build_time, self.build_timeout)
        self.assertLessEqual(result.check_time, self.test_timeout * len(self.tests))
        self.assertGreater(result.check_time, 0.01)
        self.assertTrue(result.lint_success)

    def test_c_multiple_files(self):
        result = sc.check_solution(source_code_c_multiple_files, self.tests, self.build_timeout, self.test_timeout)
        self.check_solution_ok(result)
        self.assertGreater(result.build_time, 0.01)

    def test_py_file_io(self):
        result = sc.check_solution(source_code_py_file, self.tests, self.build_timeout, self.test_timeout)
        self.check_solution_ok(result)

    def test_error_build(self):
        result = sc.check_solution(source_code_bad_build, self.tests, self.build_timeout, self.test_timeout)
        self.assertEqual(result.check_result, c.STATUS_BUILD_ERROR)
        self.assertNotEqual(len(result.check_message), 0)

    def test_error_runtime(self):
        result = sc.check_solution(source_code_bad_runtime, self.tests, self.build_timeout, self.test_timeout)
        self.assertEqual(result.check_result, c.STATUS_RUNTIME_ERROR)
        self.assertNotEqual(len(result.check_message), 0)

    def test_error_build_timeout(self):
        build_timeout = 0.1
        result = sc.check_solution(source_code_build_timeout, self.tests, build_timeout, self.test_timeout)
        self.assertEqual(result.check_result, c.STATUS_BUILD_TIMEOUT)
        time_diff = abs(result.build_time - build_timeout)
        self.assertLess(time_diff, build_timeout / 4)
        self.assertEqual(len(result.check_message), 0)

    def test_error_runtime_timeout(self):
        test_timeout = 0.1
        result = sc.check_solution(source_code_runtime_timeout, [['1 2', '3']], self.build_timeout, test_timeout)
        self.assertEqual(result.check_result, c.STATUS_RUNTIME_TIMEOUT, msg=result.json())
        time_diff = abs(result.check_time - test_timeout)
        self.assertLess(time_diff, test_timeout / 4)

    def test_error_test_error(self):
        result = sc.check_solution(source_code_py_wrong, self.tests, self.build_timeout, self.test_timeout)
        self.assertEqual(result.check_result, c.STATUS_TEST_ERROR, msg=result.json())
        self.assertEqual(result.tests_passed, 1, msg=result.json())
        self.assertNotEqual(len(result.check_message), 0)


if __name__ == '__main__':
    unittest.main()
