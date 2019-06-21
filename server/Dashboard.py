import dash_core_components as dcc
import dash_html_components as html
from dash.dependencies import Input, Output, State
from dash.exceptions import PreventUpdate
import dash
import base64
import dash_dangerously_set_inner_html
import dash_bootstrap_components as dbc
from flask import session, jsonify
import os
import json
import requests
import re
from Common import SCREEN_DIRECTORY, MEDIA_DIRECTORY, get_screens, get_media
from urllib.parse import urlparse
from datetime import datetime


# Save a file uploaded with the Upload component
def save_file(name, content):
    data = base64.b64decode(content.split(',')[1])
    with open(name, 'wb') as fp:
        fp.write(data)


# Returns True if string contains disallowed characters
def invalid_str(s):
    return re.findall(r'[^A-Za-z0-9_\-\\]', s)


def rotation_dropdown():
    return html.Div([
        html.H5('Counter-clockwise Rotation:', style={'margin': '0px 10px', 'display': 'inline-block'}),
        dcc.Dropdown(id='rotation-dropdown', options=[{'label': str(i * 90), 'value': i * 90} for i in range(4)],
                     value=0, style={'display': 'inline-block', 'width': '20%'})
    ])


def media_dropdown():
    medias = [{'label': media, 'value': media} for media in get_media()]
    return html.Div([
        html.H5('Media File:', style={'margin': '0px 10px', 'display': 'inline-block'}),
        dcc.Dropdown(id='media-dropdown', options=medias, value=medias[0]['value'],
                     style={'display': 'inline-block', 'width': '60%'})
    ])


def media_types_dropdown():
    return html.Div([
        html.H5('Media Type:', style={'margin': '0px 10px', 'display': 'inline-block'}),
        dcc.Dropdown(id='media-types-dropdown', options=[{'label': type, 'value': type} for type in
                                                         (['image', 'video', 'presentation', 'twitch', 'yelp',
                                                           'instagram',
                                                           'manual', 'countdown'] if session['login'] == 'admin' else [
                                                             'image', 'video'])],
                     value='image', style={'display': 'inline-block', 'width': '60%'})
    ])


def screen_dropdown():
    screens = [{'label': screen, 'value': screen} for screen in get_screens()]
    return html.Div([
        html.H5('Screens:', style={'margin': '0px 10px', 'display': 'inline-block'}),
        dcc.Dropdown(id='screen-dropdown', options=screens, multi=True,
                     style={'display': 'inline-block', 'width': '80%'})
    ])


# The group of components for adding new defaults
def add_defaults_screen():
    return html.Div([
        dcc.Upload(
            id='upload-media-files',
            children=html.Div([
                'Drag and Drop or ',
                html.A('Select media files')
            ]),
            style={
                'width': '100%',
                'height': '60px',
                'lineHeight': '60px',
                'borderWidth': '1px',
                'borderStyle': 'dashed',
                'borderRadius': '5px',
                'textAlign': 'center',
                'margin': '10px'
            },
            multiple=True
        ),
        # Todo: hide selected media label when nothing is selected
        html.H4('Selected Media:', style={'margin': '0px 10px', 'display': 'inline-block'}),
        html.H6('', id='selected-media', style={'display': 'inline-block'}),
        html.Div([
            html.H5('Select All Vertical Images:', style={'margin': '0px 10px', 'display': 'inline-block'}),
            dcc.Dropdown(id='vertical-image-dropdown', options=[], multi=True,
                         style={'display': 'inline-block', 'width': '80%'})
        ], id='vertical-image-dropdown-container', style={'display': 'none'}),
        html.Div(html.Button('Upload media', id='upload-media-button')),
        html.H4('Default Name: ', style={'margin': '0px 10px', 'display': 'inline-block'}),
        dcc.Input(id='default-name', style={'display': 'inline-block'}),
        media_types_dropdown(),
        media_dropdown(),
        screen_dropdown(),
        html.H4('Start Date and Time:', style={'margin': '0px 10px', 'display': 'inline-block'}),
        dcc.Input(id='default-date', type='datetime-local', value='2000-01-01T00:00:00', style={'display': 'inline'}),
        dbc.Tooltip('This is the changeover time for the new default media', target='default-date'),
        html.Div(html.Button('Create New Default', id='create-default-button'))
    ])


