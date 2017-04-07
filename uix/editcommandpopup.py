#-*- coding:utf-8 -*-
	

from kivy.uix.popup import Popup


class EditCommandPopup(Popup):
    def __init__(self, **kwargs):
        super(EditCommandPopup, self).__init__(**kwargs)
        self.title = kwargs.get('title', 'Настройка команды')
        self.ids.command_text.text = kwargs.get('command_text', '')
        self.ids.response_text.text = kwargs.get('response_text', '')

        self.list_item = kwargs['list_item']
        if not self.list_item:
            self.ids.delete_command_btn.disabled = True
