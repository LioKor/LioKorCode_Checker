from src.solution_checker.check_steps.build import build_solution
from src.solution_checker.check_steps.test import test_solution
from src.solution_checker.check_steps.lint import lint_solution
from src.solution_checker.models import CheckResult, BuildResult, TestsResult, LintResult
from src.solution_checker.utils import files_to_tar
from src.solution_checker.docker_utils import create_container, remove_container
import src.solution_checker.constants as c


def check_solution(
        source_code: dict[str, str],
        tests: list[list[str]],
        build_timeout: float,
        test_timeout: float
) -> CheckResult:
    makefile = source_code.get('Makefile', None)
    if makefile is None:
        return CheckResult(check_result=c.STATUS_BUILD_ERROR, check_message='No Makefile found!')
    if makefile.find('run:') == -1:
        return CheckResult(check_result=c.STATUS_BUILD_ERROR, check_message='Makefile must at least contain "run:"')

    need_to_build = makefile.find('build:') != -1

    try:
        tar_source = files_to_tar(source_code, 'source/')
    except Exception:
        raise Exception('Unable to parse source code!')

    client, container = create_container()

    try:
        container.put_archive('/root', tar_source.read())
    except Exception:
        remove_container(client, container.id)
        raise Exception('Unable to create requested filesystem!')

    message = ''

    build_result = BuildResult(status=c.STATUS_OK)
    if need_to_build:
        build_result = build_solution(client, container, build_timeout)
        message += build_result.message + '\n' if len(build_result.message) > 0 else ''

    tests_result = TestsResult()
    if build_result.status == c.STATUS_OK:
        tests_result = test_solution(client, container, tests, test_timeout)
        message += tests_result.message + '\n' if len(tests_result.message) > 0 else ''

    lint_result = LintResult(status=c.STATUS_LINT_ERROR)
    if build_result.status == c.STATUS_OK and tests_result.status == c.STATUS_OK:
        lint_result = lint_solution(source_code)
        message += lint_result.message if len(lint_result.message) > 0 else ''

    remove_container(client, container.id)

    check_result = build_result.status if build_result.status != c.STATUS_OK else tests_result.status
    return CheckResult(
        check_time=round(tests_result.time, 4),  # todo: rename to test_time
        build_time=round(build_result.time, 4),
        check_result=check_result,  # todo: rename to status
        check_message=message,
        tests_passed=tests_result.tests_passed,
        tests_total=tests_result.tests_total,
        lint_success=lint_result.status == c.STATUS_OK
    )
