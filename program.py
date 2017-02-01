#-*- coding: utf-8 -*-
#qpy:kivy
from kivy.app import App
from kivy.lang import Builder
from kivy.uix.screenmanager import ScreenManager, Screen

from bot_core import LongPollSession

session = LongPollSession()

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
        self.root.add_widget(HomeScreen())
        self.root.add_widget(LoginScreen())

        if not session.authorization():
            self.show_auth_form()

        return self.root

    def show_auth_form(self):
        self.root.current = 'login_screen'

    def show_home_form(self):
        self.root.current = 'home_screen'

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
    def on_main_btn_press(self):
        run_bot_text = 'Запустить бота'
        stop_bot_text = 'Остановить бота'

        if self.ids.button.text == run_bot_text:
            session.start_bot()
            self.ids.button.text = stop_bot_text
        else:
            session.stop_bot()
            self.ids.button.text = run_bot_text


class Root(ScreenManager):
    pass

if __name__ == '__main__':
    ChatBot().run()