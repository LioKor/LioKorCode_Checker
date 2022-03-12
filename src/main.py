from task_checker import check_task

example_source_code = '''#include "stdio.h"
int main() {
    int a, b;

    scanf("%d %d", &a, &b);
    
    printf("%d", a + b);
    
    return 0;
}'''

example_tests = [
    ['1 2', '3'],
    ['4 5', '9'],
    ['-2 2', '0']
]

print(check_task(example_source_code, example_tests))
