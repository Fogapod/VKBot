# -*- coding: utf-8 -*-
import time
import requests as r

import vk

def vk_request_errors(request):
    def request_errors(*args, **kwargs):
        # response = request(*args, **kwargs); time.sleep(0.66)
        # Для вывода ошибки в консоль
        try:
            response = request(*args, **kwargs)
        except Exception as error:
            error = str(error)
            if 'Too many requests per second' in error or 'timed out' in error:
                time.sleep(0.33)
                return request_errors(*args, **kwargs)

            elif 'Failed to establish a new connection' in error:
                print('Check your connection!')
                time.sleep(2)
                return request_errors(*args, **kwargs)

            elif 'incorrect password' in error:
                print('Incorrect password!')

            elif 'Read timed out' in error or 'Connection aborted' in error:
                print('WARNING\nResponse time exceeded!')
                time.sleep(0.66)
                return request_errors(*args, **kwargs)

            elif 'Failed loading' in error:
                raise

            elif 'Captcha' in error:
                print('Capthca!!!!!')
                #TODO обработать капчу

            elif 'Auth check code is needed' in error:
                print('Auth code is needed!')

            else:
                print('\nERROR! ' + error + '\n')
            return False
        else:
            return response
    return request_errors


@vk_request_errors
def log_in(**kwargs):
    # vk.logger.setLevel('DEBUG')
    """
    :token:
    :key:
    :login:
    :password:

    :return: string ( token )
    """
    scope = '70656' # messages, status, offline permissions
    app_id = '5746984'

    token = kwargs.get('token')
    key = str(kwargs.get('key'))

    if token:
        session = vk.AuthSession(
            access_token=token, scope=scope, app_id=app_id
        )
    elif key:
        login, password = kwargs['login'], kwargs['password']
        session = vk.AuthSession(
            user_login=login, user_password=password,
            scope=scope, app_id=app_id, key=key
        )
    else:
        login, password = kwargs['login'], kwargs['password']
        session = vk.AuthSession(
            user_login=login, user_password=password,
            scope=scope, app_id=app_id
        )

    global api
    try:
        api = vk.API(session, v='5.60')
        if not track_visitor():
            raise
    except: # session was not created
        return False
    else:
        return session.access_token


@vk_request_errors
def get_message_long_poll_data():
    response = api.messages.getLongPollServer(
    	    need_pts=1
    	)
    return response


@vk_request_errors
def send_message(**kwargs):
    """
    :gid:
    :uid:
    :forward:
    :rnd_id:
    
    Возвращает:
    """
    gid = None
    uid = kwargs.get('uid')
    if not uid:
        gid = kwargs['gid']
    text = kwargs['text']
    forward = kwargs.get('forward')
    rnd_id = kwargs.get('rnd_id', None)

    response = api.messages.send(
        peer_id=uid, message=text,
        forward_messages=forward,
        chat_id=gid, random_id=rnd_id
    )
    
    return response


@vk_request_errors
def get_user_name(**kwargs):
    uid = kwargs['uid']

    if uid < 0: # группа
        response = api.groups.getById(group_id=uid[1:])
        name = response[0]['name']
    else:
        response = api.users.get(user_ids=uid)
        name = response[0]['first_name'] + ' ' + response[0]['last_name']
    return name


@vk_request_errors
def get_message_updates(**kwargs):
    """
    :ts: server
    :pts: number of uodates to ignore
    
    Возвращает: массив с обновлениямии и ноаое значение pts или []
    """
    ts = kwargs['ts']
    pts = kwargs['pts']

    response = api.messages.getLongPollHistory(
    	    ts=ts, pts=pts
    	)

    if response:
        return response['history'], response['new_pts'], response['messages']


@vk_request_errors
def get_status():
    response = api.status.get()
    return response


@vk_request_errors
def set_status(**kwargs):
    text = kwargs['text']
    api.status.set(text=text)
    return True


@vk_request_errors
def track_visitor():
    api.stats.trackVisitor()
    return True