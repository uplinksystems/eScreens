from datetime import datetime

from flask import Flask, jsonify, request, send_file, redirect, session, render_template, flash, abort, \
    send_from_directory, g
from flask_restful import Resource, Api
import json
import os
import time
from flask_cors import CORS
from functools import wraps
from Common import SCREEN_DIRECTORY, MEDIA_DIRECTORY, get_screens, get_media
import threading

app = Flask(__name__, static_url_path='/static')
app.config.from_pyfile('config.cfg')
CORS(app)
api = Api(app)
with threading.Lock():
    try:
        with open('displays.json') as json_file:
            displays = json.load(json_file)
    except:
        displays = {}

# Ensure directory exists
os.makedirs(MEDIA_DIRECTORY, exist_ok=True)
os.makedirs(SCREEN_DIRECTORY, exist_ok=True)


def login_required(func):
    @wraps(func)
    def decorated_view(*args, **kwargs):
        if 'login' in session:
            return func(*args, **kwargs)
        else:
            return redirect('/')

    return decorated_view


@app.route('/')
def dashboard():
    if 'login' in session:
        return render_template('/home.html')
    return render_template('login.html')


@app.route('/login', methods=['GET', 'POST'])
def login():
    if request.method == 'POST':
        if request.form['username'].lower() == 'username' and request.form['password'].lower() == 'password':
            session['login'] = 'user'
        elif request.form['username'].lower() == 'admin' and request.form['password'].lower() == 'admin':
            session['login'] = 'admin'
        if 'login' not in session:
            flash('Invalid Credentials')
        return redirect('/')


@app.route('/error', methods=['GET', 'POST'])
def error():
    return render_template('error.html')


@app.route('/admin.html', methods=['GET'])
def admin():
    if not session.get('login', '') == 'admin':
        abort(401)
    return render_template('admin.html')


@app.route('/create-default', methods=['POST'])
def create_default():
    if not session.get('login', '') == 'user' and not session.get('login', '') == 'admin':
        abort(401)
    screens = get_screens()
    for screen in request.form['screens']:
        try:
            with open(os.path.join(SCREEN_DIRECTORY, screens[int(screen)].replace(' ', '_') + '.json')) as json_file:
                config = json.load(json_file)
            remove_index = -1
            for i in range(len(config['defaults'])):
                if config['defaults'][i]['name'] == request.form['default-name']:
                    remove_index = i
            if not remove_index == -1:
                config['defaults'].pop(remove_index)

            config['defaults'].append({'name': request.form['default-name'],
                                       'start_date_time': datetime.strptime(request.form['start-time'],
                                                                            '%Y-%m-%dT%H:%M' if len(request.form[
                                                                                                        'start-time']) == 16 else '%Y-%m-%dT%H:%M:%S').strftime(
                                           '%m/%d/%Y %H:%M'), 'type': request.form['type'],
                                       'media': get_media()[int(request.form['media-names'])]})
            with open(os.path.join(SCREEN_DIRECTORY, screens[int(screen)].replace(' ', '_') + '.json'),
                      'w') as json_file:
                json.dump(config, json_file, indent=4)
        except Exception as e:
            print(e)
            return 'Failed to create default'
    return 'Successfully updated all display configurations'


@app.route('/upload-media/<image_name>', methods=['POST'])
def upload_media(image_name):
    if not session.get('login', '') == 'user' and not session.get('login', '') == 'admin':
        abort(401)
    try:
        if (request.files['image-vertical'].filename != ''):
            request.files['image-vertical'].save(
                os.path.join(MEDIA_DIRECTORY, image_name[:-4] + '_vertical' + image_name[-4:]))
        if (request.files['image-horizontal'].filename != ''):
            request.files['image-horizontal'].save(
                os.path.join(MEDIA_DIRECTORY, image_name[:-4] + '_horizontal' + image_name[-4:]))
        if (request.files['file'].filename != ''):
            request.files['file'].save(os.path.join(MEDIA_DIRECTORY, image_name))
    except:
        return 'Failed to upload files.'
    return 'Successfully uploaded files.'


@app.route('/create-screen', methods=['POST'])
def create_screen():
    if not session.get('login', '') == 'admin':
        abort(401)
    try:
        with open(os.path.join(SCREEN_DIRECTORY, request.form['screen-name'].replace(' ', '_') + '.json'),
                  'w') as json_file:
            json.dump(
                {'config': {'name': request.form['screen-name'], 'rotation': request.form['orientation']},
                 'defaults': [],
                 'events': [],
                 'fallback': {'name': 'fallback', 'type': 'image', 'media': 'fallback.png'}}, json_file, indent=4)
        return 'Successfully created screen'
    except:
        return 'Failed to create screen'


@app.route('/<page>')
def get_static(page):
    print(page)
    return render_template(page)


@app.route('/favicon.ico')
def favicon():
    return send_from_directory(os.path.join(app.root_path, 'static'), 'favicon.ico',
                               mimetype='image/vnd.microsoft.icon')


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
    return jsonify(get_media())


@app.route('/screen-connections')
def get_screen_connections():
    online_screens = []
    for name, screen in displays.items():
        if time.time() - screen['last-response-time'] < 300:  # Last 5 minutes
            online_screens.append({'name': name, 'ip': screen['ip'], 'version': screen['version']})
    return jsonify(online_screens)


@app.route('/online-screens')
def get_online_screens():
    return jsonify(displays)


@app.route('/reboot')
def reboot():
    # if 'login' not in session:
    # abort(401)
    for name, screen in displays.items():
        if time.time() - screen['last-response-time'] < 3600:  # Last 5 minutes
            print(os.popen("echo Hello World").read())
    return 'Restarting'


class Screens(Resource):
    def get(self, screen):
        # Handle missing file better?
        if not os.path.isfile(os.path.join(SCREEN_DIRECTORY, screen + '.json')):
            abort(404)
        global displays
        with threading.Lock():
            displays[screen] = {'version': request.args.get('version', default=1, type=int), 'ip': request.remote_addr,
                                'last-response-time': time.time()}
            with open('displays.json', 'w') as json_file:
                json.dump(displays, json_file, indent=4)
        with open(os.path.join(SCREEN_DIRECTORY, screen + '.json')) as json_file:
            data = json.load(json_file)
            return jsonify(data)

    def post(self, screen):
        if 'login' not in session:
            abort(401)
        with open(os.path.join(SCREEN_DIRECTORY, screen + '.json'), 'w') as json_file:
            json.dump(request.get_json(force=True), json_file, indent=4)
        return '(Put some sort of confirmation here)'


class Update(Resource):
    def post(self):
        if not session.get('login', '') == 'admin':
            abort(401)
        try:
            file = request.files['updateFile']
            file.save('Display.py')
        except:
            return 'Failed to update program'
        return 'Successfully updated program'


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

api.add_resource(Screens, '/screen/<string:screen>')
api.add_resource(Media, '/media/<string:filename>')
api.add_resource(Update, '/update')

if __name__ == '__main__':
    app.run(host='0.0.0.0', debug=True, port=5001)
