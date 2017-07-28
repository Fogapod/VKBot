# coding:utf8


import os
import sys
import logging

from time import sleep

from kivy import platform
from kivy.logger import Logger
from kivy.config import Config
from kivy.lib import osc

parent_path = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
parent_path += '\\' if platform == 'win' else '/'
os.sys.path.append(parent_path)


from bot import utils
from bot.core import LongPollSession

if platform != 'android':
    utils.PATH = parent_path + utils.PATH
utils.DATA_PATH = parent_path + utils.DATA_PATH

utils.update_paths()

logging.captureWarnings(True)


def update_params():
    global activated
    global openweathermap_api_key

    Config.read(utils.SETTINGS_FILE_PATH)
    appeals = Config.get('General', 'appeals')
    activated = Config.get('General', 'bot_activated')
    bot_name = Config.get('General', 'bot_name')
    mark_type = Config.get('General', 'mark_type')
    use_custom_commands = Config.get('General', 'use_custom_commands')
    protect_custom_commands = Config.get('General', 'protect_cc')
    openweathermap_api_key = Config.get('General', 'openweathermap_api_key')

    session.load_params(appeals,
        activated=activated == 'True',
        bot_name=bot_name, mark_type=mark_type,
        use_custom_commands=use_custom_commands == 'True',
        protect_custom_commands=protect_custom_commands == 'True',
        openweathermap_api_key=openweathermap_api_key
    )
                        
def ping(*args):
    global session
    if session.running:
        osc.sendMsg('/pong', [], port=3002)

def send_status(status):
    osc.sendMsg('/status', [status, ], port=3002)

def send_error(error):
    osc.sendMsg('/error', [error, ], port=3002)

def send_answers_count():
    osc.sendMsg('/answers', [session.reply_count, ], port=3002)

def exit(*args):
    global session
    session.stop_bot()
    send_status('exiting')
    sys.exit()


if __name__ == '__main__':
    osc.init()
    oscid = osc.listen(ipAddr='0.0.0.0', port=3000)
    send_status('connected')

    osc.bind(oscid, ping, '/ping')
    osc.bind(oscid, exit, '/exit')

    try:
        session = LongPollSession()
        authorized, error = session.authorization()

        if error:
            send_error(error)
            exit()

        update_params()

        session.launch_bot()

        send_status('launched')
    except SystemExit:
        raise
    except:
        import traceback
        error = traceback.format_exc()
        send_error(error)
        exit()

    while True:
        osc.readQueue(oscid)
        send_answers_count()
        if session.activated != activated:
            activated = session.activated
            Config.read(utils.SETTINGS_FILE_PATH)
            Config.set('General', 'bot_activated', str(activated))
            Config.write()
        if session.openweathermap_api_key != openweathermap_api_key:
            openweathermap_api_key = session.openweathermap_api_key
            Config.read(utils.SETTINGS_FILE_PATH)
            Config.set(
                'General', 'openweathermap_api_key', openweathermap_api_key
            )
            Config.write()
        if session.runtime_error:
            if session.runtime_error != 1:
                send_error(session.runtime_error)
            break
        if session.need_restart:
            session.stop_bot()
            update_params()
            session.launch_bot()
            session.need_restart = False
        elif not session.running:
            break
        sleep(1)
    exit()
