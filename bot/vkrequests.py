# coding:utf8


import time, traceback

from kivy.app import App
from kivy.logger import Logger

from libs import vk_api as vk

from utils import load_token, save_token


def error_catcher(request):
    def do_request(*args, **kwargs):
        error = None

        try:
            response = request(*args, **kwargs)
        except Exception as raw_error:
            error = str(raw_error).lower()

            if error == 'captcha needed':
                return False, raw_error
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


@error_catcher
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
    else:
        session_params['token'] = token
        if not token:
            return False

    session = vk.VkApi(**session_params)
    session.auth(reauth=True if login and password else False)
    api = session.get_api()

    _save_token()
    return True


@error_catcher
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


@error_catcher
def get_self_id():
    return api.users.get()[0]['id']


@error_catcher
def get_message_long_poll_data():
    return api.messages.getLongPollServer(need_pts=1)


@error_catcher
def get_message_updates(ts, pts):
    response = api.messages.getLongPollHistory(ts=ts, pts=pts)

    return response['history'], response['new_pts'], response['messages']


@error_catcher
def get_album_size(album_id):
    return api.photos.get(count=0, album_id=album_id)['count']


@error_catcher
def get_photo_id(album_id, offset=0):
    photo = api.photos.get(offset=offset, album_id=album_id)['items'][0]
    media_id = 'photo' + str(photo['owner_id']) + '_' + str(photo['id'])

    return media_id


@error_catcher
def get_status():
    return api.status.get()


@error_catcher
def set_status(text):
    api.status.set(text=text)

    return True


@error_catcher
def get_user_name(user_id=None, name_case='nom'):
    response = api.users.get(user_ids=user_id, name_case=name_case)[0]

    return response['first_name'] + ' ' + response['last_name']


@error_catcher
def get_user_city(user_id=None):
    return api.users.get(user_ids=user_id, fields='city')[0]['city']['title']
