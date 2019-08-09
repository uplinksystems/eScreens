import json
import os
import time
import traceback
from threading import Thread
from time import sleep
import re

import kivy
import requests
from kivy.clock import Clock
from kivy.core.window import Window
from kivy.properties import ObjectProperty, NumericProperty
import platform

if platform.system() != 'Windows':
    from omxplayer.player import OMXPlayer, OMXPlayerDeadError
from kivy.uix.image import Image

kivy.require('1.11.1')

from kivy.app import App
from kivy.uix.screenmanager import ScreenManager, Screen, NoTransition
from kivy.lang import Builder
from subprocess import Popen, PIPE
from datetime import datetime
import subprocess

# Config.set('graphics', 'fullscreen', '1')
SERVER_IP = '192.168.1.212'
SERVER_PORT = '5001'
MEDIA_DIRECTORY = 'media/'
# os.environ['KIVY_BCM_DISPMANX_LAYER'] = '0'
omx = None
twitch = None

Builder.load_string("""
<RotatedImage>:
    canvas.before:
        PushMatrix
        Rotate:
            angle: root.angle
            axis: 0, 0, 1
            origin: root.center
    canvas.after:
        PopMatrix
        
<ImageScreen>:
    image: _image
    RotatedImage:
        id: _image
        source: 'no_media.png'
        allow_stretch: True
""")


class RotatedImage(Image):
    angle = NumericProperty()


class ImageScreen(Screen):
    image = ObjectProperty(None)


media_type = ''
media = ''
last_media = ''
last_media_type = ''
sm = ScreenManager(transition=NoTransition())
image_screen = ImageScreen(name='image')
sm.add_widget(image_screen)
# sm.canvas.opacity = 0.3
block_update = False
config = None
stopped = False
try:
    with open('config.json') as json_file:
        config = json.load(json_file)
except Exception:
    print('Failed to load config')


def show_image(image):
    splot = image.split('.')
    horizontal = config['config']['rotation'] == 0 or config['config']['rotation'] == 180
    image = MEDIA_DIRECTORY + splot[0] + ('_horizontal' if horizontal else '_vertical') + '.' + splot[1]
    if os.path.exists(image):
        image_screen.image.source = image
    else:
        image_screen.image.source = 'no_media.png'
        if media != last_media:
            print('Image not found: ' + image)
    image_screen.image.reload()
    sm.current = 'image'


def show_video(video, loop=True):
    global omx
    if os.path.exists(video):
        if platform.system() != 'Windows':
            if (omx != None):
                print('Starting video: ' + video)
                try:
                    omx.load(video)
                except OMXPlayerDeadError:
                    print('OMX was dead, creating new player for video: ' + video)
                    omx = OMXPlayer(video, args=['--loop', '--no-osd', '--layer', '-1', '--no-keys', '-b'])
            else:
                print('Starting OMX with video: ' + video)
                omx = OMXPlayer(video,
                                args=(['--loop'] if loop else []) + ['--no-osd', '--layer', '-1', '--no-keys', '-b'])
    else:
        print('Video not found: ' + video)
        image_screen.image.source = 'no_media.png'
        image_screen.image.reload()
        sm.current = 'image'


def stop_video():
    global omx
    print('Stopping OMX')
    try:
        omx.stop()
    except OMXPlayerDeadError:
        print('Can\'t close OMX, already dead')
    omx = None


def update(dt):
    global last_media
    global last_media_type
    global twitch

    if media_type != 'video' and media_type != 'manual' and omx is not None:
        stop_video()

    if media_type != 'twitch' and twitch is not None:
        twitch.kill()
        twitch = None

    if media == '' or media_type == '':
        image_screen.image.source = 'no_media.png'
        image_screen.image.reload()
        sm.current = 'image'
        return

    if media != last_media:
        print('New media: ' + media_type + ': "' + media + '"')

    if (media_type == 'image'):
        show_image(media)
    elif (media_type == 'video'):
        if (last_media != media):
            show_video(MEDIA_DIRECTORY + media)
    elif (media_type == 'slideshow'):
        splot = media.split(', ')
        duration = int(splot[0])
        entries = len(splot) - 1
        current = splot[int((int(time.time()) % (duration * entries)) / duration + 1)]
        show_image(current)
    elif (media_type == 'twitch'):
        if last_media != media or (twitch is not None and twitch.poll() != None):
            twitch = subprocess.Popen(['streamlink', '-np', 'omxplayer --adev hdmi --timeout 20 --live', media, 'best'],
                                      shell=False)
    last_media = media
    last_media_type = media_type


