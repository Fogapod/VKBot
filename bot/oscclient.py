# coding:utf8


import time

from ast import literal_eval

from kivy.lib import osc
from kivy.clock import Clock
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
        self.osc.bind(self.oscid, self.return_log, '/log')
        self.osc_read_event = None
        self.answers_request_event = None
        self.start_reading_osc_queque()
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

    def start_reading_osc_queque(self):
        if not self.osc_read_event:
            self.osc_read_event = Clock.schedule_interval(
                lambda *x: self.osc.readQueue(self.oscid),
                0.1
            )

    def stop_reading_osc_queque(self):
        if self.osc_read_event:
            self.osc_read_event.cancel()
            self.osc_read_event = None

    def start(self):
        self.start_reading_osc_queque()

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

        self.stop_reading_osc_queque()

    def ping(self):
        self.mainscreen.put_log_to_queue(
            u'Проверяю, запущен ли бот...', 1, time.time()
        )
        self.osc.sendMsg('/ping', [], port=3000)

    def pong(self, message, *args):
        self.mainscreen.put_log_to_queue(
            u'Бот уже запущен! Переподключаюсь',
            2, time.time()
        )
        self.start_requesting_answers_count()
        self.mainscreen.ids.main_btn.text = self.mainscreen.stop_bot_text

    def read_status(self, message, *args):
        status = message[2]
        if status == 'launched':
            self.mainscreen.put_log_to_queue(
                u'Бот запущен', 2, time.time()
            )
            self.mainscreen.ids.main_btn.text = self.mainscreen.stop_bot_text
        elif status == 'exiting':
            self.mainscreen.put_log_to_queue(
                u'Бот полностью остановлен', 2, time.time()
            )
            self.mainscreen.ids.main_btn.text = self.mainscreen.launch_bot_text

    def set_answers_count(self, message, *args):
        self.answers_count = str(message[2])
        if self.mainscreen:
            self.mainscreen.update_answers_count(self.answers_count)

    def return_log(self, message, *args):
        # from kivy.logger import Logger
        # Logger.info(str(message[2]))
        self.mainscreen.put_log_to_queue(*literal_eval(message[2]))
