#-*- coding: utf-8 -*-
from kivy.app import App
from kivy.uix.screenmanager import ScreenManager, Screen

from bot_core import LongPollSession
from bot_core import Bot

PATH = '' # '/storage/emulated/0/Git/ChatBot_UI/'
DATA_PATH = 'data/'

class ChatBot(App):
    def build(self):
        return LoginScreen()

    def on_pause(self):
        return True

    def on_resume(self):
        pass

class LoginScreen(Screen):
    def login(self):
        session = LongPollSession(bot=Bot())
        login = self.ids.login.text
        password = self.ids.pass_input.text

        if login != '' and password != '':
            if not session.authorization(token_path=PATH + DATA_PATH + 'token.txt', login=login, password=password):
                self.ids.login.text = self.ids.pass_input.text = ''

        self.ids.login.text = self.ids.pass_input.text = ''

class Root(ScreenManager):
    pass