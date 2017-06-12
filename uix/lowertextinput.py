from kivy.uix.textinput import TextInput


class LowerTextInput(TextInput):
    def __init__(self, **kwargs):
        self.font_name = 'Roboto-BoldItalic'
        self.regex_activated = False
        super(LowerTextInput, self).__init__(**kwargs)

    def insert_text(self, s, from_undo=False):
        if not self.regex_activated:
            s = s.lower()
        return super(LowerTextInput, self).insert_text(s, from_undo=False)