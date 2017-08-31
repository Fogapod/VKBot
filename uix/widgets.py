from kivy.uix.widget import Widget
from kivy.uix.button import Button
from kivy.uix.screenmanager import Screen
from kivy.uix.textinput import TextInput

from kivy.graphics import Color, Rectangle, RoundedRectangle
from kivy.metrics import dp


class Widget(Widget):
    pass


class ButtonWithShadow(Button):
    def __init__(self, **kwargs):
        self.disable_shadow = False
        self.shadow_visibility = .3
        self.shadow_shift_x = dp(3)
        self.shadow_shift_y = dp(3)
        self.drawing_shape = Rectangle
        super(ButtonWithShadow, self).__init__(**kwargs)


    def redraw_all(self):
        if self.canvas:
            self.canvas.before.clear()

        self.redraw_shadow()
        self.redraw_background()


    def redraw_background(self):
        with self.canvas.before:
            Color(rgba=(self.background_color[:3] + [1]))
            self.drawing_shape(pos=self.pos, size=self.size)


    def redraw_shadow(self):
        if self.disable_shadow:
            return

        with self.canvas.before:
            Color(rgba=(0, 0, 0, self.shadow_visibility))

            self.drawing_shape(
                pos=(
                    self.pos[0] + self.shadow_shift_x,
                    self.pos[1] - self.shadow_shift_y
                ),
                size=self.size
            )


    def on_size(self, *args):
        self.redraw_all()


    def on_pos(self, *args):
        self.redraw_all()


    def on_press(self):
        self.canvas.before.clear()
        self.redraw_background()


    def on_touch_up(self, touch):
        self.redraw_all()
        super(ButtonWithShadow, self).on_touch_up(touch)


class RoundedButtonWithShadow(ButtonWithShadow):
    def __init__(self, **kwargs):
        super(RoundedButtonWithShadow, self).__init__(**kwargs)
        self.drawing_shape = RoundedRectangle


class BlueButton(RoundedButtonWithShadow):
    pass


class FontelloButton(Button):
    pass


class ColoredScreen(Screen):
    pass


class LowerTextInput(TextInput):
    lower_mode = False

    def insert_text(self, s, from_undo=False):
        if self.lower_mode:
            s = s.lower()
        return super(LowerTextInput, self).insert_text(s, from_undo=from_undo)
