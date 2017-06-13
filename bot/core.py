# coding:utf8


import time
import re
import math
import random

from threading import Thread

from utils import TOKEN_FILE_PATH, load_custom_commands,\
save_custom_commands, load_blacklist, save_blacklist,\
CUSTOM_COMMAND_OPTONS_COUNT

import vkrequests as vkr

__version__ = '0.0.9dev'
AUTHOR_VK_ID = 180850898
__author__ = 'Eugene Ershov - https://vk.com/id%d' % AUTHOR_VK_ID

__help__ = (
u'''--Страница 0--
Версия: {v}

Обращения к боту: {appeals}

Базовые команды:
-Показывать это сообщение
(помощь|help <?страница=0>) ?
-Написать сообщение
(скажи|say <фраза>)
-Посчитать математическое выражение
(посчитай|calculate <выражение>) =
-Проверить, простое ли число
(простое|prime <число>) %
-Определить достоверность информации
(инфа|chance <вопрос>)
-Выбрать участника беседы
(кто|who <вопрос>)

Автор: {author}

В конце моих сообщений ставится знак верхней кавычки
''',
u'''--Страница 1--

Опциональные команды (доступ ограничивает владелец бота):
-Выучить команду
(выучи|learn <команда>::<ответ>::<?опции=00000>) +
-Забывать команды
(забудь|forgot <команда>::<?ответ>) -
''',
u'''--Страница 2--

Ограниченные команды (доступны только владельцу):
-Игнорировать пользователя (лс), беседу или группу
(blacklist <?-> <?id=id_диалога>)
-Выключить бота
(выйти|exit) !
''',
u'''--Страница 3--

Отладочные команды (доступны только владельцу):

-Спровоцировать ошибку бота
(raise <?сообщение=Default exception text>)
-Поставить бота на паузу (игнорирование сообщений)
(pause <время=5>)
-Быстрая проверка активности бота (доступна всем)
(ping)
''',
u'''--Страница 4--

Закрытые команды (доступны только автору):
-Активировать бота
(activate)
-Деактивировать бота
(deactivate)
''')


