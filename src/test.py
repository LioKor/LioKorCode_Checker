from task_checker import check_task_multiple_files
import os
from utils import create_files

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

source_code_exploit = {
    'Makefile && echo wolf': '''
run:
	python3 main.py $(ARGS)
''',
}

source_code_c = {
    'Makefile': '''build: main.c sum.o
	gcc main.c sum.o -o solution

run:
	./solution

sum.o: lib/sum.h lib/sum.c
	gcc -c lib/sum.c''',
    'main.c': '''#include "stdio.h"

#include "lib/sum.h"

int main() {
    int a, b;
    scanf("%d %d", &a, &b);
    
    printf("%d", sum(a, b));
    
    return 0;
}''',
    'lib/sum.c': '''#include "sum.h"

int sum(int a, int b) {
    return a + b;
}''',
    'lib/sum.h': '''int sum(int, int);'''
}

tests = [
    ['1 2', '3'],
    ['4 5', '9'],
    ['-2 2', '0']
]

if __name__ == '__main__':
    result = check_task_multiple_files(source_code_py_file, tests)
    print(result.json())
    # create_files(source_code_exploit, os.path.join(os.getcwd(), 'tests', 'exploit'))
