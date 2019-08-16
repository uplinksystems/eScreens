import functools
import json
import logging
import os
import sys
import time
from logging import handlers
from threading import Thread
from time import sleep
import re
import cProfile

import colorama
import coloredlogs
import kivy
import requests
from kivy import Config
from kivy.clock import Clock
from kivy.core.window import Window
from kivy.properties import ObjectProperty, NumericProperty, BooleanProperty
import platform

if platform.system() != 'Windows':
    from omxplayer.player import OMXPlayer, OMXPlayerDeadError
else:
    colorama.init()
from kivy.uix.image import Image

kivy.require('1.11.1')

from kivy.app import App
from kivy.uix.screenmanager import ScreenManager, Screen, NoTransition
from kivy.lang import Builder
from kivy.clock import mainthread
from subprocess import Popen, PIPE
from datetime import datetime
import subprocess
import psutil

#Config.set('graphics', 'fullscreen', '1')
#Config.set('modules', 'monitor', '')
SERVER_IP = '192.168.1.233'
SERVER_PORT = '5001'
MEDIA_DIRECTORY = 'media/'
MISSING_FILE_ICON = 'file_not_found_icon.png'
OFFLINE_ICON = 'offline_icon.png'
NO_MEDIA_IMAGE = 'no_media.png'
VERSION = 1
# os.environ['KIVY_BCM_DISPMANX_LAYER'] = '0'
omx = None
twitch = None
profiling = 'profile' in sys.argv

formatter = coloredlogs.ColoredFormatter('%(asctime)-23s  %(levelname)-8s  %(message)s', '%Y-%m-%d %H:%M:%S')
log = logging.getLogger('Display')
log.setLevel(logging.DEBUG)

if platform.system() != 'Windows':
    if not os.path.exists('logs'):
        os.makedirs('logs')
    log_file_handler = handlers.TimedRotatingFileHandler('logs/log.txt', 'midnight', 1)
    log_file_handler.setLevel(logging.INFO)
    log_file_handler.setFormatter(
        logging.Formatter('%(asctime)-23s  %(levelname)-8s  %(message)s', '%Y-%m-%d %H:%M:%S'))
    log_file_handler.suffix = "%Y-%m-%d"
    log.addHandler(log_file_handler)

log_console_handler = logging.StreamHandler(sys.stderr)
log_console_handler.setLevel(logging.DEBUG)
log_console_handler.setFormatter(formatter)
log.addHandler(log_console_handler)

log.info('Running version: {}'.format(VERSION))

Builder.load_string('''
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
    label: _label
    icon: _icon
    RotatedImage:
        id: _image
        source: ''
        allow_stretch: True        
    Label:
        id: _label
        font_size: 70  
        center_x: root.width / 6
        top: root.height / 2
        text: ''
    RotatedImage:
        id: _icon
        source: ''
        opacity: 0
        position: 0, 0
        size: 30, 30
''')


class RotatedImage(Image):
    angle = NumericProperty()


class ImageScreen(Screen):
    image = ObjectProperty(None)
    icon = ObjectProperty(None)
    label = ObjectProperty(None)


media_type = ''
media = ''
last_media = ''
last_media_type = ''
previous_icon = ''
datetime_cache = {}
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
    log.info('Failed to load config')


def exception(function):
    @functools.wraps(function)
    def wrapper(*args, **kwargs):
        try:
            return function(*args, **kwargs)
        except:
            err = "There was an exception in  "
            err += function.__name__
            log.exception(err)

    return wrapper


def parse_datetime(string):
    if string in datetime_cache:
        return datetime_cache[string]
    datetime_cache[string] = datetime.strptime(string, '%m/%d/%Y %H:%M')
    return datetime_cache[string]


def kill_all_omx():
    for proc in psutil.process_iter():
        if proc.name() == 'omxplayer':
            log.info('Killed leftover OMX process: ' + str(proc.pid))
            proc.kill()


