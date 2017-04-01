#-*- coding:utf-8 -*-


from kivy.uix.popup import Popup
from kivy.uix.textinput import TextInput
from kivy.uix.gridlayout import GridLayout


class CustomCommandBlock(GridLayout):
    def __init__(self, **kwargs):
        super(CustomCommandBlock, self).__init__(**kwargs)
        command = kwargs.get('command')
        self.id, self.ids.command_btn.text = command, command


class EditCommandPopup(Popup):
    def __init__(self, **kwargs):
        super(EditCommandPopup, self).__init__(**kwargs)
        self.ids.command_text.text = kwargs.get('command_text', '')
        self.ids.response_text.text = kwargs.get('response_text', '')
        self.item = kwargs['item']


class LowerTextInput(TextInput):
    def insert_text(self, substring, from_undo=False):
        s = substring.lower()
        return super(LowerTextInput, self).insert_text(s, from_undo=False)