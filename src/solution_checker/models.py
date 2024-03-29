from enum import Enum
from dataclasses import dataclass
import json


class CheckStatus(Enum):
    UNKNOWN = -1
    OK = 0
    CHECKING = 1
    BUILD_ERROR = 2
    RUNTIME_ERROR = 3
    TEST_ERROR = 4
    EXECUTION_TIMEOUT = 6
    BUILD_TIMEOUT = 7


@dataclass
class CheckResult:
    tests_time: float
    build_time: float
    status: CheckStatus
    message: str
    tests_passed: int
    tests_total: int
    lint_success: bool

    def json(self) -> str:
        # todo: remove when backend is ready to use new fields
        datakey_mapper = {
            "tests_time": "check_time",
            "status": "check_result",
            "message": "check_message",
        }

        json_data = {}
        for key, value in self.__dict__.items():
            datakey = datakey_mapper.get(key)
            key = datakey if datakey is not None else key
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
    success: bool
    message: str
