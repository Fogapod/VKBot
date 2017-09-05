from kivy.uix.modalview import ModalView

from kivy.properties import NumericProperty
from kivy.animation import Animation


class LoadingPopup(ModalView):
    angle = NumericProperty(0)

    def __init__(self, **kwargs):
        super(LoadingPopup, self).__init__(**kwargs)
        angle = 360
        if random.choice((0, 1)):
            angle = -angle

        anim = Animation(angle=angle, duration=2)
        anim += Animation(angle=angle, duration=2)
        anim.repeat = True
        anim.start(self)

    def on_angle(self, item, angle):
        if angle in (360, -360):
            item.angle = 0