from pyforms.basewidget import BaseWidget
from pyforms.controls import ControlFile
from pyforms.controls import ControlText
from pyforms.controls import ControlSlider
from pyforms.controls import ControlPlayer
from pyforms.controls import ControlButton

class Interface(BaseWidget):


    def __init__(self, *args, **kwargs):
        super().__init__('Computer vision algorithm example')


if __name__ == '__main__':
    from pyforms import start_app
    start_app(Interface)