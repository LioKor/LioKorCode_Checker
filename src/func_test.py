example_request = {
    'sourceCode': '''#include "stdio.h"
int main() {
    int a, b;

    scanf("%d %d", &a, &b);
    
    printf("%d", a + b);
    
    return 0;
}''',
    'tests': [
        ['1 2', '3'],
        ['4 5', '9'],
        ['-2 2', '0']
    ]
}
