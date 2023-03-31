from src.solution_checker.check_steps.build import build_solution
from src.solution_checker.check_steps.test import test_solution
from src.solution_checker.check_steps.lint import lint_solution
from src.solution_checker.models import CheckResult, BuildResult
from src.solution_checker.utils import files_to_tar
from src.solution_checker.docker_utils import create_container, remove_container
from src.solution_checker.models import CheckStatus


class MakefileValidationError(Exception):
    ...


class SolutionChecker:
    def __init__(
        self,
        source_code: dict[str, str],
        tests: list[list[str]],
        build_timeout: float,
        test_timeout: float,
    ):
        self.source_code = source_code
        self.tests = tests
        self.build_timeout = build_timeout
        self.test_timeout = test_timeout

        self.makefile = source_code.get("Makefile")
        self.need_to_build = (
            self.makefile.find("build:") != -1 if self.makefile else False
        )

    def check_solution(self) -> CheckResult:
        self._validate_makefile()

        try:
            tar_source = files_to_tar(self.source_code, "source/")
        except Exception:
            raise Exception("Unable to parse source code!")

        client, container = create_container()

        try:
            container.put_archive("/root", tar_source.read())
        except Exception:
            remove_container(client, container.id)
            raise Exception("Unable to create requested filesystem!")

        check_message = ""

        build_result: BuildResult | None = None
        if self.need_to_build:
            build_result = build_solution(client, container, self.build_timeout)
            check_message += f"{build_result.message}\n" if build_result.message else ""

            if build_result.status != CheckStatus.OK:
                remove_container(client, container.id)
                return CheckResult(
                    check_time=0.0,
                    build_time=build_result.time,
                    check_result=build_result.status,
                    check_message=build_result.message,
                    tests_passed=0,
                    tests_total=len(self.tests),
                    lint_success=False,
                )

        tests_result = test_solution(client, container, self.tests, self.test_timeout)
        check_message += f"{tests_result.message}\n" if tests_result.message else ""

        lint_result = lint_solution(self.source_code)
        check_message += f"{lint_result.message}\n" if lint_result.message else ""

        remove_container(client, container.id)

        return CheckResult(
            check_time=round(tests_result.time, 4),
            build_time=round(build_result.time, 4) if build_result else 0.0,
            check_result=tests_result.status,
            check_message=check_message,
            tests_passed=tests_result.tests_passed,
            tests_total=tests_result.tests_total,
            lint_success=lint_result.success,
        )

    def _validate_makefile(self) -> None:
        if self.makefile is None:
            raise MakefileValidationError("Makefile was not found in source code")
        if self.makefile.find("run:") == -1:
            raise MakefileValidationError("Makefile must at least contain 'run:'")
