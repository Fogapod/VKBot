# coding:utf8


import time
import re
import math
import random

from threading import Thread

import requests as r

from utils import TOKEN_FILE_PATH, load_custom_commands, \
save_custom_commands, load_whitelist, save_whitelist, \
load_blacklist, save_blacklist, CUSTOM_COMMAND_OPTIONS_COUNT

import vkrequests as vkr

__version__ = '0.1.0dev'
AUTHOR_VK_ID = 180850898
__author__ = 'Eugene Ershov - https://vk.com/id%d' % AUTHOR_VK_ID

__help__ = (
u'''
--Страница 0--
	
Версия: {version}

Обращения к боту: {appeals}

Открытые команды:
Необходимый уровень доступа: 0

-Показывать это сообщение (?)
(помощь|help) <?страница=0>
-Написать сообщение
(скажи|say) <фраза>
-Посчитать математическое выражение (=)
(посчитай|calculate) <выражение>
-Проверить, простое ли число (%)
(простое|prime) <число>
-Определить достоверность информации
(инфа|chance) <вопрос>
-Выбрать участника беседы
(кто|who) <вопрос>
-Сообщить информацию о погоде
погода|weather <?город=город со страницы или Москва>|-
-Быстрая проверка активности бота
ping
-Игнорировать пользователя
(ignore|игнор)

Автор: {author}''',
u'''
--Страница 1--

Базовые команды:
Необходимый уровень доступа: 1

-Выучить команду (+)
(выучи|learn) <команда>::<ответ>::<?опции=00000>
-Забыть команду (-)
(забудь|forgot) <команда>::<?ответ>''',
u'''
--Страница 2--

Ограниченные команды:
Необходимый уровень доступа: 2

-Игнорировать пользователя (лс), беседу или группу
blacklist <?+|-> <?id> <?reason:причина>
-Перезапустить бота (применение команд и настроек)
restart''',
u'''
--Страница 3--

Защищённые команды:
Необходимый уровень доступа: 3

-Выключить бота (!)
stop
-Изменить уровень доступа пользователя
whitelist <?id пользователя> <?уровень доступа=1>
-Спровоцировать ошибку бота
raise <?сообщение=Default exception text>
-Поставить бота на паузу (игнорирование сообщений)
pause <время (секунды)=5>''',
u'''
--Страница 4--

Закрытые команды:
Необходимый уровень доступа: нет, только для автора

-Активировать бота
activate
-Деактивировать бота
deactivate'''
)


def safe_format(s, *args, **kwargs):
    '''
    https://stackoverflow.com/questions/9955715/python-missing-arguments-in-string-formatting-lazy-eval
    '''

    while True:
        try:
            return s.format(*args, **kwargs)
        except KeyError as e:
            e=e.args[0]
            kwargs[e] = '{%s}' % e
        except:
            return s


