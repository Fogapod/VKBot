# coding:utf8


import os

from kivy.app import App
from kivy.lang import Builder
from kivy.config import Config
from kivy.uix.settings import SettingsWithNoMenu

from uix.screens import Manager, AuthPopup, TwoFAPopup, CaptchaPopup

from bot.core import __version__
from bot.oscclient import OSCClient
from bot.utils import SETTINGS_FILE_PATH, CUSTOM_COMMANDS_FILE_PATH, PATH


class VKBotApp(App):
    use_kivy_settings = False
    settings_cls = SettingsWithNoMenu
    config_version = 1

    _cached_login = None
    _cached_password = None


    def build(self):
        self.title = 'VKBot'

        self.load_kv_files()

        self.manager = Manager()
        self.manager.show_main_screen()

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
                    'config_version': '1',
                    'appeals': '/:бот,',
                    'bot_name': '(Бот)',
                    'mark_type': 'кавычка',
                    'stable_mode': 'True',
                    'use_custom_commands': 'True',
                    'logging_level': '1',
                    'max_log_lines': '50',
                    'bot_activated': 'False',
                    'openweathermap_api_key': '0'
                }
            )


    def build_settings(self, settings):
        settings.add_json_panel(
            'Настройки бота. Версия %s' % __version__, self.config, data=
        '''[
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
            "desc": "Нужно для того, чтобы отличать сообщения бота от ваших",
            "section": "General",
            "key": "mark_type",
            "options": ["кавычка", "имя"]
            },
            {
            "type": "bool",
            "title": "Устойчивый режим",
            "desc": "При возникновении ошибки, бот будет продолжать работу",
            "section": "General",
            "key": "stable_mode",
            "values": ["False","True"]
            },
            {
            "type": "title",
            "title": "Пользовательские команды"
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
            "type": "title",
            "title": "Логгирование"
            },
            {
            "type": "options",
            "title": "Уровень логгирования",
            "desc": "Чем больше значение, тем меньше информации будет выведено",
            "section": "General",
            "key": "logging_level",
            "options": ["0", "1", "2"]
            },
            {
            "type": "options",
            "title": "Максимальное количество строк лога",
            "desc": "Уменьшите значение, если у вас проблемы с производительностью",
            "section": "General",
            "key": "max_log_lines",
            "options": ["10", "30", "50", "100", "200"]
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


    def on_config_change(self, config, section, key, value):
        if config is self.config:
            if section == 'General':
                if key == 'max_log_lines':
                    self.manager.get_screen('main_screen').max_log_lines = \
                        int(value)
                elif key == 'logging_level':
                    self.manager.get_screen('main_screen').logging_level = \
                        int(value)


    def send_auth_request(self, login, password):
        self.osc_service.send_auth_request(login, password)


    def open_auth_popup(self):
        AuthPopup().open()


    def open_captcha_popup(self, capthca_image_url):
        CaptchaPopup(capthca_image_url, self).open()


    def open_twofa_popup(self): #, vk, auth_response_page):
        TwoFAPopup(self).open() #vk, auth_response_page)


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
        webbrowser.open(args[1][1].encode('utf8'))


    def on_start(self):
        Config.read(self.get_application_config())
        config_file_version = \
            int(Config.getdefault('General', 'config_version', 0))

        if config_file_version < self.config_version:
            self.config.write()

        self.osc_service = OSCClient(self)


    def on_pause(self):
        return True


    def on_close(self):
        self.manager.get_screen('main_screen').stop_log_check_thread()


if __name__ == '__main__':
    VKBotApp().run()
