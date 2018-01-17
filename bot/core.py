# coding:utf8


import time
import re
import random
import traceback

from threading import Thread

from plugins.pluginmanager import Pluginmanager

import utils
import vkrequests as vkr

AUTHOR_VK_ID = 180850898
AUTHOR = u'[id%d|Евгений Ершов]' % AUTHOR_VK_ID

VK_MESSAGE_LEN_LIMIT = 4096
MAX_LAST_MESSAGES = 50


class Response(object):
    """This class contains variables that will be used in response
    """

    def __init__(self, message, send_func):
        self.target      = 0      # message will be sent to this id
        self.sticker     = 0      # id of sticker to send (no text, attachments)
        self.text        = ''     # text to send
        self.attachments = []     # list of attachments 'photo1234_5678'
        self.do_mark     = True   # if True, message will be marked
        self.forward_msg = 0      # message id to forward

        if message.from_chat:
            self.target = message.chat_id
            self.forward_msg = message.msg_id
        else:
            self.target = message.user_id

        self.send = lambda: send_func(self)

    @property
    def sticker(self):
        return self.__sticker

    @sticker.setter
    def sticker(self, sticker):
        self.__sticker   = sticker
        self.text        = ''
        self.attachments = []
        self.do_mark     = False 
        self.forward_id  = 0

    @property
    def is_valid(self):
        return any(((self.text and self.text != 'pass'), self.attachments,
                     self.sticker)) and self.target != 0


class Message(object):
    """
    This class contains all nesessary information about recieved message
    Important: do NOT change anything!
    """

    def __init__(self, message, self_id, appeals):
        self.self_id = self_id  # id of bot owner
        self.appeals = appeals  # list of appeals

        self.raw_text = ''       # raw text of recieved message
        self.lower_text = ''     # lower version of raw text
        self.text = ''           # raw text with cutted appeal
        self.args = ['']         # raw text with cutted appeal, separated by ' '
        self.was_appeal = False  # True if text starts with one of the appeals
        self.from_user = False   # True if from user
        self.from_chat = False   # True if from chat
        self.from_group = False  # True if from group
        self.user_id = 0         # id of user
        self.real_user_id = 0    # id of user who has sent message
        self.chat_id = 0         # id of chat where message came from
        self.chat_users = []     # list of users in chat
        self.chat_name = ''      # chat title
        self.out = False         # True if message was sent by bot owner
        self.event_user_id = 0   # action_mid field
        self.event_text = ''     # action_text field
        self.msg_id = 0          # id of current message
        self.date = 0            # time when message uploaded

        if 'attachments' in message.keys() \
                and message['attachments'][0]['type'] == 'sticker':
            self.raw_text = 'sticker=%s:%s' % \
                (
                    message['attachments'][0]['sticker']['product_id'],
                    message['attachments'][0]['sticker']['id']
                )
        else:
            self.raw_text = message['body']

        self.text = self.raw_text
        self.lower_text = self.text.lower()

        if self.lower_text.startswith(self.appeals):
            self.was_appeal = True
            self.text = self.text[len(next(
                a for a in self.appeals if self.lower_text.startswith(a))):]

        self.text = self.text.strip()

        self.args = self.text.split(' ')
        self.lower_text = self.text.lower()

        self.msg_id = message['id']
        self.user_id = message['user_id']
        self.real_user_id = self.user_id

        if self.user_id == self.self_id:
            self.out = 1
        else:
            self.out = message['out']

        if 'chat_id' in message:
            self.from_chat = True
        elif self.user_id < 1:
            self.from_group = True
        else:
            self.from_user = True

        if self.from_chat:
            self.chat_id = message['chat_id'] + 2000000000
            self.chat_users = message['chat_users']
            self.chat_name = message['title']

            if not self.raw_text:
                action = message.get('action')

                if action:
                    event = 'bad event'

                    if action == 'chat_photo_update':
                        event = 'photo updated'

                    elif action == 'chat_photo_remove':
                        event = 'photo removed'

                    elif action == 'chat_create':
                        event = 'chat created'

                    elif action == 'chat_title_update':
                        event = 'title updated'

                    elif action == 'chat_invite_user' \
                            and not message.get('action_mid') == self.self_id:
                        event = 'user joined'

                    elif action == 'chat_kick_user' and not \
                            message['action_mid'] == self.self_id:
                        event = 'user kicked'

                    elif action == 'chat_pin_message':
                        event = 'message pinned'

                    elif action == 'chat_unpin_message':
                        event = 'message unpinned'

                    self.event_user_id = message.get('action_mid',  '')
                    self.event_text    = message.get('action_text', '')

                    self.raw_text = 'event=' + event
                    self.text = self.raw_text
                    self.lower_text = self.raw_text

        if self.from_user or self.from_group:
            if self.out:
                self.real_user_id = self.self_id

        self.date = message['date']

    def get_random_user_id(self):
        if self.from_chat:
            return random.choice(self.chat_users)

        return random.choice((self.self_id, self.user_id))


