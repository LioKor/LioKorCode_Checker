import unittest


def lint_c_or_cpp(code: str):
    errors = []

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
        need_indentation_check = True
        checking_indentation = True
        for i in range(0, len(line)):
            c = line[i]

            if checking_indentation:
                if c != '\t' and c != ' ':
                    if space_length is None and indent_symbol == ' ' and indent_level > 0:
                        space_length = current_indent / indent_level
                    checking_indentation = False
                    continue
                if indent_symbol is not None and c != indent_symbol:
                    need_indentation_check = False
                    errors.append({
                        'line': line_number,
                        'error': 'indentation/mix'
                    })
                    break
                indent_symbol = c
                current_indent += 1
            elif c == ',':
                l = len(line)
                before_space = i > 0 and line[i - 1] == ' '
                no_space = i < l - 1 and line[i + 1] != ' '
                extra_space = i < l - 2 and line[i + 2] == ' '
                if before_space or no_space or extra_space:
                    errors.append({
                        'line': line_number,
                        'error': 'spaces/punctuation'
                    })

        if need_indentation_check:
            expected_indent = indent_level
            if indent_symbol == ' ' and space_length is not None:
                expected_indent *= space_length
            if current_indent != expected_indent and need_indentation_check:
                errors.append({
                    'line': line_number,
                    'error': 'indentation/bad'
                })

        has_new_block = line.find('{') != -1
        if has_new_block:
            indent_level += 1

    return errors


class LinterTest(unittest.TestCase):
    def test_lint_files(self):
        test_cases = [
            ['test_cases/c_good_file.c', []],
            ['test_cases/c_almost_good_file.c', [
                {'line': 4, 'error': 'spaces/punctuation'},
                {'line': 6, 'error': 'indentation/bad'}
            ]],
            ['test_cases/c_bad_file.c', [
                {'line': 5, 'error': 'indentation/bad'},
                {'line': 6, 'error': 'indentation/bad'},
                {'line': 7, 'error': 'indentation/bad'},
                {'line': 9, 'error': 'indentation/bad'},
            ]]
        ]

        for case in test_cases:
            file = case[0]
            expected = case[1]

            f = open(file)
            result = lint_c_or_cpp(f.read())
            f.close()

            self.assertEqual(len(result), len(expected), msg=result)

            for got, exp in zip(result, expected):
                self.assertEqual(got['line'], exp['line'])
                self.assertEqual(got['error'], exp['error'])


if __name__ == '__main__':
    unittest.main()
