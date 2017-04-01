from kivy.uix.textinput import TextInput


class LowerTextInput(TextInput):
    def insert_text(self, substring, from_undo=False):
        s = substring.lower()
        return super(LowerTextInput, self).insert_text(s, from_undo=False)