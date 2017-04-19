from kivy.uix.gridlayout import GridLayout


class CustomCommandBlock(GridLayout):
    def __init__(self, **kwargs):
        super(CustomCommandBlock, self).__init__(**kwargs)
        self.commands = []
        self.responses = []

