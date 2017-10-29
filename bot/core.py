# coding:utf8


import time
import re
import math
import random
import traceback

from threading import Thread

import requests as r

import utils
import vkrequests as vkr


AUTHOR_VK_ID = 180850898
AUTHOR = u'[id%d|Евгений Ершов]' % AUTHOR_VK_ID

__help__ = (
    (
        u'--Страница 0--\n\n'
        u'Версия: {version}\n\n'
        u'Обращения к боту: {appeals}\n\n'
        u'Открытые команды:\n'
        u'Необходимый уровень доступа: 0\n\n'
        u'-Показывать это сообщение (?)\n'
        u'(помощь|help) <?страница=0>\n'
        u'-Написать сообщение\n'
        u'(скажи|say) <фраза>\n'
        u'-Посчитать математическое выражение (=)\n'
        u'(посчитай|calculate) <выражение>\n'
        u'-Поиск информации\n'
        u'(найди|find) <запрос>\n'
        u'-Определить достоверность утверждения (%)\n'
        u'(инфа|chance) <вопрос>\n'
        u'-Выбрать участника беседы\n'
        u'(кто|who) <вопрос>\n'
        u'-Сообщить информацию о погоде\n'
        u'(погода|weather) <?город=город со страницы или Москва>|-\n'
        u'-Быстрая проверка активности бота\n'
        u'(пинг|ping)\n'
        u'-Игнорировать пользователя\n'
        u'(игнор|ignore)\n\n'
        u'Автор: {author}'
    ),
    (
        u'\n--Страница 1--\n\n'
        u'Базовые команды:\n'
        u'Необходимый уровень доступа: 1\n\n'
        u'-Выучить команду (+)\n'
        u'(выучи|learn) <команда>::<ответ>::<?опции=00000>\n'
        u'-Забыть команду (-)\n'
        u'(забудь|forgot) <команда>::<?ответ>'
    ),
    (
        u'\n--Страница 2--\n\n'
        u'Ограниченные команды:\n'
        u'Необходимый уровень доступа: 2\n\n'
        u'-Игнорировать пользователя (лс), беседу или группу\n'
        u'(чс|blacklist) <?+|-> <?id> <?reason:причина>\n'
        u'-Перезапустить бота (применение команд и настроек)\n'
        u'перезапуск|restart)'
    ),
    (
        u'--Страница 3--\n\n'
        u'Защищённые команды:\n'
        u'Необходимый уровень доступа: 3\n\n'
        u'-Выключить бота (!)\n'
        u'(стоп|stop)\n'
        u'-Изменить уровень доступа пользователя\n'
        u'(вайтлист|whitelist) <?id пользователя> <?уровень доступа=1>\n'
        u'Спровоцировать ошибку бота\n'
        u'raise <?сообщение=Default exception text>\n'
        u'-Поставить бота на паузу (игнорирование сообщений)\n'
        u'(пауза|pause) <время (секунды)=5>'
    )
)


class Command(object):
    def __init__(self, self_id, appeals):
        self.self_id = self_id
        self.appeals = appeals
        self.raw_text = ''
        self.text = ''
        self.lower_text = ''
        self.words = ['']
        self.was_appeal = False
        self.mark_msg = True
        self.from_user = False
        self.from_chat = False
        self.from_group = False
        self.forward_msg = None
        self.user_id = 0
        self.real_user_id = 0
        self.chat_id = 0
        self.chat_users = []
        self.random_chat_user_id = 0
        self.chat_name = ''
        self.out = False
        self.event = None
        self.event_user_id = 0
        self.event_text = ''
        self.msg_id = 0
        self._pass = False

    def read(self, message):
        self.__init__(self.self_id, self.appeals)  # refresh params

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
                a for a in self.appeals if self.lower_text.startswith(a)
            )):]
            if self.text.startswith(' '):
                self.text = self.text[1:]

        if self.text:
            self.words = self.text.split(' ')
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
            self.forward_msg = self.msg_id
            self.chat_users = message['chat_active']
            if self.chat_users:
                self.random_chat_user_id = random.choice(self.chat_users)
            self.chat_name = message['title']

            if not self.raw_text:
                event = message.get('action')

                if event:
                    if event == 'chat_photo_update':
                        self.event = 'photo updated'

                    elif event == 'chat_photo_remove':
                        self.event = 'photo removed'

                    elif event == 'chat_create':
                        self.event = 'chat created'

                    elif event == 'chat_title_update':
                        self.event = 'title updated'

                    elif event == 'chat_invite_user' \
                            and not message.get('action_mid') == self.self_id:
                        self.event = 'user joined'

                    elif event == 'chat_kick_user' and not \
                            message['action_mid'] == self.self_id:
                        self.event = 'user kicked'

                    elif event == 'chat_pin_message':
                        self.event = 'message pinned'

                    elif event == 'chat_unpin_message':
                        self.event = 'message unpinned'

                if self.event:
                    self.event_user_id = message.get('action_mid',  '')
                    self.event_text    = message.get('action_text', '')

                    self.raw_text = 'event=' + self.event
                    self.text = self.raw_text
                    self.lower_text = self.raw_text

        else:
            self.random_chat_user_id = \
                random.choice((self.self_id, self.user_id))

        if self.from_user:
            if self.out:
                self.real_user_id = self.self_id


