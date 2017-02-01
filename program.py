#-*- coding: utf-8 -*-
#qpy:kivy
from kivy.app import App
from kivy.lang import Builder
from kivy.uix.screenmanager import ScreenManager, Screen

from bot_core import LongPollSession
from bot_core import Bot

session = LongPollSession(bot=Bot())

Builder.load_string('''
#:import FadeTransition kivy.uix.screenmanager.FadeTransition
<Root>:
    id: rootscr
    transition: FadeTransition()
''')

class ChatBot(App):
    def __init__(self, **kwargs):
        super(ChatBot, self).__init__(**kwargs)
        self.root = Root()

    def build(self):
        self.root.add_widget(LoginScreen())
        self.root.add_widget(HomeScreen())
        if not session.authorization():
            self.show_auth_form()
        return self.root

    def show_auth_form(self):
        self.root.current = 'login_screen'

    def on_pause(self):
        return True

    def on_resume(self):
        pass


class LoginScreen(Screen):
    def log_in(self):
        login = self.ids.login.text
        password = self.ids.pass_input.text

        if login and password:
            if session.authorization(login=login, password=password):
                self.parent.current = 'home_screen'

        self.ids.login.text = self.ids.pass_input.text = ''


class HomeScreen(Screen):
    def on_press(self):
        if self.ids.button.text == 'Запустить бота':
            self.run_bot()
            self.ids.button.text = 'Остановить бота'
        else:
            self.stop_bot()
            self.ids.button.text = 'Запустить бота'

    def run_bot(self):
        pass #session.process_updates()

    def stop_bot(self):
        pass


class Root(ScreenManager):
    pass

if __name__ == '__main__':
    ChatBot().run()