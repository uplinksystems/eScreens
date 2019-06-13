from flexx import flx, event


main = None
types = ['image', 'video', 'presentation', 'twitch', 'yelp', 'instagram', 'manual']
rotations = [0, 90, 180, 270]

class Interface(flx.Widget):
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
        # Todo: catch errors if not connected
        self.update_screen_names()
        with flx.FormLayout():
            with flx.TabLayout(flex=5):
                EditDisplay(title='Edit a Display')
                AddDefault(title='Add a Default')
                RemoveDefault(title='Remove a Default')
                AddEvent(title='Add an Event')
                RemoveEvent(title='Remove an Event')
            self.edit_media = EditMedia(flex=2)

    # noinspection PyUnresolvedReferences
    def send_request(self, type, url, data, callback):
        request = window.XMLHttpRequest()

        #def request_callback():
            #callback(request)

        request.open(type, url, False)
        request.setRequestHeader('Content-type', 'text/plain')  # application/json
        request.setRequestHeader("Authorization", "Basic " + window.btoa("username:password"))
        #request.onreadystatechange = request_callback
        request.send(data)
        return request

    # noinspection PyUnresolvedReferences
    def update_screen_names(self):
        self.send_request('GET', 'http://localhost:5000/screen', '', self.update_screen_callback)

    # noinspection PyUnresolvedReferences
    def update_screen_callback(self, request):
        screens = window.JSON.parse(request.responseText)
        print(screens)


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
            self.name = flx.LineEdit(title='Name:', text='')
            self.rotation = flx.ComboBox(title='Rotation:', options=rotations, selected_index=0)
            flx.Widget(flex=1)
            with flx.TreeWidget(flex=2, title='Defaults:'):
                self.defaults = []
                for i in range(20):
                    self.defaults[i] = flx.TreeItem(title=str(i), checked=False)
                    self.defaults[i].set_visible(False)
            with flx.TreeWidget(flex=2, title='Events:'):
                self.events = []
                for i in range(20):
                    self.events[i] = flx.TreeItem(title=str(i), checked=False)
                    self.events[i].set_visible(False)
            self.load = flx.Button(text='Load')
            self.submit = flx.Button(text='Submit')
            flx.Widget(flex=5)

    # noinspection PyUnresolvedReferences
    @flx.reaction('load.pointer_click')
    def _load(self, *events):
        request = main.send_request('GET', 'http://localhost:5000/screen/' + self.name.text, '', self.load_callback)
        if request.readyState == 4 and not request.status == 200:
            window.alert('Failed to load config. Code: ' + request.status + ', Response: ' + request.responseText)
            return
        self.json = window.JSON.parse(request.responseText)
        self.rotation.set_selected_index(rotations.index((self.json['config']['rotation'])))
        main.edit_media.show_media(self.json['fallback'], False)

    # noinspection PyUnresolvedReferences
    @flx.reaction('submit.pointer_click')
    def _submit(self, *events):
        self.json = {'config': {'name': self.name.text, 'rotation': int(self.rotation.text)}, 'defaults': [], 'events': [],
             'fallback': {'name': 'fallback', 'type': 'image', 'media': 'fallback.png'}}
        data = window.JSON.stringify(self.json)
        request = main.send_request('PUT', 'http://localhost:5000/screen/' + self.name.text, data, self.submit_callback)
        if request.readyState == 4 and not request.status == 200:
            window.alert('Failed to update config. Code: ' + request.status + ', Response: ' + request.responseText)


class AddEvent(flx.Widget):
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
            self.b1 = flx.LineEdit(title='Name:', text='Hola')
            self.b2 = flx.LineEdit(title='Age:', text='Hello world')
            self.b3 = flx.LineEdit(title='Favorite color:', text='Foo bar')
            flx.Button(text='Submit')


class AddDefault(flx.Widget):
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
            self.b1 = flx.LineEdit(title='Name:', text='Hola')
            self.b2 = flx.LineEdit(title='Age:', text='Hello world')
            self.b3 = flx.LineEdit(title='Favorite color:', text='Foo bar')
            flx.Button(text='Submit')


class RemoveEvent(flx.Widget):
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
            self.b1 = flx.LineEdit(title='Name:', text='Hola')
            self.b2 = flx.LineEdit(title='Age:', text='Hello world')
            self.b3 = flx.LineEdit(title='Favorite color:', text='Foo bar')
            flx.Button(text='Submit')


class RemoveDefault(flx.Widget):
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
            self.b1 = flx.LineEdit(title='Name:', text='Hola')
            self.b2 = flx.LineEdit(title='Age:', text='Hello world')
            self.b3 = flx.LineEdit(title='Favorite color:', text='Foo bar')
            flx.Button(text='Submit')


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
            self.label = flx.Label(text='Media')
            self.name = flx.LineEdit(title='Name:', text='media name')
            self.type = flx.ComboBox(title='Type', options=types, selected_index=0)
            self.media = flx.LineEdit(title='Media:', text='test.format')
            #flx.Widget(flex=3)

    def show_media(self, media, editable):
        self.name.set_text(media['name'])
        self.type.set_selected_index(types.index(media['type']))
        self.media.set_text(media['media'])
        self.name.set_disabled(not editable)
        self.media.set_disabled(not editable)
        #self.type.set_editable(editable)

if __name__ == '__main__':
    a = flx.App(Interface, title='Display interface')
    m = a.launch()
    flx.run()