# Dashboard layout
layout = html.Div([
    # Header
    html.H1('Display System Dashboard', style={'display': 'inline'}),
    html.A(html.Button('Logout'), href='/logout', style={'float': 'right', 'display': 'inline'}),

    # Alerts
    dbc.Alert('', id='jar-alert', color='primary', dismissable=True, is_open=False),
    dbc.Alert('', id='create-screen-alert', color='primary', dismissable=True, is_open=False),
    dbc.Alert('', id='upload-media-alert', color='primary', dismissable=True, is_open=False),
    dbc.Alert('', id='create-default-alert', color='primary', dismissable=True, is_open=False),
    dbc.Alert('', id='create-default-callback-alert', color='primary', dismissable=True, is_open=False),
    dcc.ConfirmDialog(
        id='create-default-selection-alert',
        message='Are you sure there aren\'t and vertical images to select?',
    ),

    # Main content
    html.Div(id='main-content'),

    # "Global" data
    html.Div('0', id='create-default-confirms', style={'display': 'none'}),
    dcc.Location('location')

], style={'width': '500'})


# Setup all event handling and chaining
def register_callbacks(app):
    @app.callback(Output('main-content', 'children'),
                  [Input('location', 'href')])  # Could be changed to a different callback input, just for drawing page
    def render_content(url):
        if not url:
            raise PreventUpdate
        return [dcc.Tabs(id='tabs', value='tab-add', children=[
            dcc.Tab(label='Add', value='tab-add'),
            dcc.Tab(label='Event', value='tab-event'),
            dcc.Tab(label='Edit', value='tab-edit'),
            dcc.Tab(label='System', value='tab-system')
        ]), html.Div(id='tabs-content')
                ] if session['login'] == 'admin' else add_defaults_screen()

    # Render selected tab's content
    @app.callback(Output('tabs-content', 'children'),
                  [Input('tabs', 'value')])
    def render_tab_content(tab):
        if tab == 'tab-add':
            return add_defaults_screen()

        # Event tab
        elif tab == 'tab-event':
            return html.Div([
                html.H3('Tab content 2')
            ])

        # Edit tab
        elif tab == 'tab-edit':
            return html.Div([
                html.H3('Tab content 2')
            ])

        # System tab
        elif tab == 'tab-system':
            return html.Div([
                dcc.Upload(
                    id='upload-jar-file',
                    children=html.Div([
                        'Drag and Drop or ',
                        html.A('Select JAR file')
                    ]),
                    style={
                        'width': '100%',
                        'height': '60px',
                        'lineHeight': '60px',
                        'borderWidth': '1px',
                        'borderStyle': 'dashed',
                        'borderRadius': '5px',
                        'textAlign': 'center',
                        'margin': '10px'
                    },
                    multiple=False,
                    accept='.jar'
                ),
                html.H4('Selected File:', style={'margin': '0px 10px', 'display': 'inline-block'}),
                html.H4('', id='selected-file', style={'display': 'inline-block'}),
                dcc.ConfirmDialogProvider(children=html.Button('Upload JAR'), id='upload-jar-button',
                                          message='Warning: If you upload an invalid update file, this will brick the whole system'),
                html.H3('Add New Display'),
                html.H4('Display Name: ', style={'margin': '0px 10px', 'display': 'inline-block'}),
                dcc.Input(id='display-name', style={'display': 'inline-block'}),
                rotation_dropdown(),
                html.Button('Add Display', id='add-display-button')
            ])

    # Todo: Remove 'vert' from image names and classify accordingly
    # Display selected media file names
    @app.callback([Output('selected-media', 'children'),
                   Output('vertical-image-dropdown', 'options'),
                   Output('vertical-image-dropdown-container', 'style')],
                  [Input('upload-media-files', 'filename')])
    def select_media_file(filenames):
        if filenames is None:
            return [None, [], {'display': 'none'}]
        selected = '\''
        for file in filenames:
            selected = selected + file
            selected = selected + '\', \''
        selected = selected[:-3]
        image_options = [{'label': file, 'value': file} for file in filenames if
                         file.__contains__('.jpg') or file.__contains__('.png')]
        return [selected, image_options, {}]

    # Todo: combine callback functions
    # Upload selected media
    @app.callback(
        [Output('upload-media-alert', 'is_open'),
         Output('upload-media-alert', 'children'),
         Output('upload-media-alert', 'color'),
         Output('upload-media-files', 'filename'),
         Output('media-dropdown', 'options')],
        [Input('upload-media-button', 'n_clicks')],
        [State('upload-media-files', 'filename'),
         State('upload-media-files', 'contents'),
         State('vertical-image-dropdown', 'value'),
         State('vertical-image-dropdown', 'options'),
         State('media-dropdown', 'options')]
    )
    def upload_media(n_clicks, filenames, contents, verticals, images, medias):
        if not n_clicks:
            raise PreventUpdate
        if filenames is None or contents is None:
            return [True, 'Select media files first', 'warning', filenames, medias]
        # if images is not None and len(images) > 0 and verticals is None or len(verticals) == 0:
        #    return [False, '', '', filenames, medias, True]
        if save_media_files(filenames, contents, images, verticals):
            return [True, 'Uploaded media files. Displays will syncronize within 5 minutes', 'success', None,
                    [{'label': media, 'value': media} for media in get_media()]]
        else:
            return [True, 'Failed to upload media', 'danger', filenames, medias]

    # Todo: Move
    def save_media_files(filenames, contents, images, verticals):
        for name, content in zip(filenames, contents):
            if {'label': name, 'value': name} in images:
                if verticals is not None and name in verticals:
                    media_name = name + '_vertical'
                else:
                    media_name = name + '_horizontal'
            else:
                media_name = name
            try:
                save_file(os.path.join(MEDIA_DIRECTORY, media_name), content)
            except Exception as e:
                print(e)
                return False
        return True

    # Add a new default
    @app.callback([Output('create-default-alert', 'is_open'),
                   Output('create-default-alert', 'children'),
                   Output('create-default-alert', 'color')],
                  [Input('create-default-button', 'n_clicks')],
                  [State('screen-dropdown', 'value'),
                   State('default-name', 'value'),
                   State('media-dropdown', 'value'),
                   State('media-types-dropdown', 'value'),
                   State('default-date', 'value')])
    def create_default(n_clicks, screens, name, media, media_type, raw_date):
        if not n_clicks:
            raise PreventUpdate
        if not name:
            return [True, 'A default name must be specified', 'warning']
        if screens is None or len(screens) == 0:
            return [True, 'At least one screen must be selected', 'warning']
        for screen in screens:
            try:
                with open(os.path.join(SCREEN_DIRECTORY, screen)) as json_file:
                    config = json.load(json_file)
                config['defaults'].append({'name': name,
                                           'start_date_time': datetime.strptime(raw_date, '%Y-%m-%dT%H:%M:%S').strftime(
                                               '%m/%d/%Y %H:%M'), 'type': media_type, 'media': media})
                with open(os.path.join(SCREEN_DIRECTORY, screen), 'w') as json_file:
                    json.dump(config, json_file)
                print('New config: ' + str(config))
            except Exception as e:
                print(e)
                return [True, 'Failed to update all screen configurations. System is in an unknown state.', 'warning']
        return [True, 'Successfully created new default', 'success']

    # Show selected update file name
    @app.callback(
        Output('selected-file', 'children'), [Input('upload-jar-file', 'filename')]
    )
    def select_file(filename):
        if filename is None:
            return ''
        else:
            return filename

    # Upload update file
    @app.callback(
        [Output('jar-alert', 'is_open'),
         Output('jar-alert', 'children'),
         Output('jar-alert', 'color')],
        [Input('upload-jar-button', 'submit_n_clicks')],
        [State('upload-jar-file', 'filename'),
         State('upload-jar-file', 'contents')]
    )
    def upload_jar(submit_n_clicks, filename, content):
        if not submit_n_clicks:
            raise PreventUpdate
        if filename is not None and content is not None:
            if not filename.endswith('.jar'):
                return [True, 'This has to be a jar file', 'warning']
            try:
                save_file('escreen.jar', content)
            except Exception as e:
                print(e)
                return [True, 'Failed to update JAR', 'danger']
        else:
            return [True, 'Select a JAR file first', 'secondary']
        return [True, 'Uploaded JAR file. Displays will update within 5 minutes', 'success']

    # Add a new display
    @app.callback([Output('create-screen-alert', 'is_open'),
                   Output('create-screen-alert', 'children'),
                   Output('create-screen-alert', 'color')],
                  [Input('add-display-button', 'n_clicks')],
                  [State('display-name', 'value'),
                   State('rotation-dropdown', 'value')])
    def add_display(n_clicks, name, rotation):
        if not n_clicks:
            raise PreventUpdate
        if not name:
            return [True, 'A screen name is required', 'secondary']
        if invalid_str(name):
            return [True, 'Invalid screen name', 'warning']
        screen_json = {'config': {'name': name, 'rotation': rotation}, 'defaults': [],
                       'events': [],
                       'fallback': {'name': 'fallback', 'type': 'image', 'media': 'fallback.png'}}
        try:
            with open(os.path.join(SCREEN_DIRECTORY, name), 'w') as json_file:
                json.dump(screen_json, json_file)
        except Exception as e:
            print(e)
            return [True, 'Failed create screen', 'danger']
        return [True, 'Successfully created screen', 'success']
