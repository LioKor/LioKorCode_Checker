from flask import Flask, request, Response
import json

from task_checker import check_task

app = Flask(__name__)


@app.route('/check_task/long', methods=['POST'])
def check_task_long_view():
    task = request.json
    try:
        result = check_task(task['sourceCode'], task['tests'])
        return Response(json.dumps(result), mimetype='application/json')
    except Exception as e:
        response = json.dumps({'error': str(e)})
        return Response(response, status=500, mimetype='application/json')
