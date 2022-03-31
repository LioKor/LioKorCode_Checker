from flask import Flask, request, Response
import json

from task_checker import check_task_multiple_files

app = Flask(__name__)


class ResponseJSON(Response):
    default_mimetype = 'application/json'


@app.errorhandler(400)
def handle_bad_request(e):
    return json.dumps({'error': 'We accept only correct JSON. AWU.'}), 400


@app.route('/check_task/multiple_files', methods=['POST'])
def check_task_multiple_files_view():
    task = request.json

    if type(task) != dict:
        response = json.dumps({'error': 'We accept only dict as a root element. WOOF!'})
        return ResponseJSON(response, status=400)

    source_code, tests = task.get('sourceCode', None), task.get('tests', None)

    if source_code is None or tests is None:
        response = json.dumps({'error': 'Required "sourceCode" or "tests" fields are missing!'})
        return ResponseJSON(response, status=400)

    if type(source_code) != dict or type(tests) != list:
        response = json.dumps({'error': '"sourceCode" must be dict and "tests" must be list'})
        return ResponseJSON(response, status=400)

    try:
        check_result = check_task_multiple_files(task['sourceCode'], task['tests'])
        return ResponseJSON(check_result.json())
    except Exception as e:
        response = json.dumps({'error': str(e)})
        return ResponseJSON(response, status=500)
