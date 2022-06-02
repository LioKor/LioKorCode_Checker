import unittest

from src.linter.lint import lint_code


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
                {'line': 10, 'error': 'line/noendnewline'}
            ]],
            ['test_cases/c_strings.c', [
                {'line': 9, 'error': 'indentation/bad'},
            ]],
            ['test_cases/empty_file.c', [
            ]],
            ['test_cases/c_comments.c', []]
        ]

        for case in test_cases:
            file = case[0]
            expected = case[1]

            f = open(file)
            result = lint_code(f.read())
            f.close()

            self.assertEqual(len(result), len(expected), msg=file + ': ' + str(result))

            for got, exp in zip(result, expected):
                self.assertEqual(got['line'], exp['line'], msg=file)
                self.assertEqual(got['error'], exp['error'], msg=file)


if __name__ == '__main__':
    unittest.main()