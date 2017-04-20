from kivy.uix.gridlayout import GridLayout
from kivy.uix.button import Button


class CustomCommandBlock(GridLayout):
    def __init__(self, **kwargs):
        super(CustomCommandBlock, self).__init__(**kwargs)
        self.commands = []
        self.responses = []
        

class CommandButton(Button):
    pass
