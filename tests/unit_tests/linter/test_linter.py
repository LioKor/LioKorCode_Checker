import unittest

from src.linter.linter import LintError
from src.linter import linter


class LinterTest(unittest.TestCase):
    def test_lint_files(self) -> None:
        test_cases: list[tuple[str, list[LintError]]] = [
            ("src/linter/tests/unit_tests/test_cases/c_good_file.c", []),
            (
                "src/linter/tests/unit_tests/test_cases/c_almost_good_file.c",
                [
                    {"line": 4, "message": "spaces/punctuation"},
                    {"line": 6, "message": "indentation/bad"},
                    {"line": 8, "message": "indentation/mix"},
                ],
            ),
            (
                "src/linter/tests/unit_tests/test_cases/c_bad_file.c",
                [
                    {"line": 5, "message": "indentation/bad"},
                    {"line": 6, "message": "indentation/bad"},
                    {"line": 7, "message": "indentation/bad"},
                    {"line": 9, "message": "indentation/bad"},
                    {"line": 10, "message": "line/noendnewline"},
                ],
            ),
            (
                "src/linter/tests/unit_tests/test_cases/c_strings.c",
                [
                    {"line": 9, "message": "indentation/bad"},
                ],
            ),
            ("src/linter/tests/unit_tests/test_cases/empty_file.c", []),
            ("src/linter/tests/unit_tests/test_cases/c_comments.c", []),
            (
                "src/linter/tests/unit_tests/test_cases/c_one_liners.c",
                [
                    {"line": 2, "message": "indentation/bad"},
                    {"line": 2, "message": "line/noendnewline"},
                ],
            ),
            (
                "src/linter/tests/unit_tests/test_cases/c_very_bad_file.c",
                [
                    {"line": 4, "message": "spaces/punctuation"},
                    {"line": 4, "message": "indentation/bad"},
                    {"line": 5, "message": "spaces/punctuation"},
                    {"line": 5, "message": "spaces/punctuation"},
                    {"line": 5, "message": "indentation/bad"},
                    {"line": 6, "message": "indentation/bad"},
                    {"line": 7, "message": "spaces/punctuation"},
                    {"line": 7, "message": "indentation/bad"},
                    {"line": 8, "message": "indentation/bad"},
                    {"line": 9, "message": "indentation/bad"},
                    {"line": 10, "message": "indentation/bad"},
                    {"line": 11, "message": "indentation/bad"},
                    {"line": 12, "message": "line/noendnewline"},
                ],
            ),
            (
                "src/linter/tests/unit_tests/test_cases/c_very_bad_file.c",
                [
                    {"line": 37, "message": "line/extranewline"},
                    {"line": 38, "message": "line/extranewline"},
                    {"line": 39, "message": "line/extranewline"},
                ],
            ),
        ]

        for case in test_cases:
            file: str = str(case[0])
            expected: list[LintError] = list(case[1])

            f = open(file)
            result = linter.lint_code(f.read())
            f.close()

            self.assertEqual(len(result), len(expected), msg=file + ": " + str(result))

            for got, exp in zip(result, expected):
                self.assertEqual(got["line"], exp["line"], msg=file)
                self.assertEqual(got["message"], exp["message"], msg=file)


if __name__ == "__main__":
    unittest.main()