class Command(object):
    def __init__(self, SELF_ID, appeals):
        self.SELF_ID = SELF_ID
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
        self.msg_id = 0

    def load(self, message):
        self.__init__(self.SELF_ID, self.appeals) # refresh params

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

        if self.user_id == self.SELF_ID:
            self.out = 1
        else:
            self.out = message['out']

        if 'chat_id' in message.keys():
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
                self.event = message.get('action')
                if self.event:
                    if self.event == 'chat_photo_update':
                        self.event = 'photo updated'
                    elif self.event == 'chat_photo_remove':
                        self.event = 'photo removed'
                    elif self.event == 'chat_create':
                        self.event = 'chat created'
                    elif self.event == 'chat_title_update':
                        self.event = 'title updated'
                    elif self.event == 'chat_invite_user' \
                            and not message['action_mid'] == self.SELF_ID:
                        self.event = 'user joined'
                        self.event_user_id = message['action_mid']
                    elif self.event == 'chat_kick_user' \
                        and not message['action_mid'] == self.SELF_ID:
                        self.event = 'user kicked'
                        self.event_user_id = message['action_mid']
                    else:
                        self.event = None

                if self.event:
                    self.raw_text = 'event=' + self.event
                    self.text = self.raw_text
                    self.lower_text = self.raw_text

        if self.from_user:
            if self.out:
                self.real_user_id = self.SELF_ID


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
        self.mark_type = 'кавычка'
        self.activated = False
        self.use_custom_commands = False
        self.openweathermap_api_key = '0'
        
        self.help_access_level = 0
        self.say_access_level = 0
        self.calculate_access_level = 0
        self.prime_access_level = 0
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
        self.activate_access_level = 0
        self.deactivate_access_level = 0

    def authorization(self, login= '', password= '', token='', logout=False):
        self.authorized, error = \
            vkr.log_in(login=login, password=password, logout=logout)

        return self.authorized, error

    def process_updates(self):
        try:
            if not self.authorized:
                raise Exception('Not authorized')

            SELF_ID = vkr.get_self_id()[0]
            command = Command(SELF_ID, self.appeals)

            last_msg_ids = []
            max_last_msg_ids = 30

            self.mlpd = None
            self.runtime_error = None
            self.running = True

            self.whitelist = load_whitelist()
            self.blacklist = load_blacklist()

            while self.run_bot:
                if not self.mlpd:
                    self.mlpd, error = vkr.get_message_long_poll_data()
                    if error:
                        raise Exception(error)

                updates, error = \
                    vkr.get_message_updates(ts=self.mlpd['ts'], pts=self.mlpd['pts'])
                
                if updates:
                    history = updates[0]
                    self.mlpd['pts'] = updates[1]
                    messages = updates[2]
                elif 'connection' in error:
                    error = None
                    time.sleep(3)
                    continue
                else:
                    raise Exception(error)

                for message in messages['items']:
                    user_access_level = 0
                    response_text = ''
                    attachments = []

                    command.load(message)

                    if not command.text or command.msg_id in last_msg_ids:
                        continue

                    if (command.real_user_id in self.blacklist.keys() \
                            or command.chat_id in self.blacklist.keys()) \
                            and not (command.was_appeal and command.words[0] == 'blacklist'):
                        continue

                    if self.use_custom_commands \
                            and self.custom_commands is not None:
                        response_text, command = \
                            self.custom_command(command, self.custom_commands)

                    if not response_text and command.was_appeal:
                        func, required_access_level = self.builtin_command(command.words[0].lower())
                        if func:
                            if command.out:
                                user_access_level = 3
                            elif command.real_user_id in self.whitelist.keys():
                                user_access_level = self.whitelist[command.real_user_id]
                            if user_access_level < required_access_level:
                                response_text = u'Для использования команды необходим уровень доступа: %d. Ваш уровень доступа: %d' % (required_access_level, user_access_level)
                            else:
                                response_text, command = func(command)
                        else:
                            response_text = \
                                u'Неизвестная команда. Вы можете использоват' \
                                u'ь {appeal} help для получения списка команд.'

                    if re.match('\s*$', response_text):
                        response_text = ''
                        continue

                    if not self.activated:
                        response_text += \
                            u'\n\nБот не активирован. По вопросам активации ' \
                            u'просьба обратиться к автору: {author}'

                    response_text, attachments = self._format_response(
                        response_text, command, attachments
                    )

                    if command.mark_msg:
                        if self.mark_type == u'имя':
                            response_text = self.bot_name + ' ' + response_text
                        elif self.mark_type == u'кавычка':
                            response_text += "'"
                        else:
                            raise Exception('Wrong mark type')

                    user_id = None
                    chat_id = None

                    if command.from_chat:
                        chat_id = command.chat_id
                    else:
                        user_id = command.user_id

                    message_to_resend = command.forward_msg
                    msg_id, error = \
                        vkr.send_message(text = response_text,
                                         uid = user_id,
                                         gid = chat_id,
                                         forward = message_to_resend,
                                         attachments = attachments
                                        )
                    if error:
                        if error == 'captcha needed':
                            ctime.sleep(5)
                        elif error == 'response code 413':
                            pass # message too long # TODO
                        else:
                            raise Exception(error)

                    self.reply_count += 1

                    if len(last_msg_ids) >= max_last_msg_ids:
                        last_msg_ids = last_msg_ids[1:]
                    last_msg_ids.append(msg_id)

                    time.sleep(1)
                time.sleep(2)
        except:
            import traceback
            self.runtime_error = traceback.format_exc()
            self.run_bot = False

        self.running = False
        self.reply_count = 0

    def launch_bot(self):
        self.run_bot = True
        self.bot_thread = Thread(target=self.process_updates)
        self.bot_thread.start()

        while not self.running:
            time.sleep(0.1)
            if self.runtime_error:
                raise Exception(self.runtime_error)
        return True

    def stop_bot(self):
        self.run_bot = False
        self.bot_thread.join()

        return True

    def load_params(self, appeals, activated,
                    bot_name, mark_type,
                    use_custom_commands,
                    openweathermap_api_key):
        if use_custom_commands:
            self.custom_commands = load_custom_commands()

        appeals = appeals.split(':')
        _appeals = []
        for appeal in appeals:
            if appeal and not re.match('\s+$', appeal):
                _appeals.append(appeal.lower())

        if _appeals:
            self.appeals = tuple(_appeals)

        self.activated = activated
        self.bot_name = bot_name
        self.mark_type = mark_type
        self.use_custom_commands = use_custom_commands
        self.openweathermap_api_key = openweathermap_api_key

        return True

    def _format_response(self, response_text, command, attachments):
        format_dict = {}

        random_ranges = re.findall('{random(\d{1,500})}', response_text)
        for r in random_ranges:
            format_dict['random%s' %r] = random.randrange(int(r) + 1)

        if '{version}' in response_text:
            format_dict['version'] = __version__
        if '{author}' in response_text:
            format_dict['author'] = __author__
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
        if '{my_name}' in response_text:
            name, error = vkr.get_name_by_id(object_id=command.SELF_ID)
            format_dict['my_name'] = name if name else 'No name'
        if '{my_id}' in response_text:
            format_dict['my_id'] = command.SELF_ID
        if '{user_name}' in response_text:
            name, error = vkr.get_name_by_id(object_id=command.real_user_id)
            format_dict['user_name'] = name if name else 'No name'
        if '{user_id}' in response_text:
            format_dict['user_id'] = command.real_user_id
        if '{random_user_name}' in response_text:
            name, error = vkr.get_name_by_id(object_id=command.random_chat_user_id)
            format_dict['random_user_name'] = name if name else 'No name'
        if '{random_user_id}' in response_text:
            format_dict['random_user_id'] = command.random_chat_user_id
        if '{chat_name}' in response_text and command.from_chat:
            format_dict['chat_name'] = command.chat_name
        if '{event_user_id}' in response_text and command.event_user_id:
            format_dict['event_user_id'] = command.event_user_id
        if '{event_user_name}' in response_text and command.event_user_id:
            name, error = vkr.get_name_by_id(object_id=command.event_user_id)
            format_dict['event_user_name'] = name if name else 'No name'

        for match in re.findall('{id(-?\d+)_name}', response_text):
            user_id = match
            name, error = vkr.get_name_by_id(object_id=user_id)
            format_dict['id%s_name' % user_id] = name if name else 'No name'

        media_id_search_pattern = re.compile(
            '{attach=.*?(((photo)|(album)|(video)|(audio)|(doc)|(wall)|(market))'
            '-?\d+_\d+(_\d+)?)}'
        )

        for match in media_id_search_pattern.findall(response_text):
            if len(attachments) >= 10: break

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
        
        return safe_format(response_text, **format_dict), attachments

    def custom_command(self, cmd, custom_commands):
        response_text = ''

        if not custom_commands:
            return response_text, cmd

        response = ''
        for key in random.sample(custom_commands.keys(), \
        	       len(custom_commands.keys())):
            if custom_commands[key][0][1] == 2: # use regex
                pattern = re.compile(key, re.U + re.I)
                if pattern.search(cmd.text):
                    for resp in random.sample(custom_commands[key], \
                            len(custom_commands[key])):
                        if resp[5] == 2:
                            continue
                        else:
                            choice = resp
                            response = choice[0]
                    if response:
                        groups = pattern.findall(cmd.text)
                        groupdict = pattern.search(cmd.text).groupdict()
                        response = safe_format(response, *groups, **groupdict)
                        break

            elif cmd.text.lower() == key:
                for resp in random.sample(custom_commands[key], \
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

        if choice[4] == 1: # works only WITHOUT appeal
            if cmd.was_appeal:
                return response_text, cmd
        elif choice[4] == 2: # works only WITH appeal
            if not cmd.was_appeal:
                return response_text, cmd

        if choice[3] == 2: # force forward
            cmd.forward_msg = cmd.msg_id
        elif choice[3] == 1: # never forward
            cmd.forward_msg = None
            
        if choice[2] == 1: # always mark message
            cmd.mark_msg = True
        elif choice[2] == 2: # never mark message
            cmd.mark_msg = False

        if response.startswith('self='):
            cmd.text = '_' + response[5:]

            return self.custom_command(cmd, custom_commands)
        elif response == 'pass':
            pass
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
        elif s in ('prime', u'простое', '%'):
            return self.prime, self.prime_access_level
        elif s in ('chance', u'инфа'):
            return self.chance, self.chance_access_level
        elif s in ('who', u'кто'):
            return self.who, self.who_access_level
        elif s in ('weather', u'погода'):
            return self.weather, self.weather_access_level
        elif s in ('ping'):
            return self.pong, self.pong_access_level
        elif s in ('ignore', u'игнор'):
            return self.ignore, self.ignore_access_level
        elif s in ('learn', u'выучи', '+'):
            return self.learn, self.learn_access_level
        elif s in ('forgot', u'забудь', '-'):
            return self.forgot, self.forgot_access_level
        elif s in ('blacklist'):
            return self.blacklist_command, self.blacklist_access_level
        elif s in ('restart'):
            return self.restart, self.restart_access_level
        elif s in ('stop', '!'):
            return self.stop_bot_from_message, self.stop_access_level
        elif s in ('whitelist'):
            return self.whitelist_command, self.whitelist_access_level
        elif s in ('raise'):
            return self.raise_exception, self.raise_access_level
        elif s in ('pause'):
            return self.pause, self.pause_access_level
        elif s in ('activate'):
            return self.activate_bot, self.activate_access_level
        elif s in ('deactivate'):
            return self.deactivate_bot, self.deactivate_access_level
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

        del words[0]
        text = ' '.join(words)
        return text, cmd

    def calculate(self, cmd):
        words = cmd.words
        argument_required = self._is_argument_missing(words)
        if argument_required:
            return argument_required, cmd

        if words[0].startswith('='):
            words[0] = words[0][1:]
        else:
            del words[0]
        words = ''.join(words).lower()
        if re.match(u'^([\d+\-*/%:().,^√πe]|(sqrt)|(pi))+$', words):
            words = ' ' + words + ' '
            words = re.sub(u'(sqrt)|√', 'math.sqrt', words)
            words = re.sub(u'(pi)|π', 'math.pi', words)
            words = re.sub('e', 'math.e', words)
            words = re.sub('\^', '**', words)
            words = re.sub(',', '.', words)
            words = re.sub(u':|÷', '/', words)
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

    def prime(self, cmd):
        words = cmd.words
        argument_required = self._is_argument_missing(words)
        if argument_required:
            return argument_required, cmd

        del words[0]
        input_number = ''.join(words)
        if re.match('^\d+$', input_number) and len(input_number)<=5:
            input_number = int(input_number)
            luc_number = 0
            last_luc_number = 0
            for i in range(input_number):
                if luc_number == 0:
                    luc_number = 1
                elif luc_number == 1:
                    last_luc_number = luc_number
                    luc_number = 3
                else:
                    luc_number, last_luc_number = last_luc_number\
                                                  + luc_number, luc_number
                            
            if input_number != 0:
                is_prime = True if (luc_number - 1) \
                                % input_number == 0 else False
                result = u'Является простым числом' \
                    if is_prime else u'Не является простым числом'
            else:
                result = u'0 не является простым числом'
        else:
            result = u'Дано неверное или слишком большое значение'
        return result, cmd

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
                user_id=cmd.random_chat_user_id, name_case='acc')
            if user_name:
                return u'Я выбираю [id%d|%s]' % (cmd.random_chat_user_id, user_name), cmd

    def weather(self, cmd):
        api_key = self.openweathermap_api_key
        api_key_not_confirmed = \
