from flask import Flask, Response, jsonify, request
from pydantic import ValidationError

from src.config import Config
from src.solution_checker.dtos.check_request_dto import CheckRequestDTO
from src.solution_checker.solution_checker import SolutionChecker

app = Flask(__name__)


@app.route("/check_solution", methods=["POST"])
def check_solution_view() -> tuple[Response, int]:
    config = Config()

    api_key = request.args.get("api_key")
    if api_key != config.API_KEY:
        return jsonify({"error": "You need to provide correct api_key as GET param to access this API"}), 401

    try:
        check_request = CheckRequestDTO(**request.json)
    except ValidationError as err:
        return jsonify({"error": str(err)}), 400

    build_timeout = check_request.build_timeout or config.DEFAULT_BUILD_TIMEOUT
    if build_timeout > config.MAX_BUILD_TIMEOUT:
        return jsonify({"error": f"buildTimeout is too big, maximum allowed is {config.MAX_BUILD_TIMEOUT}"}), 400

    test_timeout = check_request.test_timeout or config.DEFAULT_TEST_TIMEOUT
    if test_timeout * len(check_request.tests) > config.MAX_TESTING_TIMEOUT:
        return jsonify(
            {"error": f"testTimeout is too big, maximum allowed timeout for ALL tests is {config.MAX_TESTING_TIMEOUT}"}
        ), 400

    check_result = SolutionChecker(
        check_request.source_code,
        check_request.tests,
        build_timeout,
        test_timeout,
    ).check_solution()

    return jsonify(check_result.to_dict()), 200


if __name__ == "__main__":
    app.run(debug=True, port=8080)
