from src.linter.linter import lint_dict, lint_errors_to_str
from src.solution_checker.models import LintResult


def lint_solution(source_code: dict[str, str]) -> LintResult:
    lint_errors = lint_dict(
        source_code, [".c", ".h", ".cpp", ".hpp", ".go", ".js", ".cs", ".java"]
    )
    lint_errors_message = lint_errors_to_str(lint_errors)
    return LintResult(success=not lint_errors_message, message=lint_errors_message)
