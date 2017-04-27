#-*- coding: utf-8 -*-
#qpy:kivy


import os
import re

from kivy.app import App
from kivy.lang import Builder
from kivy.uix.settings import SettingsWithNoMenu

from uix.screens import Root

from bot.utils import *

from bot.core import LongPollSession


class VKBotApp(App):
    use_kivy_settings = False
    settings_cls = SettingsWithNoMenu

    def build(self):
        self.session = LongPollSession()
        self.load_kv_files()

        self.root = Root()

        if not self.session.authorization()[0]:
            self.root.show_auth_screen()
        else:
            self.root.show_main_screen()

            self.on_config_change(
                    self.config, 'General', 'use_custom_commands',
                    self.config.getdefault('General', 'use_custom_commands', 'False')
                ) # URGLY # TODO

        return self.root

    def load_kv_files(self):
        directories = ['uix/kv/']

        for directory in directories:
            for file in os.listdir(directory):
                if re.match('.*\.kv$', file):
                    Builder.load_file(directory + file)
                else:
                    continue

    def get_application_config(self):
        return '{}.vkbot.ini'.format(PATH)

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

    def get_captcha_key(captcha_url):
        return None

    def on_pause(self):
        return True

    def on_stop(self):
        if self.session.running:
            while not self.session.stop_bot(): continue
            bot_stopped_notification()


if __name__ == '__main__':
    VKBotApp().run()
