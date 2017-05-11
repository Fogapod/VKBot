# coding:utf8


from kivy.lib import osc
from kivy.clock import Clock
from kivy import platform

if platform == 'android':
    from android import AndroidService


class OSCClient():
    def __init__(self, mainscreen):
        self.bot_launch_params = None
        self.running = False
        self.run_trigger = False
        self.mainscreen = mainscreen
        self.osc = osc
        self.osc.init()
        oscid = self.osc.listen(port=3002)
        self.osc.bind(oscid, self.pong, '/pong')
        self.osc.bind(oscid, self.read_status, '/status')
        self.osc.bind(oscid, self.set_answers_count, '/answers')
        self.osc.bind(oscid, self.return_error, '/error')
        self.osc.bind(oscid, self.on_response, '/text')
        self.read_event = Clock.schedule_interval(lambda *x: self.osc.readQueue(oscid), 0)
        self.ping()
        self.answers_count = '0'

    def start(self, **kwargs):
        self.bot_launch_params = kwargs
        if platform == 'android':
            androidservice = AndroidService('VKBot', 'Бот работает')
            androidservice.start('Сервис запущен')
        self.run_trigger = True

    def stop(self):
        self.osc.sendMsg('/stop', [], port=3000)
        self.run_trigger = False

    def ping(self):
        self.osc.sendMsg('/ping', [], port=3000)

    def on_response(self, message, *args, **kwargs):
        print message

    def pong(self, message, *args):
        self.on_response(message)
        self.running = True
        self.mainscreen.ids.main_btn.text = self.mainscreen.stop_bot_text

    def read_status(self, message, *args):
        self.on_response(message)
        status = message[2]
        if status == 'connected':
            self.osc.sendMsg('/launch_params', [str(self.bot_launch_params), ], port=3000)
        elif status == 'authorized':
            if self.run_trigger:
                self.osc.sendMsg('/start', [], port=3000)
        elif status == 'listening':
            self.running = True
        elif status == 'not listening':
            self.running = False
        elif status == 'exiting':
            self.running = False

    def set_answers_count(self, message, *args):
        # self.on_response(message)
        self.answers_count = str(message[2])
        if self.mainscreen:
            self.mainscreen.update_answers_count(self.answers_count)

    def return_error(self, message, *args):
        self.on_response(message)
        error = message[2]
