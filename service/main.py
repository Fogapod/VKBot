# coding:utf8

import os
from time import sleep
import sys

from kivy import platform
from kivy.lib import osc

parent_path = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
parent_path += '\\' if platform == 'win' else '/'
os.sys.path.append(parent_path)

import bot.utils
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

def send_answers_count():
    osc.sendMsg('/answers', [session.reply_count, ], port=3002)

def set_launch_params(message, *args):
    global session
    launch_params = eval(message[2])
    if launch_params:
        session.load_launch_params(**launch_params)

def start_bot(*args):
    global session
    session.launch_bot()

def stop_bot(*args):
    global session
    session.stop_bot()

def kill_session():
    send_status('exiting')
    sys.exit(0)


if __name__ == '__main__':
    osc.init()
    oscid = osc.listen(ipAddr='0.0.0.0', port=3000)
    osc.bind(oscid, ping, '/ping')
    osc.bind(oscid, set_launch_params, '/launch_params')
    osc.bind(oscid, start_bot, '/start')
    osc.bind(oscid, stop_bot, '/stop')

    session = LongPollSession()
    send_status('connected')
    authorized, error = session.authorization()

    if error:
        send_error(error)
        kill_session()

    while True:
        try:
            osc.readQueue(oscid)
            while session.running:
                send_status('listening')
                sleep(1)
                send_answers_count()
                # if session.response:
                    # send(session.response)
                osc.readQueue(oscid)
            send_status('not listening')
            if session.runtime_error:
                send_error(session.runtime_error)
                kill_session()
            else:
                if session.authorized:
                    send_status('authorized')
                else:
                    send_status('connected')
            sleep(1)
        except SystemExit:
            break
        except:
            session.stop_bot()
            kill_session()
