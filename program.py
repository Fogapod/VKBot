# coding:utf8


import os

from kivy.app import App
from kivy.lang import Builder
from kivy.config import Config
from kivy.uix.settings import SettingsWithNoMenu
from kivy.uix.screenmanager import ScreenManager, FadeTransition

from uix.popups.authpopup import AuthPopup
from uix.popups.twofapopup import TwoFAPopup
from uix.popups.captchapopup import CaptchaPopup
from uix.popups.loadingpopup import LoadingPopup
from uix.screens.mainscreen import MainScreen
from uix.screens.customcommandsscreen import CustomCommandsScreen

from bot.oscclient import OSCClient
from bot import utils


class VKBotApp(App):
    use_kivy_settings = False
    settings_cls = SettingsWithNoMenu
    config_version = 1

    _cached_login = None
    _cached_password = None

    loading_popup = None

    def build(self):
        self.title = 'VKBot'

        self.load_kv_files()

        self.manager = Manager()
        self.manager.show_main_screen()

        return self.manager

    def load_kv_files(self):
        directories = ['uix/kv/']

        for directory in directories:
            for f in os.listdir(directory):
                if f.endswith('.kv'):
                    Builder.load_file(directory + f)
                else:
                    continue

    def get_application_config(self):
        return utils.SETTINGS_FILE

    def build_config(self, config):
        config.setdefaults('General', {
                                        'config_version': '1',
                                        'appeals': '/:бот,',
                                        'bot_name': '(Бот)',
                                        'mark_type': 'кавычка',
                                        'stable_mode': 'True',
                                        'use_custom_commands': 'True',
                                        'logging_level': '1',
                                        'max_log_lines': '50',
                                        'openweathermap_api_key': '0'
                                      }
                           )

    def build_settings(self, settings):
        settings.add_json_panel(
            'Настройки бота. Версия %s' % utils.__version__,
            self.config,
            data='''
            [
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
                }
            ]''' % utils.CUSTOM_COMMANDS_FILE)

    def on_config_change(self, config, section, key, value):
        if config is self.config:
            if section == 'General':
                if key == 'max_log_lines':
                    self.manager.get_screen('main_screen').max_log_lines = \
                        int(value)
                elif key == 'logging_level':
                    self.manager.get_screen('main_screen').logging_level = \
                        int(value)

    def open_auth_popup(self):
        AuthPopup(self).open()

    def open_twofa_popup(self):
        TwoFAPopup(self).open()

    def open_captcha_popup(self, capthca_image_url):
        CaptchaPopup(self, capthca_image_url).open()

    def open_loading_popup(self):
        self.loading_popup = LoadingPopup()
        self.loading_popup.open()

    def close_loading_popup(self):
        if self.loading_popup:
            self.loading_popup.dismiss()

    def _export_logs(self):
        if not os.path.exists(utils.MAIN_DIR + '.logs/'):
            os.makedirs(utils.MAIN_DIR + '.logs/')
        if not os.path.exists(utils.MAIN_DIR + '.service_logs/'):
            os.makedirs(utils.MAIN_DIR + '.service_logs/')

        from shutil import copyfile

        if os.path.exists('.kivy/logs/'):
            for file in os.listdir('.kivy/logs/'):
                copyfile('.kivy/logs/' + file, utils.MAIN_DIR + '.logs/' + file)
        if os.path.exists('service/.kivy/logs/'):
            for file in os.listdir('service/.kivy/logs/'):
                copyfile(
                    'service/.kivy/logs/' + file,
                    utils.MAIN_DIR + '.service_logs/' + file)

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

    def on_stop(self):
        if getattr(self, 'manager', None):
            try:
                self.manager.get_screen('main_screen').stop_log_check_thread()
            except:
                pass


class Manager(ScreenManager):
    def __init__(self, **kwargs):
        super(Manager, self).__init__(**kwargs)
        self.transition = FadeTransition()
        self.last_screen = None

    def show_main_screen(self):
        if 'main_screen' not in self.screen_names:
            self.add_widget(MainScreen())
        self.current = 'main_screen'

    def show_custom_commands_screen(self):
        if 'cc_screen' not in self.screen_names:
            self.add_widget(CustomCommandsScreen())
        self.current = 'cc_screen'


if __name__ == '__main__':
    VKBotApp().run()
