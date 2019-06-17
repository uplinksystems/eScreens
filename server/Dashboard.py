from flexx import flx

main = None
types = ['image', 'video', 'presentation', 'twitch', 'yelp', 'instagram', 'manual', 'countdown']
rotations = [0, 90, 180, 270]
max_scheduled = 25 # Maximum scheduable content entries
screen_num = 40 # Overestimate by a few, number to total displays
screens =[]
medias = []
url = ''


def ensure_str(s):
    if isinstance(s, str):
        return s
    return ''


def ensure_int(number, default_value=0):
    if isinstance(number, int):
        return number
    return default_value


class Root(flx.Widget):
    CSS = """
    .flx-Button {
        background: #9d9;
    }
    .flx-LineEdit {
        border: 2px solid #9d9;
    }
    """

    screens = []

    def init(self):
        global main
        main = self
        global url
        url = window.location['origin']
        print(url)
        self.update_screen_list()
        self.update_media_list()
        with flx.FormLayout():
            with flx.HSplit():
                self.logout = flx.Button(title='logout', text='Logout', flex=1)
                flx.Widget(flex=5)
                self.new_dashboard = flx.Button(title='new_dashboard', text='New Dashboard', flex=1)
            with flx.TabLayout(flex=5):
                EditDisplay(title='Edit a Display')
                Defaults(title='Modify Defaults')
                Events(title='Modify Events')
                System(title='System')
            self.edit_media = EditMedia(flex=2)

    @flx.reaction('logout.pointer_click')
    def log_out(self, *events):
        window.location.href = url + '/logout'

    @flx.reaction('new_dashboard.pointer_click')
    def open_new_dashboard(self, *events):
        window.location.href = url + '/dashboard'

    def send_request(self, type, url, data, content_type='text/plain'):
        global window
        request = window.XMLHttpRequest()
        request.withCredentials = True
        request.open(type, url, False)
        request.setRequestHeader('Content-type', content_type)  # application/json
        request.send(data)
        return request

    def upload_file(self, url, file):
        formData = window.FormData()
        formData.append('file', file)
        request = window.XMLHttpRequest()
        request.open('POST', url, False)
        request.send(formData)

    def update_screen_list(self):
        request = self.send_request('GET', url + '/screen', '')
        if request.readyState == 4 and not request.status == 200:
            window.alert('Failed to load screen list. Code: ' + request.status + ', Response: ' + request.responseText)
            return
        global screens
        screens = window.JSON.parse(request.responseText)

    def update_media_list(self):
        request = self.send_request('GET', url + '/media', '')
        if request.readyState == 4 and not request.status == 200:
            window.alert(
                'Failed to load media list. Code: ' + request.status + ', Response: ' + request.responseText)
            return
        global medias
        medias = window.JSON.parse(request.responseText)


class EditDisplay(flx.Widget):
    CSS = """
    .flx-Button {
        background: #9d9;
    }
    .flx-LineEdit {
        border: 2px solid #9d9;
    }
    """

    def init(self):
        self.json = None
        with flx.FormLayout() as self.form:
            self.name = flx.ComboBox(title='Display Name:', options=screens)
            self.rotation = flx.ComboBox(title='Rotation:', options=rotations)
            flx.Widget(flex=1)
            with flx.TreeWidget(flex=2, title='Defaults:', max_selected = 1):
                self.defaults = []
                for i in range(max_scheduled):
                    self.defaults[i] = flx.TreeItem(title=str(i), checked=False)
                    self.defaults[i].set_visible(False)
            with flx.TreeWidget(flex=2, title='Events:', max_selected = 1):
                self.events = []
                for i in range(max_scheduled):
                    self.events[i] = flx.TreeItem(title=str(i), checked=False)
                    self.events[i].set_visible(False)
            self.upload = flx.Button(text='Save and Upload')
            flx.Widget(flex=5)

    @flx.reaction('name.user_selected')
    def _select_screen(self, *events):
        global window
        request = main.send_request('GET', url + '/screen' + self.name.text, '')
        if request.readyState == 4 and not request.status == 200:
            window.alert('Failed to load config. Code: ' + request.status + ', Response: ' + request.responseText)
            return
        self.json = window.JSON.parse(request.responseText)
        print(window.JSON.stringify(self.json))
        self.rotation.set_selected_index(rotations.index((self.json['config']['rotation'])))
        main.edit_media.show_media(self.json['fallback'], False)
        for i in range(max_scheduled):
            self.defaults[i].set_visible(False)
        i = 0
        for media in self.json['defaults']:
            self.defaults[i].set__visible(True)
            self.defaults[i].set_text('a')
            i = i + 1


    @flx.reaction('upload.pointer_click')
    def _upload(self, *events):
        global window
        if not self.rotation.text.isdigit():
            window.alert('Invalid values')
            return
        if self.json is None:
            if window.confirm(
                    'Are you sure you want to push this file? If you forgot to pull, this will overwrite the existing file and erase the existing schedule.'):
                self.json = {'config': {'name': self.name.text, 'rotation': int(self.rotation.text)}, 'defaults': [],
                             'events': [],
                             'fallback': {'name': 'fallback', 'type': 'image', 'media': 'fallback.png'}}
        else:
            if not self.name.text == self.json['config']['name'] and not window.confirm('Are you sure you want to create a new config file? You cannot change the name of a display without modifying the display itself'):
                return
            if self.name.text.search(window.RegExp(r'[^A-Za-z0-9_\-\\]','g')) != -1:
                window.alert('Invalid display name')
                return
            self.json['config']['name'] = self.name.text
            self.json['config']['rotation'] = int(self.rotation.text)
        data = window.JSON.stringify(self.json)

        request = main.send_request('PUT', url + '/screen/' + self.name.text, data)
        if request.readyState == 4 and not request.status == 200:
            window.alert('Failed to update config. Code: ' + request.status + ', Response: ' + request.responseText)
        else:
            window.alert('Successfully updated or added config file for display')