@mainthread
def show_icon(icon, overwrite=False):
    if image_screen.icon.source == icon:
        return
    if not overwrite and image_screen.icon.source == OFFLINE_ICON:
        global previous_icon
        previous_icon = icon
        return

    image_screen.icon.source = icon
    image_screen.icon.opacity = 0 if icon == '' else 1
    image_screen.icon.reload()


@mainthread
def show_image(image, external=False):
    splot = image.split('.')
    horizontal = config['config']['rotation'] == 0 or config['config']['rotation'] == 180
    file = (MEDIA_DIRECTORY if external else '') + splot[0] + ('_horizontal' if horizontal else '_vertical') + '.' + \
            splot[1]
    if os.path.exists(file):
        show_icon('')
        image_screen.image.source = file
    else:
        show_icon(MISSING_FILE_ICON)
        log.warning('Image not found: ' + file)
        image_screen.image.source = 'no_media ' + ('_horizontal' if horizontal else '_vertical') + '.png'
    image_screen.image.reload()
    sm.current = 'image'


def show_video(video, loop=True):
    global omx
    if os.path.exists(video):
        show_icon('')
        if platform.system() != 'Windows':
            if (omx != None):
                log.info('Starting video: ' + video)
                try:
                    omx.load(video)
                except OMXPlayerDeadError:
                    log.info('OMX was dead, creating new player for video: ' + video)
                    omx = OMXPlayer(video, args=['--loop', '--no-osd', '--layer', '-1', '--no-keys', '-b'])
            else:
                log.info('Starting OMX with video: ' + video)
                omx = OMXPlayer(video,
                                args=(['--loop'] if loop else []) + ['--no-osd', '--layer', '-1', '--no-keys', '-b'])
    else:
        stop_video()
        show_icon(MISSING_FILE_ICON)
        log.warning('Video not found: ' + video)


def stop_video():
    global omx
    if omx is None:
        return
    log.info('Stopping OMX')
    try:
        omx.stop()
    except OMXPlayerDeadError:
        log.info('Can\'t close OMX, already dead')
    omx = None


# Update display
@exception
def update(dt):
    global last_media
    global last_media_type
    global twitch
    global previous_icon
    log.info(dt)
    if media == '' or media_type == '':
        show_image(NO_MEDIA_IMAGE)
        return

    if media_type != 'twitch' and twitch is not None:
        twitch.kill()
        twitch = None

    if (media != last_media):
        log.info('New media: ' + media_type + ': "' + media + '"')
        if image_screen.icon.source != OFFLINE_ICON:
            show_icon('')
        image_screen.label.text = ''
        previous_icon = ''
        show_image(NO_MEDIA_IMAGE)
        stop_video()

    if (media_type == 'image'):
        show_image(media, True)
    elif (media_type == 'video'):
        if (last_media != media):
            show_video(MEDIA_DIRECTORY + media)
    elif (media_type == 'slideshow'):
        splot = media.split(', ')
        duration = int(splot[0])
        entries = len(splot) - 1
        current = splot[int((int(time.time()) % (duration * entries)) / duration) + 1]
        show_image(current, True)
    elif (media_type == 'twitch'):
        image_screen.label.text = 'Connecting to stream: ' + media.split('www.')[1].split(', ')[0]
        if last_media != media or (twitch is not None and twitch.poll() != None):
            splot = media.split(', ')
            twitch = subprocess.Popen(
                ['streamlink', '-np', 'omxplayer --adev hdmi --timeout 20 --live', splot[0], splot[1]],
                shell=False)
    last_media = media
    last_media_type = media_type


# Determine current media
@exception
def update_media(dt):
    global media_type
    global media
    if block_update or not config:
        return
    # Todo: Add support for events
    if len(config['defaults']) == 0:
        media_type = config['fallback']['type']
        media = config['fallback']['media']
        return
    current = config['defaults'][0]
    now = datetime.now()
    for default in config['defaults']:
        dt = parse_datetime(default['start_date_time'])
        if dt < now and dt > parse_datetime(current['start_date_time']):
            current = default
    media_type = current['type']
    media = current['media']


