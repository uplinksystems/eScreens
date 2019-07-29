import dash_core_components as dcc
import dash_html_components as html
from dash.dependencies import Input, Output, State
from dash.exceptions import PreventUpdate
import dash
import base64
import dash_bootstrap_components as dbc
from flask import session, jsonify
import os
import json
import requests
import re
from Common import SCREEN_DIRECTORY, MEDIA_DIRECTORY, get_screens, get_media
from urllib.parse import urlparse
from datetime import datetime
from dash_callback_router import PartialUpdate
import dash_callback_router
import logging


# Save a file uploaded with the Upload component
def save_file(name, content):
    data = base64.b64decode(content.split(',')[1])
    with open(name, 'wb') as fp:
        fp.write(data)


# Returns True if string contains disallowed characters for screen names
def invalid_screen_str(s):
    return re.findall(r'[^ A-Za-z0-9_\-\\]', s)


# Todo: Pass in id parameters for reusable element functions
def rotation_dropdown():
    return html.Div([
        html.H6('Counter-clockwise Rotation:',
                style={'margin': '0px 10px 0px 0px', 'vertical-align': 'middle'}),
        dcc.Dropdown(id='rotation-dropdown', clearable=False, searchable=False,
                     options=[{'label': str(i * 90), 'value': i * 90} for i in range(4)],
                     value=0, style={'margin': '0px 20px 0px 0px', 'flex': 1,
                                     'vertical-align': 'middle'})
    ], style={'display': 'flex', 'margin': '5px 10px', 'flex-direction': 'row', 'width': '100%',
              'align-items': 'stretch'})


def media_dropdown():
    medias = [{'label': media, 'value': media} for media in get_media()]
    return html.Div([
        html.H6('Media File:',
                style={'margin': '0px 100px 0px 0px', 'vertical-align': 'middle'}),
        dcc.Dropdown(id='media-dropdown', placeholder='Select media to display', clearable=False, searchable=False,
                     options=medias, value='',
                     style={'margin': '0px 20px 0px 0px', 'flex': 1,
                            'vertical-align': 'middle'}),
        dbc.Tooltip('This is for selecting the graphic to show.', target='media-dropdown')
    ], style={'display': 'flex', 'margin': '5px 10px', 'flex-direction': 'row', 'width': '100%',
              'align-items': 'stretch'})


def media_types_dropdown():
    return html.Div([
        html.H6('Media Type:',
                style={'margin': '0px 90px 0px 0px', 'vertical-align': 'middle'}),
        dcc.Dropdown(id='media-types-dropdown', clearable=False, searchable=False, options=[],
                     value='image', style={'margin': '0px 20px 0px 0px', 'flex': 1,
                                           'vertical-align': 'middle'}),
        dbc.Tooltip('This is for selecting the type of graphic to display.', target='media-types-dropdown')
    ], style={'display': 'flex', 'margin': '5px 10px', 'flex-direction': 'row', 'width': '100%',
              'align-items': 'stretch'})


def screen_dropdown():
    screens = [{'label': screen, 'value': screen} for screen in get_screens()]
    return html.Div([
        html.H6('Screen Locations:',
                style={'margin': '0px 40px 0px 0px', 'vertical-align': 'middle'}),
        dcc.Dropdown(id='screen-dropdown', placeholder='Select screens to show media on', searchable=False,
                     options=screens, multi=True,
                     style={'margin': '0px 20px 0px 0px', 'flex': 1,
                            'vertical-align': 'middle'}),
        dbc.Tooltip('This is for selecting the screens to show the new graphic on.', target='screen-dropdown')
    ], style={'display': 'flex', 'margin': '5px 10px', 'flex-direction': 'row', 'width': '100%',
              'align-items': 'stretch'})


