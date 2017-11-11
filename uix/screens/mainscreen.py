# coding:utf8


import time
import traceback
from threading import Thread

from kivy.app import App

from uix.widgets import ColoredScreen

from bot import utils


class MainScreen(ColoredScreen):
    def __init__(self, **kwargs):
        super(MainScreen, self).__init__(**kwargs)
        self.app = App.get_running_app()
        self.launch_bot_text = 'Включить бота'
        self.launching_bot_text = 'Запуск (отменить)' 
        self.stop_bot_text = 'Выключить бота'
        self.ids.main_btn.text = self.launch_bot_text
        self.logging_level = int(
            self.app.config.getdefault(
                'General', 'logging_level', 1
            )
        )
        self.max_log_lines = int(
            self.app.config.getdefault(
                'General', 'max_log_lines', 50
            )
        )
        self.log_queue = []
        self.continue_reading_log_queue = True
        self.log_check_thread = Thread(target=self.read_log_queue)
        self.log_check_thread.start()


    def on_main_btn_press(self):
        if self.ids.main_btn.text == self.launch_bot_text:
            self.ids.main_btn.text = self.launching_bot_text
            self.app.osc_service.start()
        else:
            self.app.osc_service.stop()
            self.ids.main_btn.text = self.launch_bot_text


    def update_answers_count(self, new_answers_count):
        self.ids.actionprevious.title = 'Ответов: %s' % new_answers_count


    def read_log_queue(self):
        while self.continue_reading_log_queue:
            time.sleep(0.33)
            if not self.log_queue \
                    or not str(
                        self.app.manager.current_screen
                    )[14:-2] == 'main_screen':

                continue

            try:
                _log_queue = sorted(self.log_queue, cmp=lambda x,y: cmp(x[2], y[2]))
                new_lines = ''

                for message in _log_queue:
                    self.log_queue.remove(message)

                    if message[1] >= self.logging_level:
                        new_lines += time.strftime(
                            '\n[%H:%M:%S] ', time.localtime(message[2])
                        ) + message[0]

                new_lines = utils.safe_format(new_lines,
                    whitelist_file=utils.WHITELIST_FILE,
                    blacklist_file=utils.BLACKLIST_FILE,
                    bot_error_file=utils.BOT_ERROR_FILE,
                    custom_commands_file=utils.CUSTOM_COMMANDS_FILE
                )

                log_text = self.ids.logging_panel.text
                new_log_text = log_text + new_lines
                indent_num = new_log_text.count('\n')

                while indent_num > self.max_log_lines:
                    new_log_text = new_log_text[new_log_text.index('\n') + 1:]
                    indent_num -= 1

                self.ids.logging_panel.text = new_log_text

            except:
                self.ids.logging_panel.text += \
                    u'\n[b]Возникла ошибка! Не могу отобразить лог[/b]\n'
                self.ids.logging_panel.text += traceback.format_exc()


    def stop_log_check_thread(self):
        self.continue_reading_log_queue = False
        if self.log_check_thread:
            self.log_check_thread.join()


    def put_log_to_queue(self, line, log_importance, time):
        self.log_queue.append((line, log_importance, time))


    def logout(self):
        self.put_log_to_queue(u'Записываю пустой токен...', 0, time.time())
        utils.save_token('')
        self.put_log_to_queue(u'[b]Сессия сброшена[/b]', 2, time.time())