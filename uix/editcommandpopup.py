from kivy.uix.popup import Popup


class EditCommandPopup(Popup):
    def __init__(self, **kwargs):
        super(EditCommandPopup, self).__init__(**kwargs)
        self.ids.command_text.text = kwargs['command_text']
        self.ids.response_text.text = kwargs['response_text']

        if kwargs['use_regex']:
            self.ids.regex_btn.state = 'down'
            self.ids.regex_btn.background_color = [0, 1, 0, .6]
        if kwargs['force_unmark']:
            self.ids.force_unmark_btn.state = 'down'
            self.ids.force_unmark_btn.background_color = [0, 1, 0, .6]

        self.command_block = kwargs['command_block']
        self.command_button = kwargs['command_button']
        if not self.command_button:
            self.ids.delete_command_btn.disabled = True
