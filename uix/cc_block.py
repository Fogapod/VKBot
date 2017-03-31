#-*- coding:utf-8 -*-


from kivy.uix.gridlayout import GridLayout
from kivy.uix.popup import Popup

from bot.utils import save_custom_commands


class CustomCommandBlock(GridLayout):
    def __init__(self, **kwargs):
        super(CustomCommandBlock, self).__init__(**kwargs)
        self.ids.command_btn.text = kwargs.get('command', 'Нет пользоаательских команд')


class EditCommandPopup(Popup):
    def __init__(self, **kwargs):
        super(EditCommandPopup, self).__init__(**kwargs)
        self.custom_commands = kwargs['custom_commands']
        self.ids.command_text.text = kwargs.get('command_text', '')
        self.ids.response_text.text = kwargs.get('response_text', '')
    
    def save_edited_command(self, command, response):
        self.custom_commands[command.decode('utf8')] = [response.decode('utf8')]
        save_custom_commands(self.custom_commands)
        self.dismiss()