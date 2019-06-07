from flask import Flask, jsonify, request, send_file, redirect, url_for
from flask_restful import Resource, Api
from flask_httpauth import HTTPBasicAuth
import json, os
from flask_cors import CORS


app = Flask(__name__)
CORS(app)
api = Api(app)
auth = HTTPBasicAuth()

MEDIA_DIRECTORY = 'media'
SCREEN_DIRECTORY = 'screen'
os.makedirs(os.path.join(os.path.dirname(__file__), MEDIA_DIRECTORY), exist_ok=True)


class Screens(Resource):
    def get(self, screen):
        if not os.path.isfile(os.path.join(os.path.dirname(__file__), SCREEN_DIRECTORY, screen)):
            return 402
        with open(os.path.join(os.path.dirname(__file__), SCREEN_DIRECTORY, screen)) as json_file:
            data = json.load(json_file)
            return jsonify(data)

    @auth.login_required
    def put(self, screen):
        os.makedirs(os.path.join(os.path.dirname(__file__), SCREEN_DIRECTORY), exist_ok=True)
        with open(os.path.join(os.path.dirname(__file__), SCREEN_DIRECTORY, screen), 'w') as json_file:
            json.dump(request.get_json(force=True), json_file)
        return '(Put some sort of confirmation here)'


class Media(Resource):
    @auth.login_required
    def post(self, filename):
        file = request.files['file']
        file.save(os.path.join(os.path.dirname(__file__), MEDIA_DIRECTORY, filename))
        return '(Put some sort of confirmation here)'

    # Unused and untested
    def get(self, filename):
        if not os.path.isfile(os.path.join(os.path.dirname(__file__), MEDIA_DIRECTORY, filename)):
            return 402
        return send_file(os.path.join(os.path.dirname(__file__), MEDIA_DIRECTORY, filename))


class ScreenIndex(Resource):
    def get(self):
        files = []
        for filename in os.listdir(os.path.join(os.path.dirname(__file__), SCREEN_DIRECTORY)):
            path = os.path.join(os.path.dirname(__file__), SCREEN_DIRECTORY, filename)
            if os.path.isfile(path):
                files.append(filename)
        return jsonify(files)


class MediaIndex(Resource):
    def get(self):
        files = []
        for filename in os.listdir(os.path.join(os.path.dirname(__file__), MEDIA_DIRECTORY)):
            path = os.path.join(os.path.dirname(__file__), MEDIA_DIRECTORY, filename)
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


@auth.verify_password
def verify(username, password):
    if not (username and password):
        return False
    return password == "password" and username == "username"

api.add_resource(Screens, '/screen/<string:screen>')
api.add_resource(ScreenIndex, '/screen')
api.add_resource(Media, '/media/<string:filename>')
api.add_resource(MediaIndex, '/media')

if __name__ == '__main__':
    app.run(debug=True)
