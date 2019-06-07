from flexx import flx


# noinspection PyUnresolvedReferences
def send_put_request(url, data, request, callback):
    request.open('PUT', url, True)
    request.setRequestHeader('Content-type', 'text/plain')  # application/json
    request.setRequestHeader("Authorization", "Basic " + window.btoa("username:password"))
    request.onreadystatechange = callback
    request.send(data)


class Interface(flx.Widget):
    CSS = """
    .flx-Button {
        background: #9d9;
    }
    .flx-LineEdit {
        border: 2px solid #9d9;
    }
    """

    def init(self):
        with flx.TabLayout():
            AddDisplay(title='Add a Display')
            EditDisplay(title='Edit a Display')
            AddDefault(title='Add a Default')
            RemoveDefault(title='Remove a Default')
            AddEvent(title='Add an Event')
            RemoveEvent(title='Remove an Event')


class AddDisplay(flx.Widget):
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
            self.name = flx.LineEdit(title='Name:', text='')
            self.rotation = flx.ComboBox(title='Rotation:', options=[0, 90, 180, 270], selected_index=0)
            self.add = flx.Button(text='Add')
            flx.Widget(flex=1)

    def on_state_change(self):
        print(self.request.responseText)

    # noinspection PyUnresolvedReferences
    @flx.reaction('add.pointer_down')
    def add_display(self, *events):
        self.request = window.XMLHttpRequest()
        data = window.JSON.stringify(
            {'config': {'name': self.name.text, 'rotation': int(self.rotation.text)}, 'defaults': [], 'events': [],
             'fallback': {'type': 'image', 'media': 'fallback.png'}})
        send_put_request('http://localhost:5000/screen/' + self.name.text, data, self.request, self.on_state_change)

    # Todo: Rearrange global methods and variables
    # noinspection PyUnresolvedReferences
    def update_screen_names(self):
        self.request = window.XMLHttpRequest()
        send_get_request('http://localhost:5000/screen', data, self.request, self.update_screen_callback)

    def update_screen_callback(self):
        pass


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
        with flx.FormLayout() as self.form:
            self.name = flx.LineEdit(title='Name:', text='')
            self.rotation = flx.ComboBox(title='Rotation:', options=[0, 90, 180, 270], selected_index=0)
            flx.Widget(flex=1)
            flx.Button(text='Submit')
            flx.Widget(flex=3)


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


if __name__ == '__main__':
    a = flx.App(Interface, title='Display interface')
    m = a.launch()
    flx.run()
