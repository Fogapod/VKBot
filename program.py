# coding:utf8


import os

from kivy.app import App
from kivy.lang import Builder
from kivy.uix.settings import SettingsWithNoMenu

from uix.screens import Root

from bot.utils import PATH, CUSTOM_COMMANDS_FILE_PATH
from bot.core import LongPollSession


class VKBotApp(App):
    use_kivy_settings = False
    settings_cls = SettingsWithNoMenu

    def build(self):
        self.title = 'VKBot'
        self.session = LongPollSession()
        self.load_kv_files()

        self.root = Root()

        self.root.show_main_screen()
        if not self.session.authorization()[0]:
            self.root.show_auth_screen()

        return self.root

    def load_kv_files(self):
        directories = ['uix/kv/']

        for directory in directories:
            for file in os.listdir(directory):
                if file.endswith('.kv'):
                    Builder.load_file(directory + file)
                else:
                    continue

    def get_application_config(self):
        return '{}.vkbot.ini'.format(PATH)

    def build_config(self, config):
        config.setdefaults('General', 
                {
                    "show_bot_activity": "False",
                    "appeals": u"/:бот,",
                    "use_custom_commands": "False",
                    "protect_cc": "True",
                    "bot_activated": "False"
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
            "type": "string",
            "title": "Обращение к боту",
            "desc": "Обращения, на которые бот будет отзываться. Обращения разделяются символом :",
            "section": "General",
            "key": "appeals"
            },
            {
            "type": "title",
            "title": "Пользовательские команды (WIP)"
            },
            {
            "type": "bool",
            "title": "Использовать пользовательские команды",
            "desc": "Пользовательские команды хранятся в файле %s",
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
        ]''' % CUSTOM_COMMANDS_FILE_PATH
        )

    def get_captcha_key(captcha_url):
        return None

    def on_pause(self):
        return True

    def on_stop(self):
        if self.session.running:
            self.session.stop_bot()


if __name__ == '__main__':
    VKBotApp().run()
