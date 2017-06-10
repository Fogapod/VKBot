# coding:utf8


import time

from kivy.app import App
from kivy.lib import osc
from kivy.clock import Clock
from kivy import platform

if platform == 'android':
    from android import AndroidService


class OSCClient():
    def __init__(self, mainscreen):
        if platform == 'android':
            self.androidservice = AndroidService('VKBot', 'Бот работает')
        self.mainscreen = mainscreen
        self.osc = osc
        self.osc.init()
        oscid = self.osc.listen(port=3002)
        self.osc.bind(oscid, self.pong, '/pong')
        self.osc.bind(oscid, self.read_status, '/status')
        self.osc.bind(oscid, self.set_answers_count, '/answers')
        self.osc.bind(oscid, self.return_error, '/error')
        self.osc.bind(oscid, self.activation_changed, '/activation_changed')
        self.read_event = Clock.schedule_interval(lambda *x: self.osc.readQueue(oscid), 0)
        self.ping()
        self.answers_count = '0'
        self.started = False

    def start(self):
        if platform == 'android':
            self.androidservice.start('Сервис запущен')

    def stop(self):
        if platform == 'android':
            self.androidservice.stop()
        else:
            self.osc.sendMsg('/exit', [], port=3000)
        self.started = False

    def ping(self):
        self.osc.sendMsg('/ping', [], port=3000)

    def on_response(self, message, *args, **kwargs):
        print message

    def pong(self, message, *args):
        # self.on_response(message)
        self.mainscreen.ids.main_btn.text = self.mainscreen.stop_bot_text

    def read_status(self, message, *args):
        # self.on_response(message)
        status = message[2]
        if status == 'got params':
            self.mainscreen.ids.main_btn.text = self.mainscreen.stop_bot_text
        elif status == 'listening':
            pass
        elif status == 'exiting':
            self.mainscreen.stop_bot(None)

    def set_answers_count(self, message, *args):
        # self.on_response(message)
        self.answers_count = str(message[2])
        if self.mainscreen:
            self.mainscreen.update_answers_count(self.answers_count)

    def return_error(self, message, *args):
        # self.on_response(message)
        error = message[2]
        self.mainscreen.show_bot_error(error)

    def activation_changed(self, message, *args):
        # self.on_response(message)
        new_activation_status = message[2]
        config = App.get_running_app().config
        config.set('General', 'bot_activated', new_activation_status)
        config.write()
