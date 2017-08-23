# coding:utf8


import time
import traceback

from kivy.app import App

from libs import vk_api as vk
from utils import load_token, save_token


def error_handler(request):
    def do_request(*args, **kwargs):
        error = None

        try:
            send_log_line(u'Вызов: %s' % request.__name__, 0)
            response = request(*args, **kwargs)
        except Exception as raw_error:
            send_log_line(u'Возникла ошибка: %s' % traceback.format_exc(), 0)
            error = str(raw_error).lower()

            if error == 'captcha needed' and request.__name__ == 'log_in':
                return False, raw_error

            elif 'timed out' in error:
                send_log_line(u'Ошибка timed out. Повторяю запрос...', 1)
                return do_request(*args, **kwargs)

            return False, error
        else:
            return response, error

    return do_request


def _auth_handler(vk, auth_response_page):
    App.get_running_app().open_twofa_popup(vk, auth_response_page)


def _captcha_handler(captcha):
    app = App.get_running_app()
    if app is None: # running in service
        pass
    else:
        app.open_captcha_popup(captcha)


def _save_token(token=None):
    if token is None:
        token = api._vk.token['access_token']
    save_token(token)


def set_new_logger_function(func):
    global send_log_line
    send_log_line = func


def send_log_line(line, log_importance):
    pass


@error_handler
def log_in(login=None, password=None, logout=False):
    global api

    if logout:
        api = None
        _save_token(token='')
        return False

    token = load_token()

    session_params = {
                        'auth_handler': _auth_handler,
                        'captcha_handler': _captcha_handler,
                        'app_id': '6045412',
                        'scope': '70660' # messages, status, photos, offline
                     }

    if login and password:
        session_params['login'] = login
        session_params['password'] = password

        session = vk.VkApi(**session_params)
        session.auth()
        _save_token()
    else:
        if not token:
            return False

        session_params['token'] = token

        session = vk.VkApi(**session_params)

        if not session.check_token():
            return False

    api = session.get_api()

    return True


@error_handler
def send_message(text='', gid=None, uid=None, forward=None, attachments=[]):
    if gid:
        gid -= 2000000000

    if type(attachments) is list:
        attachments = ','.join(attachments)

    response = api.messages.send(
        peer_id=uid, message=text,
        forward_messages=forward,
        chat_id=gid, attachment=attachments
    )

    return response


@error_handler
def get_self_id():
    return api.users.get()[0]['id']


@error_handler
def get_message_long_poll_data():
    return api.messages.getLongPollServer(need_pts=1)


@error_handler
def get_message_updates(ts, pts):
    response = api.messages.getLongPollHistory(ts=ts, pts=pts)

    return response['history'], response['new_pts'], response['messages']


@error_handler
def get_album_size(album_id):
    return api.photos.get(count=0, album_id=album_id)['count']


@error_handler
def get_photo_id(album_id, offset=0):
    photo = api.photos.get(offset=offset, album_id=album_id)['items'][0]
    media_id = 'photo%d_%d' % (photo['owner_id'], photo['id'])

    return media_id


@error_handler
def get_status():
    return api.status.get()


@error_handler
def set_status(text):
    api.status.set(text=text)

    return True


@error_handler
def get_name_by_id(object_id=None, name_case='nom'):
    if object_id is not None:
        object_id = int(object_id)

    if object_id is None or 0 < object_id < 2000000000: # user
        response = api.users.get(user_ids=object_id, name_case=name_case)[0]
        name = ' '.join((response['first_name'], response['last_name']))
    elif int(object_id) > 2000000000: # chat
        response = api.messages.getChat(chat_id=object_id-2000000000)
        name = response['title']
    elif int(object_id) < 1: # group
        response = api.groups.getById(group_id=abs(object_id))[0]
        name = response['name']
    else:
        name = 'Unknown object'

    return name

@error_handler
def get_user_city(user_id=None):
    return api.users.get(user_ids=user_id, fields='city')[0]['city']['title']


@error_handler
def get_real_user_id(user_short_link):
    return api.users.get(user_ids=user_short_link)[0]['id']