class Bot():
    def blacklist(self, cmd, blacklist):
        if not cmd.out:
            return u'Отказано в доступе', blacklist
        if len(cmd.words) == 1:
            chat_id = cmd.chat_id if cmd.chat_id else cmd.user_id
            if cmd.from_chat:
                chat_id += 2000000000
            chat_id = str(chat_id)
            if chat_id in blacklist:
                return u'Данный id уже находится в чёрном списке', blacklist
            else:
                blacklist.append(chat_id)
                save_blacklist(blacklist)
                return u'id {} добавлен в чёрный список'.format(chat_id), blacklist
        else:
            if cmd.words[1] == '-':
                if len(cmd.words) == 2:
                    chat_id = cmd.chat_id if cmd.chat_id else cmd.user_id
                else:
                    if re.match('^\d+$', cmd.words[2]):
                        chat_id = cmd.words[2]
                    else:
                        return u'Неправильно указан id', blacklist
                if cmd.from_chat and chat_id < 2000000000:
                    chat_id = int(chat_id)
                    chat_id += 2000000000
                chat_id = str(chat_id)
                if chat_id not in blacklist:
                    return u'В чёрном списке нет данного id', blacklist
                else:
                    blacklist.remove(chat_id)
                    save_blacklist(blacklist)
                    return u'id {} удалён из чёрного спика'.format(chat_id), blacklist
            else:
                if re.match('\d+', cmd.words[1]):
                    chat_id = cmd.words[1]
                    chat_id = str(chat_id)
                    if chat_id in blacklist:
                        return u'Данный id уже находится в чёрном списке', blacklist
                    else:
                        blacklist.append(chat_id)
                        save_blacklist(blacklist)
                    return u'id {} добавлен в чёрный список'.format(chat_id), blacklist
                else:
                    return u'Неправильно указан id', blacklist

    def pong(self, cmd):
        cmd.forward_msg = None
        return 'pong', cmd

    def help(self, cmd):
        if len(cmd.words) > 1:
            try:
                page = int(cmd.words[1])
            except ValueError:
                return u'Неверно указана страница'
        else:
            page = 0

        if page == -1:
            response_text = '\n'.join(__help__)
        else:
            try:
                response_text = __help__[page]
            except IndexError:
                return u'Такой страницы не существует'

        return response_text.format(v=__version__, author=__author__,
                                    appeals=' '.join(cmd.appeals))

    def say(self, cmd):
        words = cmd.words
        argument_required = self._is_argument_missing(words)
        if argument_required:
            return argument_required

        del words[0]
        text = ' '.join(words)
        return text        

    def calculate(self, cmd):
        words = cmd.words
        argument_required = self._is_argument_missing(words)
        if argument_required:
            return argument_required

        if words[0].startswith('='):
            words[0] = words[0][1:]
        else:
            del words[0]
        words = ''.join(words).lower()
        if not re.match(u'[^\d+\-*/:().,^√πe]', words) or re.match('(sqrt\(.+\))|(pi)', words):
            words = ' ' + words + ' '
            words = re.sub(u'(sqrt)|√', 'math.sqrt', words)
            words = re.sub(u'(pi)|π', 'math.pi', words)
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
                result = str(eval(words))
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
                result = u'Слишком большой результат'
        else:
            result = u'Не математическая операция'
        return result

    def prime(self, cmd):
        words = cmd.words
        argument_required = self._is_argument_missing(words)
        if argument_required:
            return argument_required

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
                    luc_number, last_luc_number = last_luc_number + luc_number, luc_number
                            
            if input_number != 0:
                is_prime = True if (luc_number - 1) % input_number == 0 else False
                result = u'Является простым числом' if is_prime else u'Не является простым числом'
            else:
                result = u'0 не является простым числом'
        else:
            result = u'Дано неверное или слишком большое значение'
        return result

    def chance(self, cmd):
        argument_required = self._is_argument_missing(cmd.words)
        if argument_required:
            return argument_required

        return u'Вероятность ' + str(random.randrange(102)) + '%'

    def who(self, cmd):
        argument_required = self._is_argument_missing(cmd.words)
        if argument_required:
            return argument_required

        if not cmd.from_chat:
            return u'Данная команда работает только в беседе'
        elif len(cmd.chat_users) < 2:
            return u'Для корректной работы команды в беседе должно находиться больше одного человека'
        else:
            user_id = random.choice(cmd.chat_users)
            user_name, error = vkr.get_user_name(user_id=user_id, name_case='acc')
            if user_name:
                return u'Я выбираю [id{}|{}]'.format(str(user_id), user_name)

    def pause(self, cmd):
        if not cmd.out:
            return custom_commands, u'Отказано в доступе'

        if len(cmd.words) == 2:
            delay = float(cmd.words[1])
        else:
            delay = 5
        time.sleep(delay)

        return u'Пауза окончена'

    def learn(self, cmd, custom_commands, protect=True):
        if protect:
            if not cmd.out:
                return custom_commands, u'Отказано в доступе'

        response_text =\
