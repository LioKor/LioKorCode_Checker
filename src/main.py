from flask import Flask, request, Response
import json

from task_checker import check_task

app = Flask(__name__)

example_request = {
    'sourceCode': '''#include "stdio.h"
int main() {
    int a, b;

    scanf("%d %d", &a, &b);
    
    printf("%d", a + b);
    
    return 0;
}''',
    'tests': [
        ['1 2', '3'],
        ['4 5', '9'],
        ['-2 2', '0']
    ]
}


@app.route('/check_task/long', methods=['POST'])
def check_task_long_view():
    task = request.json
    try:
        result = check_task(task['sourceCode'], task['tests'])
        return Response(json.dumps(result), mimetype='application/json')
    except Exception as e:
        return Response('{}', status=500, mimetype='application/json')


app.run(host='0.0.0.0', port=7070)

print(json.dumps(example_request))
