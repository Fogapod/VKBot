# coding:utf8


import time

from kivy.lib import osc
from kivy.clock import Clock
from kivy import platform

from bot.utils import SETTINGS_FILE_PATH

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
        self.mainscreen = mainscreen
        self.osc = osc
        self.osc.init()
        oscid = self.osc.listen(port=3002)
        self.osc.bind(oscid, self.pong, '/pong')
        self.osc.bind(oscid, self.update_captcha_requests, '/captcha_request')
        self.osc.bind(oscid, self.read_status, '/status')
        self.osc.bind(oscid, self.set_answers_count, '/answers')
        self.osc.bind(oscid, self.return_error, '/error')
        self.read_event = Clock.schedule_interval(lambda *x: self.osc.readQueue(oscid), 0)
        self.ping()
        self.answers_count = '0'
        self.started = False

    def start(self):
        if platform == 'android':
            self.subprocess.start('Сервис запущен')
        else:
            self.subprocess = subprocess.Popen(['python2.7', 'service/main.py'])

    def stop(self):
        if platform == 'android':
            self.subprocess.stop()
        else:
            if self.subprocess is None:
                osc.sendMsg('/exit', [], port=3000)
            else:
                self.subprocess.kill()
        self.started = False

    def ping(self):
        self.osc.sendMsg('/ping', [], port=3000)

    def request_captchas(self):
        self.osc.sendMsg('/request_captchas', [], port=3000)

    def solve_captcha(self, captcha):
        pass

    def on_response(self, message, *args, **kwargs):
        print message

    def pong(self, message, *args):
        # self.on_response(message)
        self.mainscreen.ids.main_btn.text = self.mainscreen.stop_bot_text

    def update_captcha_requests(self, message, *args):
        # self.on_response(message)
        pass

    def read_status(self, message, *args):
        # self.on_response(message)
        status = message[2]
        if status == 'launched':
            self.mainscreen.ids.main_btn.text = self.mainscreen.stop_bot_text
        elif status == 'exiting':
            self.mainscreen.ids.main_btn.text = self.mainscreen.launch_bot_text

    def set_answers_count(self, message, *args):
        # self.on_response(message)
        self.answers_count = str(message[2])
        if self.mainscreen:
            self.mainscreen.update_answers_count(self.answers_count)

    def return_error(self, message, *args):
        # self.on_response(message)
        error = message[2]
        self.mainscreen.show_bot_error(error)