class Bot(object):
    def __init__(self):
        self.pluginmanager = Pluginmanager(self, vkr)

        self.authorized = False
        self.mlpd = None
        self.bot_thread = None
        self.running = False
        self.runtime_error = None
        self.reply_count = 0
        self.last_message_ids = []

        self.custom_commands = {}
        self.whitelist = {}
        self.blacklist = []

        self.settings = {}

        self.startup_response = None
        self.is_settings_changed = False

    def authorization(self, **kwargs):
        self.authorized, error = vkr.log_in(**kwargs)

        return self.authorized, error

    def update_processor(self):
        self.running = True
        self.runtime_error = None

        max_last_msg_ids = 30

        try:
            if not self.authorized:
                raise Exception('Не авторизован')

            self_id, error = vkr.get_self_id()

            self.pluginmanager.load_plugins()

            self.send_log_line(
                u'Загрузка файла whitelist\'а из {whitelist_file} ...',
                0
            )
            self.whitelist = utils.load_whitelist()

            self.send_log_line(
                u'Загрузка файла blacklist\'а из {blacklist_file} ...',
                0
            )
            self.blacklist = utils.load_blacklist()

            self.send_log_line(u'Загрузка настроек бота ...', 0)
            self.read_settings()

            if self.settings['use_custom_commands']:
                self.send_log_line(
                    u'Загрузка пользовательских команд из '
                    u'{custom_commands_file} ...',
                    0
                )
                self.custom_commands = utils.load_custom_commands()

            if self.startup_response:
                self.send_message(self.startup_response)
                self.startup_response = None

            while self.runtime_error is None:
                if not self.mlpd:
                    self.mlpd, error = vkr.get_message_long_poll_data()

                updates, error = vkr.get_message_updates(
                    ts=self.mlpd['ts'],
                    pts=self.mlpd['pts']
                )

                if updates:
                    history = updates['history']
                    self.mlpd['pts'] = updates['new_pts']
                    messages = updates['messages']

                    self.send_log_line(
                        u'Получено сообщений: %d' % messages['count'], 0)
                else:
                    raise Exception(error)

                for item in messages['items']:
                    for chat in updates['chats']:
                        if item['chat_id'] == chat['id']:
                            item['chat_users'] = chat['users']
                            break

                    message = Message(item, self_id, self.settings['appeals'])

                    if message.msg_id in self.last_message_ids or \
                            not message.text:
                        continue

                    response = Response(message, self.send_message)

                    response = \
                        self.pluginmanager.plugin_respond(message, response)

                    if not response.is_valid:
                        continue

                    self.send_message(self.format_response(message, response))

                    time.sleep(1)
                time.sleep(3)
        except Exception:
            self.send_log_line(u'Ошибка бота перехвачена', 0)
            self.runtime_error = traceback.format_exc()

        self.running = False

    def launch_bot(self):
        self.send_log_line(
            u'Создание отдельного потока для бота ...', 0, time.time()
        )
        self.bot_thread = Thread(target=self.update_processor)
        self.send_log_line(u'Запуск потока ...', 0, time.time())
        self.bot_thread.start()

        while not self.running:
            time.sleep(0.05)

            if self.runtime_error:
                raise Exception(self.runtime_error)

        self.send_log_line(
            u'Отдельный поток бота запущен и работает', 1, time.time()
        )
        return True

    def stop_bot(self):
        self.send_log_line(u'Остановка потока ...', 0, time.time())
        self.runtime_error = 0

        if self.bot_thread:
            self.bot_thread.join()

        self.send_log_line(u'Отдельный поток бота отключён', 1, time.time())
        return True

    def read_settings(self):
        settings = {}

        settings_names = [
            'appeals', 'bot_name', 'mark_type', 'use_custom_commands',
            'stable_mode'
        ]

        settings = utils.get_settings(settings_names)

        self.settings['appeals'] = []

        for appeal in settings['appeals'].split(':'):
            if appeal:
                self.settings['appeals'].append(appeal.lower())

        self.settings['appeals'] = tuple(self.settings['appeals'])
        self.settings['bot_name'] = settings['bot_name']
        self.settings['mark_type'] = settings['mark_type']
        self.settings['use_custom_commands'] = \
            settings['use_custom_commands'] == 'True'
        self.settings['stable_mode'] = settings['stable_mode'] == 'True'

    def add_mark_to_response(self, rsp):
        if rsp.do_mark and not rsp.sticker:
            if self.settings['mark_type'] == u'имя':
                rsp.text = self.settings['bot_name'] + ' ' + rsp.text
            elif self.settings['mark_type'] == u'кавычка':
                rsp.text += "'"

            else:
                raise Exception('Неизвестный способ отметки сообщения')

        return rsp

    def send_message(self, rsp):
        rsp = self.add_mark_to_response(rsp)

        if len(rsp.text) > VK_MESSAGE_LEN_LIMIT:
            rsp.text = u'Слишком длинный ответ. Не могу отправить'
            rsp = self.add_mark_to_response(rsp)

        msg_id, error = vkr.send_message(rsp.text, rsp.target,
                                         forward=rsp.forward_msg,
                                         attachments=rsp.attachments,
                                         sticker=rsp.sticker)

        if error:
            if error == 'response code 413':
                rsp.text = u'Сообщение слишком длинное для отправки'
            elif 'this sticker is not available' in error:
                rsp.text = u'Стикер (%s) недоступен' % rsp.sticker
            else:
                rsp.text = u'Неизвестная ошибка при отправке сообщения'
                self.send_log_line(
                    'Ошибка при отправке сообщения: %s' % error, 1)

            self.send_message(rsp)
            return

        self.send_log_line(u'[b]Сообщение доставлено (%d)[/b]' % msg_id, 1)

        self.count_last_message_id(msg_id)

    def count_last_message_id(self, mid):
        self.last_message_ids = [mid] + self.last_message_ids[:MAX_LAST_MESSAGES]
        self.reply_count += 1

    # TODO: use execute method to get several {...user_name} in a single request
    def format_response(self, msg, rsp):
        format_dict = {}

        sticker_ids = re.findall('{sticker=(\d+)}', rsp.text)

        if sticker_ids:
            rsp.sticker = random.choice(sticker_ids)

            return rsp

        if '{version}' in rsp.text:
            format_dict['version'] = utils.__version__

        if '{author}' in rsp.text:
            format_dict['author'] = AUTHOR

        if '{time}' in rsp.text:
            format_dict['time'] = time.strftime(
                '%Y-%m-%d %H:%M:%S', time.localtime()
            )

        if '{appeal}' in rsp.text:
            format_dict['appeal'] = random.choice(self.settings['appeals'])

        if '{appeals}' in rsp.text:
            format_dict['appeals'] = '  '.join(self.settings['appeals'])

        if '{plugins}' in rsp.text:
            format_dict['plugins'] = ' '.join(self.pluginmanager.plugin_list)

        if '{builtin_plugins}' in rsp.text:
            format_dict['builtin_plugins'] = \
                ' '.join(self.pluginmanager.builtin_plugin_list)

        if '{custom_plugins}' in rsp.text:
            format_dict['custom_plugins'] = \
                ' '.join(self.pluginmanager.custom_plugin_list)

        if '{bot_name}' in rsp.text:
            format_dict['bot_name'] = self.bot_name

        if '{my_id}' in rsp.text:
            format_dict['my_id'] = msg.self_id

        if '{my_name}' in rsp.text:
            name, error = vkr.get_name_by_id(object_id=msg.self_id)
            format_dict['my_name'] = name if name else 'No name'

        if '{user_id}' in rsp.text:
            format_dict['user_id'] = msg.real_user_id

        if '{user_name}' in rsp.text:
            name, error = vkr.get_name_by_id(object_id=msg.real_user_id)
            format_dict['user_name'] = name if name else 'No name'

        if '{random_user_id}' in rsp.text:
            format_dict['random_user_id'] = msg.get_random_user_id()

        if '{random_user_name}' in rsp.text:
            name, error = \
                vkr.get_name_by_id(object_id=msg.get_random_user_id())
            format_dict['random_user_name'] = name if name else 'No name'

        if '{chat_name}' in rsp.text and msg.from_chat:
            format_dict['chat_name'] = msg.chat_name

        if '{chat_id}' in rsp.text and msg.from_chat:
            format_dict['chat_id'] = msg.chat_id

        if '{event_user_id}' in rsp.text and msg.event_user_id:
            format_dict['event_user_id'] = msg.event_user_id

        if '{event_user_name}' in rsp.text and msg.event_user_id:
            name, error = vkr.get_name_by_id(object_id=msg.event_user_id)
            format_dict['event_user_name'] = name if name else 'No name'

        if '{event_text}' in rsp.text:
            format_dict['event_text'] = msg.event_text

        for r in re.findall('{random(\d{1,500})}', rsp.text):
            format_dict['random%s' % r] = random.randrange(int(r) + 1)

        for match in re.findall('{id(-?\d+)_name}', rsp.text):
            user_id = match
            name, error = vkr.get_name_by_id(object_id=user_id)
            format_dict['id%s_name' % user_id] = name if name else 'No name'

        media_id_search_pattern = re.compile(
            '{attach='
            '(((photo)|(album)|(video)|(audio)|(doc)|(wall)|(market)'
            '|(market_album)|(wall_reply)|(audio_playlist))'
            '-?\d+_\d+(_\d+)?)}'
        )

        for match in media_id_search_pattern.findall(rsp.text):
            if len(rsp.attachments) >= 10:
                break

            attachment_id = match[0]

            if re.match('album\d+_\d+', attachment_id):
                album_id = re.search('album\d+_(\d+)', attachment_id).group(1)
                album_len = vkr.get_album_size(album_id)[0]
                if album_len == 0:
                    rsp.text += u'\nОшибка: пустой альбом!'
                    attachment_id = ''
                else:
                    attachment_id = vkr.get_photo_id(
                                        album_id=album_id,
                                        offset=random.randrange(album_len)
                                        )[0]
            if attachment_id:
                rsp.attachments.append(attachment_id)

        rsp.text = media_id_search_pattern.sub('', rsp.text)
        rsp.text = utils.safe_format(rsp.text, **format_dict)

        return rsp

    def set_new_logger_function(self, func):
        self.send_log_line = func
        self.send_log_line(u'Подключена функция логгирования для ядра бота', 0)

        self.pluginmanager.set_logging_function(func)
        vkr.set_new_logger_function(func)

    def send_log_line(self, line, log_importance, t):
        pass

if __name__ == '__main__':
    # TODO: use core.py directly 
    pass