class Events(flx.Widget):
    CSS = """
    .flx-Button {
        background: #9d9;
    }
    .flx-LineEdit {
        border: 2px solid #9d9;
    }
    """

    def init(self):
        with flx.TreeWidget(flex=2, title='Events:'):
            self.events = []
            for i in range(max_scheduled):
                self.events[i] = flx.TreeItem(title=str(i), checked=False)
                self.events[i].set_visible(False)


class Defaults(flx.Widget):
    CSS = """
    .flx-Button {
        background: #9d9;
    }
    .flx-LineEdit {
        border: 2px solid #9d9;
    }
    """

    def init(self):
        with flx.FormLayout():
            with flx.TreeWidget(flex=2, title='Defaults:'):
                self.defaults = []
                for i in range(max_scheduled):
                    self.defaults[i] = flx.TreeItem(checked=False)
                    self.defaults[i].set_visible(False)
            flx.Widget(flex=1)
            with flx.TreeWidget(title='Screens', max_selected=0) as self.screens:
                self.screens = []
                for i in range(screen_num):
                    self.screens[i] = flx.TreeItem(checked=False)
                    self.screens[i].set_visible(False)
                self.update_screens()
            self.add_button = flx.Button(text='Add New Default')

    @flx.reaction('add_button.pointer_click')
    def set_screens(self, *events):
        self.update_screens()

    def update_screens(self):
        i = 0
        for screen in screens:
            self.screens[i].set_visible(True)
            self.screens[i].set_text(screen)
            i = i + 1

    @flx.reaction('add_button.pointer_click')
    def add_default(self, *events):
        pass


class System(flx.Widget):
    CSS = """
    .flx-Button {
        background: #9d9;
    }
    .flx-LineEdit {
        border: 2px solid #9d9;
    }
    """

    def init(self):
        with flx.FormLayout() as self.form:
            self.update_button = flx.Button(text='Update JAR')

    @flx.reaction('update_button.pointer_click')
    def on_browse(self, *events):
        input = window.document.createElement('input')
        input.type = 'file'

        def on_select_file(e):
            file = e.target.files[0]
            main.upload_file(url + '/update', file)
            window.alert('Uploaded file')
            # update media after 1 second
            main.update_media_list()
            self.media.set_options(medias)

        input.onchange = on_select_file
        input.click()

class EditMedia(flx.Widget):
    CSS = """
    .flx-Button {
        background: #9d9;
    }
    .flx-LineEdit {
        border: 2px solid #9d9;
    }
    """

    def init(self):
        with flx.FormLayout() as self.form:
            self.browse = flx.Button(text='Select Media File to Upload')
            self.name = flx.LineEdit(title='Name of Event:', text='')
            self.type = flx.ComboBox(title='Type of Media', options=types, selected_index=0)
            self.media = flx.ComboBox(title='Media File:', options=medias)
            # flx.Widget(flex=3)

    def show_media(self, media, editable):
        self.name.set_text(media['name'])
        self.type.set_selected_index(types.index(media['type']))
        self.media.set_text(media['media'])
        #self.name.set_disabled(not editable)
        #self.media.set_disabled(not editable)
        # self.type.set_editable(editable)

    @flx.reaction('browse.pointer_click')
    def on_browse(self, *events):
        input = window.document.createElement('input')
        input.type = 'file'

        def on_select_file(e):
            file = e.target.files[0]
            main.upload_file(url + '/media/' + file.name, file)
            window.alert('Uploaded file')
            # update media after 1 second
            main.update_media_list()
            self.media.set_options(medias)
        input.onchange = on_select_file
        input.click()


if __name__ == '__main__':
    a = flx.App(Root, title='Display interface')
    m = a.launch()
    flx.run()