def update_media(dt):
    global media_type
    global media
    if block_update or not config:
        print('block')
        return
    # Todo: Add support for events
    if len(config['defaults']) == 0:
        media_type = config['fallback']['type']
        media = config['fallback']['media']
        return
    current = config['defaults'][0]
    now = datetime.now()
    for default in config['defaults']:
        dt = datetime.strptime(default['start_date_time'], '%m/%d/%Y %H:%M')
        if dt < now and dt > datetime.strptime(current['start_date_time'], '%m/%d/%Y %H:%M'):
            current = default
    media_type = current['type']
    media = current['media']


def update_config():
    while not stopped:
        if platform.system() != 'Windows':
            try:
                p = Popen(['rsync', '-e', 'ssh -o StrictHostKeyChecking=no', '-avzh',
                           'pi@' + SERVER_IP + ':/home/pi/escreens/media', '/home/pi/escreens'], stdin=PIPE,
                          stdout=PIPE, stderr=PIPE, universal_newlines=True)
                output, err = p.communicate()
                match = re.search(r'list(.*?)sent', output, re.DOTALL)
                if match != None and match.group(1) != '\n\n':
                    print('Updated files:' + match.group(1))

                p = Popen(['rsync', '-e', 'ssh -o StrictHostKeyChecking=no', '-avzh',
                           'pi@' + SERVER_IP + ':/home/pi/escreens/Display.py', '/home/pi/escreens'], stdin=PIPE,
                          stdout=PIPE, stderr=PIPE, universal_newlines=True)
                output, err = p.communicate()
                if 'Display.py' in output:
                    print('Updated program')
                    if omx is not None:
                        stop_video()
                    if twitch is not None:
                        twitch.kill()
                    os._exit(69)
            except Exception as e:
                print('Failed to update media or program: ' + str(e))
                traceback.print_exc()

        try:
            global config
            response = requests.get('http://' + SERVER_IP + ':' + SERVER_PORT + '/screen/' + config['config']['name'])
            new_config = response.json()
            if new_config != config:
                if response.status_code == 200:
                    global block_update
                    block_update = True
                    config = new_config
                    block_update = False
                    print('Updated config file: ' + str(config))
                    with open('config.json', 'w') as json_file:
                        json.dump(config, json_file)
                else:
                    print('Failed to get config, server returned code: ' + str(response.status_code))
        except Exception as e:
            print('Failed to update config: ' + str(e))
        sleep(15)


if config:
    image_screen.image.angle = 0 if config['config']['rotation'] < 180 else 180
    Thread(target=update_config).start()
    Clock.schedule_interval(update, 1.0 / 60.0)
    Clock.schedule_interval(update_media, 0.1)
else:
    print('Missing config')
    image_screen.image.source = 'missing_config.jpeg'
    image_screen.image.reload()


# print(video_screen.video.source)


def on_key_up(window, something1, something2, text='', modifiers=[]):
    if media_type != 'manual' or text is None or not text.isnumeric():
        return
    splot = media.split(', ')
    if int(text) < len(splot):
        show_video(MEDIA_DIRECTORY + splot[int(text)], False)


class Display(App):

    def build(self):
        # Window.clearcolor = (0, 0, 0, 0.1)
        Window.fullscreen = 'auto'
        Window.bind(on_key_up=on_key_up)
        # Window.opacity = 0
        return sm

    def on_stop(self):
        global stopped
        stopped = True
        if omx is not None:
            stop_video()
        if twitch is not None:
            twitch.kill()
        os._exit(69)


if __name__ == '__main__':
    Display().run()
