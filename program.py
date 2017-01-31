#-*- coding: utf-8 -*-
from kivy.app import App
from kivy.uix.screenmanager import ScreenManager, Screen

from bot_core import LongPollSession
from bot_core import Bot


class ChatBot(App):
    def __init__(self, **kwargs):
        super(ChatBot, self).__init__(**kwargs)
        self.session = LongPollSession(bot=Bot())
        self.screen = MainScreen()
        self.PATH = '' # '/storage/emulated/0/Git/ChatBot_UI/'
        self.DATA_PATH = 'data/'

    def build(self):
        if not self.session.authorization(token_path=self.PATH + self.DATA_PATH + 'token.txt'):
            self.show_auth_form()
        return self.screen

    def show_auth_form(self):
        self.screen.ids.load_screen.add_widget(self.password_form)

    def on_pause(self):
        return True

    def on_resume(self):
        pass


class LoginScreen(Screen):
    def log_in(self):
        login = self.ids.login.text
        password = self.ids.pass_input.text

        if login != '' and password != '':
            if not session.authorization(token_path=PATH + DATA_PATH + 'token.txt', login=login, password=password):
                self.ids.login.text = self.ids.pass_input.text = ''

        self.ids.login.text = self.ids.pass_input.text = ''


class MainScreen(ScreenManager):
    pass
