# coding:utf8


import time

from ast import literal_eval

from kivy.lib import osc
from kivy.clock import Clock
from kivy.app import App
from kivy import platform

from bot.utils import SETTINGS_FILE_PATH, save_error, BOT_ERROR_FILE_PATH

if platform == 'android':
    from android import AndroidService
else:
    import subprocess


class OSCClient():
    def __init__(self, mainscreen):
        if platform == 'android':
            self.subprocess = AndroidService('VKBot', 'Бот работает')
        else:
            self.subprocess = None

        self.answers_count = '0'
        self.mainscreen = mainscreen
        self.osc = osc
        self.osc.init()
        self.oscid = self.osc.listen(port=3002)
        self.osc.bind(self.oscid, self.pong, '/pong')
        self.osc.bind(self.oscid, self.read_status, '/status')
        self.osc.bind(self.oscid, self.set_answers_count, '/answers count')
        self.osc.bind(self.oscid, self.return_log_from_service, '/log')
        self.osc_read_event = None
        self.answers_request_event = None
        self.start_reading_osc_queue()
        self.ping()


    def start_requesting_answers_count(self):
        if not self.answers_request_event:
            self.answers_request_event = Clock.schedule_interval(
                lambda *x: osc.sendMsg('/request answers count', [], port=3000),
                5
            )


    def stop_requesting_answers_count(self):
        if self.answers_request_event:
            self.answers_request_event.cancel()
            self.answers_request_event = None


    def start_reading_osc_queue(self):
        if not self.osc_read_event:
            self.osc_read_event = Clock.schedule_interval(
                lambda *x: self.osc.readQueue(self.oscid),
                0.1
            )


    def stop_reading_osc_queue(self):
        if self.osc_read_event:
            self.osc_read_event.cancel()
            self.osc_read_event = None


    def start(self):
        self.logging_function(u'Начинаю запуск бота', 1, time.time())
        self.start_reading_osc_queue()

        if platform == 'android':
            self.subprocess.start('Сервис запущен')
        else:
            self.subprocess = subprocess.Popen(['python2.7', 'service/main.py'])

        self.start_requesting_answers_count()


    def stop(self):
        self.stop_requesting_answers_count()

        if platform == 'android':
            self.subprocess.stop()
        else:
            osc.sendMsg('/exit', [], port=3000)

            if self.subprocess is not None:
                self.subprocess.kill()

        self.stop_reading_osc_queue()
        self.logging_function(u'[b]Бот полностью остановлен[/b]', 2, time.time())


    def ping(self):
        self.logging_function(u'Проверяю, запущен ли бот...', 1)
        self.osc.sendMsg('/ping', [], port=3000)


    def pong(self, message, *args):
        self.logging_function(
            u'[b]Бот уже запущен! Переподключение завершено[/b]',
            2, time.time()
        )
        self.start_requesting_answers_count()
        self.mainscreen.ids.main_btn.text = self.mainscreen.stop_bot_text


    def read_status(self, message, *args):
        status = message[2]

        if status == 'launched':
            self.logging_function(u'[b]Бот запущен[/b]', 2, time.time())
            self.mainscreen.ids.main_btn.text = self.mainscreen.stop_bot_text

        elif status == 'exiting':
            self.stop()
            self.mainscreen.ids.main_btn.text = self.mainscreen.launch_bot_text

        elif status == 'settings changed':
            app = App.get_running_app()
            app.close_settings()
            app.destroy_settings()
            app.load_config()


    def set_answers_count(self, message, *args):
        self.answers_count = str(message[2])
        if self.mainscreen:
            self.mainscreen.update_answers_count(self.answers_count)


    def return_log_from_service(self, message, *args):
        self.logging_function(*literal_eval(message[2]))


    def logging_function(self, message, log_importance, t=None):
        if time is None:
            t = time.time()
        self.mainscreen.put_log_to_queue(message, log_importance, t)
