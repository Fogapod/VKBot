#-*- coding:utf-8 -*-
	

from kivy.uix.popup import Popup


class EditCommandPopup(Popup):
    def __init__(self, **kwargs):
        super(EditCommandPopup, self).__init__(**kwargs)
        self.title = kwargs['title']
        self.ids.command_text.text = kwargs['command_text']
        self.ids.response_text.text = kwargs['response_text']
        self.command_block = kwargs['command_block']

        self.command_button = kwargs['command_button']
        if not self.command_button:
            self.ids.delete_command_btn.disabled = True
