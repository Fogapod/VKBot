# -*- coding:utf-8 -*-


from kivy.uix.gridlayout import GridLayout


class CustomCommandBlock(GridLayout):
    def __init__(self, **kwargs):
        super(CustomCommandBlock, self).__init__(**kwargs)
        self.ids.command.text = kwargs.get('command', 'Нет пользоаательских команд')

    def edit_command(self):
        pass
