from src.linter.linter import lint_dict, lint_errors_to_str
from src.solution_checker.models import LintResult
import src.solution_checker.constants as c


def lint_solution(source_code: dict[str, str]) -> LintResult:
    lint_errors = lint_dict(source_code, ['.c', '.h', '.cpp', '.hpp', '.go', '.js', '.cs', '.java'])
    str_lint = lint_errors_to_str(lint_errors)

    lint_status = c.STATUS_OK if len(str_lint) == 0 else c.STATUS_LINT_ERROR
    return LintResult(
        status=lint_status,
        message=str_lint
    )
