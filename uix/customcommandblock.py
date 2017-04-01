from kivy.uix.gridlayout import GridLayout


class CustomCommandBlock(GridLayout):
    def __init__(self, **kwargs):
        super(CustomCommandBlock, self).__init__(**kwargs)
        command = kwargs.get('command')
        self.id, self.ids.command_btn.text = command, command
