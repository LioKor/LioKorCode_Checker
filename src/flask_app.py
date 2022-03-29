from flask import Flask, request, Response
import json

from task_checker import check_task_multiple_files

app = Flask(__name__)


@app.route('/check_task/multiple_files', methods=['POST'])
def check_task_multiple_files_view():
    task = request.json
    try:
        result = check_task_multiple_files(task['sourceCode'], task['tests'])
        return Response(json.dumps(result), mimetype='application/json')
    except Exception as e:
        response = json.dumps({'error': str(e)})
        return Response(response, status=500, mimetype='application/json')