u"""Команда выучена.
Теперь на «{}» я буду отвечать «{}»

Опции:
use_regex: {}
force_unmark: {}
force_forward: {}
appeal_only: {}
disabled: {}"""

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
                    return custom_commands, u'Ошибка при разборе опций'
            else:
                options = [0, 0, 0, 0, 0]

            if options[0] == 0:
                command = command.lower()
        else:
            text = ''

        if argument_required:
            response_text = argument_required
        elif len(text) <2 or not (command and response):
            response_text = u'Неправильный синтаксис команды' 
        elif len(options) != CUSTOM_COMMAND_OPTONS_COUNT:
            response_text = u'Неправильное количество опций'
        elif command in custom_commands.keys() and response\
                in custom_commands[command]:
            response_text = u'Я уже знаю такой ответ'
        elif command in custom_commands.keys():
            custom_commands[command].append([response] + options)
            response_text = response_text.format(command, response, *options)
        else:
            custom_commands[command] = [[response] + options]
            response_text = response_text.format(command, response, *options)

        save_custom_commands(custom_commands)
        return custom_commands, response_text

    def forgot(self, cmd, custom_commands, protect=True):
        if protect:
            if not cmd.out:
                return custom_commands, u'Отказано в доступе'

        response_text = u'Команда забыта'
        words = cmd.words
        argument_required = self._is_argument_missing(words)
        if argument_required:
            return custom_commands, argument_required        

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
            if not command in custom_commands.keys():
                response = ''
            elif len([x for x in custom_commands[command]\
                    if response == x[0]]) == 0:
                response_text = u'В команде «{}» нет ключа «{}»'.format(
                                command.lower(), response
                                )
            else:
                for response_list in custom_commands[command.lower()]:
                    if response_list[0] == response:
                        custom_commands[command].remove(response_list)
                        break
                if len(custom_commands[command]) == 0:
                    custom_commands.pop(command)
                else:
                    response_text = u'Ключ для команды забыт'

        if not response and not custom_commands.pop(command, None):
            response_text = u'Я не знаю такой команды ({})'.format(command)
        
        save_custom_commands(custom_commands)
        return custom_commands, response_text

    def custom_command(self, cmd, custom_commands):
        response_text = ''
        attachments = []

        if not custom_commands:
            return response_text, attachments, cmd

        matched = []
        response = ''
        for key in custom_commands.keys():
            if custom_commands[key][0][1] == 2: # use regex
                pattern = re.compile(key, re.U + re.I)
                if pattern.search(cmd.text):
                    matched.append(key)
            else:
                if cmd.text.lower() in custom_commands.keys():
                    choice = random.choice(custom_commands[cmd.text.lower()])
                    response = choice[0]
                    break

        if matched:
            match = random.choice(matched)
            choice = random.choice(custom_commands[match])
            response = choice[0]

            pattern = re.compile(match, re.U + re.I)
            groupdict = pattern.search(cmd.text).groupdict()
            enterings = pattern.findall(cmd.text)
            if groupdict:
                response = response.format(**groupdict)
            if enterings:
                response = response.format(*enterings)

        if not response:
            return response_text, attachments, cmd

        if choice[5] == 2: # disabled
            return response_text, attachments, cmd

        if choice[4] == 1: # works only with appeal
            if cmd.was_appeal:
                return response_text, attachments, cmd
        elif choice[4] == 2:
            if not cmd.was_appeal:
                return response_text, attachments, cmd

        if choice[3] == 2: # force forward
            cmd.forward_msg = cmd.msg_id
        elif choice[3] == 1:
            cmd.forward_msg = None
            
        if choice[2] == 1: # remove «'»
            cmd.mark_msg = True
        elif choice[2] == 2:
            cmd.mark_msg = False

        if response.startswith('self='):
            cmd.text = '_' + response[5:]
            return self.custom_command(cmd, custom_commands)

        elif response.startswith('attach='):
            media_id = response[7:]
            if re.match('.*((photo)|(album)|(video)|(audio)|(doc)|(wall)|(market))\d+_\d+(_\d+)?$', media_id):
                if re.match('.*album\d+_\d+', media_id):
                    album_id = re.search('album\d+_(\d+)', media_id).group(1)
                    album_len = vkr.get_album_size(album_id)[0]
                    if album_len == 0:
                        response_text = u'Пустой альбом. Невозможно выбрать фото'
                        media_id = ''
                    else:
                        media_id = vkr.get_photo_id(
                                            album_id=album_id,
                                            offset=random.randrange(album_len)
                                            )[0]
                else:
                    media_id = media_id.split('/')[-1] # URGLY # FIXME
                if media_id:
                    attachments.append(media_id)
            else:
                response_text = u'Не могу показать вложение. Неправильная ссылка'
        else:
            response_text = response
        return response_text, attachments, cmd

    def activate_bot(self, cmd, activated):
        if activated:
            return u'Бот уже активирован', True
        elif cmd.from_chat and cmd.user_id == AUTHOR_VK_ID:
            return u'Активация прошла успешно', True
        else:
            return u'Отказано в доступе', False

    def deactivate_bot(self, cmd, activated):
        if cmd.from_chat and cmd.user_id == AUTHOR_VK_ID:
            return u'Деактивация прошла успешно', False
        elif activated:
            return u'Отказано в доступе', True
        else:
            return u'Отказано в доступе', False

    def _is_argument_missing(self, words):
        if len(words) == 1:
            return u'Команду необходимо использовать с аргументом'
        else:
            return False


class Command():
    def __init__(self, SELF_ID, appeals):
        self.SELF_ID = SELF_ID
        self.appeals = appeals
        self.raw_text = u''
        self.text = u''
        self.lower_text = u''
        self.words = [u'']
        self.was_appeal = False
        self.mark_msg = True
        self.from_user = False
        self.from_chat = False
        self.from_group = False
        self.forward_msg = None
        self.user_id = None
        self.chat_id = None
        self.chat_users = []
        self.out = False
        self.msg_id = None

    def load(self, message):
        self.__init__(self.SELF_ID, self.appeals) # refresh params

        self.raw_text = message['body']
        self.text = self.raw_text
        self.lower_text = self.text.lower()

        if self.lower_text.startswith(self.appeals):
            self.text = self.text[len(next(
                a for a in self.appeals if self.lower_text.startswith(a)
            )):]
            if self.text.startswith(' '):
                self.text = self.text[1:]
            self.was_appeal = True
            if self.text.startswith('/'):
                self.text = self.text[1:]
                self.mark_msg = False

        if self.text:
            self.words = self.text.split(' ')
        self.lower_text = self.text.lower()

        self.msg_id = message['id']
        self.user_id = message['user_id']

        if 'chat_id' in message.keys():
            self.from_chat = True
        elif self.user_id < 1:
            self.from_group = True
        else:
            self.from_user = True

        if self.from_chat:
            self.chat_id = message['chat_id']
            self.forward_msg = self.msg_id
            self.chat_users = message['chat_active']

        if self.user_id == self.SELF_ID:
            self.out = 1
        else:
            self.out = message['out']
        