# The group of components for adding new defaults
def add_defaults_screen():
    date = datetime.now().strftime('%Y-%m-%dT%H:%M')

    return html.Div([
        html.Div(style={'margin': '20px 0px'}),
        media_types_dropdown(),
        # Todo: filter out images from other types for when image type is selected in dropdown
        media_dropdown(),
        html.Div([html.Img(id='default-preview-image-horizontal',
                           style={'height': '20%', 'width': '40%', 'display': 'inline-bock'}),
                  html.Img(id='default-preview-image-vertical',
                           style={'height': '25%', 'width': '22%', 'display': 'inline-bock'},
                           className='rotateimgvertical')
                  ], id='default-preview-images', style={'display': 'none'}),
        screen_dropdown(),
        html.Div([html.H6('Start Date and Time:', style={'margin': '0px 23px 0px 0px', 'vertical-align': 'middle'}),
                  dcc.Input(id='default-date', type='datetime-local', value=date,
                            style={'margin': '0px 20px 0px 0px', 'flex': 1, 'vertical-align': 'middle'})],
                 style={'display': 'flex', 'margin': '5px 10px', 'flex-direction': 'row', 'width': '100%',
                        'align-items': 'stretch'}),
        dbc.Tooltip('This is the changeover time for the new graphic to display.', target='default-date'),
        html.Div([html.H6('Graphic Name:', style={'margin': '0px 66px 0px 0px', 'vertical-align': 'middle'}),
                  dcc.Input(id='default-name',
                            style={'margin': '0px 20px 0px 0px', 'flex': 1, 'vertical-align': 'middle'})],
                 style={'display': 'flex', 'margin': '5px 10px', 'flex-direction': 'row', 'width': '100%',
                        'align-items': 'stretch'}),
        dbc.Tooltip('This is the name for the new graphic to display.', target='default-name'),
        html.Div(html.Button('Create New Configuration', id='create-default-button', style={'width': '100%'}),
                 style={'margin': 'auto', 'width': '60%', 'align-items': 'stretch'})
    ], id='add-pane', style={'display': 'none'})


def add_upload_screen():
    return html.Div([
        html.Div([html.H4('Media Upload Type: ', style={'margin': '0px 23px 0px 0px', 'vertical-align': 'middle'}),
                  dcc.Dropdown(id='upload-types-dropdown', clearable=False, searchable=False,
                               options=[{'label': type, 'value': type} for type in ['image', 'file']],
                               value='image',
                               style={'margin': '0px 20px 0px 0px', 'flex': 1, 'vertical-align': 'middle'})],
                 style={'display': 'flex', 'margin': '5px 10px', 'flex-direction': 'row', 'width': '100%',
                        'align-items': 'stretch'}),

        # Image upload panel
        html.Div([
            html.Div([html.H4('Image Name:', style={'margin': '0px 85px 0px 0px', 'vertical-align': 'middle'}),
                      dcc.Input(id='image-name',
                                style={'margin': '0px 20px 0px 0px', 'flex': 1, 'vertical-align': 'middle'})],
                     style={'display': 'flex', 'margin': '5px 10px', 'flex-direction': 'row', 'width': '100%',
                            'align-items': 'stretch'}),
            dcc.Upload(id='upload-horizontal-image',
                       children=html.Div([html.A('Select horizontal image', id='horizontal-image-label')],
                                         style={'textAlign': 'center'}),
                       style={'width': '99%', 'height': '60px', 'lineHeight': '60px', 'borderWidth': '1px',
                              'borderStyle': 'dashed', 'borderRadius': '5px', 'display': 'inline-block',
                              'margin': '5px'},
                       multiple=False, accept='image/*'),
            dcc.Upload(id='upload-vertical-image',
                       children=html.Div(
                           [html.A('Select vertical image', id='vertical-image-label')], style={'textAlign': 'center'}),
                       style={'width': '99%', 'height': '60px', 'lineHeight': '60px', 'borderWidth': '1px',
                              'borderStyle': 'dashed', 'borderRadius': '5px', 'display': 'inline-block',
                              'margin': '5px'},
                       multiple=False, accept='image/*'),
        ], id='image-upload-container'),

        # Media upload panel
        html.Div([
            dcc.Upload(id='upload-media-files', children=html.Div(['Drag and Drop or ', html.A('Select media files')]),
                       style={'width': '100%', 'height': '60px', 'lineHeight': '60px', 'borderWidth': '1px',
                              'borderStyle': 'dashed', 'borderRadius': '5px', 'textAlign': 'center', 'margin': '10px'},
                       multiple=True),
            html.Div([html.H4('Selected Media:', style={'margin': '0px 10px', 'display': 'inline-block'}),
                      html.H6('', id='selected-media', style={'display': 'inline-block'})],
                     id='media-selection-container', style={'display': 'none'})
        ], id='media-upload-container', style={'display': 'none'}),

        # Todo: hide selected media label when nothing is selected
        html.Div(html.Button('Upload Media', id='upload-media-button', style={'width': '100%'}),
                 style={'margin': 'auto', 'width': '60%', 'align-items': 'stretch'})
    ], id='upload-pane')


