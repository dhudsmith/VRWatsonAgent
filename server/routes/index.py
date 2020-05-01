from server import app
import json
from flask import render_template, Response, request

@app.route('/')
def hello_world():
    return app.send_static_file('index.html')

@app.route('/job_results', methods=['GET', 'POST'])
def stt_callback():
    print('Made it here!')
    body = request.args['challenge_string']

    resp = Response(body, status=500, mimetype='text/plain')

    return resp


@app.errorhandler(404)
@app.route("/error404")
def page_not_found(error):
    return app.send_static_file('404.html')

@app.errorhandler(500)
@app.route("/error500")
def requests_error(error):
    return app.send_static_file('500.html')
