from flask import Flask, jsonify, request, send_file, redirect, session, render_template, flash, abort, send_from_directory, g
from flask_restful import Resource, Api
import json
import os
import time
from flask_cors import CORS
from flexx import flx
import OldDashboard
import Dashboard as Dashboard
from functools import wraps
import dash
import dash_bootstrap_components as dbc
from Common import SCREEN_DIRECTORY, MEDIA_DIRECTORY, get_screens, get_media
import dash_callback_router
import threading


app = Flask(__name__)
app.config.from_pyfile('config.cfg')
CORS(app)
api = Api(app)
displays = {}

# Ensure directory exists
os.makedirs(MEDIA_DIRECTORY, exist_ok=True)
os.makedirs(SCREEN_DIRECTORY, exist_ok=True)

# Initialize Dashboard
a = flx.App(OldDashboard.Root, title='Display Dashboard')
assets = a.dump('index.html', link=0)


def login_required(func):
    @wraps(func)
    def decorated_view(*args, **kwargs):
        if 'login' in session:
            return func(*args, **kwargs)
        else:
            return redirect('/')

    return decorated_view


def _protect_dash_views(dash_app):
    for view_func in dash_app.server.view_functions:
        if view_func.startswith('/dashboard/'):
            dash_app.server.view_functions[view_func] = login_required(dash_app.server.view_functions[view_func])


external_stylesheets = [dbc.themes.BOOTSTRAP, 'https://codepen.io/chriddyp/pen/bWLwgP.css',
                        'https://codepen.io/chriddyp/pen/brPBPO.css']
dash_app = dash.Dash(__name__, server=app, show_undo_redo=False, url_base_pathname='/dashboard/', external_stylesheets=external_stylesheets,
                     meta_tags=[
                         {
                             'name': 'Display Dashboard',
                             'content': 'Edit media shown on displays here.'
                         },
                         {
                             'http-equiv': 'X-UA-Compatible',
                             'content': 'IE=edge'
                         },
                         {
                             'name': 'viewport',
                             'content': 'width=device-width, initial-scale=1.0'
                         }
                     ])
callback_router = dash_callback_router.CallbackRouter(dash_app, hijack_callbacks=True)
dash_app.config['suppress_callback_exceptions'] = True
dash_app.layout = Dashboard.layout
_protect_dash_views(dash_app)
Dashboard.register_callbacks(dash_app)
callback_router.register_callbacks()


@app.route('/')
def dashboard():
    if 'login' in session:
        return redirect('/dashboard/')
    return render_template('login.html')


@app.route('/old-dashboard')
def old_dashboard():
    if 'login' in session:
        return assets['index.html'].decode()
    return render_template('login.html')


@app.route('/login', methods=['GET', 'POST'])
def login():
    if request.method == 'POST':
        if request.form['username'].lower() == 'username' and request.form['password'].lower() == 'password':
            session['login'] = 'user'
        elif request.form['username'].lower() == 'admin' and request.form['password'].lower() == 'admin':
            session['login'] = 'admin'
        if not 'login' in session:
            flash('Invalid Credentials')
        return redirect('/')


@app.route('/static/<filename>')
def get_static(filename):
    return send_from_directory('templates', filename)


@app.route('/logout')
def logout():
    session.pop('login', None)
    return redirect('/')


@app.route('/auth')
def get_auth():
    return session.get('login', '')


@app.route('/screen')
def get_screens_json():
    return jsonify(get_screens())


@app.route('/media')
def get_media_json():
    return jsonify(get_screens())


@app.route('/online-screens')
def get_online_screens():
    return jsonify(g['displays'] if 'displays' in g else {})


class Screens(Resource):
    def get(self, screen):
        # Handle missing file better?
        if not os.path.isfile(os.path.join(SCREEN_DIRECTORY, screen + '.json')):
            abort(404)
        global displays
        with threading.Lock():
            displays[screen] = {'version': request.args.get('version', default=1, type=int), 'ip': request.remote_addr,
                                'last-response-time': time.time()}

        with open(os.path.join(SCREEN_DIRECTORY, screen + '.json')) as json_file:
            data = json.load(json_file)
            return jsonify(data)

    def put(self, screen):
        if 'login' not in session:
            abort(401)
        with open(os.path.join(SCREEN_DIRECTORY, screen + '.json'), 'w') as json_file:
            json.dump(request.get_json(force=True), json_file)
        return '(Put some sort of confirmation here)'


class Update(Resource):
    def post(self):
        if not session.get('login', '') == 'admin':
            abort(401)
        file = request.files['file']
        file.save('escreen.jar')
        return '(Put some sort of confirmation here)'


class Media(Resource):
    def post(self, filename):
        if 'login' not in session:
            abort(401)
        file = request.files['file']
        file.save(os.path.join(MEDIA_DIRECTORY, filename))
        return '(Put some sort of confirmation here)'

    def get(self, filename):
        if not os.path.isfile(os.path.join(MEDIA_DIRECTORY, filename)):
            return abort(404)
        return send_from_directory(MEDIA_DIRECTORY, filename)


# Todo: Convert classes to routes
# Todo: store map of time and ip in requests to show active IP, maybe


api.add_resource(Screens, '/screen/<string:screen>')
api.add_resource(Media, '/media/<string:filename>')
api.add_resource(Update, '/update')

if __name__ == '__main__':
    app.run(host='0.0.0.0', debug=True, port=5000)
