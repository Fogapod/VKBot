# coding:utf8

import os
from time import sleep
import sys

from kivy import platform
from kivy.logger import Logger
from kivy.lib import osc

parent_path = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
parent_path += '\\' if platform == 'win' else '/'
os.sys.path.append(parent_path)

import bot.utils
if platform != 'android':
    bot.utils.PATH = parent_path + bot.utils.PATH
bot.utils.DATA_PATH = parent_path + bot.utils.DATA_PATH

from bot.core import LongPollSession


def ping(*args):
    global session
    if session.running:
        osc.sendMsg('/pong', [], port=3002)

def send_text(text):
    osc.sendMsg('/text', [text, ], port=3002)

def send_status(status):
    osc.sendMsg('/status', [status, ], port=3002)

def send_error(error):
    osc.sendMsg('/error', [error, ], port=3002)
    Logger.info(error)

def send_answers_count():
    osc.sendMsg('/answers', [session.reply_count, ], port=3002)

def set_launch_params(message, *args):
    global session, got_launch_params, activated
    got_launch_params = True
    launch_params = eval(message[2])
    activated = launch_params['activated']
    session.load_params(**launch_params)

def exit(*args):
    send_status('exiting')
    session.runtime_error = 1
    sys.exit()


if __name__ == '__main__':
    got_launch_params = False
    activated = False 
    osc.init()
    oscid = osc.listen(ipAddr='0.0.0.0', port=3000)
    osc.bind(oscid, ping, '/ping')
    osc.bind(oscid, set_launch_params, '/launch_params')    
    osc.bind(oscid, exit, '/exit')    

    session = LongPollSession()
    send_status('connected')
    authorized, error = session.authorization()

    if error:
        send_error(error)
        exit()
    
    while not got_launch_params:
        osc.readQueue(oscid)
        sleep(0.1)

    send_status('got params')
    session.launch_bot()
    while True:
        osc.readQueue(oscid)
        send_answers_count()
        if session.activated != activated:
            activated = session.activated
            osc.sendMsg('/activation_changed', [str(activated), ], port=3002)
        if session.runtime_error:
            send_error(session.runtime_error)
            break
        if not session.running:
            break
        sleep(1)
    exit()
