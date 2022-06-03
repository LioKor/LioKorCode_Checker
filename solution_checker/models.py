import json


class CheckResult:
    def __init__(self,
                 check_time: float = 0.0,
                 build_time: float = 0.0,
                 check_result: int = -1,
                 check_message: str = '',
                 tests_passed: int = 0,
                 tests_total: int = 0,
                 lint_success: bool = False,
                 ):
        self.check_time = check_time  # todo: rename to test_time
        self.build_time = build_time
        self.check_result = check_result  # todo: rename to status
        self.check_message = check_message  # todo: rename to message
        self.tests_passed = tests_passed
        self.tests_total = tests_total
        self.lint_success = lint_success

    def json(self) -> str:
        json_data = {}
        for key, value in self.__dict__.items():
            key_split = key.split('_')
            new_key = key_split[0] + ''.join(word.capitalize() for word in key_split[1:])
            json_data[new_key] = value
        return json.dumps(json_data)
