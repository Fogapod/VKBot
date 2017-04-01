#-*- coding: utf-8 -*-
#qpy:kivy


import os
import re

from kivy.app import App
from kivy.lang import Builder
from kivy.clock import Clock, mainthread
from kivy.uix.settings import SettingsWithNoMenu
from kivy.uix.screenmanager import ScreenManager, Screen, FadeTransition

from plyer import notification
from libs.toast import toast

from uix.cc_block import CustomCommandBlock, EditCommandPopup

from bot.utils import PATH, DATA_PATH, load_custom_commands, save_custom_commands
from bot.core import LongPollSession


def statusbar_notification(title='VKBot', message=''):
    notification.notify(title=title, message=message)

def bot_launched_notification():
    statusbar_notification(u'Бот запущен')

def bot_stopped_notification():
    statusbar_notification(u'Бот остановлен')

def toast_notification(text, length_long=False):
    toast(text, length_long=length_long)


class VKBotApp(App):
    use_kivy_settings = False
    settings_cls = SettingsWithNoMenu

    def __init__(self, **kwargs):
        super(VKBotApp, self).__init__(**kwargs)
        self.root = Root()
        self.session = LongPollSession()

    def build(self):
        self.load_kv_files('uix/kv/')

        if not self.session.authorization()[0]:
            self.root.show_auth_screen()
        else:
            self.root.show_home_screen()

            self.on_config_change(
                    self.config, 'General', 'use_custom_commands',
                    self.config.getdefault('General', 'use_custom_commands', 'False')
                ) # URGLY # TODO

        return self.root

    def load_kv_files(self, path):
        for kv_file in os.listdir(path):
            if re.match('.*\.kv$', kv_file):
                Builder.load_file(path + kv_file)
            else:
                continue

    def get_application_config(self):
        return super(VKBotApp, self).get_application_config(
            '{}.%(appname)s.ini'.format(DATA_PATH))
            # FIXME: реальный путь конфига для андроида - /sdcard/.(appname).ini

    def build_config(self, config):
        config.setdefaults('General', 
                {
                    "show_bot_activity":"False",
                    "bot_activated":"False",
                    "use_custom_commands":"False",
                    "protect_cc": "True"
                }
            )

    def build_settings(self, settings):
        settings.add_json_panel("Настройки бота", self.config, data=
        '''[
            {
            "type": "bool",
            "title": "Отображать состояние бота в статусе",
            "desc": "Если включено, в статус будет добавлено уведомление о том, что бот активен. Иначе вернется предыдущий текст",
            "section": "General",
            "key": "show_bot_activity",
            "values": ["False","True"],
            "disabled": 1
            },
            {
            "type": "title",
            "title": "Пользовательские команды (WIP)"
            },
            {
            "type": "bool",
            "title": "Использовать пользовательские команды",
            "desc": "Пользовательские команды хранятся в файле %spresets.txt",
            "section": "General",
            "key": "use_custom_commands",
            "values": ["False","True"]
            },
            {
            "type": "bool",
            "title": "Защитить пользовательские команды",
            "desc": "Только владелец сможет настраивать пользовательские команды через сообщения",
            "section": "General",
            "key": "protect_cc",
            "values": ["False", "True"]
            },
            {
            "type": "title",
            "title": "Активация бота"
            },
            {
            "type": "bool",
            "title": "Бот активирован",
            "section": "General",
            "key": "bot_activated",
            "values": ["False","True"],
            "disabled": 1
            }
        ]''' % PATH
        )

    def on_config_change(self, config, section, key, value):
        if config is self.config:
            if key == 'use_custom_commands':
                self.root.current_screen.ids.open_cc_screen_btn.disabled = value != 'True'

    def on_pause(self):
        return True

    def on_stop(self):
        if self.session.running:
            while not self.session.stop_bot(): continue
            bot_stopped_notification()
            