# Update config and media files
def update_config():
    @exception
    def _update_config():
        if platform.system() != 'Windows':
            try:
                p = Popen(['rsync', '-e', 'ssh -o StrictHostKeyChecking=no', '-avzh',
                           'pi@' + SERVER_IP + ':/home/pi/escreens/media', '/home/pi/escreens'], stdin=PIPE,
                          stdout=PIPE, stderr=PIPE, universal_newlines=True)
                output, err = p.communicate()
                log.debug(output)
                match = re.search(r'list(.*?)sent', output, re.DOTALL)
                if match != None and match.group(1) != '\n\n':
                    log.info('Updated files:' + match.group(1))

                p = Popen(['rsync', '-e', 'ssh -o StrictHostKeyChecking=no', '-avzh',
                           'pi@' + SERVER_IP + ':/home/pi/escreens/Display.py', '/home/pi/escreens'], stdin=PIPE,
                          stdout=PIPE, stderr=PIPE, universal_newlines=True)
                output, err = p.communicate()
                log.debug(output)
                if 'Display.py' in output:
                    log.info('Updated program')
                    if omx is not None:
                        stop_video()
                    if twitch is not None:
                        twitch.kill()
                    os._exit(69)
            except Exception as e:
                log.warning('Failed to update media or program: ' + str(e))
                # traceback.print_exc()
        global previous_icon
        try:
            global config
            response = requests.get(
                'http://' + SERVER_IP + ':' + SERVER_PORT + '/screen/' + config['config']['name'] + '?version=' + str(
                    VERSION))
            new_config = response.json()
            if response.status_code == 200:
                if image_screen.icon.source == OFFLINE_ICON:
                    show_icon(previous_icon, overwrite=True)
                if new_config != config:
                    global block_update
                    block_update = True
                    config = new_config
                    block_update = False
                    log.info('Updated config file: ' + str(config))
                    with open('config.json', 'w') as json_file:
                        json.dump(config, json_file)
            else:
                log.warning('Failed to get config, server returned code: ' + str(response.status_code))
        except Exception as e:
            if 'Max retries exceeded' in str(e):
                previous_icon = image_screen.icon.source
                show_icon(OFFLINE_ICON, overwrite=True)
            log.warning('Failed to update config: ' + str(e))
        sleep(15)

    while not stopped:
        _update_config()


kill_all_omx()
if config:
    image_screen.image.angle = 0 if config['config']['rotation'] < 180 else 180
    image_screen.icon.angle = 0 if config['config']['rotation'] < 180 else 180
    Thread(target=update_config).start()
    Clock.schedule_interval(update, 0.5)
    Clock.schedule_interval(update_media, 0.5)
else:
    log.critical('Missing config')
    show_image('missing_config.jpeg')


def on_key_up(window, something1, something2, text='', modifiers=[]):
    if media_type != 'manual' or text is None or not text.isnumeric():
        return
    splot = media.split(', ')
    if int(text) < len(splot):
        show_video(MEDIA_DIRECTORY + splot[int(text)], False)


Window.fullscreen = 'auto'
Window.bind(on_key_up=on_key_up)


class Display(App):

    def build(self):
        # Window.clearcolor = (0, 0, 0, 0.1)
        show_image(NO_MEDIA_IMAGE)
        # Window.opacity = 0
        return sm

    def on_start(self):
        if profiling:
            self.profile = cProfile.Profile()
            self.profile.enable()
        pass

    def on_stop(self):
        if profiling:
            self.profile.disable()
            self.profile.dump_stats('Display.profile')
        global stopped
        stopped = True
        if omx is not None:
            stop_video()
        if twitch is not None:
            twitch.kill()
        os._exit(69)


if __name__ == '__main__':
    Display().run()
