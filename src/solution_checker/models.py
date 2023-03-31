from enum import Enum
from dataclasses import dataclass
import json


class CheckStatus(Enum):
    STATUS_UNKNOWN = -1
    STATUS_OK = 0
    STATUS_CHECKING = 1
    STATUS_BUILD_ERROR = 2
    STATUS_RUNTIME_ERROR = 3
    STATUS_TEST_ERROR = 4
    STATUS_RUNTIME_TIMEOUT = 6
    STATUS_BUILD_TIMEOUT = 7
    STATUS_LINT_ERROR = 8
    STATUS_DRAFT = 9


@dataclass
class CheckResult:
    check_time: float  # todo: rename to test_time
    build_time: float
    check_result: CheckStatus  # todo: rename to status
    check_message: str  # todo: rename to message
    tests_passed: int
    tests_total: int
    lint_success: bool

    def json(self) -> str:
        json_data = {}
        for key, value in self.__dict__.items():
            key_split = key.split("_")
            new_key = key_split[0] + "".join(
                word.capitalize() for word in key_split[1:]
            )
            if type(value) == CheckStatus:
                value = value.value
            json_data[new_key] = value
        return json.dumps(json_data)


@dataclass
class BuildResult:
    status: CheckStatus
    time: float
    message: str


@dataclass
class TestResult:
    status: CheckStatus
    time: float
    message: str


@dataclass
class TestsResult:
    status: CheckStatus
    time: float
    message: str
    tests_passed: int
    tests_total: int


@dataclass
class LintResult:
    status: CheckStatus
    message: str
