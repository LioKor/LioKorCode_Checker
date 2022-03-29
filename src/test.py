from task_checker import check_task_multiple_files

source_code_py = {
    'Makefile': '''compile:
	echo wolf
run:
	python3 main.py
''',
    'main.py': '''A, B = list(map(int, input().split()))
print(A + B, end='')
'''
}

source_code_c = {
    'Makefile': '''compile: main.c sum.o
	gcc main.c sum.o -o solution

run: solution
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
    result = check_task_multiple_files(source_code_py, tests)
    print(result)
