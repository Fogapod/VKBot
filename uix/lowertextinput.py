from kivy.uix.textinput import TextInput


class LowerTextInput(TextInput):
    def __init__(self, **kwargs):
        self.font_name = 'Roboto-BoldItalic'
        super(LowerTextInput, self).__init__(**kwargs)

    def insert_text(self, substring, from_undo=False):
        s = substring.lower()
        return super(LowerTextInput, self).insert_text(s, from_undo=False)