u'''
Команда не может функционировать. Для её активации необходим специальный ключ:
ИНСТРУКЦИЯ_ПО_ПОЛУЧЕНИЮ_КЛЮЧА

Скопируйте полученный ключ и повторите команду, добавив его, чтобы получилось
/погода 9ld10763q10b2cc882a4a10fg90fc974

[id{my_id}|НИКОМУ НЕ ПОКАЗЫВАЙТЕ ДАННЫЙ КЛЮЧ, ИНАЧЕ РИСКУЕТЕ ЕГО ПОТЕРЯТЬ!]'''

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
                return api_key_not_confirmed, cmd

            city, error = vkr.get_user_city(user_id=cmd.real_user_id)
            if not city:
                city = u'Москва'

        url = u'http://api.openweathermap.org/data/2.5/weather?APPID={api_key}&lang=ru&q={city}&units=metric'
        url = url.format(api_key=api_key, city=city)

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

        weather_response = \
u'''
Погода для: {city} ({country})

Состояние погоды: {description}
Температура: {temp}°C
Облачность: {cloud}%
Влажность: {humidity}%
Давление: {pressure} hPa
Прошло с момента последнего измерения: {time_since_calculation}'''.format(
    **format_dict)

        return weather_response, cmd

    def _verify_openweathermap_api_key(self, cmd):
        api_key = cmd.words[1]

        test_url = 'https://api.openweathermap.org/data/2.5/weather?APPID=%s' % api_key
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
        save_blacklist(self.blacklist)

        return u'id %s добавлен в чёрный список по собственному желанию' % user_id, cmd

    def learn(self, cmd):
        if self.custom_commands is None:
            return u'Пользовательские команды отключены или повреждены', cmd

        response_text = \
