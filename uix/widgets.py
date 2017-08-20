from kivy.uix.widget import Widget
from kivy.uix.button import Button
from kivy.uix.screenmanager import Screen
from kivy.uix.textinput import TextInput


class Widget(Widget):
    pass


class FontelloButton(Button):
    pass


class ColoredScreen(Screen):
    pass


class LowerTextInput(TextInput):
    def __init__(self, **kwargs):
        self.regex_activated = False
        super(LowerTextInput, self).__init__(**kwargs)

    def insert_text(self, s, from_undo=False):
        if not self.regex_activated:
            s = s.lower()
        return super(LowerTextInput, self).insert_text(s, from_undo=from_undo)


class Apply(Button):
    pass
