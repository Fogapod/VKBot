# coding:utf8


import os
import sys
import traceback
import time

from ast import literal_eval

from kivy import platform
from kivy.lib import osc
from kivy.utils import escape_markup

if platform == 'android':
    os.sys.path.append(os.path.dirname(os.getcwd()))  # go to parent folder
else:
    os.sys.path.append(os.getcwd())


from bot import utils
from bot.core import Bot

# GLOBALS

authorized = False
twofactor_code = None
captcha_code = None


def pong(*args):
    global bot
    if bot.running:
        osc.sendMsg('/pong', [], port=3002)


def send_status(status):
    osc.sendMsg('/status', [status, ], port=3002)


def send_error(error):
    send_log_line(u'[b]Во время работы произошла непредвиденная ошибка![/b]', 2)
    send_log_line(escape_markup(error.decode('unicode-escape')), 2)

    utils.save_error(error, from_bot=True)

    send_log_line(u'[b]Ошибка сохранена в файле {bot_error_file}[/b]', 2)


def send_answers_count(*args):
    osc.sendMsg('/answers count', [bot.reply_count, ], port=3002)


def send_log_line(line, log_importance, t=None):
    if t is None:
        t = time.time()

    osc.sendMsg('/log', [str((line, log_importance, t)), ], port=3002)


def exit(*args):
    bot.stop_bot()
    send_status('exiting')
    sys.exit()


def first_auth():
    global authorized
    authorized = False

    osc.sendMsg('/first auth', [], port=3002)

    while not authorized:
        time.sleep(0.5)
        osc.readQueue(oscid)


def on_auth_request(message, *args):
    global authorized
    login, password = literal_eval(message[2])
    send_log_line(u'Логин и пароль доставлены', 0)

    authorized, error = bot.authorization(
        login=login, password=password,
        twofactor_handler=twofactor_handler, captcha_handler=captcha_handler
    )
    if error:
        osc.sendMsg('/auth failed', [], port=3002)
        if error == 'bad password':
            send_log_line(u'[b]Неправильный логин или пароль[/b]', 2)
        else:
            send_error(error)

        exit()

    osc.sendMsg('/auth successful', [], port=3002)


def twofactor_handler():
    global twofactor_code
    twofactor_code = None
    osc.sendMsg('/auth twofactor needed', [], port=3002)

    while not twofactor_code:
        time.sleep(0.5)
        osc.readQueue(oscid)

    send_log_line(u'Повторяю запрос с кодом', 0)
    return twofactor_code, True


def captcha_handler(captcha):
    global captcha_code
    captcha_code = None
    osc.sendMsg('/auth captcha needed', [captcha.get_url(), ], port=3002)

    while not captcha_code:
        time.sleep(0.5)
        osc.readQueue(oscid)

    send_log_line(u'Повторяю запрос с капчей', 0)
    captcha.try_again(captcha_code)


def on_twofactor(message, *args):
    send_log_line(u'Код получен', 1, time.time())
    global twofactor_code
    twofactor_code = message[2]


def on_captcha(message, *args):
    send_log_line(u'Код получен', 1, time.time())
    global captcha_code
    captcha_code = message[2]


if __name__ == '__main__':
    osc.init()
    send_log_line(u'Служба OSC подключена', 0)
    oscid = osc.listen(ipAddr='0.0.0.0', port=3000)

    osc.bind(oscid, pong, '/ping')
    osc.bind(oscid, exit, '/exit')
    osc.bind(oscid, send_answers_count, '/request answers count')
    osc.bind(oscid, on_auth_request, '/auth request')
    osc.bind(oscid, on_twofactor, '/twofactor response')
    osc.bind(oscid, on_captcha, '/captcha response')

    try:
        bot = Bot()
        bot.set_new_logger_function(send_log_line)
        send_log_line(u'Попытка авторизации ...', 0)

        authorized = False
        while not authorized:
            authorized, error = bot.authorization()

            if error:
                if error == 'no token':
                    first_auth()
                    break
                else:
                    send_log_line(u'Авторизация не удалась', 2)
                    send_error(error)
                    exit()

        send_log_line(u'Авторизация прошла без ошибок', 1)

        send_log_line(u'Включение бота ...', 0)
        bot.launch_bot()

    except SystemExit:
        raise

    except:
        send_log_line(u'Обработка и отправка ошибки ...', 0)
        error = traceback.format_exc()
        send_error(error)
        exit()

    send_status('launched')

    while True:
        osc.readQueue(oscid)

        if bot.is_settings_changed:
            send_status('settings changed')
            bot.is_settings_changed = False

        if bot.runtime_error is not None:
            if bot.runtime_error == 0:
                send_log_line(u'[b]Бот остановлен через сообщение[/b]', 2)

            elif bot.runtime_error == 1:
                bot.runtime_error = None
                bot.stop_bot()
                bot.launch_bot()
                continue

            else:
                send_error(bot.runtime_error)
                bot.stop_bot()

            if bot.settings['stable_mode']:
                send_log_line(
                    u'Активирован устойчивый режим. '
                    u'Сброс параметров и повторный запуск бота ...',
                    1
                )
                bot.runtime_error = None
                bot.stop_bot()
                bot.launch_bot()
                send_log_line(u'Повторный запуск произведён', 0)

                continue
            else:
                break

        elif not bot.running:
            break

        time.sleep(1)
    exit()
