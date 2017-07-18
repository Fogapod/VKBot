# coding:utf8


import os

from kivy.app import App
from kivy.lang import Builder
from kivy.uix.settings import SettingsWithNoMenu

from uix.screens import Manager, TwoFAKeyEnterPopup, CaptchaPopup

from bot.utils import SETTINGS_FILE_PATH, CUSTOM_COMMANDS_FILE_PATH, PATH
from bot.core import LongPollSession, __version__


class VKBotApp(App):
    use_kivy_settings = False
    settings_cls = SettingsWithNoMenu

    def build(self):
        self.title = 'VKBot'
        self.session = LongPollSession()
        self.load_kv_files()

        self.manager = Manager()

        self.manager.show_main_screen()
        if not self.session.authorization()[0]:
            self.manager.show_auth_screen()

        return self.manager

    def load_kv_files(self):
        directories = ['uix/kv/']

        for directory in directories:
            for file in os.listdir(directory):
                if file.endswith('.kv'):
                    Builder.load_file(directory + file)
                else:
                    continue

    def get_application_config(self):
        return SETTINGS_FILE_PATH

    def build_config(self, config):
        config.setdefaults('General', 
                {
                    'show_bot_activity': 'False',
                    'appeals': '/:бот,',
                    'bot_name': '(Бот)',
                    'mark_type': 'кавычка',
                    'use_custom_commands': 'False',
                    'protect_cc': 'True',
                    'bot_activated': 'False',
                    'openweathermap_api_key': '0'
                }
            )

    def build_settings(self, settings):
        settings.add_json_panel(
            'Настройки бота. Версия %s' % __version__, self.config, data=
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
            "type": "string",
            "title": "Имя бота",
            "desc": "Используется в случае выбора имени как способа отмечать сообщения",
            "section": "General",
            "key": "bot_name"
            },
            {
            "type": "options",
            "title": "Отметка сообщений бота",
            "section": "General",
            "key": "mark_type",
            "options": ["кавычка", "имя"]
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

    def open_captcha_popup(self, capthca):
        CaptchaPopup().open(capthca)

    def open_twofa_popup(self, vk, auth_response_page):
        TwoFAKeyEnterPopup().open(vk, auth_response_page)

    def _get_captchas(self, service):
        service.request_captchas()

    def _show_captchas(self, captcha_requests):
        for request in captcha_requests:
            pass

    def _export_logs(self):
        if not os.path.exists(PATH + '.logs/'):
            os.makedirs(PATH + '.logs/')
        if not os.path.exists(PATH + '.service_logs/'):
            os.makedirs(PATH + '.service_logs/')

        from shutil import copyfile

        if os.path.exists('.kivy/logs/'):
            for file in os.listdir('.kivy/logs/'):
                copyfile('.kivy/logs/' + file, PATH + '.logs/' + file)
        if os.path.exists('service/.kivy/logs/'):
            for file in os.listdir('service/.kivy/logs/'):
                copyfile('service/.kivy/logs/' + file, PATH + '.service_logs/' + file)

    def _open_url(*args):
        import webbrowser
        webbrowser.open(args[1][1])

    def on_pause(self):
        return True


if __name__ == '__main__':
    VKBotApp().run()
