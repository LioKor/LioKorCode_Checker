c_cpp = '''
#include <stdio.h>

int main() {
    int a,b;
    if (a > b) {
        printf("TRUE");
    } else {
        printf("FALSE");
    }
}
'''

fpc = '''
var
    a, b: integer;
begin
    readln(a, b);
    writeln(a + b);
end.
'''


def lint_c_or_cpp(code: str):
    errors = ''

    indent_level = 0
    space_length = None
    line_number = 0

    for line in code.split('\n'):
        line_number += 1

        has_end_block = line.find('}') != -1
        if has_end_block:
            indent_level -= 1

        current_indent = 0
        indent_symbol = None
        need_check = True
        for i in range(0, len(line)):
            c = line[i]
            if c != '\t' and c != ' ':
                if space_length is None and indent_symbol == ' ' and indent_level > 0:
                    space_length = current_indent / indent_level
                break
            if indent_symbol is not None and c != indent_symbol:
                need_check = False
                errors += 'Line {}: Mixing tab and spaces is a bad practice\n'.format(line_number)
                break
            indent_symbol = c
            current_indent += 1

        if need_check:
            expected_indent = indent_level
            if indent_symbol == ' ' and space_length is not None:
                expected_indent *= space_length
            if current_indent != expected_indent and need_check:
                errors += 'Line {}: incorrect indentation or curly braces missing\n'.format(line_number)

        has_new_block = line.find('{') != -1
        if has_new_block:
            indent_level += 1

    return errors


# def check_coma_spaces():
#     pass

# print('C_CPP:')
print(lint_c_or_cpp(c_cpp))

# print()
#
# print('FPC:')
# print(check_indentation(fpc))