class LongPollSession(Bot):
    def __init__(self):
        self.authorized = False
        self.update_processing = None
        self.run_bot = False
        self.running = False
        self.runtime_error = None
        self.reply_count = 0
        self.custom_commands = None

        self.appeals = ('/')
        self.activated = False
        self.use_custom_commands = False
        self.protect_custom_commands = True

    def authorization(self, login= '', password= '', token='', key='', logout=False):
        authorized = False
        error = None
        if logout:
            open(TOKEN_FILE_PATH, 'w').close()
            self.authorized = False
            return authorized, error

        if not (login and password):
            if token:
                response, error = vkr.log_in(token=token)
                if response and not error:
                    authorized = True
            else:
                try:
                    with open(TOKEN_FILE_PATH, 'r') as token_file:
                        lines = token_file.readlines()
                        if lines:
                            token = lines[0][:-1]
                except:
                    token = None
                    open(TOKEN_FILE_PATH, 'w').close()

                if token:
                    response, error = vkr.log_in(token=token)
                    if response and not error:
                        authorized = True
                        if error:
                            if 'invalid access_token' in error:
                                open(TOKEN_FILE_PATH, 'w').close()
        else:
            new_token, error = vkr.log_in(login=login, password=password, key=key)
            if new_token and not error:
                with open(TOKEN_FILE_PATH, 'w') as token_file:
                    token_file.write('{}\n{}'.format(\
                        new_token, 'НИКОМУ НЕ ПОКАЗЫВАЙТЕ СОДЕРЖИМОЕ ЭТОГО ФАЙЛА'
                        )
                    )
                authorized = True
            elif self.authorized:
                return authorized, error

        self.authorized = authorized
        return authorized, error

    def _process_updates(self):
        try:
            if not self.authorized: raise Exception('Not authorized')               

            self.black_list = load_blacklist()

            SELF_ID = vkr.get_self_id()[0]
            command = Command(SELF_ID, self.appeals)

            mlpd = None
            last_msg_ids = [0, 0, 0, 0, 0]
            response_text = ''
            custom_response = ''
            attachments = []
            self.runtime_error = None
            self.running = True

            print('@LAUNCHED')
            while self.run_bot:
                if not mlpd:
                    mlpd, error = vkr.get_message_long_poll_data()
                    if error:
                        raise Exception(error)

                updates, error = vkr.get_message_updates(ts=mlpd['ts'],
                	                                        pts=mlpd['pts'])
                
                if updates:
                    history = updates[0]
                    mlpd['pts'] = updates[1]
                    messages = updates[2]
                elif 'connection' in error or 'too many request' in error:
                    error = None
                    time.sleep(1)
                    continue
                else:
                    raise Exception(error)

                response_str = str(updates)
                # if u'emoji' in messages.keys():
                #     print(response_str)
                # else:
                #     print(response_str.decode('unicode-escape').encode('utf8'))

                for message in messages['items']:
                    command.load(message)
                    if not command.text or command.msg_id in last_msg_ids:
                        continue

                    blacklisted = False
                    if command.was_appeal and re.match(u'^blacklist$', command.words[0].lower()):
                        response_text, self.black_list = self.blacklist(command, self.black_list)
                    elif str(command.user_id) in self.black_list\
                            or (command.chat_id and str(command.chat_id + 2000000000)\
                                in self.black_list):
                        blacklisted = True

                    if command.was_appeal and not blacklisted and not response_text:
                        if re.match('ping$', command.lower_text):
                            response_text, command = self.pong(command)

                        elif re.match(u'((help)|(помощь)|\?)$',\
                                command.words[0].lower()):
                            response_text = self.help(command)

                        elif re.match(u'((скажи)|(say))$', command.words[0].lower()):
                            response_text = self.say(command)

                        elif re.match(u'((посчитай)|(calculate)|=)$', command.words[0].lower()):
                            response_text = self.calculate(command)    

                        elif re.match(u'((простое)|(prime)|%)$', command.words[0].lower()):
                            response_text = self.prime(command)

                        elif re.match(u'((инфа)|(chance)),?$', command.words[0].lower()):
                            response_text = self.chance(command)

                        elif re.match(u'((кто)|(кого)|(who)|(whom))$', command.words[0].lower()):
                            response_text = self.who(command)

                        elif re.match(u'((выучи)|(learn)|\+)$', command.words[0].lower()):
                            self.custom_commands, response_text = self.learn(
                                command,
                                self.custom_commands,
                                protect=self.protect_custom_commands
                                )

                        elif re.match(u'((забудь)|(forgot)|\-)$', command.words[0].lower()):
                            self.custom_commands, response_text = self.forgot(
                                command,
                                self.custom_commands,
                                protect=self.protect_custom_commands
                                )
                            
                        elif re.match(u'((выйти)|(exit)|\!)$',\
                                command.lower_text):
                            response_text = self._stop_bot_from_message(command)

                        elif command.words[0].lower() == 'pause':
                            mlpd = None
                            response_text = self.pause(command)

                        elif command.lower_text == 'activate':
                            response_text, self.activated = self.activate_bot(command, self.activated)

                        elif command.lower_text == 'deactivate':
                            response_text, self.activated = self.deactivate_bot(command, self.activated)

                        elif command.words[0].lower() == 'raise':
                            response_text = self._raise_debug_exception(command)

                        else:
                            response_text =\
                                u'Неизвестная команда. Вы можете использовать {}help для получения списка команд.'.format(
                                    random.choice(self.appeals))
                            if self.use_custom_commands:
                                custom_response, attachments, command=\
                                    self.custom_command(command, self.custom_commands)

                    elif self.use_custom_commands\
                            and self.custom_commands is not None\
                            and not blacklisted:
                        custom_response, attachments, command =\
                            self.custom_command(command, self.custom_commands)

                    if custom_response or attachments:
                        response_text = custom_response

                    if not (response_text or attachments):
                        continue

                    if not self.activated:
                        response_text +=\
                            u'\n\nБот не активирован. По вопросам активации просьба обратиться к автору: %s' % __author__

                    if command.mark_msg:
                        response_text += "'"

                    user_id = None
                    chat_id = None
                    if command.from_chat:
                        chat_id = command.chat_id
                    else:
                        user_id = command.user_id

                    message_to_resend = command.forward_msg
                    msg_id, error = vkr.send_message(
                                        text = response_text,
                                        uid = user_id,
                                        gid = chat_id,
                                        forward = message_to_resend,
                                        attachments = attachments
                                        )
                    if error:
                        raise Exception(error)

                    response_text = ''
                    attachments = []
                    custom_response = ''
                    self.reply_count += 1
                    last_msg_ids = last_msg_ids[1:] + [msg_id]
                time.sleep(2)
        except:
            if not 'traceback' in globals():
                import traceback
            self.runtime_error = traceback.format_exc()
            self.run_bot = False

        self.running = False
        self.reply_count = 0
        print('@STOPPED')

    def launch_bot(self):
        self.run_bot = True

        self.update_processing = Thread(target=self._process_updates)
        self.update_processing.start()

        while not self.running:
            time.sleep(0.1)
            if self.runtime_error:
                raise Exception(self.runtime_error)
        return True

    def stop_bot(self):
        self.run_bot = False

        while self.running: continue
        self.update_processing = None
        return True, self.activated

    def load_params(self, appeals, activated,
                    use_custom_commands,
                    protect_custom_commands):
        if use_custom_commands:
            self.custom_commands = load_custom_commands()

        appeals = appeals.split(':')
        _appeals = []
        for appeal in appeals:
            if appeal and not re.match('^\s+$', appeal):
                _appeals.append(appeal.lower())

        if _appeals:
            self.appeals = tuple(_appeals)

        self.activated = activated
        self.use_custom_commands = use_custom_commands
        self.protect_custom_commands = protect_custom_commands
        return True

    def _stop_bot_from_message(self, command):
        if command.out:
            self.run_bot = False
            self.runtime_error = 1
            return u'Завершаю работу'
        else:
            return u'Отказано в доступе'

    def _raise_debug_exception(self, command):
        if command.out:
            words = command.words
            del words[0]
            if not words:
                exception_text = 'Default exception text'
            else:
                exception_text = ' '.join(words)
            raise Exception(exception_text)
        else:
            return u'Отказано в доступе'
