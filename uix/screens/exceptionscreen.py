from kivy.uix.screenmanager import Screen
from kivy.lang import Builder

import webbrowser


class ExceptionScreen(Screen):
    Builder.load_file('uix/kv/exceptionscreen/exceptionscreen.kv')

    def __init__(self, exception_text, **kwargs):
        self.exception_text = exception_text
        super(ExceptionScreen, self).__init__(**kwargs)


    def send_report_to_vk(self, text):
        webbrowser.open('https://vk.com/topic-71248303_36001195')


    def send_report_to_github(self, text):
        webbrowser.open(
            'https://github.com/Fogapod/VKBot/issues/new?body=' + text
        )
