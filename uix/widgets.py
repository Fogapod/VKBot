from kivy.uix.widget import Widget
from kivy.uix.button import Button
from kivy.uix.screenmanager import Screen
from kivy.uix.textinput import TextInput

from kivy.properties import BooleanProperty


class Widget(Widget):
    pass


class BlueButton(Button):
    pass


class FontelloButton(Button):
    pass


class ColoredScreen(Screen):
    pass


class LowerTextInput(TextInput):
    lower_mode = BooleanProperty(False)

    def insert_text(self, s, from_undo=False):
        if self.lower_mode:
            s = s.lower()
        return super(LowerTextInput, self).insert_text(s, from_undo=from_undo)
