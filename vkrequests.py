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

            elif 'Failed receiving session' in error:
                print('Error receiving session!')

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
    scope = '69632' # messages, offline permissions
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
    finally:
        return session.access_token


@vk_request_errors
def get_message_long_poll_data():
    response = api.messages.getLongPollServer()
    return response

@vk_request_errors
def get_new_messages(**kwargs):
    ts = kwargs.get('ts')
    pts = kwargs.get('pts')
    if not ts or not pts:
        new_ts, new_pts = get_long_poll_data()
    return api.messages.getLongPollHistory(
        ts=ts if ts else new_ts,
        pts=pts if pts else new_pts
    )


@vk_request_errors
def send_message(**kwargs):
    """
    """
    gid = None
    uid = kwargs.get('uid')
    if not uid:
        gid = kwargs['gid']
    text = kwargs['text']
    forward = kwargs.get('forward')
    rnd_id = kwargs['rnd_id']

    response = api.messages.send(
        peer_id=uid, message=text,
        forward_messages=forward,
        chat_id=gid, random_id=rnd_id
    )
    
    return response


@vk_request_errors
def get_user_name(**kwargs):
    uid = str(kwargs['uid'])

    if int(uid) < 0: # группа
        response = api.groups.getById(group_id=uid[1:])
        name = response[0]['name']
    else:
        response = api.users.get(user_ids=uid)
        name = response[0]['first_name'] + ' ' + response[0]['last_name']
    return name


@vk_request_errors
def do_message_long_poll_request(**kwargs):
    """
    :url: специальный url, собранный с использованием данных из get_message_long_poll_data()
    Этот метод должен быть запущен в отдельном потоке.
    Он вернёт ответ только когда случится определённое событие.
    
    Возвращает: json список событий или [] (если истекло время ожидания)
    Структура события:
        События различаются первой цифрой:
            1 - Замена флагов сообщения
                [1, id сообщения ( int ), сумма флагов]
                Возможные флаги сообщения:
                    1 - сообщение не прочитано
                    2 - исходящее сообщение
                    4 - на сообщение был создан ответ
                    8 - помеченное сообщение
                    16 - сообщение отправлено через чат
                    32 - сообщение отправлено другом
                    64 - сообщение помечено как "Спам"
                    128 - сообщение удалено (в корзине)
                    256 - сообщение проверено пользователем на спам
                    512 - сообщение содержит медиаконтент
            2 - Установка флагов сообщения
                [2, id сообщения ( int ), сумма флагов]
            3 - Сброс флагов сообщения
                [3, id сообщения ( int ), сумма флагов]
            4 - Обнаружено новое сообщение
                [
                    4,
                    id сообщения ( int ),
                    сумма флагов сообщения ( int ),
                    id назначения ( int )(для пользователя его id, для беседы 2000000000 + id беседы, для группы -id группы или id группы + 1000000000),
                    время отправки сообщения в Unixtime ( int ),
                    тема сообщения (для диалога == ' ... ', для беседы это название беседы),
                    текст сообщения ( str ),
                    словарь вложений или {},
                    параметр random_id ( int ), если он был передан при отправке сообщений (нужен для предотвращения отправки одного сообщения несколько раз)
                ]
            6 - Прочитаны входящие сообщения на данном отрезке
                [
                    6,
                    id назначения ( str )(для пользователя его id, для беседы 2000000000 + id беседы, для группы -id группы или id группы + 1000000000),
                    до ( int )
                ]
            7 - Прочитаны исходящие сообщения на данном отрезке
                [
                    7,
                    id назначения ( str )(для пользователя его id; для беседы 2000000000 + id беседы; для группы -id группы или id группы + 1000000000),
                    до ( int )
                ]
            8 - Друг зашёл на сайт
                [8, -id пользователя ( int ), extra???]
            9 - Друг вышел с сайта
                [9, -id пользователя ( int ), extra???]
            10 - Сброшен флаг диалога
                [10, флаг диалога]
                Флаги диалога:
                    1 - важный диалог
                    2 - диалог с ответом от группы
            11 - Заменён флаг диалога
                [11, флаг диалога]
            12 - Установлен флаг диалога
                [12, флаг диалога]
            51 - Изменились параметры беседы (название/состав)
                [51, id беседы ( int ), изменения сделаны пользователем (1/0)]
            61 - Пользователь начал набирать текст в диалоге
                [61, id пользователя ( int ), id диалога ( int )]
            62 - Пользователь начал набирать текст в беседе
                [62, id пользователя ( int ), id беседы ( int )]
            70 - Пользователь совершил звонок
                [70, id пользователя ( int ), идентификатор звонка ( int )]
                Идентификаторы звонка:
                    ???
            80 - Изменение счётчика непрочитанных сообщений
                [80, значение счётчика ( int ), 0]
            114 - Изменены настройки оповещений
                [
                    114,
                    id пользователя или беседы ( int ),
                    звуковые сообщения включены (1/0),
                    оповещения отключены до: -1 - навсегда; 0 - включены; другое число - когда нужно включить
                ]
    Более полная информация о событиях:
    https://vk.com/dev/using_longpoll?f=3.%20%D0%A1%D1%82%D1%80%D1%83%D0%BA%D1%82%D1%83%D1%80%D0%B0%20%D1%81%D0%BE%D0%B1%D1%8B%D1%82%D0%B8%D0%B9
    """
    url = kwargs['url']
    return r.post(url)


@vk_request_errors
def get_user_id(**kwargs):
    user_link = kwargs.get('link')
    response = api.users.get(user_ids=user_link)
    return response[0]['id']


@vk_request_errors
def get_self_id():
    return api.users.get()[0]['id']


@vk_request_errors
def track_visitor():
    api.stats.trackVisitor()