# Dashboard layout
layout = html.Div([
    # Header
    html.Div([html.H1('Display System Dashboard',
                      style={'display': 'inline-block', 'flex': 1, 'vertical-align': 'middle'}),
              html.A(html.Button('Logout'), href='/logout',
                     style={'display': 'inline', 'vertical-align': 'middle', 'margin': '0px 20px'})],
             style={'display': 'flex', 'margin': '5px 10px', 'flex-direction': 'row', 'width': '100%',
                    'align-items': 'stretch'}),

    # Alerts
    dbc.Alert('', id='jar-alert', color='primary', dismissable=True, is_open=False),
    dbc.Alert('', id='create-screen-alert', color='primary', dismissable=True, is_open=False),
    dbc.Alert('', id='upload-media-alert', color='primary', dismissable=True, is_open=False),
    dbc.Alert('', id='create-default-alert', color='primary', dismissable=True, is_open=False),
    dbc.Alert('', id='create-default-callback-alert', color='primary', dismissable=True, is_open=False),
    dcc.ConfirmDialog(id='confirm-dialog', message=''),

    dcc.Tabs(id='tabs', value='tab-upload', children=[
        dcc.Tab(label='Upload New Media', value='tab-upload'),
        dcc.Tab(label='Configure Media', value='tab-add'),
        dcc.Tab(label='Add Event', value='tab-event'),
        dcc.Tab(label='Edit', value='tab-edit'),
        dcc.Tab(label='System', value='tab-system')], style={'margin': '0px 10px'}),

    # Main content
    html.Div([
        add_upload_screen(),
        add_defaults_screen(),

        html.Div([
            html.H4('Event')
        ], id='event-pane', style={'display': 'none'}),

        html.Div([
            html.H4('Edit')
        ], id='edit-pane', style={'display': 'none'}),

        html.Div([
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
                                      message='Warning: If you upload an invalid update file, '
                                              'this will brick the whole system'),
            html.H3('Add New Display'),
            html.H4('Display Name: ', style={'margin': '0px 10px', 'display': 'inline-block'}),
            dcc.Input(id='display-name', style={'display': 'inline-block'}),
            rotation_dropdown(),
            html.Button('Add Display', id='add-display-button')
        ], id='system-pane', style={'display': 'none'})
    ]),

    # "Global" data
    html.Div('0', id='create-default-confirms', style={'display': 'none'}),
    dcc.Location('location')

], style={'width': '500'})


