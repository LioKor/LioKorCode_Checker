import json

from flask import Flask, Response, request

import config
from src.solution_checker.solution_checker import SolutionChecker

app = Flask(__name__)


class ResponseJSON(Response):
    default_mimetype = "application/json"


@app.errorhandler(400)
def handle_bad_request() -> tuple[str, int]:
    return json.dumps({"message": "Bad request!"}), 400


@app.route("/check_solution", methods=["POST"])
def check_solution_view() -> Response:
    api_key = request.args.get("api_key")
    if api_key != config.API_KEY:
        response = json.dumps({"error": "You need to provide correct api_key as GET param to access this API"})
        return ResponseJSON(response, status=401)

    check_request = request.json

    if not isinstance(check_request, dict):
        response = json.dumps({"error": "We accept only dict as a root element."})
        return ResponseJSON(response, status=400)

    source_code, tests = check_request.get("sourceCode", None), check_request.get("tests", None)
    if source_code is None or tests is None:
        response = json.dumps({"error": 'Required "sourceCode" or "tests" fields are missing!'})
        return ResponseJSON(response, status=400)

    if not isinstance(source_code, dict) or not isinstance(tests, list):
        response = json.dumps({"error": '"sourceCode" must be dict and "tests" must be list'})
        return ResponseJSON(response, status=400)

    build_timeout = check_request.get("buildTimeout", config.DEFAULT_BUILD_TIMEOUT)
    if build_timeout > config.MAX_BUILD_TIMEOUT:
        response = json.dumps(
            {"error": "buildTimeout is too big, maximum allowed is {}".format(config.MAX_BUILD_TIMEOUT)}
        )
        return ResponseJSON(response, status=401)

    test_timeout = check_request.get("testTimeout", config.DEFAULT_TEST_TIMEOUT)
    if test_timeout * len(tests) > config.MAX_TESTING_TIMEOUT:
        response = json.dumps(
            {
                "error": f"testTimeout is too big, maximum allowed timeout for ALL tests is "
                f"{config.MAX_TESTING_TIMEOUT}"
            }
        )
        return ResponseJSON(response, status=401)

    # try:
    check_result = SolutionChecker(
        check_request["sourceCode"],
        check_request["tests"],
        build_timeout,
        test_timeout,
    ).check_solution()
    return ResponseJSON(check_result.json())
    # except Exception as e:
    #     response = json.dumps({"error": str(e)})
    #     return ResponseJSON(response, status=500)


if __name__ == "__main__":
    app.run(debug=True, port=8080)
