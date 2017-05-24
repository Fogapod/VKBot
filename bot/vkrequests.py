# coding:utf8


import time

try:
    from libs import vk
except ImportError:
    from .libs import vk

def error_catcher(request):
    def do_request(*args, **kwargs):
        error = None
        try:
            response = request(*args, **kwargs)
        except Exception as raw_error:
            raw_error = str(raw_error)
            error = raw_error.lower()

            if 'too many requests' in error or 'timed out' in error:
                print 'Too many requests/response time out'
                time.sleep(0.33)
                if request.__name__ == 'get_message_updates':
                    return False, error
                else:
                    return do_request(*args, **kwargs) # TODO: add counter

            elif '[errno 1]_ssl.c:503' in error:
                if request.__name__ == '_create_session':
                    print 'Sertificate verify failed. Trying unsafe request'
                    vk.api.Session.need_verify_request_sert = False
                    return do_request(*args, **kwargs)
                else:
                    print 'Sertificate verify failed.'

            elif 'connection' in error:
                print 'Check your connection'

            elif 'incorrect password' in error:
                print 'Incorrect password'
            
            elif 'invalid access_token' in error:
                print 'Invalid access_token'

            elif 'captcha' in error:
                print 'Capthca'
                #TODO обработать капчу

            elif 'auth check code is needed' in error:
                print 'Auth code is needed'

            else:
                print('\nUnknown error: ' + raw_error + '\n')
            return False, error
        else:
            return response, error
    return do_request


def log_in(**kwargs):
    """
    :token:
    :key:
    :login:
    :password:

    :return: string ( token )
    """
    error = None

    response, error = _create_session(**kwargs)
    if error:
        return response, error
    
    session = response

    global api
    api = vk.API(session, v='5.60')

    response, error = track_visitor()
    if error:
        return response, error
    else:
        return session.access_token, error


@error_catcher
def _create_session(**kwargs):
    scope = '70660' # messages, status, photos, offline
    app_id = '6045412'

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
    return session


@error_catcher
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
    attachments = kwargs.get('attachments', '')
    if type(attachments) is list:
        attachments = ','.join(attachments)

    response = api.messages.send(
        peer_id=uid, message=text,
        forward_messages=forward,
        chat_id=gid, random_id=rnd_id,
        attachment=attachments
    )
    
    return response


@error_catcher
def get_self_id(**kwargs):
    id = api.users.get()[0]['id']
    return id


@error_catcher
def get_message_long_poll_data():
    response = api.messages.getLongPollServer(
    	    need_pts=1
    	)
    return response


@error_catcher
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
    return response['history'], response['new_pts'], response['messages']


@error_catcher
def get_album_size(*args):
    album_id = args
    return api.photos.get(count=0, album_id=album_id)['count']


@error_catcher
def get_photo_id(**kwargs):
    album_id = kwargs['album_id']
    offset = kwargs.get('offset', 0)
    photo = api.photos.get(offset=offset, album_id=album_id)['items'][0]
    media_id = 'photo' + str(photo['owner_id']) + '_' + str(photo['id'])
    return media_id


@error_catcher
def get_status():
    response = api.status.get()
    return response


@error_catcher
def set_status(**kwargs):
    text = kwargs['text']
    api.status.set(text=text)
    return True


@error_catcher
def get_user_name(**kwargs):
    uid = kwargs.get('user_id')
    name_case = kwargs.get('name_case', 'nom')
    response = api.users.get(user_ids=uid, name_case=name_case)[0]
    return response['first_name'] + u' ' + response['last_name']

@error_catcher
def track_visitor():
    api.stats.trackVisitor()
    return True