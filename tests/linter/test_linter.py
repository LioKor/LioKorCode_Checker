import unittest

import linter.linter as linter


class LinterTest(unittest.TestCase):
    def test_lint_files(self):
        test_cases = [
            ['test_cases/c_good_file.c', []],
            ['test_cases/c_almost_good_file.c', [
                {'line': 4, 'error': 'spaces/punctuation'},
                {'line': 6, 'error': 'indentation/bad'},
                {'line': 8, 'error': 'indentation/mix'}
            ]],
            ['test_cases/c_bad_file.c', [
                {'line': 5, 'error': 'indentation/bad'},
                {'line': 6, 'error': 'indentation/bad'},
                {'line': 7, 'error': 'indentation/bad'},
                {'line': 9, 'error': 'indentation/bad'},
                {'line': 10, 'error': 'line/noendnewline'},
            ]],
            ['test_cases/c_strings.c', [
                {'line': 9, 'error': 'indentation/bad'},
            ]],
            ['test_cases/empty_file.c', [
            ]],
            ['test_cases/c_comments.c', []],
            ['test_cases/c_one_liners.c', [
                {'line': 1, 'error': 'indentation/bad'},
                {'line': 1, 'error': 'line/noendnewline'},
            ]],
            ['test_cases/c_very_bad_file.c', [
                {'line': 4, 'error': 'spaces/punctuation'},
                {'line': 4, 'error': 'indentation/bad'},
                {'line': 5, 'error': 'spaces/punctuation'},
                {'line': 5, 'error': 'spaces/punctuation'},
                {'line': 5, 'error': 'indentation/bad'},
                {'line': 6, 'error': 'indentation/bad'},
                {'line': 7, 'error': 'spaces/punctuation'},
                {'line': 7, 'error': 'indentation/bad'},
                {'line': 8, 'error': 'indentation/bad'},
                {'line': 9, 'error': 'indentation/bad'},
                {'line': 10, 'error': 'indentation/bad'},
                {'line': 11, 'error': 'indentation/bad'},
                {'line': 12, 'error': 'line/noendnewline'}
            ]]
        ]

        for case in test_cases:
            file = case[0]
            expected = case[1]

            f = open(file)
            result = linter.lint_code(f.read())
            f.close()

            self.assertEqual(len(result), len(expected), msg=file + ': ' + str(result))

            for got, exp in zip(result, expected):
                self.assertEqual(got['line'], exp['line'], msg=file)
                self.assertEqual(got['error'], exp['error'], msg=file)


if __name__ == '__main__':
    unittest.main()