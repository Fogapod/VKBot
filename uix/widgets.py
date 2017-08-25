from kivy.uix.widget import Widget
from kivy.uix.button import Button
from kivy.uix.screenmanager import Screen
from kivy.uix.textinput import TextInput

from kivy.properties import BooleanProperty
from kivy.graphics import Color, Rectangle
from kivy.metrics import dp


class Widget(Widget):
    pass


class ShadeButton(Button):
    def __init__(self, **kwargs):
        self.use_shade = BooleanProperty(True)
        super(ShadeButton, self).__init__(**kwargs)
        self.redraw_shade()

    def redraw_shade(self):
        if self.disabled or not self.use_shade:
            return

        if self.canvas.before:
            self.canvas.before.clear()

        with self.canvas.before:
            Color(rgba=(0, 0, 0, 0.7))

            Rectangle(
                pos=(self.pos[0] + dp(4), self.pos[1] - dp(4)), 
                size=self.size
            )

    def on_size(self, *args):
        self.redraw_shade()

    def on_pos(self, *args):
        self.redraw_shade()

    def on_press(self):
        self.canvas.before.clear()

    def on_touch_up(self, touch):
        self.redraw_shade()
        super(ShadeButton, self).on_touch_up(touch)


class BlueButton(ShadeButton):
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