class Bot(object):
    def __init__(self):
        self.authorized = False
        self.mlpd = None
        self.need_restart = False
        self.bot_thread = None
        self.run_bot = False
        self.running = False
        self.runtime_error = None
        self.reply_count = 0

        self.custom_commands = {}
        self.whitelist = {}
        self.blacklist = []

        self.appeals = ('/')
        self.bot_name = u'(Бот)'
        self.mark_type = u'кавычка'
        self.use_custom_commands = False
        self.openweathermap_api_key = '0'

        self.help_access_level = 0
        self.say_access_level = 0
        self.calculate_access_level = 0
        self.find_access_level = 0
        self.chance_access_level = 0
        self.who_access_level = 0
        self.weather_access_level = 0
        self.pong_access_level = 0
        self.ignore_access_level = 0
        self.learn_access_level = 1
        self.forgot_access_level = 1
        self.blacklist_access_level = 2
        self.restart_access_level = 2
        self.stop_access_level = 3
        self.whitelist_access_level = 3
        self.raise_access_level = 3
        self.pause_access_level = 3

    def authorization(self, **kwargs):
        self.authorized, error = vkr.log_in(**kwargs)

        return self.authorized, error

    def process_updates(self):
        self.running = True

        try:
            if not self.authorized:
                raise Exception('Не авторизован')

            self.send_log_line(u'Инициализация переменных бота...', 0)
            self_id, error = vkr.get_self_id()
            command = Command(self_id, self.appeals)

            last_msg_ids = []
            max_last_msg_ids = 30

            self.runtime_error = None

            self.send_log_line(
                u'Загрузка файла whitelist\'а из {whitelist_file}...',
                0
            )
            self.whitelist = utils.load_whitelist()

            self.send_log_line(
                u'Загрузка файла blacklist\'а из {blacklist_file}...',
                0
            )
            self.blacklist = utils.load_blacklist()

            if self.use_custom_commands:
                self.send_log_line(
                    u'Загрузка пользовательских команд из '
                    u'{custom_commands_file}...',
                    0
                )
                self.custom_commands = utils.load_custom_commands()

            while self.run_bot:
                if not self.mlpd:
                    self.mlpd, error = vkr.get_message_long_poll_data()

                updates, error = vkr.get_message_updates(
                    ts=self.mlpd['ts'],
                    pts=self.mlpd['pts']
                )

                if updates:
                    history = updates[0]
                    self.mlpd['pts'] = updates[1]
                    messages = updates[2]
                    self.send_log_line(
                        u'Получено сообщений: %d' % messages['count'],
                        0
                    )
                else:
                    raise Exception(error)

                for message in messages['items']:
                    user_access_level = 0
                    response_text = ''
                    attachments = []

                    command.read(message)

                    if not command.text or command.msg_id in last_msg_ids:
                        continue

                    if (command.real_user_id in self.blacklist.keys() or
                            command.chat_id in self.blacklist.keys()) and not (
                                command.was_appeal and
                                command.words[0] == 'blacklist'
                            ):
                        continue

                    if command.words[0] not in \
                        ('+', 'learn', u'выучи', '-', 'forgot', u'забудь') \
                            and self.use_custom_commands \
                            and self.custom_commands is not None:
                        response_text, command = \
                            self.custom_command(command, self.custom_commands)

                    if command._pass:
                        continue

                    if command.was_appeal and not response_text:
                        func, required_access_level = \
                            self.builtin_command(command.words[0].lower())

                        if func:
                            if command.out:
                                user_access_level = 3
                            elif command.real_user_id in self.whitelist:
                                user_access_level = \
                                    self.whitelist[command.real_user_id]
                            if user_access_level < required_access_level:
                                response_text = u'Для использования команды ' \
                                    u'необходим уровень доступа: %d. Ваш уро' \
                                    u'вень доступа: %d' % \
                                    (required_access_level, user_access_level)
                            else:
                                response_text, command = func(command)
                        else:
                            response_text = \
                                u'Неизвестная команда. Вы можете использоват' \
                                u'ь {appeal} help для получения списка команд.'

                    if re.match('\s*$', response_text):
                        response_text = ''
                        continue

                    response_text, attachments, sticker_id = \
                        self._format_response(
                            response_text, command, attachments
                        )

                    if command.mark_msg:
                        if self.mark_type == u'имя':
                            response_text = self.bot_name + ' ' + response_text
                        elif self.mark_type == u'кавычка':
                            response_text += "'"
                        else:
                            raise Exception(
                                'Неизвестный способ отметки сообщения'
                            )

                    user_id = None
                    chat_id = None

                    if command.from_chat:
                        chat_id = command.chat_id
                    else:
                        user_id = command.user_id

                    message_to_resend = command.forward_msg
                    msg_id, error = vkr.send_message(
                                                     text=response_text,
                                                     uid=user_id,
                                                     gid=chat_id,
                                                     forward=message_to_resend,
                                                     attachments=attachments,
                                                     sticker_id=sticker_id
                                                    )
                    if error:
                        if error == 'response code 413':
                            self.send_log_line(
                                u'Сообщение слишком длинное для отправки',
                                # u'Разделяю сообщение', # TODO
                                2
                            )
                            continue
                        elif 'this sticker is not available' in error:
                            self.send_log_line(
                                u'Стикер (%d) недоступен! Не могу отправить'
                                u' сообщение' % sticker_id, 1
                            )
                        else:
                            self.send_log_line(
                                u'Неизвестная ошибка при отправке сообщения',
                                1
                            )
                            raise Exception(error)
                        continue

                    self.send_log_line(
                        u'[b]Сообщение доставлено (%d)[/b]' % msg_id,
                        1
                    )

                    self.reply_count += 1

                    if len(last_msg_ids) >= max_last_msg_ids:
                        last_msg_ids = last_msg_ids[1:]
                    last_msg_ids.append(msg_id)

                    time.sleep(1)
                time.sleep(3)
        except:
            self.send_log_line(u'Ошибка бота перехвачена', 0)
            self.runtime_error = traceback.format_exc()
            self.run_bot = False

        self.running = False

    def launch_bot(self):
        self.run_bot = True
        self.send_log_line(
            u'Создание отдельного потока для бота...', 0, time.time()
        )
        self.bot_thread = Thread(target=self.process_updates)
        self.send_log_line(u'Запуск потока...', 0, time.time())
        self.bot_thread.start()

        while not self.running:
            time.sleep(0.01)
            if self.runtime_error:
                raise Exception(self.runtime_error)

        self.send_log_line(
            u'Отдельный поток бота запущен и работает', 1, time.time()
        )
        return True

    def stop_bot(self):
        self.send_log_line(u'Остановка потока...', 0, time.time())
        self.run_bot = False
        if self.bot_thread:
            self.bot_thread.join()

        self.send_log_line(u'Отдельный поток бота отключён', 1, time.time())
        return True

    def load_params(self, appeals,
                    bot_name, mark_type,
                    use_custom_commands,
                    openweathermap_api_key):

        appeals = appeals.split(':')
        _appeals = []
        for appeal in appeals:
            if appeal and not re.match('\s+$', appeal):
                _appeals.append(appeal.lower())

        if _appeals:
            self.appeals = tuple(_appeals)

        self.bot_name = bot_name
        self.mark_type = mark_type
        self.use_custom_commands = use_custom_commands
        self.openweathermap_api_key = openweathermap_api_key

        return True

    def _format_response(self, response_text, command, attachments):
        format_dict = {}

        sticker_ids = re.findall('{sticker=(\d+)}', response_text)
        if sticker_ids:
            return '', [], random.choice(sticker_ids)

        if '{version}' in response_text:
            format_dict['version'] = utils.__version__

        if '{author}' in response_text:
            format_dict['author'] = AUTHOR

        if '{time}' in response_text:
            format_dict['time'] = time.strftime(
                '%Y-%m-%d %H:%M:%S', time.localtime()
            )

        if '{appeal}' in response_text:
            format_dict['appeal'] = random.choice(self.appeals)

        if '{appeals}' in response_text:
            format_dict['appeals'] = '  '.join(self.appeals)

        if '{bot_name}' in response_text:
            format_dict['bot_name'] = self.bot_name

        if '{my_id}' in response_text:
            format_dict['my_id'] = command.self_id

        if '{my_name}' in response_text:
            name, error = vkr.get_name_by_id(object_id=command.self_id)
            format_dict['my_name'] = name if name else 'No name'

        if '{user_id}' in response_text:
            format_dict['user_id'] = command.real_user_id

        if '{user_name}' in response_text:
            name, error = vkr.get_name_by_id(object_id=command.real_user_id)
            format_dict['user_name'] = name if name else 'No name'

        if '{random_user_id}' in response_text:
            format_dict['random_user_id'] = command.random_chat_user_id

        if '{random_user_name}' in response_text:
            name, error = \
                vkr.get_name_by_id(object_id=command.random_chat_user_id)
            format_dict['random_user_name'] = name if name else 'No name'

        if '{chat_name}' in response_text and command.from_chat:
            format_dict['chat_name'] = command.chat_name

        if '{event_user_id}' in response_text and command.event_user_id:
            format_dict['event_user_id'] = command.event_user_id

        if '{event_user_name}' in response_text and command.event_user_id:
            name, error = vkr.get_name_by_id(object_id=command.event_user_id)
            format_dict['event_user_name'] = name if name else 'No name'

        if '{event_text}' in response_text:
            format_dict['event_text'] = command.event_text

        for r in re.findall('{random(\d{1,500})}', response_text):
            format_dict['random%s' % r] = random.randrange(int(r) + 1)

        for match in re.findall('{id(-?\d+)_name}', response_text):
            user_id = match
            name, error = vkr.get_name_by_id(object_id=user_id)
            format_dict['id%s_name' % user_id] = name if name else 'No name'

        media_id_search_pattern = re.compile(
            '{attach=.*?'
            '(((photo)|(album)|(video)|(audio)|(doc)|(wall)|(market))'
            '-?\d+_\d+(_\d+)?)}'
        )

        for match in media_id_search_pattern.findall(response_text):
            if len(attachments) >= 10:
                break

            attachment_id = match[0]

            if re.match('album\d+_\d+', attachment_id):
                album_id = re.search('album\d+_(\d+)', attachment_id).group(1)
                album_len = vkr.get_album_size(album_id)[0]
                if album_len == 0:
                    response_text = u'Пустой альбом. Невозможно выбрать фото'
                    attachment_id = ''
                else:
                    attachment_id = vkr.get_photo_id(
                                        album_id=album_id,
                                        offset=random.randrange(album_len)
                                        )[0]
            if attachment_id:
                attachments.append(attachment_id)

        response_text = media_id_search_pattern.sub('', response_text)

        return utils.safe_format(response_text, **format_dict), attachments, None

    def custom_command(self, cmd, custom_commands):
        response_text = ''

        if not custom_commands:
            return response_text, cmd

        response = ''
        for key in random.sample(
                                 custom_commands.keys(),
                                 len(custom_commands.keys())):

            if custom_commands[key][0][1] == 2:  # use regex
                pattern = re.compile(key, re.U + re.I)
                if pattern.search(cmd.text):
                    for resp in random.sample(
                                              custom_commands[key],
                                              len(custom_commands[key])):
                        if resp[5] == 2:
                            continue
                        else:
                            choice = resp
                            response = choice[0]
                    if response:
                        groups = pattern.findall(cmd.text)
                        groupdict = pattern.search(cmd.text).groupdict()
                        response = utils.safe_format(response, *groups, **groupdict)
                        break

            elif cmd.text.lower() == key:
                for resp in random.sample(
                                          custom_commands[key],
                                          len(custom_commands[key])):
                    if resp[5] == 2:
                        continue
                    else:
                        choice = resp
                        response = choice[0]
                if response:
                    break

        if not response:
            return response_text, cmd

        if choice[4] == 1:  # works only WITHOUT appeal
            if cmd.was_appeal:
                return response_text, cmd
        elif choice[4] == 2:  # works only WITH appeal
            if not cmd.was_appeal:
                return response_text, cmd

        if choice[3] == 2:  # force forward
            cmd.forward_msg = cmd.msg_id
        elif choice[3] == 1:  # never forward
            cmd.forward_msg = None

        if choice[2] == 2:  # do not mark message
            cmd.mark_msg = False

        if response.startswith('self='):
            cmd.text = '_' + response[5:]

            return self.custom_command(cmd, custom_commands)

        elif response == 'pass':
            cmd._pass = True

        else:
            response_text = response

        return response_text, cmd

    def builtin_command(self, s):
        if s in ('help', u'помощь', '?'):
            return self.help, self.help_access_level
        elif s in ('say', u'скажи'):
            return self.say, self.say_access_level
        elif s in ('calculate', u'посчитай', '='):
            return self.calculate, self.calculate_access_level
        elif s in ('find', u'найди'):
            return self.find, self.find_access_level
        elif s in ('chance', u'инфа', '%'):
            return self.chance, self.chance_access_level
        elif s in ('who', u'кто'):
            return self.who, self.who_access_level
        elif s in ('weather', u'погода'):
            return self.weather, self.weather_access_level
        elif s in ('ping', u'пинг'):
            return self.pong, self.pong_access_level
        elif s in ('ignore', u'игнор'):
            return self.ignore, self.ignore_access_level
        elif s in ('learn', u'выучи', '+'):
            return self.learn, self.learn_access_level
        elif s in ('forgot', u'забудь', '-'):
            return self.forgot, self.forgot_access_level
        elif s in ('blacklist', u'чс'):
            return self.blacklist_command, self.blacklist_access_level
        elif s in ('restart', u'перезапуск'):
            return self.restart, self.restart_access_level
        elif s in ('stop', u'стоп', '!'):
            return self.stop_bot_from_message, self.stop_access_level
        elif s in ('whitelist', u'вайтлист'):
            return self.whitelist_command, self.whitelist_access_level
        elif s in ('raise'):
            return self.raise_exception, self.raise_access_level
        elif s in ('pause', u'пауза'):
            return self.pause, self.pause_access_level
        else:
            return None, None

    def help(self, cmd):
        if len(cmd.words) > 1:
            try:
                page = int(cmd.words[1])
            except ValueError:
                return u'Неверно указана страница', cmd
        else:
            page = 0

        if page == -1:
            response_text = '\n\n'.join(__help__)
        else:
            try:
                response_text = __help__[page]
            except IndexError:
                return u'Такой страницы не существует', cmd

        return response_text, cmd

    def say(self, cmd):
        words = cmd.words
        argument_required = self._is_argument_missing(words)
        if argument_required:
            return argument_required, cmd

        text = ' '.join(words[1:])
        return text, cmd

    def calculate(self, cmd):
        words = cmd.words
        argument_required = self._is_argument_missing(words)
        if argument_required:
            return argument_required, cmd


        words = ''.join(words[1:]).lower()

        if re.match(u'^([\d+\-*/%:().,^√πe]|(sqrt)|(pi))+$', words):
            words = ' ' + words + ' '
            words = re.sub(u'(sqrt)|√', 'math.sqrt', words)
            words = re.sub(u'(pi)|π',   'math.pi',   words)
            words = re.sub(u':|÷',      '/',         words)
            words = re.sub('e',         'math.e',    words)
            words = re.sub('\^',        '**',        words)
            words = re.sub(',',         '.',         words)

            while True:
                if '/' in words:
                    index = re.search('[^.\d]\d+[^.\de]', words)
                    if index:
                        index = index.end() - 1
                        words = words[:index] + '.' + words[index:]
                    else:
                        break
                else:
                    break
            try:
                result = eval(words)
            except SyntaxError:
                result = u'Ошибка [0]'
            except NameError:
                result = u'Ошибка [1]'
            except AttributeError:
                result = u'Ошибка [2]'
            except TypeError:
                result = u'Ошибка [3]'
            except ZeroDivisionError:
                result = u'Деление на 0'
            except OverflowError:
                result = 'Infinite'
            else:
                if type(result) not in (int, long, float):
                    result = u'Не математическая операция'
                else:
                    result = str(result)
        else:
            result = u'Не математическая операция'

        return result, cmd

    def find(self, cmd):
        words = cmd.words
        argument_required = self._is_argument_missing(words)
        if argument_required:
            return argument_required, cmd

        response, error = vkr.http_r_g(
            'http://api.duckduckgo.com/?',
            params = {
                    'q': ' '.join(cmd.words[1:]),
                    'o': 'json'
            }
        )

        if error:
            self.send_log_line(u'Ошибка при получении ответа: ' + error, 0)
            return u'Возникла ошибка', cmd

        response = response.json()

        if 'RelatedTopics' in response:
            topics = response['RelatedTopics']

            if len(topics) > 0 and 'Text' in topics[0]:
                text = u'ФУНКЦИЯ В РАЗРАБОТКЕ\n\n' + topics[0]['Text']

                if 'Icon' in topics[0]:
                    image_url = topics[0]['Icon']['URL']

                    text += '\n\n' + 'Image url: ' + image_url + ' '

                return text, cmd

        return u'ФУНКЦИЯ В РАЗРАБОТКЕ\n\nНичего не найдено :/', cmd

    def chance(self, cmd):
        argument_required = self._is_argument_missing(cmd.words)
        if argument_required:
            return argument_required, cmd

        return u'Вероятность ' + str(random.randrange(102)) + '%', cmd

    def who(self, cmd):
        argument_required = self._is_argument_missing(cmd.words)
        if argument_required:
            return argument_required, cmd

        if not cmd.from_chat:
            return u'Данная команда работает только в беседе', cmd
        elif len(cmd.chat_users) < 2:
            return u'Для корректной работы команды, в беседе должно находить' \
                   u'ся больше одного человека', cmd
        else:
            user_name, error = vkr.get_name_by_id(
                object_id=cmd.random_chat_user_id, name_case='acc')
            if user_name:
                return u'Я выбираю [id%d|%s]' \
                    % (cmd.random_chat_user_id, user_name), cmd

    def weather(self, cmd):
        api_key = self.openweathermap_api_key
        api_key_not_confirmed_text = (
            u'Команда не может функционировать. '
            u'Для её активации необходим специальный ключ:\n'
            u'https://github.com/Fogapod/VKBot/blob/master/README.md#openweathermap\n'
            u'Скопируйте полученный ключ и повторите команду, добавив его, '
            u'чтобы получилось\n/погода 9ld10763q10b2cc882a4a10fg90fc974\n\n'
            u'[id{my_id}|НИКОМУ НЕ ПОКАЗЫВАЙТЕ ДАННЫЙ КЛЮЧ, ИНАЧЕ РИСКУЕТЕ ЕГО ПОТЕРЯТЬ!]'
        )

        if len(cmd.words) > 1:
            if ' '.join(cmd.words[1:]) == '-':
                self.openweathermap_api_key = '0'
                return u'Ключ сброшен', cmd

            if api_key == '0':
                if self._verify_openweathermap_api_key(cmd):
                    self.openweathermap_api_key = cmd.words[1]
                    return u'Ключ подтверждён', cmd
                else:
                    return u'Неверный ключ (%s)' % cmd.words[1], cmd

            city = ' '.join(cmd.words[1:])
        else:
            if api_key == '0':
                return api_key_not_confirmed_text, cmd

            city, error = vkr.get_user_city(user_id=cmd.real_user_id)
            if not city:
                city = u'Москва'

        url = (
            u'http://api.openweathermap.org/data/2.5/weather?'
            u'APPID={api_key}&'
            u'lang=ru&'
            u'q={city}&'
            u'units=metric'
            ).format(api_key=api_key, city=city)

        weather_data = r.get(url)
        weather_json = weather_data.json()

        if 'cod' in weather_json and weather_json['cod'] == '404':
            return u'Город не найден (%s)' % city, cmd

        format_dict = {}
        format_dict['city'] = city
        format_dict['country'] = weather_json['sys']['country']
        format_dict.update(weather_json['main'])
        format_dict.update(weather_json['weather'][0])
        format_dict['temp'] = round(format_dict['temp'], 1)
        format_dict['temp'] = format_dict['temp']
        format_dict['cloud'] = weather_json['clouds']['all']
        format_dict['time_since_calculation'] = time.strftime(
            '%H:%M:%S', time.gmtime(time.time() - weather_json['dt'])
        )

        weather_response = (
            u'Погода для: {city} ({country})\n\n'
            u'Состояние погоды: {description}\n'
            u'Температура: {temp}°C\n'
            u'Облачность: {cloud}%\n'
            u'Влажность: {humidity}%\n'
            u'Давление: {pressure} hPa\n'
            u'Прошло с момента последнего измерения: {time_since_calculation}'
        ).format(**format_dict)

        return weather_response, cmd

    def _verify_openweathermap_api_key(self, cmd):
        api_key = cmd.words[1]

        test_url = 'https://api.openweathermap.org/data/2.5/weather?APPID=%s' \
            % api_key
        test_weather_json = r.get(test_url).json()

        if 'cod' in test_weather_json:
            if test_weather_json['cod'] == '401':
                return False
            elif test_weather_json['cod'] == '400':
                return True

    def pong(self, cmd):
        cmd.forward_msg = None

        return 'pong', cmd

    def ignore(self, cmd):
        user_id = cmd.real_user_id
        self.blacklist[user_id] = u'По собственному желанию'

        utils.save_blacklist(self.blacklist)

        return u'id %s добавлен в чёрный список по собственному желанию' \
            % user_id, cmd

    def learn(self, cmd):
        if self.custom_commands is None:
            return u'Пользовательские команды отключены или повреждены', cmd

        response_text = (
            u'Команда выучена.'
            u'Теперь на «{}» я буду отвечать «{}»\n\n'
            u'Опции:\n'
            u'use_regex: {}\n'
            u'force_unmark: {}\n'
            u'force_forward: {}\n'
            u'appeal_only: {}\n'
            u'disabled: {}\n'
        )

        words = cmd.words
        argument_required = self._is_argument_missing(words)

        del words[0]
        text = ' '.join(words)
        if '::' in text:
            text = text.split('::')
            command = text[0]
            response = text[1]
            if len(text) == 3 and text[2]:
                try:
                    options = map(lambda x: int(x), text[2])
                except:
                    return u'Ошибка при разборе опций', cmd
            else:
                options = [0, 0, 0, 0, 0]

            if options[0] == 0:
                command = command.lower()
        else:
            text = ''

        if argument_required:
            response_text = argument_required
        elif len(text) < 2 or not command:
            response_text = u'Неправильный синтаксис команды'
        elif len(options) != utils.CUSTOM_COMMAND_OPTIONS_COUNT:
            response_text = u'Неправильное количество опций'
        elif command in self.custom_commands.keys() \
                and response in self.custom_commands[command]:
            response_text = u'Я уже знаю такой ответ'
        elif command in self.custom_commands:
            # update regex option for all responses
            for r in self.custom_commands[command]:
                r[1] = options[0] if options[0] in (0, 2) else 0

            self.custom_commands[command].append([response] + options)
            response_text = response_text.format(command, response, *options)
        else:
            self.custom_commands[command] = [[response] + options]
            response_text = response_text.format(command, response, *options)

        self.send_log_line(u'Пользовательские команды сохраняются...', 0)
        utils.save_custom_commands(self.custom_commands)
        self.send_log_line(u'Пользовательские команды сохранены', 1)

        return response_text, cmd

    def forgot(self, cmd):
        if self.custom_commands is None:
            return u'Пользовательские команды отключены или повреждены', cmd

        response_text = u'Команда забыта'
        words = cmd.words
        argument_required = self._is_argument_missing(words)
        if argument_required:
            return argument_required, cmd

        del words[0]
        text = ' '.join(words)
        if '::' in text:
            text = text.split('::')
            command = text[0]
            response = text[1]
        else:
            command = text
            response = ''

        if command:
            if command not in self.custom_commands:
                response = None
            elif len([x for x in self.custom_commands[command]
                     if response == x[0]]) == 0:
                response_text = u'В команде «%s» нет ключа «%s»' \
                                            % (command, response)
            else:
                for response_list in self.custom_commands[command]:
                    if response_list[0] == response:
                        self.custom_commands[command].remove(response_list)
                        break
                if len(self.custom_commands[command]) == 0:
                    self.custom_commands.pop(command)
                else:
                    response_text = u'Ключ для команды забыт'

        if response is None and self.custom_commands.pop(command, None) is None:
            response_text = u'Я не знаю такой команды (%s)' % command

        self.send_log_line(u'Пользовательские команды сохраняются...', 0)
        utils.save_custom_commands(self.custom_commands)
        self.send_log_line(u'Пользовательские команды сохранены', 1)

        return response_text, cmd

    def blacklist_command(self, cmd):
        if len(cmd.words) == 1:
            if not self.blacklist:
                response = u'Список пуст'
            else:
                response = ''
                for i, uid in enumerate(self.blacklist.keys()):
                    response += u'%d. {id%d_name} (%d): %s\n' \
                                % (i+1, uid, uid, self.blacklist[uid])
                response = response[:-1]
            return response, cmd
        else:
            if cmd.words[1] == '+':
                blacklist_reason = ''

                if len(cmd.words) == 2:
                    chat_id = cmd.chat_id if cmd.from_chat else cmd.user_id
                else:
                    blacklist_reason = re.search(
                        u'.*?((причина)|(reason)):((.|\n)+)', cmd.text, re.I)

                    if blacklist_reason:
                        blacklist_reason = blacklist_reason.group(4)
                        if len(cmd.words) == 3:
                            chat_id = \
                                cmd.chat_id if cmd.from_chat else cmd.user_id
                        else:
                            if cmd.words[2].lower().startswith(
                                    ('reason:', u'причина')):
                                chat_id = cmd.chat_id if cmd.from_chat \
                                    else cmd.user_id
                            else:
                                chat_id = cmd.words[2]
                    else:
                        chat_id = cmd.words[2]

                    if not (type(chat_id) is int or re.match('\d+$', chat_id)):
                        chat_id, error = vkr.get_real_user_id(chat_id)
                        if not chat_id and '113' in error:
                            return u'Неправильно указан id', cmd
                    else:
                        chat_id = int(chat_id)

                if not blacklist_reason:
                    blacklist_reason = u'Причина не указана'
                self.blacklist[chat_id] = blacklist_reason
                utils.save_blacklist(self.blacklist)

                self.send_log_line(
                    u'id %s добавлен в чёрный список по причине: %s'
                    % (chat_id, blacklist_reason), 1)

                return u'id %s добавлен в список по причине: %s' \
                    % (chat_id, blacklist_reason), cmd

            elif cmd.words[1] == '-':
                if len(cmd.words) == 2:
                    chat_id = cmd.chat_id if cmd.from_chat else cmd.user_id
                else:
                    chat_id = cmd.words[2]
                    if not re.match('-?\d+$', chat_id):
                        chat_id, error = vkr.get_real_user_id(chat_id)
                        if not chat_id and '113' in error:
                            return u'Неправильно указан id', cmd
                    else:
                        chat_id = int(chat_id)

                if chat_id not in self.blacklist:
                    return u'В списке нет данного id', cmd

                self.blacklist.pop(chat_id)
                utils.save_blacklist(self.blacklist)

                self.send_log_line(
                    u'id %s удалён из чёрного списка' % chat_id, 1
                )
                return u'id %s удалён из списка' % chat_id, cmd

            else:
                return u'Неизвестная опция', cmd

    def restart(self, cmd):
        self.send_log_line(u'Вызов функции перезагрузки', 0)
        self.need_restart = True
        return u'Начинаю перезагрузку', cmd

    def stop_bot_from_message(self, cmd):
        self.send_log_line(u'Вызов функции остановки', 0)
        self.run_bot = False
        self.runtime_error = 1
        return u'Завершаю работу', cmd

    def whitelist_command(self, cmd):
        self.send_log_line(u'Вызов функции whitelist', 0)
        default_access_level = 1

        if len(cmd.words) == 1:
            if len(self.whitelist.keys()) == 0:
                response = u'Список пуст'
            else:
                response = ''
                for i, uid in enumerate(self.whitelist.keys()):
                    response += u'%d. {id%d_name} (%d) Доступ: %d\n' \
                        % (i+1, uid, uid, self.whitelist[uid])
                response = response[:-1]
            return response, cmd

        user_id = cmd.words[1]
        if not re.match('\d+$', user_id):
            user_id, error = vkr.get_real_user_id(user_id)
            if not user_id and '113' in error:
                return u'Указан неверный id пользователя', cmd

        user_id = int(user_id)

        if len(cmd.words) == 2:
            access_level = default_access_level
        else:
            access_level = cmd.words[2]
            if not re.match('\d+$', access_level) \
                    or int(access_level) not in range(4):
                return u'Указан неверный уровень доступа', cmd
            else:
                access_level = int(access_level)

        if access_level == 0:
            if user_id in self.whitelist:
                self.whitelist.pop(user_id)
        else:
            self.whitelist[user_id] = access_level

        utils.save_whitelist(self.whitelist)

        self.send_log_line(
            u'[b]id %s добавлен в whitelist. Доступ: %d[/b]'
            % (user_id, access_level), 2)

        return u'Теперь {id%s_name} имеет доступ %d' \
            % (user_id, access_level), cmd

    def raise_exception(self, cmd):
        self.send_log_line(u'Вызов искуственной ошибки', 1)
        if cmd.out:
            words = cmd.words
            del words[0]
            if not words:
                exception_text = 'Default exception text'
            else:
                exception_text = ' '.join(words)
            raise Exception(exception_text)

    def pause(self, cmd):
        if len(cmd.words) == 2:
            if re.match('\d+(\.\d+)?$', cmd.words[1]):
                delay = float(cmd.words[1])
            else:
                return u'Неправильный аргумент', cmd
        else:
            delay = 5

        self.send_log_line(u'Начало паузы длиной в (%s) секунд' % delay, 1)
        time.sleep(delay)
        self.send_log_line(u'Окончание паузы длиной в (%s) секунд' % delay, 1)
        self.mlpd = None

        return u'Пауза окончена', cmd

    def _is_argument_missing(self, words):
        if len(words) == 1:
            return u'Команду необходимо использовать с аргументом'
        else:
            return False

    def set_new_logger_function(self, func):
        self.send_log_line = func
        self.send_log_line(
            u'Подключена функция логгирования для ядра бота', 0)
        vkr.set_new_logger_function(func)
        self.send_log_line(
            u'Подключена функция логгирования для vkrequests', 0)

    def send_log_line(self, line, log_importance, t):
        pass
