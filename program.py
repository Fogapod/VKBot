#-*- coding: utf-8 -*-
#qpy:kivy
from kivy.app import App
from kivy.lang import Builder
from kivy.uix.screenmanager import ScreenManager, Screen
from kivy.clock import Clock

from libs.plyer import notification
from libs.toast import toast

from bot.utils import PATH, DATA_PATH
from bot.core import LongPollSession


Builder.load_file('uix/kv/vkbotapp.kv')


def statusbar_notification(title='VKBot', message=''):
    #notification.notify(title=title, message=message)
    pass # вызывает падение приложенич

def bot_launched_notification():
    statusbar_notification(u'Бот запущен')

def bot_stopped_notification():
    statusbar_notification(u'Бот остановлен')

def toast_notification(text, length_long=False):
    toast(text, length_long=length_long)


class VKBotApp(App):
    use_kivy_settings = False
    def __init__(self, *args, **kwargs):
        super(VKBotApp, self).__init__(*args, **kwargs)
        self.root = Root()
        self.session = LongPollSession()
    
    def build(self):
        self.root.add_widget(HomeScreen())
        self.root.add_widget(TwoFAKeyEnterForm())
        self.root.add_widget(LoginScreen())
        self.root.add_widget(CustomCommandsScreen())

        if not self.session.authorization()[0]:
            self.root.show_auth_form()

        self.root.show_home_form()
        return self.root

    def get_application_config(self):
        return super(VKBotApp, self).get_application_config(
            '{}.%(appname)s.ini'.format(DATA_PATH))
            # FIXME: реальный путь конфига - /sdcard/.(appname).ini

    def build_config(self, config):
        config.setdefaults('General', 
                {
                	"show_bot_activity":"False",
                	"bot_activated":"False",
                	"custom_commands":"False",
                	"open_cc_form": "Открыть"
                }
            )

    def build_settings(self, settings):
        settings.add_json_panel("Настройки бота", self.config, data=
            '''[
                {"type": "bool",
                "title": "Отображать состояние бота в статусе",
                "desc": "Если включено, в статус будет добавлено уведомление о том, что бот активен. Иначе вернется предыдущий текст",
                "section": "General",
                "key": "show_bot_activity",
                "values": ["False","True"],
                "disabled": 1
                },
                {"type": "title",
                "title": "Пользовательские команды (WIP)"
                },
                {"type": "bool",
                "title": "Использовать пользовательские команды",
                "desc": "Пользовательские команды хранятся в файле %spresets.txt",
                "section": "General",
                "key": "custom_commands",
                "values": ["False","True"]
                },
                {"type": "options",
                "title": "Открыть окно настройки пользовательских команд",
                "section": "General",
                "key": "open_cc_form",
                "disabled": "True"                
                },                
                {"type": "title",
                "title": "Активация бота"
                },
                {"type": "bool",
                "title": "Бот активирован",
                "section": "General",
                "key": "bot_activated",
                "values": ["False","True"],
                "disabled": 1
                }
            ]''' % PATH
        )
        # settings.close_button.text = 'Закрыть'

    def on_pause(self):
        return True

    def on_stop(self):
        if self.session.running:
            while not self.session.stop_bot(): continue
            bot_stopped_notification()
            

class LoginScreen(Screen):
    def __init__(self, *args, **kwargs):
        super(LoginScreen, self).__init__(*args, **kwargs)
        self.session = VKBotApp.get_running_app().session
        
    def on_enter(self):
        self.ids.pass_auth.disabled = not self.session.authorized

    def log_in(self, twofa_key=''):
        login = self.ids.login.text
        password = self.ids.pass_input.text

        if login and password:
            authorized, error = self.session.authorization(login=login, password=password, key=twofa_key)
            if authorized:
                self.ids.pass_input.text = ''
                if twofa_key:
                    return True
                self.parent.show_home_form()
            elif error:
                if 'code is needed' in error:
                    self.parent.show_twofa_form()
                    return
                elif 'incorrect password' in error:
                    toast_notification(u'Неправильный логин или пароль')
                else:
                    toast_notification(error, length_long=True)
                    return
        self.ids.pass_input.text = ''
        

class TwoFAKeyEnterForm(Screen):
    def twofa_auth(self):
        if self.ids.twofa_textinput.text:
            login_screen_widget = self.parent.get_screen('login_screen')
            if login_screen_widget.log_in(twofa_key=self.ids.twofa_textinput.text):
                self.parent.show_home_form()
            else:
                toast_notification(u'Неправильный код подтверждения')
            self.ids.twofa_textinput.text = ''


class HomeScreen(Screen):
    def __init__(self, *args, **kwargs):
        super(HomeScreen, self).__init__(*args, **kwargs)
        self.bot_check_event = Clock.schedule_interval(self.check_if_bot_active, 1)
        self.session = VKBotApp.get_running_app().session
        self.launch_bot_text = 'Включить бота'
        self.stop_bot_text = 'Выключить бота'
        self.ids.main_btn.text = self.launch_bot_text

    def on_main_btn_press(self):
        config = VKBotApp.get_running_app().config

        if self.ids.main_btn.text == self.launch_bot_text:
            self.launch_bot(config)
        else:
            self.stop_bot(config)

    def launch_bot(self, config):
        self.activation_status = config.getdefault('General', 'bot_activated', 'False')
        use_custom_commands = config.getdefault('General', 'custom_commands', 'False')

        while not self.session.launch_bot(activated=self.activation_status == 'True',\
            use_custom_commands=use_custom_commands == 'True'): continue

        self.ids.main_btn.text = self.stop_bot_text
        self.bot_check_event()
        bot_launched_notification()

    def stop_bot(self, config):
        self.bot_check_event.cancel()
        bot_stopped = False

        while not bot_stopped:
            bot_stopped, new_activation_status = self.session.stop_bot()

        if new_activation_status != self.activation_status:
            config.set('General', 'bot_activated', str(new_activation_status))
            config.write()

        self.ids.main_btn.text = self.launch_bot_text
        bot_stopped_notification()

    def update_answers_count(self):
        self.ids.answers_count_lb.text = 'Ответов: {}'.format(self.session.reply_count)

    def logout(self):
        self.session.authorization(logout=True)
        self.parent.show_auth_form()
    
    def check_if_bot_active(self, tick):
        self.update_answers_count()
        if self.ids.main_btn.text == self.stop_bot_text and\
                not self.session.running:
            self.bot_check_event.cancel()
            self.ids.main_btn.text = self.launch_bot_text
            bot_stopped_notification()

            if self.session.runtime_error:
                toast_notification(self.session.runtime_error, length_long=True)


class CustomCommandsScreen(Screen):
    def leave(self):
        self.app = VKBotApp.get_running_app()
        self.app.open_settings()
        self.parent.open_last_screen()


class Root(ScreenManager):
    def __init__(self, *args, **kwargs):
        super(Root, self).__init__(*args, **kwargs)
        self.last_screen = None

    def show_auth_form(self):
        self.current = 'login_screen'

    def show_twofa_form(self):
        self.current = 'twofa_form'

    def show_home_form(self):
        self.current = 'home_screen'

    def show_custom_commands_screen(self):
        self.current = 'cc_screen'
    
    def save_last_screen(self):
        self.last_screen = self.current_screen

    def open_last_screen(self):
        if self.last_screen:
            self.current = self.last_screen
        else:
            self.show_home_form()


if __name__ == '__main__':
    VKBotApp().run()