u'''Команда выучена.
Теперь на «{}» я буду отвечать «{}»

Опции:
use_regex: {}
force_unmark: {}
force_forward: {}
appeal_only: {}
disabled: {}'''

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
        elif len(text) < 2 or not (command and response):
            response_text = u'Неправильный синтаксис команды' 
        elif len(options) != CUSTOM_COMMAND_OPTIONS_COUNT:
            response_text = u'Неправильное количество опций'
        elif command in self.custom_commands.keys() \
                and response in self.custom_commands[command]:
            response_text = u'Я уже знаю такой ответ'
        elif command in self.custom_commands.keys():
            updated_commands = []

            if options[0] == 2: # use_regex
                for r in self.custom_commands[command]:
                    r[1] = 2
                    updated_commands.append(r)
            else:
                for r in self.custom_commands[command]:
                    r[1] = 0
                    updated_commands.append(r)

            self.custom_commands[command] = updated_commands

            self.custom_commands[command].append([response] + options)
            response_text = response_text.format(command, response, *options)
        else:
            self.custom_commands[command] = [[response] + options]
            response_text = response_text.format(command, response, *options)

        save_custom_commands(self.custom_commands)
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

        if command and response:
            if not command in self.custom_commands.keys():
                response = ''
            elif len([x for x in self.custom_commands[command]\
                    if response == x[0]]) == 0:
                response_text = u'В команде «%s» нет ключа «%s»' \
                                            % (command.lower(), response)
            else:
                for response_list in self.custom_commands[command.lower()]:
                    if response_list[0] == response:
                        self.custom_commands[command].remove(response_list)
                        break
                if len(self.custom_commands[command]) == 0:
                    self.custom_commands.pop(command)
                else:
                    response_text = u'Ключ для команды забыт'

        if not response and not self.custom_commands.pop(command, None):
            response_text = u'Я не знаю такой команды (%s)' % command
        
        save_custom_commands(self.custom_commands)
        return response_text, cmd

    def blacklist_command(self, cmd):
        if len(cmd.words) == 1:
            if not self.blacklist:
                response = u'Список пуст'
            else:
                response = ''
                for i, uid in enumerate(self.blacklist.keys()):
                    response += u'%d. {id%d_name} (%d) Причина: %s\n' % (i+1, uid, uid, self.blacklist[uid])
                response = response[:-1]
            return response, cmd
        else:
            if cmd.words[1] == '+':
                blacklist_reason = ''

                if len(cmd.words) == 2:
                    chat_id = cmd.chat_id if cmd.from_chat else cmd.user_id
                else:
                    blacklist_reason = re.search(u'.*?((причина)|(reason)):(.*)', cmd.lower_text)
                    if blacklist_reason:
                        blacklist_reason = blacklist_reason.group(4)
                        if len(cmd.words) == 3:
                            chat_id = cmd.chat_id if cmd.from_chat else cmd.user_id
                        else:
                            if cmd.words[2].lower().startswith(('reason:', u'причина')):
                                chat_id = cmd.chat_id if cmd.from_chat else cmd.user_id
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
                save_blacklist(self.blacklist)

                return u'id %s добавлен в список по причине: %s' % (chat_id, blacklist_reason), cmd

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

                if chat_id not in self.blacklist.keys():
                    return u'В списке нет данного id', cmd

                self.blacklist.pop(chat_id)
                save_blacklist(self.blacklist)

                return u'id %s удалён из списка' % chat_id, cmd

            else:
                return u'Неизвестная опция', cmd

    def restart(self, cmd):
        if cmd.out:
            self.need_restart = True
            return u'Начинаю перезагрузку', cmd

    def stop_bot_from_message(self, cmd):
        if cmd.out:
            self.run_bot = False
            self.runtime_error = 1
            return u'Завершаю работу', cmd

    def whitelist_command(self, cmd):
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
            if user_id in self.whitelist.keys():
                self.whitelist.pop(user_id)
        else:
            self.whitelist[user_id] = access_level

        save_whitelist(self.whitelist)

        return u'Теперь {id%s_name} имеет доступ %d' \
            % (user_id, access_level), cmd

    def raise_exception(self, cmd):
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

        time.sleep(delay)
        self.mlpd = None

        return u'Пауза окончена', cmd

    def activate_bot(self, cmd):
        if cmd.real_user_id == AUTHOR_VK_ID:
            self.activated = True
            return u'Активация прошла успешно', cmd
        else:
            return u'Отказано в доступе', cmd

    def deactivate_bot(self, cmd):
        if cmd.real_user_id == AUTHOR_VK_ID:
            self.activated = False
            return u'Деактивация прошла успешно', cmd
        else:
            return u'Отказано в доступе', cmd

    def _is_argument_missing(self, words):
        if len(words) == 1:
            return u'Команду необходимо использовать с аргументом'
        else:
            return False
