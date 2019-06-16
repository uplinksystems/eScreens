from flask import Flask, jsonify, request, send_file, redirect, session, render_template, flash, abort
from flask_restful import Resource, Api
import json, os
from flask_cors import CORS
from flexx import flx
import Dashboard
from functools import wraps
import dash
import dash_core_components as dcc
import dash_html_components as html
import base64


app = Flask(__name__)
app.config.from_pyfile('config.cfg')
CORS(app)
api = Api(app)

MEDIA_DIRECTORY = os.path.join(os.path.dirname(__file__), 'media')
SCREEN_DIRECTORY = os.path.join(os.path.dirname(__file__), 'screen')

# Ensure directory exists
os.makedirs(MEDIA_DIRECTORY, exist_ok=True)
os.makedirs(SCREEN_DIRECTORY, exist_ok=True)

# Initialize Dashboard
a = flx.App(Dashboard.Root, title='Display Dashboard')
assets = a.dump('index.html', link=0)


# A function
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
        if view_func.startswith(dash_app.url_base_pathname):
            dash_app.server.view_functions[view_func] = login_required(dash_app.server.view_functions[view_func])


dash_app = dash.Dash(__name__, server=app, url_base_pathname='/dashboard/')
dash_app.layout = html.Div([
    html.H1('Stock Tickers'),
    dcc.Dropdown(
        id='my-dropdown',
        options=[
            {'label': 'Coke', 'value': 'COKE'},
            {'label': 'Tesla', 'value': 'TSLA'},
            {'label': 'Apple', 'value': 'AAPL'}
        ],
        value='COKE'
    ),
    dcc.Graph(id='my-graph')
], style={'width': '500'})
_protect_dash_views(dash_app)


@app.route('/')
def dashboard():
    print(request.headers)
    if 'login' in session:
        return assets['index.html'].decode()
    return render_template('login.html')


@app.route('/login', methods=['GET', 'POST'])
def login():
    if request.method == 'POST':
        if request.form['username'] == 'username' and request.form['password'] == 'password':
            session['login'] = 'user'
        elif request.form['username'] == 'admin' and request.form['password'] == 'admin':
            session['login'] = 'admin'
        if not 'login' in session:
            flash('Invalid Credentials')
        return redirect('/')


@app.route('/logout')
def logout():
   session.pop('login', None)
   return redirect('/')


@app.route('/auth')
def get_auth():
   return 'login' in session


@app.route('/screen')
def get_screens():
    files = []
    for filename in os.listdir(SCREEN_DIRECTORY):
        path = os.path.join(SCREEN_DIRECTORY, filename)
        if os.path.isfile(path):
            files.append(filename)
    return jsonify(files)


@app.route('/media')
def get_media():
    files = []
    for filename in os.listdir(MEDIA_DIRECTORY):
        path = os.path.join(MEDIA_DIRECTORY, filename)
        if os.path.isfile(path):
            if filename.endswith('_horizontal'):
                if not filename[:-11] in files:
                    files.append(filename[:-11])
            elif filename.endswith('_vertical'):
                if not filename[:-9] in files:
                    files.append(filename[:-9])
            else:
                files.append(filename)
    return jsonify(files)


class Screens(Resource):
    def get(self, screen):
        if not os.path.isfile(os.path.join(SCREEN_DIRECTORY, screen)):
            return 402
        with open(os.path.join(SCREEN_DIRECTORY, screen)) as json_file:
            data = json.load(json_file)
            return jsonify(data)

    def put(self, screen):
        if not 'user' in session:
            abort(401)
        with open(os.path.join(SCREEN_DIRECTORY, screen), 'w') as json_file:
            json.dump(request.get_json(force=True), json_file)
        return '(Put some sort of confirmation here)'


class Media(Resource):
    def post(self, filename):
        #if not 'user' in session:
        #    abort(401)
        #print(request.form)
        #print(request.files)
        #print(request.headers)
        #print(request.json)
        #b64_string = request.form['file']
        #with open(os.path.join(MEDIA_DIRECTORY, filename), 'wb') as fh:
        #    b64_string += '=' * (-len(b64_string) % 4)
        #    print(b64_string)
        #    fh.write(base64.decodebytes(b64_string.encode()))

        file = request.files['file']
        file.save(os.path.join(MEDIA_DIRECTORY, filename))
        return '(Put some sort of confirmation here)'

    # Unused and untested
    #def get(self, filename):
    #    if not os.path.isfile(os.path.join(MEDIA_DIRECTORY, filename)):
    #        return 402
    #    return send_file(os.path.join(MEDIA_DIRECTORY, filename))


api.add_resource(Screens, '/screen/<string:screen>')
api.add_resource(Media, '/media/<string:filename>')

if __name__ == '__main__':
    app.run(host='0.0.0.0', debug=True, port=5001)