class LoginScreen(Screen):
    def __init__(self, **kwargs):
        super(LoginScreen, self).__init__(**kwargs)
        self.session = VKBotApp.get_running_app().session
        
    def on_enter(self):
        self.ids.pass_auth.disabled = not self.session.authorized

    def log_in(self, twofa_key=''):
        login = self.ids.login.text
        password = self.ids.pass_input.text

        if login and password:
            authorized, error = self.session.authorization(
                                login=login, password=password, key=twofa_key
                                )
            if authorized:
                self.ids.pass_input.text = ''
                if twofa_key:
                    return True
                self.parent.show_home_screen()
            elif error:
                if 'code is needed' in error:
                    self.parent.show_twofa_screen()
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
                self.parent.show_home_screen()
            else:
                toast_notification(u'Неправильный код подтверждения')
            self.ids.twofa_textinput.text = ''


class HomeScreen(Screen):
    def __init__(self, **kwargs):
        super(HomeScreen, self).__init__(**kwargs)
        self.bot_check_event = Clock.schedule_interval(self.check_if_bot_active, 1)
        self.session = VKBotApp.get_running_app().session
        self.launch_bot_text = 'Включить бота'
        self.stop_bot_text = 'Выключить бота'
        self.ids.main_btn.text = self.launch_bot_text

    @mainthread
    def on_main_btn_press(self):
        config = VKBotApp.get_running_app().config

        if self.ids.main_btn.text == self.launch_bot_text:
            self.launch_bot(config)
        else:
            self.stop_bot(config)

    def launch_bot(self, config):
        self.activation_status = config.getdefault('General', 'bot_activated', 'False')
        use_custom_commands = config.getdefault('General', 'use_custom_commands', 'False')
        protect_custom_commands = config.getdefault('General', 'protect_cc', "True")

        while not self.session.launch_bot(
                activated=self.activation_status == 'True',
                use_custom_commands=use_custom_commands == 'True',
                protect_custom_commands=protect_custom_commands == 'True'
                ):
            continue

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
        self.parent.show_auth_screen()
    
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
    def __init__(self, **kwargs):
        super(CustomCommandsScreen, self).__init__(**kwargs)
        self.included_keys = []

    def leave(self):
        self.parent.show_home_screen()

    def on_enter(self):
        self.custom_commands = load_custom_commands()
        
        for key in sorted(self.custom_commands.keys()):
            if key not in self.included_keys and len(self.custom_commands[key]) == 1:
                block = CustomCommandBlock(command=key)
                self.ids.cc_list.add_widget(block)
                self.included_keys.append(key)
        Clock.schedule_once(self.update_commands_list_size, .1)

    def update_commands_list_size(self, delay):
        self.ids.cc_list.size_hint_y = None
        self.ids.cc_list.height = self.ids.cc_list.minimum_height

    def open_edit_popup(self, command, item):
        popup = EditCommandPopup(
            command_text=command,
            response_text=self.custom_commands[command][0],
            item=item
            )
        popup.ids.delete_command_btn.bind(
            on_press=lambda x: self.remove_command(
                popup.ids.command_text.text.decode('utf8'),
                item
                )
            )
        popup.ids.apply_btn.bind(
            on_press=lambda x: self.save_edited_command(
                popup.ids.command_text.text,
                popup.ids.response_text.text
            )
        )
        popup.open()

    def save_edited_command(self, command, response):
        self.custom_commands[command.decode('utf8')] = [response.decode('utf8')]
        save_custom_commands(self.custom_commands)

    def remove_command(self, command, item):
        self.custom_commands.pop(command, None)
        save_custom_commands(self.custom_commands)
        self.included_keys.remove(command)
        self.ids.cc_list.remove_widget(item)
        Clock.schedule_once(self.update_commands_list_size, .1)

    def add_command(self):
        pass


class Root(ScreenManager):
    def __init__(self, **kwargs):
        super(Root, self).__init__(**kwargs)
        self.transition = FadeTransition()

    def show_auth_screen(self):
        if not 'login_screen' in self.screen_names:
            self.add_widget(LoginScreen())
        self.current = 'login_screen'

    def show_twofa_screen(self):
        if not 'twofa_screen' in self.screen_names:
            self.add_widget(TwoFAKeyEnterForm())
        self.current = 'twofa_screen'

    def show_home_screen(self):
        if not 'home_screen' in self.screen_names:
            self.add_widget(HomeScreen())
        self.current = 'home_screen'

    def show_custom_commands_screen(self):
        if not 'cc_screen' in self.screen_names:
            self.add_widget(CustomCommandsScreen())
        self.current = 'cc_screen'


if __name__ == '__main__':
    VKBotApp().run()