# Setup all event handling and chaining
def register_callbacks(app):
    # Render selected tab's content
    @app.callback([Output('upload-pane', 'style'),
                   Output('add-pane', 'style'),
                   Output('event-pane', 'style'),
                   Output('edit-pane', 'style'),
                   Output('system-pane', 'style')],
                  [Input('tabs', 'value')])
    def render_tab_content(tab):
        if tab == 'tab-upload':
            return {}, {'display': 'none'}, {'display': 'none'}, {'display': 'none'}, {'display': 'none'}
        elif tab == 'tab-add':
            return {'display': 'none'}, {}, {'display': 'none'}, {'display': 'none'}, {'display': 'none'}
        elif tab == 'tab-event':
            return {'display': 'none'}, {'display': 'none'}, {}, {'display': 'none'}, {'display': 'none'}
        elif tab == 'tab-edit':
            return {'display': 'none'}, {'display': 'none'}, {'display': 'none'}, {}, {'display': 'none'}
        elif tab == 'tab-system':
            return {'display': 'none'}, {'display': 'none'}, {'display': 'none'}, {'display': 'none'}, {}

    # Display selected upload panel for media type
    @app.callback([Output('image-upload-container', 'style'),
                   Output('media-upload-container', 'style')],
                  [Input('upload-types-dropdown', 'value')])
    def select_upload_type(upload_type):
        if upload_type == 'image':
            return {}, {'display': 'none'}
        else:
            return {'display': 'none'}, {}

    # Display selected image names
    @app.callback([Output('horizontal-image-label', 'children'),
                   Output('vertical-image-label', 'children')],
                  [Input('upload-horizontal-image', 'contents'),
                   Input('upload-vertical-image', 'contents')],
                  [State('upload-horizontal-image', 'filename'),
                   State('upload-vertical-image', 'filename')])
    def select_media_file(cont_h, cont_v, horizontal, vertical):
        return 'Horizontal image: \'{}\''.format(
            horizontal) if horizontal else 'Select horizontal image', 'Vertical image: \'{}\''.format(
            vertical) if vertical else 'Select vertical image'

    # Display selected media file names
    @app.callback([Output('selected-media', 'children'),
                   Output('media-selection-container', 'style')],
                  [Input('upload-media-files', 'contents')],
                  [State('upload-media-files', 'filename')])
    def select_media_file(contents, filenames):
        if filenames is None:
            return [None, {'display': 'none'}]
        selected = '\''
        for file in filenames:
            selected = selected + file
            selected = selected + '\', \''
        selected = selected[:-3]
        return [selected, {}]

    # Upload selected media
    @app.callback([Output('upload-media-alert', 'is_open'),
                   Output('upload-media-alert', 'children'),
                   Output('upload-media-alert', 'color'),
                   Output('upload-media-files', 'filename'),
                   Output('upload-vertical-image', 'filename'),
                   Output('upload-horizontal-image', 'filename'),
                   Output('media-dropdown', 'options'),
                   Output('confirm-dialog', 'message'),
                   Output('confirm-dialog', 'displayed'),
                   Output('horizontal-image-label', 'children'),
                   Output('vertical-image-label', 'children'),
                   Output('image-name', 'value')],
                  [Input('upload-media-button', 'n_clicks'),
                   Input('confirm-dialog', 'submit_n_clicks')],
                  [State('upload-media-files', 'filename'),
                   State('upload-media-files', 'contents'),
                   State('upload-horizontal-image', 'contents'),
                   State('upload-vertical-image', 'contents'),
                   State('upload-horizontal-image', 'filename'),
                   State('upload-vertical-image', 'filename'),
                   State('upload-types-dropdown', 'value'),
                   State('image-name', 'value')])
    def upload_media(n_clicks, submit_n_clicks, media_filenames, media_contents, horizontal_image, vertical_image,
                     horizontal_name,
                     vertical_name, upload_type,
                     image_name):
        # Todo: clear non-image files from selection after upload
        if not n_clicks:
            raise PreventUpdate
        if upload_type == 'image':
            if not horizontal_name and not vertical_name:
                send_alert('upload-media-alert', 'Neither a horizontal nor a vertical image have been selected',
                           'warning')
            if (not horizontal_name or not vertical_name) and not check_confirm():
                send_confirm(
                    'Are you sure you only want to upload a {} image? If there are {} screens, '
                    'they won\'t have media to display'.format(
                        'vertical' if not horizontal_name else 'horizontal',
                        'horizontal' if not horizontal_name else 'vertical'))
            if not image_name:
                send_alert('upload-media-alert', 'An image name must be specified', 'warning')
            if invalid_screen_str(image_name):
                send_alert('upload-media-alert', 'Invalid image name entered', 'warning')
            try:
                if horizontal_name:
                    save_file(
                        os.path.join(MEDIA_DIRECTORY, image_name + '_horizontal.' + horizontal_name.split('.')[1]),
                        horizontal_image)
                if vertical_name:
                    save_file(os.path.join(MEDIA_DIRECTORY, image_name + '_vertical.' + vertical_name.split('.')[1]),
                              vertical_image)
            except Exception as e:
                logging.exception(e)
                send_alert('upload-media-alert', 'Failed to upload image', 'danger')
        else:
            if media_filenames is None or media_contents is None:
                send_alert('upload-media-alert', 'A file must be specified first', 'warning')
            for name, content in zip(media_filenames, media_contents):
                try:
                    save_file(os.path.join(MEDIA_DIRECTORY, name), content)
                except Exception as e:
                    logging.exception(e)
                    send_alert('upload-media-alert', 'Failed to upload media: \'{}\''.format(name), 'danger')
        return [True, 'Uploaded media files. Displays will syncronize within 5 minutes', 'success', None, None, None,
                [{'label': media, 'value': media} for media in get_media()], '', False, 'Select horizontal image',
                'Select vertical image', '']

    # Check if current callback is a result of a prompt confirmation
    # Compare message content afterwards to confirm it's the correct prompt if multiple are used in a callback
    def check_confirm():
        for triggered in dash.callback_context.triggered:
            if triggered['prop_id'] == 'confirm-dialog.submit_n_clicks':
                return True
        return False

    # Append confirm values to partial update dict
    def send_confirm(message, update_dict=None):
        if update_dict is None:
            update_dict = {}
        update_dict['confirm-dialog.message'] = message
        update_dict['confirm-dialog.displayed'] = True
        raise PartialUpdate(update_dict)

    # Append alert values to partial update dict
    def send_alert(alert, message, color, update_dict=None):
        if update_dict is None:
            update_dict = {}
        update_dict[alert + '.color'] = color
        update_dict[alert + '.children'] = message
        update_dict[alert + '.is_open'] = True
        raise PartialUpdate(update_dict)

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
            return [True, 'A graphic name must be specified', 'warning']
        if not media:
            return [True, 'Media content must be specified', 'warning']
        if screens is None or len(screens) == 0:
            return [True, 'At least one screen must be selected', 'warning']
        for screen in screens:
            try:
                with open(os.path.join(SCREEN_DIRECTORY, screen.replace(' ', '_') + '.json')) as json_file:
                    config = json.load(json_file)

                # Remove if name is already present
                # Todo: Check if this is the desired behavior
                remove_index = -1
                for i in range(len(config['defaults'])):
                    if config['defaults'][i]['name'] == name:
                        remove_index = i
                if not remove_index == -1:
                    config['defaults'].pop(remove_index)

                config['defaults'].append({'name': name,
                                           'start_date_time': datetime.strptime(raw_date, '%Y-%m-%dT%H:%M' if len(
                                               raw_date) == 16 else '%Y-%m-%dT%H:%M:%S').strftime(
                                               '%m/%d/%Y %H:%M'), 'type': media_type, 'media': media})
                with open(os.path.join(SCREEN_DIRECTORY, screen.replace(' ', '_') + '.json'), 'w') as json_file:
                    json.dump(config, json_file)
                    logging.info('New config: ' + str(config))
            except Exception as e:
                logging.warning('Failed to update config: ' + str(screen))
                logging.exception(e)
                return [True, 'Failed to update all screen configurations. System is in an unknown state.', 'danger']
        return [True, 'Successfully created new default', 'success']

    # Show selected update file name
    @app.callback(Output('selected-file', 'children'), [Input('upload-jar-file', 'filename')])
    def select_file(filename):
        if filename is None:
            return ''
        else:
            return filename

    # Preview images
    @app.callback([Output('default-preview-image-horizontal', 'src'),
                   Output('default-preview-image-vertical', 'src'),
                   Output('default-preview-images', 'style')],
                  [Input('media-types-dropdown', 'value'),
                   Input('media-dropdown', 'value')])
    def preview_image(type, media):
        if type == 'image':
            media_parts = media.split('.')
            if os.path.isfile(os.path.join(MEDIA_DIRECTORY, media_parts[0] + '_horizontal.' + media_parts[1])):
                horizontal = '/media/' + media_parts[0] + '_horizontal.' + media_parts[1]
            else:
                horizontal = '/static/horizontal_missing.png'
            if os.path.isfile(os.path.join(MEDIA_DIRECTORY, media_parts[0] + '_vertical.' + media_parts[1])):
                vertical = '/media/' + media_parts[0] + '_vertical.' + media_parts[1]
            else:
                vertical = '/static/vertical_missing.png'
            return horizontal, vertical, {}
        else:
            return '', '', {'display': 'none'}

    # Upload update file
    @app.callback([Output('jar-alert', 'is_open'),
                   Output('jar-alert', 'children'),
                   Output('jar-alert', 'color')],
                  [Input('upload-jar-button', 'submit_n_clicks')],
                  [State('upload-jar-file', 'filename'),
                   State('upload-jar-file', 'contents')])
    def upload_jar(submit_n_clicks, filename, content):
        if not submit_n_clicks:
            raise PreventUpdate
        if filename is not None and content is not None:
            if not filename.endswith('.jar'):
                return [True, 'This has to be a jar file', 'warning']
            try:
                save_file('escreen.jar', content)
            except Exception as e:
                logging.exception(e)
                return [True, 'Failed to update JAR', 'danger']
        else:
            return [True, 'Select a JAR file first', 'secondary']
        return [True, 'Uploaded JAR file. Displays will update within 5 minutes', 'success']

    # Add a new display
    @app.callback([Output('create-screen-alert', 'is_open'),
                   Output('create-screen-alert', 'children'),
                   Output('create-screen-alert', 'color'),
                   Output('screen-dropdown', 'options')],
                  [Input('add-display-button', 'n_clicks')],
                  [State('display-name', 'value'),
                   State('rotation-dropdown', 'value')])
    def add_display(n_clicks, name, rotation):
        if not n_clicks:
            raise PreventUpdate
        if not name:
            return [True, 'A screen name is required', 'secondary']
        if invalid_screen_str(name):
            return [True, 'Invalid screen name', 'warning']
        screen_json = {'config': {'name': name, 'rotation': rotation}, 'defaults': [],
                       'events': [],
                       'fallback': {'name': 'fallback', 'type': 'image', 'media': 'fallback.png'}}
        try:
            with open(os.path.join(SCREEN_DIRECTORY, name.replace(' ', '_') + '.json'), 'w') as json_file:
                json.dump(screen_json, json_file)
        except Exception as e:
            logging.exception(e)
            # Todo: Replace with partial updates and a call to a function to handle setting alert parameters by name
            return [True, 'Failed create screen', 'danger',
                    [{'label': media, 'value': media} for media in get_screens()]]
        return [True, 'Successfully created screen', 'success',
                [{'label': media, 'value': media} for media in get_screens()]]

    # Last callback gets called with None or dummy arguments when page loads
    @app.callback([Output('tabs', 'children'),
                   Output('media-types-dropdown', 'options')],
                  [Input('location', 'href')])
    def initialize(url):
        if session['login'] == 'admin':
            return [
                       dcc.Tab(label='Upload New Media', value='tab-upload'),
                       dcc.Tab(label='Configure Media', value='tab-add'),
                       dcc.Tab(label='Add Event', value='tab-event'),
                       dcc.Tab(label='Edit', value='tab-edit'),
                       dcc.Tab(label='System', value='tab-system')], [{'label': type, 'value': type} for type in
                                                                      ['image', 'video', 'presentation', 'twitch',
                                                                       'yelp', 'instagram', 'manual', 'countdown']]
        else:
            return [dcc.Tab(label='Upload New Media', value='tab-upload'),
                    dcc.Tab(label='Configure Media', value='tab-add')], [{'label': type, 'value': type} for type in
                                                                         ['image', 'video']]


if __name__ == '__main__':
    app = dash.Dash(__name__)
    app.layout = layout
    callback_router = dash_callback_router.CallbackRouter(app, True)
    register_callbacks(app)
    callback_router.register_callbacks()
    app.run_server(debug=True)
